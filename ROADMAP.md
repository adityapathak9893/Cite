# ROADMAP.md — Weaverbit Cite

> **Governance:** No feature enters **Approved** without Aditya's explicit sign-off.
> Anything else lives in **Proposed** or **Parked**. Items move down this file, never
> silently appear in code. Evidence column cites eval cases / production findings
> where a feature is justified by data rather than opinion.
>
> Last updated: 2026-07-06

---

## 1. Now (in progress)

| Item | Detail | Status |
|------|--------|--------|
| Eval set additions | `coverage-01` (epistemics of absence — coverage questions must show evidence the model saw document structure) and `followup-01` (two-turn "tell me more" ambiguity — resolve from history or ask, label channels) | Approved — pending implementation |
| Overview-detector coverage patterns | Add coverage phrasings ("not covered", "does it cover", "what's missing", "doesn't include") to `is_overview_question` in rag.py so coverage questions always receive document structure. Absence claims are only groundable via structure; verified 2026-07-03 these phrasings are absent from the detector. | Approved — rides with the eval-case sitting |
| Publish chunking-bug engineering post | LinkedIn + X drafts ready since 2026-06-12 | Approved — pending publish |

## 2. Next (approved, in order)

| # | Item | Detail | Evidence |
|---|------|--------|----------|
| 1 | **Hybrid search** (tsvector + RRF) | Add Postgres full-text search over chunks; fuse keyword + vector rankings via reciprocal rank fusion. Design must decide the tsvector language config ('simple' vs 'english') — couples to the multilingual item. Acceptance: `grounded-02` flips green, no regressions on the full eval set. | grounded-02 failed 3 consecutive runs — "schedule" query never retrieved the section literally titled "Scan Scheduling" |
| 2 | **Extraction quality gate** | Post-extraction garbage detection (language-detection failure / gibberish heuristics); failing documents marked **failed** with an honest reason instead of "Ready". Never index lies. | Production 2026-07: real-user kundali PDF (legacy Kruti Dev encoding) silently indexed as 76 mojibake chunks; birth-date answered from page footers |
| 3 | **Embeddable widget** (Phase 6) | Public rate-limited chat endpoint + iframe widget per existing CLAUDE.md spec. This is what makes a first paying customer mechanically possible. | Planned since Feb; README promises it |

## 3. Proposed (awaiting Aditya's approval)

| Item | Detail | Why |
|------|--------|-----|
| Retrieval observability | Log per-query: retrieved chunks, similarities, threshold path (0.5 vs 0.3 retry), mode, latency. Simple queries table + crude admin view. | Production misses are currently invisible; every logged miss becomes a future eval case |
| Answer feedback chip | Thumbs up/down per assistant message, stored with message_id. | Begins real-user eval data; trivial build |
| Eval harness in CI | GitHub Actions running structural checks on a fixture KB per PR. | Turns the harness into a regression gate |
| Eval candidate harvesting (human-labeled) | Surface interesting production events (zero-retrieval queries, thumbs-downs, low-similarity retrievals) as a candidate queue; Aditya adjudicates labels; only human-approved cases enter the set. Depends on: observability + feedback chip. | The system may harvest candidates; only a human mints ground truth. Auto-labeling from own responses would enshrine current behavior as correct (would have protected the Feb chunking bug). |
| Format-expansion ingestion (ETL) | Per-format extraction fan-in to the existing canonical chunk schema: docx (python-docx), xlsx (openpyxl, table-aware), OCR for scanned PDFs and legacy-font PDFs. Origin: Aditya's data-cleansing vision behind the original AI chunking. | "We ingest your messy real documents" is a customer-felt feature; sequenced after retrieval is fixed. Production evidence 2026-07: real-user kundali PDF (legacy Kruti Dev font encoding + linearized tables) silently indexed as mojibake. |
| Multilingual support (verify + harden) | Tiered: query language / document language / UI language. First step is measurement, not building: 2–3 multilingual eval cases (Hindi + German questions vs the English corpus) and analysis of the kundali-session transcripts. Couples to the hybrid-search tsvector config decision ('simple' vs 'english'). | Production 2026-07: real-user Hindi/Hinglish session; cross-lingual embedding similarity unverified |
| Contract addendum: ambiguous follow-ups | One line authorizing clarifying questions outside posture E when a follow-up is ambiguous between document and domain content, with channel labeling. | Model already does this correctly (followup-01 probe); rule should match observed-good behavior |

## 4. Parked (do not build; revisit only on customer signal or Aditya's call)

Each entry records: what it is, where it came from, why it is parked, and what would unpark it.

### Per-KB tone setting
A `tone` column on `knowledge_bases` letting the KB owner choose the assistant's voice (e.g. formal / friendly / playful), interpolated into the contract's `{tone}` slot — which is currently hardcoded to neutral-professional. Origin: contract design; a sassier voice was considered and rejected for end-users. **Parked because** every tone variant multiplies the eval surface (5 postures × N tones all need grading) for a personalization feature no customer has asked for. **Unpark on:** a paying customer requesting brand voice.

