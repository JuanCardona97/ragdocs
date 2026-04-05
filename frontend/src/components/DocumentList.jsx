function getFileExt(filename) {
  if (!filename) return "?";
  return filename.split(".").pop().toLowerCase();
}

export default function DocumentList({ documents, activeDocId, onSelect, onDelete }) {
  if (documents.length === 0) return null;

  return (
    <div className="doc-list">
      <h3>Documents</h3>
      {documents.map((doc) => {
        const ext = getFileExt(doc.filename);
        return (
          <div
            key={doc.id}
            className={`doc-item ${doc.id === activeDocId ? "active" : ""}`}
            onClick={() => onSelect(doc.id)}
          >
            <div className={`doc-type-badge ${ext}`}>
              {ext}
            </div>
            <div className="doc-info">
              <span className="doc-name">{doc.filename}</span>
              <span className="doc-meta">
                <span>{doc.chunks} chunks</span>
                <span className="doc-meta-dot" />
                <span>{(doc.characters / 1000).toFixed(1)}k chars</span>
              </span>
            </div>
            <button
              className="doc-delete"
              onClick={(e) => { e.stopPropagation(); onDelete(doc.id); }}
              title="Delete document"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </div>
        );
      })}
    </div>
  );
}
