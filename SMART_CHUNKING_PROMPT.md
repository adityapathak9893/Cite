# Prompt for Claude Code: AI-Powered Intelligent Document Chunking

Copy everything below this line into Claude Code:

---

## TASK: Replace the dumb fixed-character chunking with AI-powered intelligent chunking

### THE PROBLEM

Currently, `app/services/chunking.py` splits documents at every ~2000 characters with 200 character overlap. This causes two critical problems:

1. **Topics split across chunks.** A section like "Anti-Bribery Policy" (150 words) gets embedded inside a larger chunk that also contains "Conflict of Interest" and "Confidentiality". The chunk embedding becomes a diluted average of all 3 topics. When a user searches for "anti-bribery", the similarity score is low because "bribery" is a tiny fraction of the chunk's total text.

2. **No document overview chunk.** When a user asks "What are the main topics covered?", no single chunk contains a summary of the entire document. Every chunk is about a specific section, so vector search finds nothing similar to a meta-question about the document's structure.

### THE SOLUTION: 3-step intelligent chunking pipeline

Replace the current chunking with a 3-step process that uses an AI call (Claude) during document processing to understand the document structure BEFORE chunking.

### STEP 1: Find where the files are

First, read and understand these existing files completely before making ANY changes:

- `backend/app/services/chunking.py` — current dumb chunking logic (REPLACE this)
- `backend/app/services/extraction.py` — text extraction from PDF/TXT/MD
- `backend/app/services/embedding.py` — OpenAI embedding generation
- `backend/app/services/claude.py` — Claude API calls (currently used for chat, we'll add a new function)
- `backend/app/services/rag.py` — vector search and prompt assembly
- `backend/app/routers/documents.py` — document upload and background processing pipeline
- `backend/app/config.py` — env vars and settings

Understand the full processing flow: upload → extract text → chunk → embed → store in document_chunks table.

### STEP 2: Modify `backend/app/services/chunking.py`

Replace the entire chunking logic. The new `chunk_document()` function should:

#### 2A: AI-powered section detection

Create an async function `identify_sections(text: str) -> list[dict]` that:

1. Takes the full extracted text of the document
2. Sends it to Claude (claude-sonnet-4-5-20250929) with this system prompt:

```
You are a document structure analyzer. Your job is to identify the logical sections in the document text provided.

Rules:
- Identify every distinct section, subsection, and topic boundary
- A "section" is a self-contained unit about ONE topic (a policy, a procedure, a definition, etc.)
- Return the EXACT start and end character positions for each section
- Each section should be between 200-3000 characters. If a section is longer than 3000 characters, split it into logical sub-sections
- If a section is shorter than 200 characters, merge it with the adjacent section that is most topically related
- Preserve complete paragraphs — never split mid-paragraph
- Include a short title (max 10 words) describing what each section is about

Respond with ONLY a JSON array, no other text:
[
  {"title": "Section title here", "start": 0, "end": 1523},
  {"title": "Next section title", "start": 1524, "end": 3201},
  ...
]

The character positions must be exact — they will be used to slice the original text. The end of one section should be the start of the next (no gaps, no overlaps).
```

3. Parse the JSON response
4. Extract each section from the original text using the character positions
5. If the AI call fails (timeout, malformed JSON, etc.), fall back to the current dumb chunking (split at ~2000 chars with 200 overlap) — NEVER let the whole processing pipeline fail because of this
6. Handle edge case: if the document is very short (< 500 characters), just return it as a single chunk

**Important cost consideration:** For large documents (> 50,000 characters), don't send the ENTIRE text to Claude. Instead, send the first 30,000 characters and ask Claude to identify sections in that portion. Then for the remaining text, use a simpler heuristic: split at double-newlines (\n\n) or heading patterns (lines starting with numbers like "4.2" or all-caps lines). This keeps API costs reasonable.

#### 2B: Generate document summary chunk

Create an async function `generate_summary(sections: list[dict]) -> str` that:

1. Takes the list of section titles and first 100 characters of each section
2. Sends to Claude with this prompt:

```
Below are the sections found in a document. Write a comprehensive 150-200 word summary of what this document covers. List ALL the main topics. This summary will be used to answer questions like "What is this document about?" and "What topics are covered?"

Sections:
{formatted list of section titles}
```

3. Returns the summary text
4. This summary will be stored as chunk_index 0 (the first chunk) with metadata: `{"is_summary": true, "title": "Document Overview"}`
5. If the AI call fails, generate a basic summary by concatenating all section titles: "This document covers: [title 1], [title 2], [title 3]..."

#### 2C: Generate per-chunk search description

Create an async function `generate_chunk_descriptions(sections: list[dict]) -> list[str]` that:

1. Takes all sections with their content
2. For EACH section, generate a one-line search-friendly description
3. Do this in a SINGLE Claude API call to minimize cost. Send all section titles and first 150 chars to Claude with:

```
For each section below, write a one-line search description (max 100 characters) that someone would use to find this section. Focus on specific keywords, not generic descriptions.

Sections:
1. "Welcome to Acme Corporation" — "Welcome to Acme Corporation! Since our founding in 1995..."
2. "Anti-Harassment & Anti-Discrimination Policy" — "Acme Corporation is firmly committed to maintaining..."
...

Respond with ONLY a JSON array of descriptions in the same order:
["description 1", "description 2", ...]
```

4. These descriptions will be stored in the chunk's metadata as `{"search_description": "..."}` and will be used to improve retrieval
5. If the AI call fails, use the section title as the description

#### 2D: Main function signature

```python
async def chunk_document(text: str, file_name: str) -> list[dict]:
    """
    Intelligently chunks a document using AI-powered section detection.
    
    Returns list of dicts:
    [
        {
            "content": "full chunk text...",
            "chunk_index": 0,
            "metadata": {
                "title": "Document Overview",
                "is_summary": true,
                "search_description": "Overview of all topics in the document",
                "file_name": "Agreement.pdf"
            }
        },
        {
            "content": "Section 4.5: Anti-Bribery Policy...",
            "chunk_index": 1,
            "metadata": {
                "title": "Anti-Bribery & Anti-Corruption Policy",
                "is_summary": false,
                "search_description": "anti-bribery FCPA corruption gift policy reporting",
                "file_name": "Agreement.pdf"
            }
        },
        ...
    ]
    """
```

### STEP 3: Modify `backend/app/services/rag.py` — Improve retrieval

Update the search to use the new metadata:

1. When searching for chunks, ALSO search against the `search_description` field in metadata. The approach:
   - Currently you embed the user question and search against chunk content embeddings
   - Now, when storing embeddings, create a COMBINED text for embedding: `"{search_description}\n\n{content}"` — this way the embedding captures both the description keywords and the full content
   - This means the embedding is generated from the combined text, not just the raw content

2. Increase `match_count` from 3 back to 5. With better chunking, 5 results will be more precise because each chunk is now a coherent topic.

3. Keep the threshold at 0.5 (first pass), fallback to 0.3 if fewer than 2 results. The AI-chunked sections should have better similarity scores naturally.

### STEP 4: Modify `backend/app/services/claude.py` — Better citation prompt

Update the system prompt for chat responses. Find the current system prompt and update it to:

```
You are a helpful document assistant. Answer questions using ONLY the document excerpts provided below.

Rules:
1. If an excerpt directly answers the question, cite it using [Source: filename, Section N] format
2. ONLY cite excerpts that DIRECTLY contain information answering the question. Do not cite excerpts that are merely related to the topic.
3. For each citation, briefly quote the specific phrase (under 20 words) that supports your answer
4. If the answer is not found in any excerpt, say: "I don't have enough information in the uploaded documents to answer this question."
5. Do NOT make up information or use knowledge outside the provided excerpts
6. It is better to cite 1 precise source than 5 vague ones
7. If the question is about the overall document (e.g., "what topics are covered?"), look for the Document Overview section first
```

### STEP 5: Modify the document processing pipeline

In `backend/app/routers/documents.py` (or wherever the background processing function lives), update the pipeline:

**Old flow:**
1. Extract text
2. chunk_text(text, chunk_size=2000, chunk_overlap=200)  ← dumb chunking
3. embed_texts([chunk["content"] for chunk in chunks])
4. Store chunks with embeddings

**New flow:**
1. Extract text
2. `chunks = await chunk_document(text, file_name)`  ← new intelligent chunking (this is async because it calls Claude)
3. For each chunk, create the combined embedding text: `f"{chunk['metadata']['search_description']}\n\n{chunk['content']}"`
4. embed_texts(combined_texts)
5. Store chunks with embeddings (the content field stores the ORIGINAL section text, NOT the combined text — the combined text is only for embedding)

**CRITICAL:** The background processing function must now be async-compatible since `chunk_document()` makes API calls to Claude. Check that the BackgroundTasks function that calls processing is properly set up for async. If it's currently a sync function, convert it to async.

### STEP 6: Update the `document_chunks` metadata

The metadata JSONB field in document_chunks should now store:
```json
{
    "title": "Anti-Bribery & Anti-Corruption Policy",
    "is_summary": false,
    "search_description": "anti-bribery FCPA corruption gift policy reporting",
    "file_name": "Acme_Corp_Employee_Handbook_2026.pdf"
}
```

No database schema changes needed — metadata is already a JSONB column. Just store richer data in it.

### STEP 7: Update citation preview text on the frontend

Find the component that renders source citations (likely `SourceCitation.tsx` or wherever citation chips are rendered). Currently it shows a preview snippet from the chunk content. Update it to:

1. Show the section **title** from metadata as the primary text (e.g., "Anti-Bribery Policy")
2. Show the search_description or first 80 chars of content as the secondary preview text in italic
3. Format: `📄 Filename Section N` on first line, `"section title"` on second line

### WHAT NOT TO CHANGE

- Do NOT change the database schema (document_chunks table stays the same)
- Do NOT change the match_chunks PostgreSQL function
- Do NOT change the frontend chat streaming logic
- Do NOT change the embedding model (still text-embedding-3-small, 1536 dims)
- Do NOT change the Supabase client or authentication logic

### TESTING

After making all changes:

1. The backend should still start without errors: `uvicorn app.main:app --reload`
2. Existing documents will NOT automatically re-chunk (they keep old chunks). Users need to delete and re-upload documents to get the new chunking.
3. Log the chunking results during processing: log number of sections found, their titles, and whether AI chunking succeeded or fell back to dumb chunking

### COMMIT MESSAGE

```
feat: replace fixed-size chunking with AI-powered intelligent document chunking

- AI identifies logical section boundaries instead of splitting at character count
- Generates document summary chunk (chunk 0) for overview questions
- Generates per-section search descriptions for better retrieval
- Embeds combined description + content for improved vector similarity
- Falls back to original chunking if AI calls fail
- Updates chat prompt for stricter citation precision
```
