import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getAnalysis, analyzeRepo, getAllDiagrams } from '../api/client';
import type { AnalysisResult, DatabaseTable } from '../types';
import mermaid from 'mermaid';
import {
  Loader2, AlertCircle, Search, Layers, GitBranch, Box, Workflow, FileSearch,
  Puzzle, ArrowRight, Star, GitFork, Users, GitCommit, Database, FolderTree,
  Code2, Download, X, ChevronRight, ChevronDown, Table2,
  BookOpen, BarChart3, MessageSquare
} from 'lucide-react';

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

const DIAGRAM_TABS = [
  { key: 'architecture', label: 'Architecture', icon: Layers },
  { key: 'dependency', label: 'Dependencies', icon: GitBranch },
  { key: 'sequence', label: 'Sequence', icon: Workflow },
  { key: 'directory', label: 'Directory', icon: FolderTree },
  { key: 'layer', label: 'Layers', icon: Box },
] as const;

const INFO_TABS = [
  { key: 'overview', label: 'Overview', icon: BarChart3 },
  { key: 'architecture', label: 'Architecture', icon: Layers },
  { key: 'dependencies', label: 'Dependencies', icon: GitBranch },
  { key: 'database', label: 'Database', icon: Database },
  { key: 'callgraph', label: 'Call Graph', icon: Workflow },
  { key: 'diagrams', label: 'Diagrams', icon: FolderTree },
  { key: 'contributors', label: 'Contributors', icon: Users },
] as const;

