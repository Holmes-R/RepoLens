export interface LanguageStat {
  language: string;
  percentage: number;
  files: number;
  lines: number;
}

export interface Framework {
  name: string;
  version: string | null;
  category: string;
}

export interface Dependency {
  name: string;
  version: string;
  type: string;
  source: string;
  source_file?: string;
}

export interface ModuleInfo {
  name: string;
  path: string;
  type: string;
  language: string | null;
  imports: string[];
  exports: string[];
  classes: string[];
  functions: string[];
}

export interface Architecture {
  pattern: string;
  confidence: number;
  description: string;
  layers: string[];
}

export interface ComplexityMetrics {
  total_files: number;
  total_lines: number;
  total_functions: number;
  total_classes: number;
  avg_function_length: number;
  avg_complexity: number;
  max_complexity: number;
  max_complexity_file: string | null;
}

export interface AnalysisResult {
  repository: Repository;
  language_stats: LanguageStat[];
  frameworks: Framework[];
  dependencies: Dependency[];
  modules: ModuleInfo[];
  architecture: Architecture | null;
  call_graph: Record<string, string[]>;
  complexity: ComplexityMetrics | null;
  health_score: number | null;
  contributors: Contributor[];
  readme_content: string | null;
  diagrams: Record<string, string>;
  analyzed_at: string;
}

export interface Repository {
  id: string;
  url: string;
  name: string;
  full_name: string;
  default_branch: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  local_path: string | null;
  error_message: string | null;
}

export interface Contributor {
  name: string;
  email: string;
  commits: number;
  last_commit: string;
}

export interface HealthScores {
  overall: number;
  security: number;
  maintainability: number;
  documentation: number;
  testing: number;
  architecture: number;
  performance: number;
  quality: number;
  complexity: number;
  dependency: number;
  activity: number;
  details: {
    breakdown: Record<string, { score: number; max: number; weight: number }>;
    recommendations: string[];
  };
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}
