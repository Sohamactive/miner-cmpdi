import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Bot, CircleAlert, FileText, Send, ShieldCheck, UserRound } from 'lucide-react'

type Claim = {
  value: number | string
  unit?: string | null
  document_id?: string
  page_range?: string | null
  evidence_snippet?: string
  status: 'SUPPORTED' | 'NEEDS_REVIEW' | 'UNSUPPORTED'
}

type Answer = { answer_text: string; claims: Claim[] }
type Message = { role: 'user' | 'assistant'; content: string; answer?: Answer }

const API = '/api'

function CitationChart({ claims }: { claims: Claim[] }) {
  const numeric = claims.filter((claim) => typeof claim.value === 'number' && claim.status !== 'UNSUPPORTED')
  if (numeric.length < 2) return null
  const max = Math.max(...numeric.map((claim) => Number(claim.value)), 1)
  return (
    <div className="chat-chart" aria-label="Chart of cited values">
      <div className="chat-chart-label">Cited values</div>
      {numeric.map((claim, index) => (
        <div className="chat-bar-row" key={`${claim.document_id}-${claim.value}-${index}`}>
          <span>{claim.value}{claim.unit ? ` ${claim.unit}` : ''}</span>
          <div className="chat-bar-track"><i style={{ width: `${Math.max(4, Number(claim.value) / max * 100)}%` }} /></div>
        </div>
      ))}
    </div>
  )
}

function CitationLine({ claims }: { claims: Claim[] }) {
  const citations = claims
    .filter((claim) => claim.document_id)
    .map((claim) => `${claim.document_id!.slice(0, 12)} · p. ${claim.page_range || '?'}`)
    .filter((citation, index, all) => all.indexOf(citation) === index)
  if (citations.length === 0) return null

  return (
    <div className="chat-citation-line">
      <FileText size={12} />
      <span>Sources: {citations.join('  ·  ')}</span>
    </div>
  )
}

function AnswerCard({ answer }: { answer: Answer }) {
  return (
    <div className="chat-answer">
      <div className="chat-answer-text">{answer.answer_text}</div>
      <CitationLine claims={answer.claims} />
      <CitationChart claims={answer.claims} />
      {answer.claims.length > 0 && (
        <div className="chat-citations">
          <div className="chat-citations-title"><ShieldCheck size={14} /> Evidence and citations</div>
          {answer.claims.map((claim, index) => (
            <div className="chat-citation" key={`${claim.document_id}-${claim.value}-${index}`}>
              <div className="chat-citation-head">
                <span className={`claim-status ${claim.status}`}>{claim.status.replace('_', ' ')}</span>
                <strong>{claim.value}{claim.unit ? ` ${claim.unit}` : ''}</strong>
              </div>
              <p>{claim.evidence_snippet || 'No evidence snippet returned.'}</p>
              <small>{claim.document_id || 'Document unavailable'} · page {claim.page_range || 'range unavailable'}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ChatPage() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const history = useMemo(() => messages.map(({ role, content }) => ({ role, content })), [messages])

  async function ask(event: FormEvent) {
    event.preventDefault()
    const text = question.trim()
    if (!text || sending) return
    setQuestion('')
    setError('')
    setMessages((current) => [...current, { role: 'user', content: text }])
    setSending(true)
    try {
      const response = await fetch(`${API}/qa/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, conversation_history: history }),
      })
      if (!response.ok) {
        const detail = await response.text()
        throw new Error(response.status === 404 ? 'No reliable evidence found for that question.' : detail || `Request failed (${response.status})`)
      }
      const answer = await response.json() as Answer
      setMessages((current) => [...current, { role: 'assistant', content: answer.answer_text, answer }])
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to query the evidence store.')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat-workspace">
      <div className="chat-shell">
        <header className="chat-hero">
          <div className="eyebrow"><span className="eyebrow-dot" /> Evidence desk / cited QA</div>
          <h1>Ask the archive.</h1>
          <p>Answers come from PostgreSQL facts first, then Qdrant context. Numeric claims stay attached to their document and page.</p>
        </header>
        <main className="chat-panel">
          <div className="chat-trust"><ShieldCheck size={16} /> Facts-first retrieval · uncited numbers are flagged, not trusted</div>
          <div className="chat-thread">
            {messages.length === 0 && (
              <div className="chat-empty"><Bot size={30} /><strong>What do you need to verify?</strong><span>Try “What production figures are available for the indexed mines?”</span></div>
            )}
            {messages.map((message, index) => (
              <div className={`chat-message ${message.role}`} key={`${message.role}-${index}`}>
                <div className="chat-avatar">{message.role === 'user' ? <UserRound size={15} /> : <Bot size={15} />}</div>
                <div className="chat-bubble">
                  <div className="chat-role">{message.role === 'user' ? 'You' : 'MINER evidence assistant'}</div>
                  {message.answer ? <AnswerCard answer={message.answer} /> : <p>{message.content}</p>}
                </div>
              </div>
            ))}
            {sending && <div className="chat-message assistant"><div className="chat-avatar"><Bot size={15} /></div><div className="chat-bubble"><div className="chat-role">MINER evidence assistant</div><p className="chat-thinking">Searching facts and cited context…</p></div></div>}
          </div>
          {error && <div className="error-note"><CircleAlert size={16} /> {error}</div>}
          <form className="chat-composer" onSubmit={(event) => void ask(event)}>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question about production, manpower, finance, or operations…" rows={2} disabled={sending} />
            <button className="primary-action" type="submit" disabled={!question.trim() || sending}><Send size={16} /> {sending ? 'Searching' : 'Ask archive'}</button>
          </form>
          <div className="chat-footer"><span><FileText size={13} /> Every answer includes reviewable evidence</span><span>PostgreSQL + Qdrant</span></div>
        </main>
      </div>
    </div>
  )
}