### Competitor-comparison toggle (per-KB)
A per-KB boolean relaxing the contract's competitor rule, for owners who *want* the assistant to discuss competitors (e.g. sales-enablement KBs). Origin: contract design; the default rule (never evaluate competitors) is the safe choice for unknown customers. **Parked because** the safe default is correct until a real customer with a real use case defines what "allowed comparison" should even mean — and a relaxed rule needs its own bait eval cases before shipping. **Unpark on:** explicit customer demand.

### Web augmentation / live search as a third labeled channel
Extend the two-channel format (documents / domain knowledge) with a third fenced channel: live web results. Origin: research-mode design discussions. **Parked because** it adds a large trust surface (web content quality, citation of external URLs, prompt-injection via fetched pages) on top of a retrieval layer that isn't finished — hybrid search (Next #1) must land first. The two-channel epistemics should be boringly solid before a third channel exists. **Unpark on:** Aditya's call, after hybrid search ships and holds.

### LLM-as-judge in run_eval.py
Automate posture-quality grading via the existing `judge_posture_quality()` stub. **Parked because** at 25–30 cases, manual grading is cheap and is itself how Aditya builds judgment about the system (three of the June sprint's findings came from *reading* responses behind green checkmarks — a judge would have hidden them). A judge also needs its own calibration against human grades before it can be trusted. **Unpark on:** eval set growing past ~75 cases, or CI integration making manual grading the bottleneck.

### Agentic actions on documents — HARD BLOCK
Letting the assistant *act*: create tickets, edit documents, trigger workflows from chat. **Parked because** action multiplies the testing surface roughly tenfold, and the retrieval layer has demonstrated (grounded-02, three runs) that it can miss a section titled with the literal query word. An agent acting on incomplete retrieval is a liability, not a feature. Fix truth before action. **Unpark on:** hybrid search shipped + observability live + Aditya's explicit call. Not before.

### GDPR-MCP product idea
A separate product idea (compliance-focused MCP tooling) raised mid-sprint. **Parked because** it is a new product, and the standing rule is no new products until Cite has revenue. Recorded here so the idea isn't lost; recorded *here* so it isn't built. **Unpark on:** Cite reaching paying customers, per the 12-month roadmap.

### Staging environment
A separate Railway/Vercel environment between local and production. **Parked because** with one developer and zero customers, the eval suite + local testing covers the risk, and a staging env adds standing cost and config drift to maintain. **Unpark on:** first paying customer (at which point breaking prod has a victim).

### Lint cleanup (5 pre-existing frontend errors)
Five lint errors that predate Research Mode, deliberately left untouched during Phase D to honor scope discipline. **Parked because** zero user impact. Genuinely fine to do in any idle half-hour; listed only so it's tracked, not because it's controversial.

### bait-03 brevity tuning
The "B-brief" posture ignores its brevity instruction (produces a full structured essay where the tiebreak rule asks for a short anchored answer). A quality nit, not a grounding violation — content is accurate and properly channeled. **Parked because** prompt-tuning for length risks regressing postures that currently pass, for a cosmetic gain. Same accept-and-document discipline as bait-07. **Unpark on:** real users complaining about verbosity.

### Multi-KB / cross-KB search, analytics dashboards, billing tiers
Scale and monetization machinery: querying across knowledge bases, usage analytics for KB owners, paid plan enforcement. **Parked because** these serve a customer base that does not yet exist; building them now is polishing the product instead of getting a user. **Unpark on:** customer signal — billing specifically on the first person who asks to pay.

## 5. Known limitations (tracked, accepted)

- **bait-07 overlong zero-retrieval answer** — Hard Rule reduces but does not eliminate; no false attribution observed across 4 runs. Documented in CLAUDE.md.
- **Vector-only retrieval keyword blindness** — remediated by Next #1.
- **Coverage-question grounding** — absence claims not guaranteed to be structure-grounded; remediated by the approved overview-detector patterns + coverage-01 eval case.
- **Silent garbage indexing** — extraction failures currently produce "Ready" documents; remediated by Next #2 (extraction quality gate).

## 6. Recently done

- 2026-07-06 — Rulings: extraction quality gate approved (Next #2); multilingual support entered Proposed; overview-detector coverage patterns moved to the active sitting
- 2026-07-03 — ROADMAP.md committed to repo root
- 2026-07-03 — Repo state verified after 3-week gap (US export-control ban on Fable 5, June 12 – July 1): June 12 punch-list items confirmed present in code (zero-source brevity + non-attribution checks, bait-07 label, KB query invalidation)
- 2026-06-11/12 — Research Mode Phases A–F complete, eval-verified across 4 runs
- 2026-06-11 — Chunking rewrite: deterministic markdown split + verbatim markers (root-cause fix for mid-word seam bug shipped in Feb)
- 2026-06-12 — KB query invalidation on document-ready (suggestion-chips staleness)
- 2026-06-12 — Eval checks: zero-source brevity + zero-source non-attribution; bait-07 label corrected