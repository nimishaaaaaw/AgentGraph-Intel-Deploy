import React, { useEffect, useState, useCallback } from 'react'
import DocumentUpload from '../components/documents/DocumentUpload'
import DocumentList from '../components/documents/DocumentList'
import ErrorBoundary from '../components/common/ErrorBoundary'
import { uploadDocument, getDocuments, deleteDocument } from '../services/api'
import { FileText } from 'lucide-react'

/**
 * Document management page — upload, list, and delete documents.
 */
export default function DocumentsPage() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    try {
      const docs = await getDocuments()
      setDocuments(Array.isArray(docs) ? docs : [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  const handleUpload = useCallback(
    async (file) => {
      await uploadDocument(file)
      await fetchDocuments()
    },
    [fetchDocuments]
  )

  const handleDelete = useCallback(
    async (docId) => {
      try {
        await deleteDocument(docId)
        setDocuments((docs) => docs.filter((d) => d.doc_id !== docId))
      } catch (err) {
        setError(err.message)
      }
    },
    []
  )

  return (
    <ErrorBoundary>
      <div className="max-w-3xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center gap-2 mb-6">
          <FileText size={20} className="text-indigo-400" />
          <div>
            <h1 className="font-semibold text-slate-100">Documents</h1>
            <p className="text-xs text-slate-500">
              {documents.length} document{documents.length !== 1 ? 's' : ''} in knowledge base
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 bg-red-950/30 border border-red-800/50 rounded-xl p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Upload area */}
        <div className="card mb-4">
          <DocumentUpload onUpload={handleUpload} />
        </div>

        {/* Document list */}
        <div className="card">
          <div className="px-4 py-3 border-b border-slate-700/50">
            <h2 className="font-medium text-slate-300 text-sm">Knowledge Base</h2>
          </div>
          <DocumentList documents={documents} onDelete={handleDelete} loading={loading} />
        </div>
      </div>
    </ErrorBoundary>
  )
}
