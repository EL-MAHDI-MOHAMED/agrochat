import ChatBox from '../components/ChatBox'

export default function Page() {
  return (
    <main className="min-h-screen flex items-start justify-center p-8 bg-gradient-to-b from-gray-50 to-white">
      <div className="w-full max-w-3xl">
        <section className="mb-6 flex items-center gap-4">
          <img src="/logo.svg" alt="Agrosys logo" className="w-14 h-14" />
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900">Agrosys — Chatbot Agricole</h1>
            <p className="text-sm text-gray-700">Une interface simple, claire et rapide pour aider les agriculteurs.</p>
          </div>
        </section>

        <ChatBox />
      </div>
    </main>
  )
}
