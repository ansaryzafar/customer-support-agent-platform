import { useState } from 'react'
import './App.css'

// TODO(Phase 1): mirror the backend's ChatRequest/ChatResponse shape here
// (see backend/app/models/schemas.py) — e.g. in a new src/types.ts file.

type ChatMessage = { role: 'user' | 'agent'; text: string }

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')

  // TODO(Phase 1): implement sendMessage
  //   1. Append the user's message to `messages` optimistically.
  //   2. POST { conversation_id, message: input } to `/api/chat`
  //      (see backend/app/api/routes.py for the contract).
  //   3. Append the agent's response (response.message) to `messages`.
  //   4. Handle loading + error states — don't leave the input silently
  //      swallowing failures (a production support widget should show
  //      "something went wrong, try again" rather than nothing).
  async function sendMessage() {
    // TODO: implement
  }

  return (
    <div className="chat">
      <h1>Nimbus Support</h1>
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.text}
          </div>
        ))}
      </div>
      <div className="input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your plan, billing, or a device issue..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  )
}

export default App
