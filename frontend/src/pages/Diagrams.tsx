import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { analyzeRepo, getAllDiagrams, getAnalysis } from '../api/client';
import { Loader2, Search, ArrowLeft, MessageSquare } from 'lucide-react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  securityLevel: 'loose',
  themeVariables: {
    background: '#09090b',
    primaryColor: '#1e1b4b',
    primaryTextColor: '#e4e4e7',
    primaryBorderColor: '#312e81',
    lineColor: '#6366f1',
    secondaryColor: '#27272a',
    tertiaryColor: '#18181b',
    clusterBkg: '#18181b',
    clusterBorder: '#27272a',
    nodeTextColor: '#e4e4e7',
    titleColor: '#e4e4e7',
    edgeLabelBackground: '#27272a',
    nodeBorder: '#312e81',
    mainBkg: '#09090b',
  },
});

const DIAGRAM_TYPES = ['architecture', 'dependency', 'sequence', 'directory', 'layer'];

export function DiagramsPage() {
  const { id } = useParams<{ id: string }>();
  const [url, setUrl] = useState('');
  const [repoName, setRepoName] = useState('');
  const [repoId, setRepoId] = useState('');
  const [diagrams, setDiagrams] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [loadingExisting, setLoadingExisting] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('architecture');

  useEffect(() => {
    if (id) {
      setLoadingExisting(true);
      getAllDiagrams(id).then((res) => {
        setDiagrams(res.diagrams || {});
        getAnalysis(id).then((a) => { setRepoName(a.repository.name); setRepoId(a.repository.id); }).catch(() => {});
      }).catch(() => {}).finally(() => setLoadingExisting(false));
    }
  }, [id]);

  const renderDiagram = (type: string) => {
    const code = diagrams[type];
    if (!code) return;
    setTimeout(() => {
      const el = document.getElementById(`diagram-${type}`);
      if (el) {
        el.innerHTML = '<div class="text-zinc-600 text-sm animate-pulse">Rendering...</div>';
        mermaid.render(`svg-${type}`, code).then(({ svg }) => { el.innerHTML = svg; }).catch((err: Error) => {
          el.innerHTML = `<pre class="text-red-400 text-xs">${err.message || 'Failed to render diagram'}</pre>`;
        });
      }
    }, 50);
  };

  useEffect(() => {
    if (Object.keys(diagrams).length > 0) renderDiagram(activeTab);
  }, [diagrams, activeTab]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await analyzeRepo({ repo_url: url.trim() });
      setRepoName(url.split('/').pop() || '');
      setRepoId(res.analysis_id);
      window.history.replaceState(null, '', `/diagrams/${res.analysis_id}`);
      const diagRes = await getAllDiagrams(res.analysis_id);
      setDiagrams(diagRes.diagrams || {});
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
          {(repoName || !id) && (
            <div className="flex items-center gap-3 mb-5">
              {id && <Link to={`/analysis/${id}`} className="text-zinc-600 hover:text-zinc-400"><ArrowLeft className="w-4 h-4" /></Link>}
              <h1 className="text-xl font-bold text-white">{repoName || 'Architecture Diagrams'}</h1>
              {repoId && <Link to={`/chat/${repoId}`} className="flex items-center gap-1.5 text-xs text-primary-500 hover:text-primary-400 bg-primary-900/20 border border-primary-800/30 px-2.5 py-1.5"><MessageSquare className="w-3 h-3" /> Chat</Link>}
            </div>
          )}

          {!id && (
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
              {DIAGRAM_TYPES.map((type) => (
                <div key={type} className={activeTab !== type ? 'hidden' : ''}>
                  <div className="card">
                    <h3 className="text-xs font-semibold text-white uppercase tracking-wider mb-3">{type} Diagram</h3>
                    <div id={`diagram-${type}`} className="bg-zinc-950 p-4 min-h-[300px]" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
