import { Header } from "@/components/layout/Header"

export default function Dashboard() {
  return (
    <>
      <Header title="Dashboard" />
      <div className="p-6">
        <div className="mx-auto max-w-[1200px]">
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <p className="text-[var(--text-secondary)] font-body">
              No knowledge bases yet. Create your first one to get started.
            </p>
          </div>
        </div>
      </div>
    </>
  )
}
