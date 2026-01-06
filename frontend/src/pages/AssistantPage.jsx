import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { getChatHistory, sendChatMessage, clearChatSession } from '../services/api'
import { getSessionId, clearSessionId } from '../utils/sessionManager'
import './AssistantPage.css'

const AssistantPage = ({ filters }) => {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [initialLoad, setInitialLoad] = useState(true)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    const sid = getSessionId()
    setSessionId(sid)
    loadHistory(sid)
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const loadHistory = async (sid) => {
    try {
      setInitialLoad(true)
      const response = await getChatHistory(sid)
      setMessages(response.history || [])
    } catch (err) {
      console.error('Error loading history:', err)
      setMessages([])
    } finally {
      setInitialLoad(false)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || !sessionId) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)
    setError(null)

    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    try {
      const response = await sendChatMessage(sessionId, userMessage, filters)
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }])
    } catch (err) {
      console.error('Chat error:', err)
      setError(err.response?.data?.error || 'Failed to send message')
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const handleClearChat = async () => {
    if (!confirm('Are you sure you want to clear this conversation?')) return

    try {
      await clearChatSession(sessionId)
      clearSessionId()

      const newSessionId = getSessionId()
      setSessionId(newSessionId)
      setMessages([])
      setError(null)
    } catch (err) {
      console.error('Error clearing chat:', err)
      setError('Failed to clear conversation')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="assistant-page">
      <div className="assistant-header">
        <h1>BUMI AI Assistant</h1>
        <div className="assistant-actions">
          {filters && (
            <span className="context-badge">
              Context: {filters.days || 30} days
            </span>
          )}
          <button className="clear-btn" onClick={handleClearChat}>
            <i className="fas fa-trash"></i> Clear Chat
          </button>
        </div>
      </div>

      <div className="messages-container">
        {initialLoad ? (
          <div className="empty-state">
            <i className="fas fa-spinner fa-spin"></i>
            <p>Loading conversation...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="empty-state">
            <i className="fas fa-comments"></i>
            <p>No conversation yet. Start by asking a question!</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'user' ? (
                  <i className="fas fa-user"></i>
                ) : (
                  <i className="fas fa-robot"></i>
                )}
              </div>
              <div className="message-content">
                <div className="message-role">
                  {msg.role === 'user' ? 'You' : 'BUMI'}
                </div>
                <div className="message-text">
                  {msg.role === 'assistant' ? (
                    <div>
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="message assistant typing">
            <div className="message-avatar">
              <i className="fas fa-robot"></i>
            </div>
            <div className="message-content">
              <div className="message-role">BUMI</div>
              <div className="typing-indicator">
                <span></span><span></span><span></span>
                <span className="typing-text">Analyzing your data...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="error-banner">
          <i className="fas fa-exclamation-triangle"></i> {error}
        </div>
      )}

      <div className="input-container">
        <textarea
          className="message-input"
          placeholder="Ask about sentiment trends, key issues, or analysis..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          rows={2}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          {loading ? (
            <i className="fas fa-spinner fa-spin"></i>
          ) : (
            <>
              <i className="fas fa-paper-plane"></i> Send
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default AssistantPage
