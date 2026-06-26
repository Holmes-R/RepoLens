import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setAnalyzing(true);
    setError('');
    try {
      const res = await analyzeRepo({ repo_url: url.trim() });
      setAnalysisId(res.analysis_id);
      const analysis = await getAnalysis(res.analysis_id);
      setResult(analysis);
      setMessages([{
        role: 'assistant',
        content: `I've analyzed **${analysis.repository.name}**. You can ask me anything about it — architecture, code flow, specific functions, how things work, etc.`,
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
      const res = await chatWithRepo({
        analysis_id: analysisId,
        message: userMsg.content,
        history,
      });
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.response,
        sources: res.sources,
      }]);
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to get response';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${detail}`,
        error: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-2rem)] p-6 max-w-5xl mx-auto flex flex-col">
      {!analysisId ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-xl">
            <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <MessageSquare className="w-8 h-8 text-primary-600" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900 mb-3">AI Repository Chat</h1>
            <p className="text-slate-500 mb-8">
              Analyze any GitHub repository, then ask questions in natural language.
            </p>
            <form onSubmit={handleAnalyze} className="flex gap-3">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/user/repository"
                className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
              />
              <button type="submit" disabled={analyzing} className="btn-primary flex items-center gap-2">
                {analyzing ? <Loader2 className="w-4 h-4 animate-spin" /> : <BarChart3 className="w-4 h-4" />}
                Analyze
              </button>
            </form>
            {error && (
              <div className="flex items-center gap-2 text-red-600 bg-red-50 px-4 py-3 rounded-lg mt-4">
                <AlertCircle className="w-5 h-5" /> {error}
              </div>
            )}
            <div className="mt-8 grid grid-cols-2 gap-3 text-left">
              {[
                'Explain the authentication flow',
                'What does this function do?',
                'Where is the main entry point?',
                'Describe the project architecture',
                'How are dependencies managed?',
                'Find all API routes',
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => { setUrl(q); }}
                  className="text-sm text-slate-500 bg-slate-50 hover:bg-slate-100 rounded-lg px-3 py-2 text-left transition-colors"
                >
                  "{q}"
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-3 mb-4 pb-4 border-b border-slate-200">
            <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4 text-primary-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-slate-900 truncate">{result?.repository.name || 'Repository'}</p>
              <p className="text-xs text-slate-400">AI-powered code analysis</p>
            </div>
            <button onClick={() => { setAnalysisId(null); setResult(null); setMessages([]); }} className="text-xs text-slate-400 hover:text-slate-600 underline">
              New analysis
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-primary-600" />
                  </div>
                )}
                <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                  <div className={`rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : msg.error
                        ? 'bg-red-50 text-red-700 border border-red-200'
                        : 'bg-white border border-slate-200 text-slate-800'
                  }`}>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {msg.sources.slice(0, 5).map((src, j) => (
                        <span key={j} className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          {src.split('/').pop()}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center shrink-0">
                    <User className="w-4 h-4 text-slate-500" />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-primary-600" />
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              placeholder="Ask about the repository..."
              className="flex-1 px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 outline-none"
              disabled={loading}
            />
            <button onClick={handleSend} disabled={loading || !input.trim()} className="btn-primary px-5 py-3">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
