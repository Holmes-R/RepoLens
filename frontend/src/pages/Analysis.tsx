import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getAnalysis, analyzeRepo, getAllDiagrams } from '../api/client';
import type { AnalysisResult, DatabaseTable } from '../types';
import mermaid from 'mermaid';
import {
  Loader2, AlertCircle, Search, Layers, GitBranch, Box, Workflow, FileSearch,
  Puzzle, ArrowRight, Star, GitFork, Users, GitCommit, Database, FolderTree,
  Code2, Download, Network, X, ChevronRight, ChevronDown, Table2,
  BookOpen, BarChart3
} from 'lucide-react';

mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' });

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
  { key: 'callgraph', label: 'Call Graph', icon: Network },
  { key: 'diagrams', label: 'Diagrams', icon: FileSearch },
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
    if (result && !result.diagrams && result.repository?.id) {
      getAllDiagrams(result.repository.id).then(r => setDiagrams(r.diagrams || {})).catch(() => {});
    } else if (result?.diagrams) {
      setDiagrams(result.diagrams);
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
          el.innerHTML = '<div class="text-slate-400 text-sm animate-pulse">Rendering...</div>';
          mermaid.render(`svg-${activeDiagram}`, diagrams[activeDiagram])
            .then(({ svg }) => { el.innerHTML = svg; })
            .catch((err: Error) => {
              el.innerHTML = `<pre class="text-red-500 text-xs whitespace-pre-wrap">${err.message || 'Failed to render'}</pre>`;
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
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load analysis');
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
          <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-slate-600">Analyzing repository...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <form onSubmit={handleSubmit} className="flex-1 flex gap-3">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/user/repository"
            className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
          />
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            <Search className="w-4 h-4" /> {loading ? '...' : 'Analyze'}
          </button>
        </form>
        {result && (
          <button onClick={exportReport} className="btn-secondary flex items-center gap-2">
            <Download className="w-4 h-4" /> Export
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 px-4 py-3 rounded-lg mb-6">
          <AlertCircle className="w-5 h-5" /> {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">{result.repository.name}</h2>
                <a href={result.repository.url} className="text-primary-600 text-sm hover:underline" target="_blank" rel="noreferrer">
                  {result.repository.url}
                </a>
              </div>
              <div className="flex items-center gap-2">
                <span className={`badge ${result.repository.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                  {result.repository.status}
                </span>
              </div>
            </div>
            {result.repository.description && <p className="text-slate-600 mb-4">{result.repository.description}</p>}
          </div>

          <div className="grid grid-cols-6 gap-4">
            <StatCard label="Stars" value={result.repository.stars.toLocaleString()} icon={<Star className="w-4 h-4 text-amber-500" />} />
            <StatCard label="Forks" value={result.repository.forks.toLocaleString()} icon={<GitFork className="w-4 h-4 text-blue-500" />} />
            <StatCard label="Contributors" value={result.contributors.length.toString()} icon={<Users className="w-4 h-4 text-green-500" />} />
            <StatCard label="Languages" value={result.language_stats.length.toString()} icon={<Code2 className="w-4 h-4 text-purple-500" />} />
            <StatCard label="Dependencies" value={result.dependencies.length.toString()} icon={<Box className="w-4 h-4 text-sky-500" />} />
            <StatCard label="Modules" value={result.modules.length.toString()} icon={<FolderTree className="w-4 h-4 text-orange-500" />} />
          </div>

          <div className="flex gap-2 border-b border-slate-200 pb-2 overflow-x-auto">
            {INFO_TABS.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                    activeTab === tab.key ? 'bg-primary-100 text-primary-700' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="w-4 h-4" /> {tab.label}
                </button>
              );
            })}
          </div>

          <div className="space-y-6">
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
                <div className="flex gap-2 mb-4">
                  {DIAGRAM_TABS.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.key}
                        onClick={() => { setActiveDiagram(tab.key); diagramRendered.current.delete(`diagram-${tab.key}`); }}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                          activeDiagram === tab.key ? 'bg-primary-100 text-primary-700' : 'text-slate-500 hover:text-slate-700'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" /> {tab.label}
                      </button>
                    );
                  })}
                </div>
                <div className="card">
                  <h3 className="text-lg font-semibold text-slate-900 mb-4 capitalize">{activeDiagram} Diagram</h3>
                  <div id={`diagram-${activeDiagram}`} className="bg-white rounded-lg p-4 overflow-auto min-h-[400px]" />
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
        <div className="card mb-6">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-slate-400 shrink-0" />
            <input
              type="text"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search repository entities..."
              className="flex-1 text-sm border-0 outline-none bg-transparent"
            />
            {search && (
              <button onClick={() => onSearchChange('')} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}
      <div className="grid grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold text-slate-900 mb-4">Languages ({filteredLanguages.length})</h3>
          <div className="space-y-3">
            {filteredLanguages.map((lang) => (
              <div key={lang.language}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium">{lang.language}</span>
                  <span className="text-slate-500">{lang.percentage}% ({lang.files} files)</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-primary-500 h-2 rounded-full transition-all" style={{ width: `${lang.percentage}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h3 className="font-semibold text-slate-900 mb-4">Complexity</h3>
          {result.complexity ? (
            <div className="grid grid-cols-2 gap-4">
              <MetricItem label="Total Files" value={result.complexity.total_files} />
              <MetricItem label="Total Lines" value={result.complexity.total_lines} />
              <MetricItem label="Functions" value={result.complexity.total_functions} />
              <MetricItem label="Classes" value={result.complexity.total_classes} />
              <MetricItem label="Avg Function Length" value={`${result.complexity.avg_function_length} lines`} />
              <MetricItem label="Avg Complexity" value={result.complexity.avg_complexity.toFixed(2)} />
            </div>
          ) : (
            <p className="text-sm text-slate-500">No complexity data</p>
          )}
        </div>
        {filteredFrameworks.length > 0 && (
          <div className="card">
            <h3 className="font-semibold text-slate-900 mb-3">Frameworks ({filteredFrameworks.length})</h3>
            <div className="flex flex-wrap gap-2">
              {filteredFrameworks.map((fw) => (
                <span key={fw.name} className="text-sm bg-purple-50 text-purple-700 px-3 py-1.5 rounded-lg">
                  {fw.name}{fw.version ? ` v${fw.version}` : ''}
                  <span className="ml-1.5 text-xs text-purple-400">({fw.category})</span>
                </span>
              ))}
            </div>
          </div>
        )}
        {filteredCommits.length > 0 && (
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <GitCommit className="w-5 h-5 text-sky-600" />
              <h3 className="font-semibold text-slate-900">Recent Commits ({filteredCommits.length})</h3>
            </div>
            <div className="space-y-1.5 max-h-64 overflow-y-auto">
              {filteredCommits.map((c, i) => (
                <div key={i} className="flex items-start gap-2 text-sm p-2 rounded-lg hover:bg-slate-50">
                  <span className="text-xs font-mono text-slate-400 mt-0.5 shrink-0">{c.sha}</span>
                  <p className="flex-1 text-slate-700 truncate">{c.message}</p>
                  <div className="text-right shrink-0">
                    <p className="text-xs text-slate-500">{c.author}</p>
                    <p className="text-xs text-slate-400">{new Date(c.date).toLocaleDateString()}</p>
                  </div>
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
        <Layers className="w-6 h-6 text-purple-600" />
        <h3 className="text-lg font-semibold text-slate-900">Architecture Analysis</h3>
      </div>
      <div className="flex items-center gap-3 mb-4">
        <span className="text-lg font-bold text-purple-700">{arch.pattern}</span>
        <span className="badge bg-purple-100 text-purple-700">{arch.confidence}% confidence</span>
      </div>
      <p className="text-slate-600 mb-6">{arch.description}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch className="w-4 h-4 text-slate-500" />
            <h4 className="font-medium text-slate-700">Layers Detected</h4>
          </div>
          {arch.layers.length > 0 ? (
            <div className="space-y-2">
              {arch.layers.map((layer, i) => (
                <div key={layer} className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold">
                    {i + 1}
                  </div>
                  <span className="text-sm text-slate-700">{layer}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No specific layers</p>
          )}
        </div>
        <div className="bg-slate-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Box className="w-4 h-4 text-slate-500" />
            <h4 className="font-medium text-slate-700">How It Was Detected</h4>
          </div>
          <p className="text-sm text-slate-600 mb-4">
            Scanned <strong>{result.modules.length} modules</strong> across the codebase.
          </p>
          {arch.scores && Object.keys(arch.scores).length > 0 && (
            <div className="mb-4">
              <div className="flex items-center gap-1.5 mb-2 text-xs font-medium text-slate-500 uppercase tracking-wide">
                <Puzzle className="w-3 h-3" />
                Pattern Scores
              </div>
              <div className="space-y-1.5">
                {Object.entries(arch.scores)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 5)
                  .map(([pattern, score]) => {
                    const isWinner = pattern === arch.pattern;
                    const maxScore = Math.max(...Object.values(arch.scores!));
                    const barWidth = maxScore > 0 ? (score / maxScore) * 100 : 0;
                    return (
                      <div key={pattern} className="flex items-center gap-2">
                        <span className={`text-xs w-32 truncate shrink-0 ${isWinner ? 'text-purple-700 font-semibold' : 'text-slate-500'}`}>
                          {isWinner && <ArrowRight className="w-3 h-3 inline mr-0.5 text-purple-600" />}
                          {pattern}
                        </span>
                        <div className="flex-1 bg-slate-200 rounded-full h-1.5">
                          <div className={`h-1.5 rounded-full transition-all ${isWinner ? 'bg-purple-500' : 'bg-slate-300'}`}
                            style={{ width: `${barWidth}%` }} />
                        </div>
                        <span className="text-xs text-slate-400 w-8 text-right">{score.toFixed(1)}</span>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
          {arch.evidence && arch.evidence.length > 0 && (
            <div className="mb-4">
              <div className="flex items-center gap-1.5 mb-2 text-xs font-medium text-slate-500 uppercase tracking-wide">
                <FileSearch className="w-3 h-3" />
                Key Evidence
              </div>
              <div className="flex flex-wrap gap-1.5">
                {arch.evidence.slice(0, 8).map((item, i) => (
                  <span key={i} className="text-xs bg-white border border-slate-200 text-slate-600 px-2 py-1 rounded-md font-mono">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}
          {result.frameworks.length > 0 && (
            <div className="mb-2">
              <div className="flex items-center gap-1.5 mb-2 text-xs font-medium text-slate-500 uppercase tracking-wide">
                <Puzzle className="w-3 h-3" />
                Related Frameworks
              </div>
              <div className="flex flex-wrap gap-1.5">
                {result.frameworks.map((fw) => (
                  <span key={fw.name} className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded-md">
                    {fw.name}{fw.version ? ` v${fw.version}` : ''}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div className="flex items-center gap-2 text-xs text-slate-500 pt-2 border-t border-slate-200">
            <Workflow className="w-3 h-3" />
            Detected via dir structure, file naming & source patterns
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
      <h3 className="font-semibold text-slate-900 mb-4">Dependencies ({filtered.length})</h3>
      {filtered.length === 0 ? (
        <div className="text-center py-8">
          <Box className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">No dependencies detected</p>
          <p className="text-xs text-slate-400 mt-1">Looked for package.json, requirements.txt, Cargo.toml, go.mod, Gemfile, pubspec.yaml, pom.xml</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="pb-2 font-medium">Name</th>
                  <th className="pb-2 font-medium">Version</th>
                  <th className="pb-2 font-medium">Source</th>
                </tr>
              </thead>
              <tbody>
                {displayDeps.map((d, i) => (
                  <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-2 text-slate-900 font-medium">{d.name}</td>
                    <td className="py-2 text-slate-500">{d.version}</td>
                    <td className="py-2"><span className="badge bg-slate-100 text-slate-600">{d.source}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length > 50 && (
            <button onClick={() => setExpanded(!expanded)} className="mt-3 text-sm text-primary-600 hover:underline">
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
      <div className="card text-center py-12">
        <Table2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500">No database schema detected</p>
        <p className="text-xs text-slate-400 mt-1">Scanned for .sql, Laravel/Alembic migrations, Django/SQLAlchemy models, TypeORM entities, Prisma schemas</p>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {tables.map((tbl) => (
        <div key={tbl.name} className="card">
          <button
            onClick={() => setExpandedTable(expandedTable === tbl.name ? null : tbl.name)}
            className="flex items-center gap-2 w-full text-left"
          >
            {expandedTable === tbl.name ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
            <Database className="w-4 h-4 text-blue-500" />
            <span className="font-semibold text-slate-900">{tbl.name}</span>
            <span className="text-xs text-slate-400">({tbl.columns.length} columns{tbl.foreign_keys.length > 0 ? `, ${tbl.foreign_keys.length} FKs` : ''})</span>
          </button>
          {expandedTable === tbl.name && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-200">
                    <th className="pb-2 font-medium">Column</th>
                    <th className="pb-2 font-medium">Type</th>
                    <th className="pb-2 font-medium">PK</th>
                    <th className="pb-2 font-medium">FK</th>
                  </tr>
                </thead>
                <tbody>
                  {tbl.columns.map((col) => {
                    const fk = tbl.foreign_keys.find(f => f.column === col.name);
                    return (
                      <tr key={col.name} className="border-b border-slate-100">
                        <td className="py-2 text-slate-900 font-medium">{col.name}</td>
                        <td className="py-2 text-slate-500"><code>{col.type}</code></td>
                        <td className="py-2">{col.primary_key ? <span className="text-amber-500 text-xs font-bold">PK</span> : ''}</td>
                        <td className="py-2 text-xs text-blue-500">
                          {fk ? `${fk.references_table}.${fk.references_column}` : ''}
                        </td>
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
  const entries = Object.entries(callGraph).filter(([fn]) =>
    !search || fn.toLowerCase().includes(search.toLowerCase())
  );
  if (entries.length === 0) {
    return (
      <div className="card text-center py-12">
        <Network className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500">No call graph data available</p>
        <p className="text-xs text-slate-400 mt-1">Call graphs are generated for .py, .js, .ts, .go, .rs, .java, .php, .rb files</p>
      </div>
    );
  }
  return (
    <div className="card">
      <h3 className="font-semibold text-slate-900 mb-4">Call Graph ({entries.length} functions)</h3>
      <div className="space-y-1">
        {entries.slice(0, 100).map(([fn, calls]) => (
          <div key={fn}>
            <button
              onClick={() => setExpanded(prev => ({ ...prev, [fn]: !prev[fn] }))}
              className="flex items-center gap-2 w-full text-left p-2 rounded-lg hover:bg-slate-50 text-sm"
            >
              {expanded[fn] ? <ChevronDown className="w-3 h-3 text-slate-400" /> : <ChevronRight className="w-3 h-3 text-slate-400" />}
              <code className="text-slate-800 font-medium">{fn}</code>
              <span className="text-xs text-slate-400">({calls.length} calls)</span>
            </button>
            {expanded[fn] && calls.length > 0 && (
              <div className="ml-6 pl-4 border-l-2 border-slate-200 space-y-1 mb-2">
                {calls.map((callee, i) => (
                  <div key={i} className="text-sm text-slate-600 flex items-center gap-2">
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                    <code>{callee}</code>
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
  const filteredContributors = result.contributors.filter(c =>
    !search || (c.name || '').toLowerCase().includes(search.toLowerCase())
  );
  const filteredCommits = result.commit_messages.filter(c =>
    !search || c.message.toLowerCase().includes(search.toLowerCase()) || c.author.toLowerCase().includes(search.toLowerCase())
  );
  return (
    <div className="grid grid-cols-2 gap-6">
      {filteredContributors.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <Users className="w-6 h-6 text-green-600" />
            <h3 className="text-lg font-semibold text-slate-900">Contributors ({filteredContributors.length})</h3>
          </div>
          <div className="grid grid-cols-2 gap-3 max-h-80 overflow-y-auto">
            {filteredContributors.filter(c => c.name).map((c, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-slate-50">
                <div className="w-8 h-8 rounded-full bg-green-100 text-green-700 flex items-center justify-center text-sm font-bold shrink-0">
                  {(c.name || '?')[0].toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-900 truncate">{c.name}</p>
                  <p className="text-xs text-slate-500">{c.commits ?? 0} commit{(c.commits ?? 0) !== 1 ? 's' : ''}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {filteredCommits.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <GitCommit className="w-6 h-6 text-sky-600" />
            <h3 className="text-lg font-semibold text-slate-900">Recent Commits ({filteredCommits.length})</h3>
          </div>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {filteredCommits.map((c, i) => (
              <div key={i} className="flex items-start gap-3 text-sm p-2 rounded-lg hover:bg-slate-50">
                <span className="text-xs font-mono text-slate-400 mt-0.5 shrink-0">{c.sha}</span>
                <p className="flex-1 text-slate-700">{c.message}</p>
                <div className="text-right shrink-0">
                  <p className="text-xs text-slate-500">{c.author}</p>
                  <p className="text-xs text-slate-400">{new Date(c.date).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {result.readme_content && (
        <div className="card col-span-2">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="w-5 h-5 text-slate-600" />
            <h3 className="font-semibold text-slate-900">README</h3>
          </div>
          <pre className="text-sm text-slate-600 whitespace-pre-wrap max-h-96 overflow-y-auto bg-slate-50 rounded-lg p-4">
            {result.readme_content}
          </pre>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div className="card text-center">
      {icon && <div className="flex justify-center mb-1">{icon}</div>}
      <div className="text-2xl font-bold text-primary-600 mb-1">{value}</div>
      <div className="text-sm text-slate-500">{label}</div>
    </div>
  );
}

function MetricItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="text-lg font-semibold text-slate-900">{value}</div>
    </div>
  );
}
