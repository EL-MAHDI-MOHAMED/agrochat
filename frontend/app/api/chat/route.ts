import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const message = body?.message
    if (!message) return NextResponse.json({ error: 'Missing message' }, { status: 400 })

    // Backend expects POST /ask with JSON { query: string } and returns { answer: ... }
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000/ask'
    try {
      const res = await fetch(backendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: message })
      })
        if (!res.ok) {
          const text = await res.text()
          // Instead of returning 502 to the frontend, return a friendly fallback reply so the UI stays usable.
          return NextResponse.json({ reply: `Le backend a retourne une erreur: ${text || res.statusText}. Essayez de verifier les variables d'environnement cote serveur.` })
        }
        const json = await res.json()
        // Normalize to `reply` expected by frontend
        return NextResponse.json({ reply: json.answer ?? json.reply ?? json })
    } catch (err) {
      // fallback echo
      return NextResponse.json({ reply: `Echo: ${message}` })
    }
  } catch (err) {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
}
