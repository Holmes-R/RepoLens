import { Routes, Route, Link, useLocation, useParams } from 'react-router-dom';
import { BarChart3, Search, GitBranch, Activity, Home, MessageSquare } from 'lucide-react';
import { HomePage } from './pages/Home';
import { AnalysisPage } from './pages/Analysis';
import { DiagramsPage } from './pages/Diagrams';
import { ChatPage } from './pages/Chat';

function NavLink({ to, icon: Icon, label, currentPath, analysisId }: { to: string; icon: any; label: string; currentPath: string; analysisId?: string }) {
  const path = analysisId && to !== '/' ? `${to}/${analysisId}` : to;
  const isActive = currentPath === path || (analysisId && currentPath.startsWith(to) && currentPath.includes(analysisId));
  return (
    <Link
      to={path}
      className={`flex items-center gap-3 px-3 py-2.5 text-sm font-medium transition-colors ${
        isActive
          ? 'bg-primary-900/20 text-primary-400 border-l-2 border-primary-500'
          : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 border-l-2 border-transparent'
      }`}
    >
      <Icon className="w-4 h-4" />
      {label}
    </Link>
  );
}

function App() {
  const location = useLocation();
  const analysisMatch = location.pathname.match(/^\/(analysis|diagrams|chat)\/(.+)$/);
  const currentAnalysisId = analysisMatch ? analysisMatch[2] : undefined;

  return (
    <div className="min-h-screen bg-[#0a0a0b] flex">
      <aside className="w-56 bg-zinc-900 border-r border-zinc-800 p-5 flex flex-col shrink-0">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-9 h-9 bg-primary-600 flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">RepoLens</h1>
            <p className="text-[11px] text-zinc-500">AI Analyzer</p>
          </div>
        </div>
        <nav className="space-y-0.5 flex-1">
          <NavLink to="/" icon={Home} label="Home" currentPath={location.pathname} />
          <NavLink to="/analysis" icon={Search} label="Analysis" currentPath={location.pathname} analysisId={currentAnalysisId} />
          <NavLink to="/diagrams" icon={GitBranch} label="Diagrams" currentPath={location.pathname} analysisId={currentAnalysisId} />
          <NavLink to="/chat" icon={MessageSquare} label="AI Chat" currentPath={location.pathname} analysisId={currentAnalysisId} />
        </nav>
        <div className="pt-5 border-t border-zinc-800 px-2">
          <div className="flex items-center gap-3 py-2">
            <Activity className="w-3.5 h-3.5 text-green-500" />
            <span className="text-xs text-zinc-600">System Online</span>
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/analysis/:id" element={<AnalysisPage />} />
          <Route path="/diagrams" element={<DiagramsPage />} />
          <Route path="/diagrams/:id" element={<DiagramsPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:id" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
