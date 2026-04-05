import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

/* ── Tabular data (CSV / XLSX) ── */
function TabularLine({ line }) {
  if (line.startsWith("--- Sheet:")) {
    const name = line.replace(/^-+\s*Sheet:\s*/, "").replace(/\s*-+$/, "");
    return <div className="preview-sheet-header">{name}</div>;
  }

  if (line.includes(" | ")) {
    const parts = line.split(" | ");
    return (
      <div className="preview-row">
        {parts.map((part, i) => {
          const colonIdx = part.indexOf(": ");
          if (colonIdx > -1) {
            const key = part.slice(0, colonIdx);
            const val = part.slice(colonIdx + 2);
            return (
              <span key={i}>
                {i > 0 && <span className="preview-separator">|</span>}
                <strong className="preview-key">{key}:</strong> {val}
              </span>
            );
          }
          return <span key={i}>{part}</span>;
        })}
      </div>
    );
  }

  if (line.trim()) return <div className="preview-text-line">{line}</div>;
  return <div className="preview-spacer" />;
}

function TabularPreview({ text }) {
  const lines = text.split("\n");
  return (
    <div className="preview-formatted">
      {lines.map((line, i) => (
        <TabularLine key={i} line={line} />
      ))}
    </div>
  );
}

/* ── Document text (PDF / DOCX / TXT / MD) ── */
function DocumentTextPreview({ text }) {
  return (
    <div className="preview-document">
      <ReactMarkdown>{text}</ReactMarkdown>
    </div>
  );
}

/* ── File type detection ── */
function isTabular(filename) {
  if (!filename) return false;
  const ext = filename.split(".").pop().toLowerCase();
  return ext === "csv" || ext === "xlsx";
}

/* ── Main component ── */
export default function DocumentPreview({ apiUrl, documentId, filename, mobileOpen, onMobileClose }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (!documentId) return;
    setLoading(true);
    fetch(`${apiUrl}/documents/${documentId}/preview`)
      .then((res) => res.json())
      .then((data) => setText(data.text || ""))
      .catch(() => setText("Failed to load preview"))
      .finally(() => setLoading(false));
  }, [apiUrl, documentId]);

  if (!documentId) return null;

  return (
    <div className={`preview-panel ${visible ? "" : "collapsed"} ${mobileOpen ? "mobile-open" : ""}`}>
      <div className="preview-header">
        <div className="preview-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          <span>{filename || "Document"}</span>
        </div>
        <div className="preview-actions">
          {/* Mobile close button */}
          <button className="preview-mobile-close" onClick={onMobileClose} aria-label="Close preview">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
          {/* Desktop toggle */}
          <button className="preview-toggle" onClick={() => setVisible(!visible)}>
            {visible ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6" />
              </svg>
            )}
          </button>
        </div>
      </div>
      {visible && (
        <div className="preview-content">
          {loading ? (
            <div className="preview-loading">Loading preview...</div>
          ) : isTabular(filename) ? (
            <TabularPreview text={text} />
          ) : (
            <DocumentTextPreview text={text} />
          )}
        </div>
      )}
    </div>
  );
}
