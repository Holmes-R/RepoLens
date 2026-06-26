import { useState, useEffect } from 'react';
import { analyzeRepo, getAnalysis, getAllDiagrams } from '../api/client';
import { Loader2, Search } from 'lucide-react';
import mermaid from 'mermaid';

mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' });

const DIAGRAM_TYPES = ['architecture', 'dependency', 'sequence', 'class', 'layer'];

export function DiagramsPage() {
  const [url, setUrl] = useState('');
  const [diagrams, setDiagrams] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('architecture');

  const renderDiagram = (type: string) => {
    const code = diagrams[type];
    if (!code) return;
    setTimeout(() => {
      const el = document.getElementById(`diagram-${type}`);
      if (el) {
        el.innerHTML = '';
        mermaid.render(`svg-${type}`, code).then(({ svg }) => { el.innerHTML = svg; }).catch(() => {
          el.innerHTML = '<pre class="text-red-500 text-sm">Failed to render diagram</pre>';
        });
      }
    }, 100);
  };

  useEffect(() => {
    if (Object.keys(diagrams).length > 0) {
      renderDiagram(activeTab);
    }
  }, [diagrams, activeTab]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await analyzeRepo({ repo_url: url.trim() });
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
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-slate-900 mb-6">Architecture Diagrams</h1>

      <form onSubmit={handleSubmit} className="flex gap-3 mb-8">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/user/repository"
          className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
        />
        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
          <Search className="w-4 h-4" /> Generate Diagrams
        </button>
      </form>

      {loading && <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-primary-600" /></div>}
      {error && <div className="text-red-600 bg-red-50 px-4 py-3 rounded-lg mb-6">{error}</div>}

      {Object.keys(diagrams).length > 0 && (
        <div>
          <div className="flex gap-2 mb-6 border-b border-slate-200 pb-2">
            {DIAGRAM_TYPES.map((type) => (
              <button
                key={type}
                onClick={() => setActiveTab(type)}
                className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all ${
                  activeTab === type ? 'bg-primary-100 text-primary-700' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
          {DIAGRAM_TYPES.map((type) => (
            <div key={type} className={activeTab !== type ? 'hidden' : ''}>
              <div className="card">
                <h3 className="text-lg font-semibold text-slate-900 mb-4 capitalize">{type} Diagram</h3>
                <div id={`diagram-${type}`} className="bg-white rounded-lg p-4 overflow-auto min-h-[300px]" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
