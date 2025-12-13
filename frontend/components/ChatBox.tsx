"use client"
import { useEffect, useRef, useState } from 'react'

type Msg = { id: string; role: 'user' | 'bot'; text: string }

export default function ChatBox() {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const ref = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [messages])

  const send = async () => {
    const trimmed = input.trim()
    if (!trimmed) return
    const userMsg = { id: String(Date.now()), role: 'user' as const, text: trimmed }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed })
      })
      const json = await res.json()
      const botMsg = { id: String(Date.now() + 1), role: 'bot' as const, text: json.reply ?? 'Pas de réponse' }
      setMessages((m) => [...m, botMsg])
    } catch (err) {
      setMessages((m) => [...m, { id: String(Date.now()), role: 'bot', text: 'Erreur: impossible de joindre le backend' }])
    } finally {
      setLoading(false)
    }
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); send()
    }
  }

  return (
    <div className="bg-white border rounded-2xl shadow-xl overflow-hidden">
      {/* Header with logo and headline */}
      <div className="px-6 py-5 bg-gradient-to-r from-emerald-600 via-green-600 to-teal-500 text-white">
        <div className="flex items-center gap-4">
          <img src="/logo.svg" alt="Agrosys logo" className="w-12 h-12" />
          <div>
            <div className="text-lg font-extrabold leading-tight">Agrosys — Assistant Agricole</div>
            <div className="text-sm opacity-90">Conseils pratiques et diagnostics rapides</div>
          </div>
        </div>
      </div>

      {/* Messages area */}
      <div ref={ref} className="p-6 h-[62vh] overflow-y-auto space-y-4 bg-gradient-to-b from-white to-gray-50">
        {messages.length === 0 && <div className="text-gray-500">Démarrez la conversation — posez une question sur une culture, une maladie, ou une pratique.</div>}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className="flex items-end gap-3">
              {m.role === 'bot' && <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">B</div>}
              <div className={`${m.role === 'user' ? 'bg-emerald-600 text-white' : 'bg-white border text-gray-800'} px-4 py-2 rounded-2xl shadow-sm max-w-[70%]`}>{m.text}</div>
              {m.role === 'user' && <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center">U</div>}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border px-3 py-2 rounded-2xl shadow-sm flex items-center gap-2">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="p-4 border-t bg-white flex gap-3 items-center">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Tapez votre message..."
          className="flex-1 p-3 rounded-xl border resize-none h-14 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-300 text-gray-900 placeholder-gray-400"
          aria-label="Message"
        />
        <button disabled={loading || !input.trim()} onClick={send} className="bg-emerald-600 text-white px-5 py-3 rounded-xl shadow hover:shadow-lg disabled:opacity-50">Envoyer</button>
      </div>
    </div>
  )
}
