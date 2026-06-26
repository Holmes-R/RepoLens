import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, GitBranch, Shield, BarChart3, FileText, LayoutDashboard } from 'lucide-react';
import { analyzeRepo } from '../api/client';

export function HomePage() {
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setLoading(true);
    setError('');
    try {
      const result = await analyzeRepo({ repo_url: repoUrl.trim() });
      navigate(`/analysis/${result.analysis_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze repository');
    } finally {
      setLoading(false);
    }
  };

  const features = [
    { icon: GitBranch, label: 'Architecture Detection', desc: 'Automatic pattern recognition' },
    { icon: BarChart3, label: 'Dependency Graph', desc: 'Visual dependency mapping' },
    { icon: Shield, label: 'Security Analysis', desc: 'Vulnerability detection' },
    { icon: FileText, label: 'Documentation', desc: 'Auto-generated docs' },
    { icon: Search, label: 'Code Analysis', desc: 'AST-based understanding' },
    { icon: LayoutDashboard, label: 'Interactive Dashboard', desc: 'All insights in one place' },
  ];

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-slate-900 mb-4">Understand Any Repository</h1>
        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
          Paste a GitHub URL and get instant architecture diagrams, dependency graphs,
          security analysis, and AI-powered explanations.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto mb-12">
        <div className="flex gap-3">
          <input
            type="text"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/user/repository"
            className="flex-1 px-5 py-4 text-lg border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all bg-white"
          />
          <button type="submit" disabled={loading || !repoUrl.trim()} className="btn-primary px-8 py-4 text-lg flex items-center gap-2">
            {loading ? <span className="animate-pulse">Analyzing...</span> : <><Search className="w-5 h-5" /> Analyze</>}
          </button>
        </div>
        {error && <p className="mt-3 text-red-500 text-sm bg-red-50 px-4 py-2 rounded-lg">{error}</p>}
      </form>

      <div className="grid grid-cols-3 gap-6">
        {features.map((f) => {
          const Icon = f.icon;
          return (
            <div key={f.label} className="card hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center mb-4">
                <Icon className="w-6 h-6 text-primary-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-1">{f.label}</h3>
              <p className="text-sm text-slate-500">{f.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
