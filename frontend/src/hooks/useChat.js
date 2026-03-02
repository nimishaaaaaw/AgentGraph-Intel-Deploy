/**
 * Custom hook for managing chat state and interactions.
 */
import { useState, useCallback, useEffect } from 'react'
import { sendMessage } from '../services/api'

const STORAGE_KEY = 'agentgraph_chat_messages'

function loadMessages() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

export function useChat() {
  const [messages, setMessages] = useState(loadMessages)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

  const addMessage = useCallback((message) => {
    setMessages((prev) => [...prev, { ...message, id: Date.now().toString(), timestamp: Date.now() }])
  }, [])

  const send = useCallback(async (query) => {
    if (!query.trim() || isLoading) return
    addMessage({ role: 'user', content: query })
    setIsLoading(true)
    setError(null)
    try {
      const data = await sendMessage(query)
      addMessage({
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        agent_trail: data.steps_taken || [],
        entities: data.entities || [],
      })
    } catch (err) {
      setError(err.message)
      addMessage({
        role: 'assistant',
        content: `⚠️ Error: ${err.message}`,
        sources: [],
        agent_trail: [],
        entities: [],
      })
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, addMessage])

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  return { messages, isLoading, error, send, clearMessages }
}
