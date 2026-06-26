import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { BarChart3, Search, MessageSquare, GitBranch, Activity, Home } from 'lucide-react';
import { HomePage } from './pages/Home';
import { AnalysisPage } from './pages/Analysis';
import { ChatPage } from './pages/Chat';
import { DiagramsPage } from './pages/Diagrams';

function App() {
  const location = useLocation();
  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/analysis', label: 'Analysis', icon: Search },
    { path: '/diagrams', label: 'Diagrams', icon: GitBranch },
    { path: '/chat', label: 'AI Chat', icon: MessageSquare },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-64 bg-white border-r border-slate-200 p-6 flex flex-col">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">RepoLens</h1>
            <p className="text-xs text-slate-500">AI Analyzer</p>
          </div>
        </div>
        <nav className="space-y-1 flex-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                  isActive ? 'bg-primary-50 text-primary-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="pt-6 border-t border-slate-200">
          <div className="flex items-center gap-3 px-4 py-3">
            <Activity className="w-4 h-4 text-green-500" />
            <span className="text-xs text-slate-500">System Online</span>
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/analysis/:id" element={<AnalysisPage />} />
          <Route path="/diagrams" element={<DiagramsPage />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
