import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { analyzeRepo, getAllDiagrams, getAnalysis } from '../api/client';
import { Loader2, Search, ArrowLeft, MessageSquare } from 'lucide-react';
import { MermaidDiagram } from '../components/MermaidDiagram';

const DIAGRAM_TYPES = ['architecture', 'dependency', 'sequence', 'directory', 'layer'];

export function DiagramsPage() {
  const { id } = useParams<{ id: string }>();
  const [url, setUrl] = useState('');
  const [repoName, setRepoName] = useState('');
  const [repoId, setRepoId] = useState('');
  const [diagrams, setDiagrams] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [loadingExisting, setLoadingExisting] = useState(Boolean(id));
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('architecture');
  const navigate = useNavigate();

  useEffect(() => {
    if (id) {
      setLoadingExisting(true);
      Promise.all([getAllDiagrams(id), getAnalysis(id)]).then(([res, analysis]) => {
        setDiagrams(res.diagrams || {});
        setRepoName(analysis.repository.name);
        setRepoId(analysis.repository.id);
      }).catch((err: any) => {
        setError(err.response?.data?.detail || 'Failed to load diagrams');
      }).finally(() => setLoadingExisting(false));
    }
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await analyzeRepo({ repo_url: url.trim() });
      navigate(`/diagrams/${res.analysis_id}`);
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || err.message?.includes('NetworkError')) {
        setError('Cannot connect to backend server. Make sure it is running on http://127.0.0.1:8000');
      } else if (err.response?.status === 404) {
        setError('Analysis not found. The server may have restarted — please submit again.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to generate diagrams');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {loadingExisting ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-7 h-7 animate-spin text-primary-500" />
        </div>
      ) : (
        <>
          <div className="flex items-center gap-3 mb-5">
            {id && <Link to={`/analysis/${id}`} className="text-zinc-600 hover:text-zinc-400"><ArrowLeft className="w-4 h-4" /></Link>}
            <h1 className="text-xl font-bold text-white">{repoName || 'Architecture Diagrams'}</h1>
            {repoId && <Link to={`/chat/${repoId}`} className="flex items-center gap-1.5 text-xs text-primary-500 hover:text-primary-400 bg-primary-900/20 border border-primary-800/30 px-2.5 py-1.5"><MessageSquare className="w-3 h-3" /> Chat</Link>}
          </div>

          {(!id || error) && (
            <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
              <input type="text" value={url} onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/user/repository" className="input flex-1 text-sm" />
              <button type="submit" disabled={loading} className="btn-primary text-sm flex items-center gap-2">
                <Search className="w-3.5 h-3.5" /> Generate
              </button>
            </form>
          )}

          {loading && <div className="flex items-center justify-center py-16"><Loader2 className="w-7 h-7 animate-spin text-primary-500" /></div>}
          {error && <div className="text-xs text-red-400 bg-red-900/20 border border-red-800/50 px-3 py-2 mb-6">{error}</div>}

          {Object.keys(diagrams).length > 0 && (
            <div>
              <div className="flex gap-4 border-b border-zinc-800 mb-5">
                {DIAGRAM_TYPES.map((type) => (
                  <button key={type} onClick={() => setActiveTab(type)}
                    className={`pb-2 text-xs font-medium capitalize transition-colors ${
                      activeTab === type ? 'tab-active' : 'tab-inactive'
                    }`}>{type}</button>
                ))}
              </div>
              <div className="card">
                <h3 className="text-xs font-semibold text-white uppercase tracking-wider mb-3">{activeTab} Diagram</h3>
                <MermaidDiagram code={diagrams[activeTab]} className="bg-zinc-950 p-4 min-h-[300px]" />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
