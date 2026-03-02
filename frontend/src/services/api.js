/**
 * API service layer — centralizes all HTTP requests to the backend.
 * Uses axios with a configured base URL and interceptors.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    console.error('[API Error]', message)
    return Promise.reject(new Error(message))
  }
)

/**
 * Send a chat message to the AI agent.
 * @param {string} query - User's query
 * @returns {Promise<Object>} Response with answer, sources, agent_trail
 */
export const sendMessage = (query) =>
  api.post('/chat', { message: query }).then((r) => r.data)

/**
 * Upload a document for processing.
 * @param {File} file - File to upload
 * @returns {Promise<Object>} Upload result with document metadata
 */
export const uploadDocument = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

/**
 * List all uploaded documents.
 * @returns {Promise<Array>} List of document objects
 */
export const getDocuments = () =>
  api.get('/documents').then((r) => r.data)

/**
 * Delete a document by ID.
 * @param {string} docId - Document identifier
 * @returns {Promise<Object>} Deletion result
 */
export const deleteDocument = (docId) =>
  api.delete(`/documents/${docId}`).then((r) => r.data)

/**
 * Fetch all graph nodes for visualization.
 * @returns {Promise<Array>} List of node objects
 */
export const getGraphNodes = () =>
  api.get('/graph/entities').then((r) => r.data)

/**
 * Fetch all graph relationships for visualization.
 * @returns {Promise<Array>} List of relationship objects
 */
export const getGraphRelationships = () =>
  api.get('/graph/relationships').then((r) => r.data)

/**
 * Search the knowledge graph.
 * @param {string} query - Search query
 * @returns {Promise<Object>} Search results
 */
export const searchGraph = (query) =>
  api.get('/graph/search', { params: { query } }).then((r) => r.data)

/**
 * Get graph statistics.
 * @returns {Promise<Object>} Stats object
 */
export const getGraphStats = () =>
  api.get('/graph/stats').then((r) => r.data)

/**
 * Get system health status.
 * @returns {Promise<Object>} Health check result
 */
export const getHealth = () =>
  api.get('/health').then((r) => r.data)

export default api
