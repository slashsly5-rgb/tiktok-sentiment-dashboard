/**
 * Session Manager for Chat Sessions
 * Uses sessionStorage for browser-session scoped IDs
 */

const SESSION_KEY = 'bumi_chat_session_id'

/**
 * Generate a UUID v4
 */
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

/**
 * Get or create session ID
 */
export function getSessionId() {
  let sessionId = sessionStorage.getItem(SESSION_KEY)

  if (!sessionId) {
    sessionId = generateUUID()
    sessionStorage.setItem(SESSION_KEY, sessionId)
    console.log('Created new chat session:', sessionId)
  }

  return sessionId
}

/**
 * Clear session ID (useful for logout or reset)
 */
export function clearSessionId() {
  sessionStorage.removeItem(SESSION_KEY)
  console.log('Cleared chat session')
}

/**
 * Check if session exists
 */
export function hasSession() {
  return sessionStorage.getItem(SESSION_KEY) !== null
}

export default {
  getSessionId,
  clearSessionId,
  hasSession
}