export function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [diagrams, setDiagrams] = useState<Record<string, string>>({});
  const [activeDiagram, setActiveDiagram] = useState('architecture');
  const diagramRendered = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (id) loadAnalysis(id);
  }, [id]);

  useEffect(() => {
    if (result) {
      setUrl(result.repository.url);
      if (!result.diagrams && result.repository?.id) {
        getAllDiagrams(result.repository.id).then(r => setDiagrams(r.diagrams || {})).catch(() => {});
      } else if (result?.diagrams) {
        setDiagrams(result.diagrams);
      }
    }
  }, [result]);

  useEffect(() => {
    if (activeTab === 'diagrams' && diagrams[activeDiagram]) {
      const key = `diagram-${activeDiagram}`;
      if (diagramRendered.current.has(key)) return;
      diagramRendered.current.add(key);
      setTimeout(() => {
        const el = document.getElementById(key);
        if (el) {
          el.innerHTML = '<div class="text-zinc-600 text-sm animate-pulse">Rendering...</div>';
          mermaid.render(`svg-${activeDiagram}`, diagrams[activeDiagram])
            .then(({ svg }) => { el.innerHTML = svg; })
            .catch((err: Error) => {
              el.innerHTML = `<pre class="text-red-400 text-xs">${err.message || 'Failed to render'}</pre>`;
            });
        }
      }, 50);
    }
  }, [activeTab, activeDiagram, diagrams]);

  const loadAnalysis = async (analysisId: string) => {
    setLoading(true);
    try {
      const res = await getAnalysis(analysisId);
      setResult(res);
      setUrl(res.repository.url);
    } catch (_err: any) {
      // silently fall back to input form
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await analyzeRepo({ repo_url: url.trim() });
      await loadAnalysis(res.analysis_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze');
    } finally {
      setLoading(false);
    }
  };

  const exportReport = () => {
    if (!result) return;
    const data = {
      repository: result.repository,
      analyzed_at: result.analyzed_at,
      languages: result.language_stats,
      frameworks: result.frameworks,
      architecture: result.architecture,
      complexity: result.complexity,
      dependencies: result.dependencies,
      modules: result.modules,
      contributors: result.contributors,
      commit_count: result.commit_messages.length,
      database_tables: result.database_schema.length,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.repository.name}-analysis.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading && !result) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-primary-500 mx-auto mb-3" />
          <p className="text-sm text-zinc-500">Analyzing repository...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-2 mb-5">
        <form onSubmit={handleSubmit} className="flex-1 flex gap-2">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/user/repository"
            className="input flex-1 text-sm"
          />
          <button type="submit" disabled={loading} className="btn-primary text-sm flex items-center gap-2">
            <Search className="w-3.5 h-3.5" /> {loading ? '...' : 'Analyze'}
          </button>
        </form>
        {result && (
          <button onClick={exportReport} className="btn-secondary text-sm flex items-center gap-2">
            <Download className="w-3.5 h-3.5" /> Export
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-400 bg-red-900/20 border border-red-800/50 px-3 py-2 mb-5">
          <AlertCircle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {result && (
        <div className="space-y-5">
          <div className="card">
            <div className="flex items-start justify-between mb-3">
              <div className="min-w-0">
                <h2 className="text-xl font-bold text-white truncate">{result.repository.name}</h2>
                <a href={result.repository.url} className="text-xs text-primary-500 hover:underline" target="_blank" rel="noreferrer">
                  {result.repository.url}
                </a>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Link to={`/diagrams/${result.repository.id}`} className="flex items-center gap-1.5 text-xs text-purple-500 hover:text-purple-400 bg-purple-900/20 border border-purple-800/30 px-2.5 py-1.5 transition-colors">
                  <FolderTree className="w-3.5 h-3.5" /> Diagrams
                </Link>
                <Link to={`/chat/${result.repository.id}`} className="flex items-center gap-1.5 text-xs text-primary-500 hover:text-primary-400 bg-primary-900/20 border border-primary-800/30 px-2.5 py-1.5 transition-colors">
                  <MessageSquare className="w-3.5 h-3.5" /> Chat
                </Link>
                <span className={`badge ${result.repository.status === 'completed' ? 'bg-green-900/30 text-green-400 border border-green-800/50' : 'bg-yellow-900/30 text-yellow-400 border border-yellow-800/50'}`}>
                  {result.repository.status}
                </span>
              </div>
            </div>
            {result.repository.description && <p className="text-sm text-zinc-500">{result.repository.description}</p>}
          </div>

          <div className="grid grid-cols-6 gap-px bg-zinc-800">
            <StatCard label="Stars" value={result.repository.stars.toLocaleString()} icon={<Star className="w-3.5 h-3.5 text-amber-500" />} />
            <StatCard label="Forks" value={result.repository.forks.toLocaleString()} icon={<GitFork className="w-3.5 h-3.5 text-blue-500" />} />
            <StatCard label="Contributors" value={result.contributors.length.toString()} icon={<Users className="w-3.5 h-3.5 text-green-500" />} />
            <StatCard label="Languages" value={result.language_stats.length.toString()} icon={<Code2 className="w-3.5 h-3.5 text-purple-500" />} />
            <StatCard label="Dependencies" value={result.dependencies.length.toString()} icon={<Box className="w-3.5 h-3.5 text-sky-500" />} />
            <StatCard label="Modules" value={result.modules.length.toString()} icon={<FolderTree className="w-3.5 h-3.5 text-orange-500" />} />
          </div>

          <div className="flex gap-6 border-b border-zinc-800">
            {INFO_TABS.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-1.5 pb-2 text-xs font-medium transition-colors ${
                    activeTab === tab.key ? 'tab-active' : 'tab-inactive'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" /> {tab.label}
                </button>
              );
            })}
          </div>

          <div>
            {activeTab === 'overview' && (
              <OverviewTab result={result} search={searchQuery} onSearchChange={setSearchQuery} />
            )}
            {activeTab === 'architecture' && result.architecture && (
              <ArchitectureTab result={result} />
            )}
            {activeTab === 'dependencies' && (
              <DependenciesTab deps={result.dependencies} searchQuery={searchQuery} />
            )}
            {activeTab === 'database' && (
              <DatabaseTab tables={result.database_schema} />
            )}
            {activeTab === 'callgraph' && (
              <CallGraphTab callGraph={result.call_graph} search={searchQuery} />
            )}
            {activeTab === 'contributors' && (
              <ContributorsTab result={result} search={searchQuery} />
            )}
            {activeTab === 'diagrams' && (
              <div>
                <div className="flex gap-1 mb-4">
                  {DIAGRAM_TABS.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.key}
                        onClick={() => { setActiveDiagram(tab.key); diagramRendered.current.delete(`diagram-${tab.key}`); }}
                        className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                          activeDiagram === tab.key ? 'bg-primary-900/30 text-primary-400' : 'text-zinc-500 hover:text-zinc-300 bg-zinc-900'
                        }`}
                      >
                        <Icon className="w-3 h-3 inline mr-1" /> {tab.label}
                      </button>
                    );
                  })}
                </div>
                <div className="card">
                  <h3 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">{activeDiagram} Diagram</h3>
                  <div id={`diagram-${activeDiagram}`} className="bg-zinc-950 p-4 min-h-[400px]" />
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function OverviewTab({ result, search, onSearchChange }: {
  result: AnalysisResult; search: string; onSearchChange: (v: string) => void;
}) {
  const filteredLanguages = result.language_stats.filter(l =>
    !search || l.language.toLowerCase().includes(search.toLowerCase())
  );
  const filteredFrameworks = result.frameworks.filter(f =>
    !search || f.name.toLowerCase().includes(search.toLowerCase())
  );
  const filteredCommits = result.commit_messages.filter(c =>
    !search || c.message.toLowerCase().includes(search.toLowerCase()) || c.author.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      {(result.modules.length > 0 || result.commit_messages.length > 0 || result.language_stats.length > 0) && (
        <div className="card mb-5">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-zinc-600 shrink-0" />
            <input
              type="text"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search repository entities..."
              className="flex-1 text-sm bg-transparent border-0 outline-none text-zinc-300 placeholder-zinc-600"
            />
            {search && (
              <button onClick={() => onSearchChange('')} className="text-zinc-600 hover:text-zinc-400">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}
      <div className="grid grid-cols-2 gap-5">
        <div className="card">
          <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Languages ({filteredLanguages.length})</h3>
          <div className="space-y-2.5">
            {filteredLanguages.map((lang) => (
              <div key={lang.language}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span className="text-zinc-300">{lang.language}</span>
                  <span className="text-zinc-500">{lang.percentage}% ({lang.files} files)</span>
                </div>
                <div className="w-full bg-zinc-800 h-1">
                  <div className="bg-primary-700 h-1" style={{ width: `${lang.percentage}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Complexity</h3>
          {result.complexity ? (
            <div className="grid grid-cols-2 gap-3">
              <MetricItem label="Files" value={result.complexity.total_files} />
              <MetricItem label="Lines" value={result.complexity.total_lines} />
              <MetricItem label="Functions" value={result.complexity.total_functions} />
              <MetricItem label="Classes" value={result.complexity.total_classes} />
              <MetricItem label="Avg Function" value={`${result.complexity.avg_function_length} lines`} />
              <MetricItem label="Avg Complexity" value={result.complexity.avg_complexity.toFixed(2)} />
            </div>
          ) : (
            <p className="text-xs text-zinc-600">No complexity data</p>
          )}
        </div>
        {filteredFrameworks.length > 0 && (
          <div className="card">
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Frameworks ({filteredFrameworks.length})</h3>
            <div className="flex flex-wrap gap-1.5">
              {filteredFrameworks.map((fw) => (
                <span key={fw.name} className="text-xs bg-primary-900/20 text-primary-400 border border-primary-800/30 px-2 py-1">
                  {fw.name}{fw.version ? ` v${fw.version}` : ''}
                </span>
              ))}
            </div>
          </div>
        )}
        {filteredCommits.length > 0 && (
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <GitCommit className="w-3.5 h-3.5 text-sky-500" />
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Recent Commits ({filteredCommits.length})</h3>
            </div>
            <div className="space-y-1 max-h-60 overflow-y-auto">
              {filteredCommits.map((c, i) => (
                <div key={i} className="flex items-start gap-2 text-xs py-1.5 border-b border-zinc-800 last:border-0">
                  <span className="text-zinc-600 font-mono shrink-0">{c.sha.slice(0, 7)}</span>
                  <p className="flex-1 text-zinc-400 truncate">{c.message}</p>
                  <span className="text-zinc-600 shrink-0">{c.author}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ArchitectureTab({ result }: { result: AnalysisResult }) {
  if (!result.architecture) return null;
  const arch = result.architecture;
  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-4">
        <Layers className="w-5 h-5 text-purple-400" />
        <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Architecture Analysis</h3>
      </div>
      <div className="flex items-center gap-3 mb-4">
        <span className="text-base font-bold text-purple-400">{arch.pattern}</span>
        <span className="badge bg-purple-900/30 text-purple-400 border border-purple-800/50">{arch.confidence}%</span>
      </div>
      <p className="text-sm text-zinc-400 mb-5">{arch.description}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="bg-zinc-800/50 p-4">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch className="w-3.5 h-3.5 text-zinc-500" />
            <h4 className="text-xs font-semibold text-zinc-500 uppercase">Layers Detected</h4>
          </div>
          {arch.layers.length > 0 ? (
            <div className="space-y-1.5">
              {arch.layers.map((layer, i) => (
                <div key={layer} className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-purple-900/30 text-purple-400 border border-purple-800/50 flex items-center justify-center text-[10px] font-bold">{i + 1}</span>
                  <span className="text-sm text-zinc-300">{layer}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-zinc-600">No specific layers</p>
          )}
        </div>
        <div className="bg-zinc-800/50 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Box className="w-3.5 h-3.5 text-zinc-500" />
            <h4 className="text-xs font-semibold text-zinc-500 uppercase">How It Was Detected</h4>
          </div>
          <p className="text-xs text-zinc-500 mb-3">Scanned <strong className="text-zinc-300">{result.modules.length} modules</strong> across the codebase.</p>
          {arch.scores && Object.keys(arch.scores).length > 0 && (
            <div className="mb-3">
              <p className="text-[10px] font-semibold text-zinc-600 uppercase mb-1.5">Pattern Scores</p>
              <div className="space-y-1">
                {Object.entries(arch.scores).sort(([, a], [, b]) => b - a).slice(0, 5).map(([pattern, score]) => {
                  const isWinner = pattern === arch.pattern;
                  const max = Math.max(...Object.values(arch.scores!));
                  const w = max > 0 ? (score / max) * 100 : 0;
                  return (
                    <div key={pattern} className="flex items-center gap-2">
                      <span className={`text-[11px] w-28 truncate shrink-0 ${isWinner ? 'text-purple-400 font-semibold' : 'text-zinc-500'}`}>
                        {isWinner && <ArrowRight className="w-2.5 h-2.5 inline mr-0.5 text-purple-400" />}{pattern}
                      </span>
                      <div className="flex-1 bg-zinc-800 h-1">
                        <div className={`h-1 ${isWinner ? 'bg-purple-500' : 'bg-zinc-700'}`} style={{ width: `${w}%` }} />
                      </div>
                      <span className="text-[10px] text-zinc-600 w-6 text-right">{score.toFixed(1)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {arch.evidence && arch.evidence.length > 0 && (
            <div className="mb-3">
              <p className="text-[10px] font-semibold text-zinc-600 uppercase mb-1.5">Key Evidence</p>
              <div className="flex flex-wrap gap-1">
                {arch.evidence.slice(0, 8).map((item, i) => (
                  <span key={i} className="text-[10px] bg-zinc-900 border border-zinc-800 text-zinc-500 px-1.5 py-0.5">{item}</span>
                ))}
              </div>
            </div>
          )}
          {result.frameworks.length > 0 && (
            <div className="mb-2">
              <p className="text-[10px] font-semibold text-zinc-600 uppercase mb-1.5">Related Frameworks</p>
              <div className="flex flex-wrap gap-1">
                {result.frameworks.map((fw) => (
                  <span key={fw.name} className="text-[10px] bg-purple-900/20 text-purple-400 border border-purple-800/30 px-1.5 py-0.5">{fw.name}{fw.version ? ` v${fw.version}` : ''}</span>
                ))}
              </div>
            </div>
          )}
          <div className="flex items-center gap-1.5 text-[10px] text-zinc-600 pt-2 border-t border-zinc-800">
            <Workflow className="w-3 h-3" /> Detected via dir structure, file naming & source patterns
          </div>
        </div>
      </div>
    </div>
  );
}

function DependenciesTab({ deps, searchQuery }: { deps: { name: string; version: string; type: string; source: string; source_file?: string }[]; searchQuery: string }) {
  const [expanded, setExpanded] = useState(false);
  const filtered = deps.filter(d => !searchQuery || d.name.toLowerCase().includes(searchQuery.toLowerCase()));
  const displayDeps = expanded ? filtered : filtered.slice(0, 50);
  return (
    <div className="card">
      <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Dependencies ({filtered.length})</h3>
      {filtered.length === 0 ? (
        <div className="text-center py-8">
          <Box className="w-10 h-10 text-zinc-700 mx-auto mb-2" />
          <p className="text-xs text-zinc-600">No dependencies detected</p>
          <p className="text-[10px] text-zinc-700 mt-1">Scanned package.json, requirements.txt, Cargo.toml, go.mod, Gemfile, pubspec.yaml, pom.xml</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-zinc-600 border-b border-zinc-800">
                  <th className="pb-2 font-medium">Name</th>
                  <th className="pb-2 font-medium">Version</th>
                  <th className="pb-2 font-medium">Source</th>
                </tr>
              </thead>
              <tbody>
                {displayDeps.map((d, i) => (
                  <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                    <td className="py-1.5 text-zinc-300 font-medium">{d.name}</td>
                    <td className="py-1.5 text-zinc-500">{d.version}</td>
                    <td className="py-1.5"><span className="badge text-[10px]">{d.source}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length > 50 && (
            <button onClick={() => setExpanded(!expanded)} className="mt-2 text-xs text-primary-500 hover:underline">
              {expanded ? 'Show less' : `Show all ${filtered.length} dependencies`}
            </button>
          )}
        </>
      )}
    </div>
  );
}

function DatabaseTab({ tables }: { tables: DatabaseTable[] }) {
  const [expandedTable, setExpandedTable] = useState<string | null>(null);
  if (tables.length === 0) {
    return (
      <div className="card text-center py-10">
        <Table2 className="w-10 h-10 text-zinc-700 mx-auto mb-2" />
        <p className="text-xs text-zinc-600">No database schema detected</p>
        <p className="text-[10px] text-zinc-700 mt-1">Scanned SQL files, migrations, ORM models, Prisma schemas</p>
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {tables.map((tbl) => (
        <div key={tbl.name} className="card">
          <button onClick={() => setExpandedTable(expandedTable === tbl.name ? null : tbl.name)} className="flex items-center gap-2 w-full text-left">
            {expandedTable === tbl.name ? <ChevronDown className="w-3.5 h-3.5 text-zinc-600" /> : <ChevronRight className="w-3.5 h-3.5 text-zinc-600" />}
            <Database className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-sm font-semibold text-white">{tbl.name}</span>
            <span className="text-[10px] text-zinc-600">({tbl.columns.length} cols{tbl.foreign_keys.length > 0 ? `, ${tbl.foreign_keys.length} FK` : ''})</span>
          </button>
          {expandedTable === tbl.name && (
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-zinc-600 border-b border-zinc-800">
                    <th className="pb-1.5 font-medium">Column</th>
                    <th className="pb-1.5 font-medium">Type</th>
                    <th className="pb-1.5 font-medium">PK</th>
                    <th className="pb-1.5 font-medium">FK</th>
                  </tr>
                </thead>
                <tbody>
                  {tbl.columns.map((col) => {
                    const fk = tbl.foreign_keys.find(f => f.column === col.name);
                    return (
                      <tr key={col.name} className="border-b border-zinc-800/30">
                        <td className="py-1 text-zinc-300 font-medium">{col.name}</td>
                        <td className="py-1 text-zinc-500"><strong className="font-semibold">{col.type}</strong></td>
                        <td className="py-1">{col.primary_key ? <span className="text-[10px] text-amber-500 font-bold">PK</span> : ''}</td>
                        <td className="py-1 text-[10px] text-blue-400">{fk ? `${fk.references_table}.${fk.references_column}` : ''}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function CallGraphTab({ callGraph, search }: { callGraph: Record<string, string[]>; search: string }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const entries = Object.entries(callGraph).filter(([fn]) => !search || fn.toLowerCase().includes(search.toLowerCase()));
  if (entries.length === 0) {
    return (
      <div className="card text-center py-10">
        <Workflow className="w-10 h-10 text-zinc-700 mx-auto mb-2" />
        <p className="text-xs text-zinc-600">No call graph data</p>
        <p className="text-[10px] text-zinc-700 mt-1">Generated for .py, .js, .ts, .go, .rs, .java, .php, .rb files</p>
      </div>
    );
  }
  return (
    <div className="card">
      <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Call Graph ({entries.length} functions)</h3>
      <div className="space-y-0.5">
        {entries.slice(0, 100).map(([fn, calls]) => (
          <div key={fn}>
            <button onClick={() => setExpanded(prev => ({ ...prev, [fn]: !prev[fn] }))}
              className="flex items-center gap-2 w-full text-left py-1.5 hover:bg-zinc-800/30 text-xs">
              {expanded[fn] ? <ChevronDown className="w-3 h-3 text-zinc-600" /> : <ChevronRight className="w-3 h-3 text-zinc-600" />}
              <strong className="text-zinc-300 font-semibold">{fn}</strong>
              <span className="text-zinc-600">({calls.length})</span>
            </button>
            {expanded[fn] && calls.length > 0 && (
              <div className="ml-5 pl-3 border-l border-zinc-800 space-y-0.5 mb-1">
                {calls.map((callee, i) => (
                  <div key={i} className="text-xs text-zinc-500 flex items-center gap-1.5 py-0.5">
                    <ArrowRight className="w-2.5 h-2.5 text-zinc-700" /> <strong className="font-semibold text-zinc-500">{callee}</strong>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ContributorsTab({ result, search }: { result: AnalysisResult; search: string }) {
  const filteredContributors = result.contributors.filter(c => !search || (c.name || '').toLowerCase().includes(search.toLowerCase()));
  const filteredCommits = result.commit_messages.filter(c => !search || c.message.toLowerCase().includes(search.toLowerCase()) || c.author.toLowerCase().includes(search.toLowerCase()));
  return (
    <div className="grid grid-cols-2 gap-5">
      {filteredContributors.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-4 h-4 text-green-500" />
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Contributors ({filteredContributors.length})</h3>
          </div>
          <div className="grid grid-cols-2 gap-2 max-h-72 overflow-y-auto">
            {filteredContributors.filter(c => c.name).map((c, i) => (
              <div key={i} className="flex items-center gap-2 p-2 bg-zinc-800/50">
                <div className="w-7 h-7 bg-green-900/30 text-green-400 border border-green-800/50 flex items-center justify-center text-xs font-bold shrink-0">
                  {(c.name || '?')[0].toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-zinc-300 truncate">{c.name}</p>
                  <p className="text-[10px] text-zinc-600">{c.commits ?? 0} commit{(c.commits ?? 0) !== 1 ? 's' : ''}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {filteredCommits.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <GitCommit className="w-4 h-4 text-sky-500" />
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Recent Commits ({filteredCommits.length})</h3>
          </div>
          <div className="space-y-1.5 max-h-72 overflow-y-auto">
            {filteredCommits.map((c, i) => (
              <div key={i} className="flex items-start gap-2 text-xs py-1.5 border-b border-zinc-800 last:border-0">
                <span className="text-zinc-600 font-mono shrink-0">{c.sha.slice(0, 7)}</span>
                <p className="flex-1 text-zinc-400 truncate">{c.message}</p>
                <span className="text-zinc-600 shrink-0">{c.author}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {result.readme_content && (
        <div className="card col-span-2">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="w-4 h-4 text-zinc-500" />
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">README</h3>
          </div>
          <pre className="text-xs text-zinc-300 whitespace-pre-wrap max-h-72 overflow-y-auto bg-zinc-800/50 p-3">{result.readme_content}</pre>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div className="bg-zinc-900 p-4 text-center">
      {icon && <div className="flex justify-center mb-1">{icon}</div>}
      <div className="text-lg font-bold text-primary-400 mb-0.5">{value}</div>
      <div className="text-[10px] text-zinc-600 uppercase tracking-wider">{label}</div>
    </div>
  );
}

function MetricItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-zinc-800/30 p-2.5">
      <div className="text-[10px] text-zinc-600 uppercase">{label}</div>
      <div className="text-sm font-semibold text-zinc-200">{value}</div>
    </div>
  );
}
