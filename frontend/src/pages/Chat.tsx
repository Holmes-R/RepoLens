import { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { chatWithRepo, getAnalysis, analyzeRepo } from '../api/client';
import type { AnalysisResult } from '../types';
import { Send, Loader2, AlertCircle, MessageSquare, Bot, User, FileText, BarChart3 } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  error?: boolean;
}

export function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const [url, setUrl] = useState('');
  const [analysisId, setAnalysisId] = useState<string | null>(id || null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [loadingExisting, setLoadingExisting] = useState(false);
  const [error, setError] = useState('');
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (id) {
      setLoadingExisting(true);
      getAnalysis(id).then((analysis) => {
        setResult(analysis);
        setMessages([{
          role: 'assistant',
          content: `I've analyzed **${analysis.repository.name}**. Ask me anything — architecture, code flow, specific functions, how things work.`,
        }]);
      }).catch(() => setAnalysisId(null)).finally(() => setLoadingExisting(false));
    }
  }, [id]);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setAnalyzing(true);
    setError('');
    try {
      const res = await analyzeRepo({ repo_url: url.trim() });
      setAnalysisId(res.analysis_id);
      window.history.replaceState(null, '', `/chat/${res.analysis_id}`);
      const analysis = await getAnalysis(res.analysis_id);
      setResult(analysis);
      setMessages([{
        role: 'assistant',
        content: `I've analyzed **${analysis.repository.name}**. Ask me anything — architecture, code flow, specific functions, how things work.`,
      }]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze repository');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !analysisId || loading) return;
    const userMsg: Message = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const res = await chatWithRepo({ analysis_id: analysisId, message: userMsg.content, history });
      setMessages(prev => [...prev, { role: 'assistant', content: res.response, sources: res.sources }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.response?.data?.detail || 'Failed to get response'}`, error: true }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-1px)] p-6 max-w-4xl mx-auto flex flex-col">
      {loadingExisting ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-10 h-10 animate-spin text-primary-500 mx-auto mb-3" />
            <p className="text-sm text-zinc-500">Loading analysis...</p>
          </div>
        </div>
      ) : !analysisId ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-lg">
            <div className="w-14 h-14 bg-primary-900/30 flex items-center justify-center mx-auto mb-5 border border-primary-800/30">
              <MessageSquare className="w-7 h-7 text-primary-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">AI Repository Chat</h1>
            <p className="text-sm text-zinc-500 mb-6">Analyze any GitHub repo with natural language questions.</p>
            <form onSubmit={handleAnalyze} className="flex gap-2">
              <input type="text" value={url} onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/user/repository" className="input flex-1 text-sm" />
              <button type="submit" disabled={analyzing} className="btn-primary text-sm flex items-center gap-2">
                {analyzing ? <Loader2 className="w-4 h-4 animate-spin" /> : <BarChart3 className="w-4 h-4" />} Analyze
              </button>
            </form>
            {error && (
              <div className="flex items-center gap-2 text-xs text-red-400 bg-red-900/20 border border-red-800/50 px-3 py-2 mt-3">
                <AlertCircle className="w-4 h-4 shrink-0" /> {error}
              </div>
            )}
            <div className="mt-6 grid grid-cols-2 gap-2 text-left">
              {['Explain the authentication flow', 'Where is the main entry point?', 'Describe the architecture', 'Find all API routes', 'Explain how caching works', 'What does this app do?'].map((q) => (
                <button key={q} onClick={() => setUrl(q)}
                  className="text-xs text-zinc-600 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 px-3 py-2 text-left transition-colors">"{q}"</button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-3 mb-3 pb-3 border-b border-zinc-800">
            <div className="w-7 h-7 bg-primary-900/30 flex items-center justify-center">
              <Bot className="w-4 h-4 text-primary-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">{result?.repository.name || 'Repository'}</p>
              <p className="text-[11px] text-zinc-600">AI chat</p>
            </div>
            <Link to="/chat" onClick={() => { setAnalysisId(null); setResult(null); setMessages([]); }} className="text-[11px] text-zinc-600 hover:text-zinc-400 underline">New analysis</Link>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 mb-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-7 h-7 flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-zinc-800' : 'bg-primary-900/30'}`}>
                  {msg.role === 'user' ? <User className="w-3.5 h-3.5 text-zinc-500" /> : <Bot className="w-3.5 h-3.5 text-primary-400" />}
                </div>
                <div className={`max-w-[75%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                  <div className={`px-3 py-2 text-sm ${
                    msg.role === 'user' ? 'bg-primary-600 text-white' :
                    msg.error ? 'bg-red-900/20 text-red-400 border border-red-800/50' :
                    'bg-zinc-900 border border-zinc-800 text-zinc-300'
                  }`}>
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1 justify-end">
                      {msg.sources.slice(0, 5).map((src, j) => (
                        <span key={j} className="text-[10px] bg-zinc-900 text-zinc-600 border border-zinc-800 px-1.5 py-0.5 flex items-center gap-1">
                          <FileText className="w-2.5 h-2.5" /> {src.split('/').pop()}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-7 h-7 bg-primary-900/30 flex items-center justify-center shrink-0">
                  <Bot className="w-3.5 h-3.5 text-primary-400" />
                </div>
                <div className="bg-zinc-900 border border-zinc-800 px-3 py-2">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 bg-zinc-700 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-zinc-700 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-zinc-700 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          <div className="flex gap-2">
            <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              placeholder="Ask about the repository..." className="input flex-1 text-sm" disabled={loading} />
            <button onClick={handleSend} disabled={loading || !input.trim()} className="btn-primary px-4">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
