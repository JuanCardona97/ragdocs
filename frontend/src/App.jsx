import { useState, useEffect } from "react";
import FileUpload from "./components/FileUpload";
import ChatWindow from "./components/ChatWindow";
import DocumentList from "./components/DocumentList";
import DocumentPreview from "./components/DocumentPreview";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [activeDocId, setActiveDocId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);

  // Close sidebar on doc select (mobile)
  const handleSelect = (docId) => {
    setActiveDocId(docId);
    setSidebarOpen(false);
  };

  const handleUpload = (doc) => {
    setDocuments((prev) => [...prev, doc]);
    setActiveDocId(doc.id);
    setSidebarOpen(false);
  };

  const handleDelete = async (docId) => {
    await fetch(`${API_URL}/documents/${docId}`, { method: "DELETE" });
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
    if (activeDocId === docId) setActiveDocId(null);
  };

  // Close panels on escape key
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") {
        setSidebarOpen(false);
        setPreviewOpen(false);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  const activeDoc = documents.find((d) => d.id === activeDocId);

  return (
    <div className="app">
      {/* ── Mobile top bar ── */}
      <header className="mobile-header">
        <button
          className="mobile-menu-btn"
          onClick={() => setSidebarOpen(true)}
          aria-label="Open menu"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <h1 className="mobile-logo">RAGDocs</h1>
        {activeDocId && (
          <button
            className="mobile-preview-btn"
            onClick={() => setPreviewOpen(true)}
            aria-label="View document"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </button>
        )}
      </header>

      {/* ── Sidebar overlay (mobile) ── */}
      <div
        className={`sidebar-overlay ${sidebarOpen ? "visible" : ""}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* ── Sidebar ── */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-top">
          <div>
            <h1 className="logo">RAGDocs</h1>
            <p className="tagline">Chat with any document</p>
          </div>
          <button
            className="sidebar-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <FileUpload apiUrl={API_URL} onUpload={handleUpload} />
        <DocumentList
          documents={documents}
          activeDocId={activeDocId}
          onSelect={handleSelect}
          onDelete={handleDelete}
        />
      </aside>

      {/* ── Chat ── */}
      <main className="chat-area">
        <ChatWindow apiUrl={API_URL} documentId={activeDocId} />
      </main>

      {/* ── Preview (desktop: normal panel, mobile: overlay) ── */}
      <div
        className={`preview-overlay ${previewOpen ? "visible" : ""}`}
        onClick={() => setPreviewOpen(false)}
      />
      <DocumentPreview
        apiUrl={API_URL}
        documentId={activeDocId}
        filename={activeDoc?.filename}
        mobileOpen={previewOpen}
        onMobileClose={() => setPreviewOpen(false)}
      />
    </div>
  );
}
