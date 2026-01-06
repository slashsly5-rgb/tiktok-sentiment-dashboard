import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { sendChatMessage, getChatHistory } from '../services/api'
import { getSessionId } from '../utils/sessionManager'
import './ChatInterface.css'

const ChatInterface = ({ filters }) => {
  const [message, setMessage] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  const [suggestions] = useState([
    'Summarize sentiment trends',
    'What are the top issues?',
    'Explain sentiment distribution'
  ])

  useEffect(() => {
    // Initialize session ID and load history
    const sid = getSessionId()
    setSessionId(sid)
    loadHistory(sid)
  }, [])

  useEffect(() => {
    // Auto-scroll to bottom when messages change
    if (isExpanded) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading, isExpanded])

  const loadHistory = async (sid) => {
    try {
      const response = await getChatHistory(sid)
      setMessages(response.history || [])
    } catch (err) {
      console.error('Error loading history:', err)
      // If no history exists yet, that's fine
      setMessages([])
    }
  }

  const handleSubmit = async (text) => {
    if (!text || text.trim() === '') return
    if (!sessionId) return

    const userMessage = text.trim()
    setMessage('')
    setLoading(true)
    setError(null)

    // Optimistically add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    try {
      const response = await sendChatMessage(sessionId, userMessage, filters)

      // Add assistant response
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }])
    } catch (err) {
      console.error('Chat error:', err)
      setError('Failed to send message')

      // Remove optimistic user message on error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(message)
    }
  }

  return (
    <div
      className={`chat-widget ${isExpanded ? 'expanded' : ''}`}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      {/* Chat Button (Always Visible) */}
      <div className="chat-widget-button">
        <i className="fas fa-robot"></i>
        <span className="chat-badge">BUMI</span>
        {messages.length > 0 && (
          <span className="message-count-badge">{messages.length}</span>
        )}
      </div>

      {/* Expanded Chat Panel */}
      <div className="chat-widget-panel">
        <div className="chat-widget-header">
          <h3>BUMI AI Assistant</h3>
          {filters && (
            <p className="chat-context-info">
              Context: Last {filters.days || 30} days
            </p>
          )}
        </div>

        <div className="chat-widget-body">
          {messages.length === 0 ? (
            <>
              <p className="chat-widget-hint">
                Ask me anything about your sentiment data
              </p>

              {/* Suggestions */}
              <div className="chat-suggestions">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    className="suggestion-chip"
                    onClick={() => handleSubmit(suggestion)}
                    disabled={loading}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <>
              {/* Messages Display */}
              <div className="chat-messages">
                {messages.map((msg, index) => (
                  <div key={index} className={`chat-message ${msg.role}`}>
                    <div className="message-avatar">
                      {msg.role === 'user' ? (
                        <i className="fas fa-user"></i>
                      ) : (
                        <i className="fas fa-robot"></i>
                      )}
                    </div>
                    <div className="message-bubble">
                      {msg.role === 'assistant' ? (
                        <div className="markdown-content">
                          <ReactMarkdown>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p>{msg.content}</p>
                      )}
                    </div>
                  </div>
                ))}

                {/* Loading Indicator */}
                {loading && (
                  <div className="chat-message assistant">
                    <div className="message-avatar">
                      <i className="fas fa-robot"></i>
                    </div>
                    <div className="message-bubble loading">
                      <div className="typing-indicator">
                        <span></span><span></span><span></span>
                      </div>
                      <p className="typing-text">Analyzing your data...</p>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </>
          )}

          {/* Error Display */}
          {error && (
            <div className="chat-error">
              <i className="fas fa-exclamation-circle"></i> {error}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="chat-widget-input">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask BUMI..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <button
            className="chat-send-btn"
            onClick={() => handleSubmit(message)}
            disabled={!message.trim() || loading}
            title="Send message"
          >
            {loading ? (
              <i className="fas fa-spinner fa-spin"></i>
            ) : (
              <i className="fas fa-paper-plane"></i>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
