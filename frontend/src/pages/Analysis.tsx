import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getAnalysis, analyzeRepo } from '../api/client';
import type { AnalysisResult } from '../types';
import { Loader2, AlertCircle, Search, Layers, GitBranch, Box, Workflow, FileSearch, Puzzle, ArrowRight } from 'lucide-react';

export function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) loadAnalysis(id);
  }, [id]);

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
    <div className="p-8 max-w-7xl mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-3 mb-8">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/user/repository"
          className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
        />
        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
          <Search className="w-4 h-4" /> Analyze
        </button>
      </form>

      {error && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 px-4 py-3 rounded-lg mb-6">
          <AlertCircle className="w-5 h-5" /> {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">{result.repository.name}</h2>
                <a href={result.repository.url} className="text-primary-600 text-sm hover:underline" target="_blank" rel="noreferrer">
                  {result.repository.url}
                </a>
              </div>
              <span className={`badge ${result.repository.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                {result.repository.status}
              </span>
            </div>
            {result.repository.description && <p className="text-slate-600 mb-4">{result.repository.description}</p>}
          </div>

          <div className="grid grid-cols-3 gap-6">
            <StatCard label="Languages" value={result.language_stats.length.toString()} />
            <StatCard label="Dependencies" value={result.dependencies.length.toString()} />
            <StatCard label="Modules" value={result.modules.length.toString()} />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="card">
              <h3 className="font-semibold text-slate-900 mb-4">Languages</h3>
              <div className="space-y-3">
                {result.language_stats.map((lang) => (
                  <div key={lang.language}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium">{lang.language}</span>
                      <span className="text-slate-500">{lang.percentage}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-primary-500 h-2 rounded-full transition-all" style={{ width: `${lang.percentage}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h3 className="font-semibold text-slate-900 mb-4">Complexity Metrics</h3>
              {result.complexity && (
                <div className="grid grid-cols-2 gap-4">
                  <MetricItem label="Total Files" value={result.complexity.total_files} />
                  <MetricItem label="Total Lines" value={result.complexity.total_lines} />
                  <MetricItem label="Functions" value={result.complexity.total_functions} />
                  <MetricItem label="Classes" value={result.complexity.total_classes} />
                  <MetricItem label="Avg Function Length" value={`${result.complexity.avg_function_length} lines`} />
                  <MetricItem label="Avg Complexity" value={result.complexity.avg_complexity.toFixed(2)} />
                </div>
              )}
            </div>
          </div>

          {result.architecture && (
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <Layers className="w-6 h-6 text-purple-600" />
                <h3 className="text-lg font-semibold text-slate-900">Architecture Analysis</h3>
              </div>

              <div className="flex items-center gap-3 mb-4">
                <span className="text-lg font-bold text-purple-700">{result.architecture.pattern}</span>
                <span className="badge bg-purple-100 text-purple-700">{result.architecture.confidence}% confidence</span>
              </div>

              <p className="text-slate-600 mb-6">{result.architecture.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <GitBranch className="w-4 h-4 text-slate-500" />
                    <h4 className="font-medium text-slate-700">Layers Detected</h4>
                  </div>
                  {result.architecture.layers.length > 0 ? (
                    <div className="space-y-2">
                      {result.architecture.layers.map((layer, i) => (
                        <div key={layer} className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold">
                            {i + 1}
                          </div>
                          <span className="text-sm text-slate-700">{layer}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">No specific layers identified</p>
                  )}
                </div>

                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Box className="w-4 h-4 text-slate-500" />
                    <h4 className="font-medium text-slate-700">How It Was Detected</h4>
                  </div>
                  <p className="text-sm text-slate-600 mb-4">
                    The architecture detector scanned <strong>{result.modules.length} modules</strong> across the codebase,
                    analyzing directory structures, file names, and source code for architecture pattern indicators.
                  </p>

                  {result.architecture.scores && (
                    <div className="mb-4">
                      <div className="flex items-center gap-1.5 mb-2 text-xs font-medium text-slate-500 uppercase tracking-wide">
                        <Puzzle className="w-3 h-3" />
                        Pattern Scores
                      </div>
                      <div className="space-y-1.5">
                        {Object.entries(result.architecture.scores)
                          .sort(([, a], [, b]) => b - a)
                          .slice(0, 5)
                          .map(([pattern, score]) => {
                            const isWinner = pattern === result.architecture!.pattern;
                            const maxScore = Math.max(...Object.values(result.architecture!.scores!));
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

                  {result.architecture.evidence && result.architecture.evidence.length > 0 && (
                    <div className="mb-4">
                      <div className="flex items-center gap-1.5 mb-2 text-xs font-medium text-slate-500 uppercase tracking-wide">
                        <FileSearch className="w-3 h-3" />
                        Key Evidence
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {result.architecture.evidence.slice(0, 8).map((item, i) => (
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
                    Detected via dir structure, file naming &amp; source patterns
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card text-center">
      <div className="text-3xl font-bold text-primary-600 mb-1">{value}</div>
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
