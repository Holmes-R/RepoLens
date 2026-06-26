import { useState, useRef, useEffect } from 'react';
import { chatWithRepo, analyzeRepo } from '../api/client';
import type { ChatMessage } from '../types';
import { Send, Loader2, Search, MessageSquare, FileText } from 'lucide-react';

export function ChatPage() {
  const [url, setUrl] = useState('');
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Enter a GitHub URL to start asking questions about a repository.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setAnalyzing(true);
    try {
      const res = await analyzeRepo({ repo_url: url.trim() });
      setAnalysisId(res.analysis_id);
      setMessages([{ role: 'assistant', content: `Repository analyzed! Ask me anything about it.` }]);
    } catch (err: any) {
      setMessages([...messages, { role: 'assistant', content: `Error: ${err.response?.data?.detail || 'Failed to analyze'}` }]);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !analysisId) return;
    const userMsg: ChatMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await chatWithRepo({ analysis_id: analysisId, message: input, history: messages.map(m => ({ role: m.role, content: m.content })) });
      const assistantMsg: ChatMessage = { role: 'assistant', content: res.response, sources: res.sources };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col h-[calc(100vh-2rem)]">
      <h1 className="text-3xl font-bold text-slate-900 mb-6">AI Repository Chat</h1>

      <form onSubmit={handleAnalyze} className="flex gap-3 mb-6">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/user/repository"
          className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
        />
        <button type="submit" disabled={analyzing} className="btn-primary flex items-center gap-2">
          <Search className="w-4 h-4" /> {analyzing ? 'Analyzing...' : 'Load'}
        </button>
      </form>

      <div className="flex-1 bg-white rounded-xl border border-slate-200 p-6 overflow-y-auto mb-4">
        {messages.map((msg, i) => (
          <div key={i} className={`mb-4 ${msg.role === 'user' ? 'text-right' : ''}`}>
            <div className={`inline-block max-w-[80%] rounded-xl px-4 py-3 text-left ${
              msg.role === 'user' ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-800'
            }`}>
              <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-300/30">
                  <div className="flex items-center gap-1 text-xs opacity-70">
                    <FileText className="w-3 h-3" /> Sources:
                  </div>
                  {msg.sources.slice(0, 3).map((src, j) => (
                    <div key={j} className="text-xs opacity-60 truncate">{src}</div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-slate-500">
            <Loader2 className="w-4 h-4 animate-spin" /> Thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={analysisId ? "Ask about the repository..." : "Analyze a repository first..."}
          disabled={!analysisId}
          className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none disabled:opacity-50"
        />
        <button onClick={handleSend} disabled={!input.trim() || !analysisId || loading} className="btn-primary px-6 flex items-center gap-2">
          <Send className="w-4 h-4" /> Send
        </button>
      </div>
    </div>
  );
}
