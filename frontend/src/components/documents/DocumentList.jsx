import React from 'react'
import { Trash2, FileText, Calendar, Hash } from 'lucide-react'

/**
 * Table/card list of uploaded documents.
 *
 * @param {Object} props
 * @param {Array} props.documents - List of document objects
 * @param {Function} props.onDelete - Callback to delete a document
 * @param {boolean} props.loading - Whether documents are loading
 */
export default function DocumentList({ documents = [], onDelete, loading }) {
  if (loading) {
    return (
      <div className="p-4 space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-slate-800 rounded-xl p-4 animate-pulse">
            <div className="h-4 bg-slate-700 rounded w-1/3 mb-2" />
            <div className="h-3 bg-slate-700 rounded w-1/4" />
          </div>
        ))}
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center px-4">
        <FileText size={40} className="text-slate-600 mb-3" />
        <p className="text-slate-400 font-medium">No documents uploaded yet</p>
        <p className="text-slate-600 text-sm mt-1">
          Upload a PDF or text file to get started
        </p>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-2">
      {documents.map((doc) => (
        <div
          key={doc.doc_id}
          className="bg-slate-800 border border-slate-700/50 rounded-xl px-4 py-3 flex items-center gap-3 group hover:border-slate-600 transition-colors"
        >
          <div className="w-9 h-9 rounded-lg bg-indigo-600/20 flex items-center justify-center flex-shrink-0">
            <FileText size={18} className="text-indigo-400" />
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-200 truncate">{doc.name || doc.filename}</p>
            <div className="flex items-center gap-3 mt-0.5">
              {doc.size && (
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Hash size={10} />
                  {(doc.size / 1024).toFixed(1)} KB
                </span>
              )}
              {doc.chunks && (
                <span className="text-xs text-slate-500">{doc.chunks} chunks</span>
              )}
              {doc.uploaded_at && (
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Calendar size={10} />
                  {new Date(doc.uploaded_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          <button
            onClick={() => onDelete?.(doc.doc_id)}
            className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 transition-all p-1"
            aria-label="Delete document"
          >
            <Trash2 size={16} />
          </button>
        </div>
      ))}
    </div>
  )
}
