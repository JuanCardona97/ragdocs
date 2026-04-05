import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

export default function ChatWindow({ apiUrl, documentId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const buildChatHistory = () => {
    return messages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({ role: m.role, content: m.content }));
  };

  const sendMessage = async (text) => {
    const question = (text || input).trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    const chatHistory = buildChatHistory();

    try {
      const res = await fetch(`${apiUrl}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          document_id: documentId,
          chat_history: chatHistory,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to get response");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let assistantMsg = { role: "assistant", content: "", sources: [] };

      setMessages((prev) => [...prev, assistantMsg]);

      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = JSON.parse(line.slice(6));

          if (data.type === "sources") {
            assistantMsg = { ...assistantMsg, sources: data.sources };
            setMessages((prev) => [...prev.slice(0, -1), { ...assistantMsg }]);
          } else if (data.type === "token") {
            assistantMsg = {
              ...assistantMsg,
              content: assistantMsg.content + data.token,
            };
            setMessages((prev) => [...prev.slice(0, -1), { ...assistantMsg }]);
          }
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev.filter((m) => m.content !== ""),
        { role: "error", content: err.message },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                <polyline points="14 2 14 8 20 8" />
                <path d="M8 13h2" />
                <path d="M8 17h6" />
              </svg>
            </div>
            <h2>Ask anything about your documents</h2>
            <p>Upload a PDF, DOCX, or TXT file and start a conversation<br />with your knowledge base.</p>
            <div className="suggestions">
              {[
                "What are the key takeaways?",
                "Summarize the main points",
                "What data supports the conclusion?",
              ].map((s) => (
                <button
                  key={s}
                  className="suggestion"
                  onClick={() => sendMessage(s)}
                >
                  <span style={{ position: "relative", zIndex: 1 }}>{s}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.role === "assistant" && (
              <div className="message-avatar">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 2 7 12 12 22 7 12 2" />
                  <polyline points="2 17 12 22 22 17" />
                  <polyline points="2 12 12 17 22 12" />
                </svg>
              </div>
            )}
            {msg.role === "user" ? (
              <div className="message-content">{msg.content}</div>
            ) : msg.role === "error" ? (
              <span>{msg.content}</span>
            ) : (
              <div className="message-body">
                <div className="message-content">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
                {msg.sources?.length > 0 && (
                  <div className="sources">
                    <span className="sources-label">Sources</span>
                    {msg.sources.map((s, j) => (
                      <span key={j} className="source-chip">
                        {s.filename} &middot; chunk {s.chunk_index + 1}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && messages[messages.length - 1]?.role !== "assistant" && (
          <div className="message assistant">
            <div className="message-avatar">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12 2 2 7 12 12 22 7 12 2" />
                <polyline points="2 17 12 22 22 17" />
                <polyline points="2 12 12 17 22 12" />
              </svg>
            </div>
            <div className="message-body">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form className="input-area" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your document..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ position: "relative", zIndex: 1 }}>
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </form>
    </div>
  );
}
