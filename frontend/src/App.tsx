import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Sparkles, Compass, ShieldCheck } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import ResearchSession from './pages/ResearchSession';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-slate-100 font-sans flex flex-col">
        {/* Navigation Bar */}
        <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform duration-200">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  Autonomous Research
                </span>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-blue-400">
                  Multi-Agent Intelligence
                </span>
              </div>
            </Link>

            <div className="flex items-center gap-6 text-sm font-medium text-slate-400">
              <Link to="/" className="hover:text-white transition-colors flex items-center gap-1.5">
                <Compass className="w-4 h-4 text-blue-400" />
                <span>New Research</span>
              </Link>
              <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-xs text-slate-300">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Verified Citations</span>
              </div>
            </div>
          </div>
        </header>
        
        {/* Main Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/research/:id" element={<ResearchSession />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800/60 py-6 text-center text-xs text-slate-500">
          Autonomous Research Agent &bull; Powered by Multi-Agent RAG &bull; Groq &bull; Tavily &bull; PostgreSQL
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;

