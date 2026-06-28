import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, GitBranch, BarChart3, Activity, Code2, Network, MessageSquare,
  Database, Layers, Workflow, FolderTree, Shield, Globe, Zap, Github,
} from 'lucide-react';
import { analyzeRepo } from '../api/client';

const SAMPLES = [
  'https://github.com/facebook/react',
  'https://github.com/tailwindlabs/tailwindcss',
  'https://github.com/vercel/next.js',
];

const features = [
  { icon: Layers, label: 'Architecture Detection', desc: 'Identifies MVC, Clean Architecture, layered patterns with confidence scoring. Detects directory conventions, file naming, and source patterns automatically.' },
  { icon: Workflow, label: 'Call Graph', desc: 'Extracts function calls across Python, JS, TS, Go, Rust, Java, PHP, Ruby. Visualizes relationships between modules and functions.' },
  { icon: GitBranch, label: 'Dependency Graph', desc: 'Maps dependencies from npm, PyPI, Cargo, Go modules, RubyGems, Pub, Maven. Groups by source with version info.' },
  { icon: FolderTree, label: 'Directory Tree', desc: 'Generates an interactive project structure diagram. Shows depth-limited directory hierarchy for quick orientation.' },
  { icon: Database, label: 'Schema Analysis', desc: 'Detects database schemas from SQL files, migrations, ORM models (Django, SQLAlchemy, TypeORM, Prisma, Laravel, Alembic).' },
  { icon: Code2, label: 'Code Metrics', desc: 'AST-based analysis of files, lines, functions, classes. Computes cyclomatic complexity and average function length.' },
  { icon: MessageSquare, label: 'AI Chat', desc: 'Natural language Q&A about the repository powered by local Ollama. Retrieves relevant source files for context-aware answers.' },
  { icon: Shield, label: 'Framework Detection', desc: 'Identifies frameworks and libraries used across the codebase. Displays versions and related technologies.' },
  { icon: BarChart3, label: 'Language Breakdown', desc: 'Per-file language detection with percentage distribution. Shows line counts and file totals per language.' },
];

const steps = [
  { icon: Github, label: '1. Paste URL', desc: 'Enter any public GitHub repository URL' },
  { icon: Zap, label: '2. Analyze', desc: 'We scan architecture, dependencies, and structure' },
  { icon: BarChart3, label: '3. Explore', desc: 'View diagrams, metrics, and chat with AI about the code' },
];

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

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="text-center pt-12 pb-10">
        <div className="w-14 h-14 bg-primary-900/30 flex items-center justify-center mx-auto mb-6 border border-primary-800/30">
          <BarChart3 className="w-7 h-7 text-primary-400" />
        </div>
        <div className="relative inline-block">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight mb-4 text-transparent bg-clip-text bg-gradient-to-r from-primary-400 via-purple-400 to-sky-400" style={{ WebkitTextFillColor: 'transparent' }}>
            Understand Any Repository
          </h1>
        </div>
        <p className="text-lg text-zinc-500 max-w-2xl mx-auto leading-relaxed">
          Paste a GitHub URL and get instant architecture analysis, interactive diagrams,<br />
          code metrics, and AI-powered insights about the codebase.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto mb-5">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/user/repository"
              className="w-full bg-zinc-900 border border-zinc-800 pl-10 pr-4 py-3.5 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-primary-700 transition-colors"
            />
          </div>
          <button type="submit" disabled={loading || !repoUrl.trim()}
            className="bg-primary-600 text-white px-7 py-3.5 font-semibold hover:bg-primary-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm shrink-0">
            {loading ? (
              <span className="flex items-center gap-2"><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Analyzing</span>
            ) : (
              <><Search className="w-4 h-4" /> Analyze</>
            )}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-red-400 bg-red-900/20 border border-red-800/50 px-3 py-2">{error}</p>}
      </form>

      <div className="flex items-center justify-center gap-3 mb-12">
        <span className="text-xs text-zinc-600 shrink-0">Try:</span>
        {SAMPLES.map((url) => (
          <button key={url} onClick={() => setRepoUrl(url)}
            className="text-xs text-zinc-500 hover:text-zinc-300 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 px-2.5 py-1.5 transition-colors truncate max-w-[220px]">
            {url.replace('https://github.com/', '')}
          </button>
        ))}
      </div>

      <div className="mb-14">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-px flex-1 bg-zinc-800" />
          <span className="text-[11px] text-zinc-600 uppercase tracking-widest font-semibold">How It Works</span>
          <div className="h-px flex-1 bg-zinc-800" />
        </div>
        <div className="grid grid-cols-3 gap-px bg-zinc-800">
          {steps.map((s) => {
            const Icon = s.icon;
            return (
              <div key={s.label} className="bg-zinc-900 p-6 text-center">
                <div className="w-10 h-10 bg-primary-900/20 flex items-center justify-center mx-auto mb-3 border border-primary-800/30">
                  <Icon className="w-5 h-5 text-primary-400" />
                </div>
                <h3 className="text-sm font-semibold text-white mb-1">{s.label}</h3>
                <p className="text-xs text-zinc-500">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mb-14">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-px flex-1 bg-zinc-800" />
          <span className="text-[11px] text-zinc-600 uppercase tracking-widest font-semibold">Capabilities</span>
          <div className="h-px flex-1 bg-zinc-800" />
        </div>
        <div className="grid grid-cols-3 gap-px bg-zinc-800">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.label} className="bg-zinc-900 p-5 hover:bg-zinc-800/80 transition-colors">
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="w-7 h-7 bg-primary-900/25 flex items-center justify-center">
                    <Icon className="w-3.5 h-3.5 text-primary-400" />
                  </div>
                  <h3 className="text-sm font-semibold text-white">{f.label}</h3>
                </div>
                <p className="text-xs text-zinc-500 leading-relaxed">{f.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="text-center py-6 border-t border-zinc-800">
        <div className="flex items-center justify-center gap-6 text-xs text-zinc-700">
          <span className="flex items-center gap-1.5"><Globe className="w-3 h-3" /> GitHub repos</span>
          <span className="flex items-center gap-1.5"><Code2 className="w-3 h-3" /> 12+ languages</span>
          <span className="flex items-center gap-1.5"><Network className="w-3 h-3" /> 7 package managers</span>
          <span className="flex items-center gap-1.5"><Database className="w-3 h-3" /> 8 schema detectors</span>
          <span className="flex items-center gap-1.5"><Zap className="w-3 h-3" /> Local AI (Ollama)</span>
        </div>
      </div>
    </div>
  );
}
