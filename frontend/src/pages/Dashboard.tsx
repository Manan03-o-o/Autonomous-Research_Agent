import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startResearch } from '../services/api';
import { 
  Search, 
  Sparkles, 
  Zap, 
  Layers, 
  Cpu, 
  ShieldCheck, 
  ArrowRight,
  Loader2 
} from 'lucide-react';

const EXAMPLE_PROMPTS = [
  {
    title: "AI Code Assistants",
    prompt: "Compare architecture, benchmarks, and latency tradeoffs of modern AI coding assistants.",
    tag: "Tech"
  },
  {
    title: "EV Market in India",
    prompt: "Analyze EV market adoption in India: government subsidies, charging infra, and market leaders.",
    tag: "Market"
  },
  {
    title: "Vector Databases",
    prompt: "Compare pgvector vs Pinecone vs Qdrant for large-scale enterprise RAG pipelines.",
    tag: "Architecture"
  },
  {
    title: "Solid-State Batteries",
    prompt: "What is the commercial viability and timeline for quantum solid-state battery deployment?",
    tag: "Deep Tech"
  }
];

const DEPTH_OPTIONS: Array<{
  id: 'quick' | 'standard' | 'deep';
  label: string;
  description: string;
  badge: string;
}> = [
  {
    id: 'quick',
    label: 'Quick Overview',
    description: 'Fast synthesis across 1-2 targeted searches',
    badge: '~15s'
  },
  {
    id: 'standard',
    label: 'Standard Research',
    description: 'Multi-query agentic loop with evidence critic',
    badge: '~45s'
  },
  {
    id: 'deep',
    label: 'Deep Research',
    description: 'Multi-iteration deep dive, heavy extraction & fact checks',
    badge: '~90s'
  }
];

const Dashboard = () => {
  const [question, setQuestion] = useState('');
  const [depth, setDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleStartResearch = async (promptText: string) => {
    const query = promptText.trim();
    if (!query) return;

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const job = await startResearch({
        user_question: query,
        research_depth: depth
      });
      navigate(`/research/${job.id}`);
    } catch (error: any) {
      console.error('Failed to start research:', error);
      setErrorMessage(
        error?.response?.data?.detail || 
        'Failed to connect to backend server. Make sure the backend is running at port 8000.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleStartResearch(question);
  };

  return (
    <div className="flex flex-col items-center justify-center max-w-5xl mx-auto pt-6 sm:pt-12 pb-16">
      {/* Hero Badge */}
      <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold tracking-wide mb-6 animate-pulse">
        <Sparkles className="w-3.5 h-3.5 text-blue-400" />
        <span>Next-Generation Autonomous Research Engine</span>
      </div>

      {/* Hero Title & Subtitle */}
      <div className="text-center max-w-3xl mb-10 px-4">
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight mb-4 leading-tight">
          Intelligence that <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-violet-400 bg-clip-text text-transparent">
            Searches, Verifies & Synthesizes.
          </span>
        </h1>
        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Ask complex questions. Autonomous multi-agent pipelines plan search strategies, extract verified evidence, critique findings, and build citation-backed reports.
        </p>
      </div>

      {/* Main Research Input Card */}
      <div className="w-full max-w-3xl glass-panel rounded-2xl p-4 sm:p-6 shadow-2xl border border-slate-700/60 mb-8 glow-subtle">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative flex items-center">
            <Search className="absolute left-4 text-slate-400 w-5 h-5 pointer-events-none" />
            <input
              type="text"
              id="research-query-input"
              className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl py-4 pl-12 pr-32 text-base sm:text-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
              placeholder="What topic or question do you want to research deeply?..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              id="start-research-button"
              disabled={isLoading || !question.trim()}
              className="absolute right-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium py-2.5 px-5 rounded-lg transition-all shadow-md shadow-blue-500/20 disabled:opacity-40 flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Starting...</span>
                </>
              ) : (
                <>
                  <span>Research</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {/* Depth Selector */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Research Depth</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {DEPTH_OPTIONS.map((opt) => {
                const isSelected = depth === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setDepth(opt.id)}
                    className={`text-left p-3 rounded-xl border transition-all ${
                      isSelected
                        ? 'bg-blue-600/15 border-blue-500/60 text-white shadow-sm ring-1 ring-blue-500/30'
                        : 'bg-slate-900/40 border-slate-800/80 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-sm font-semibold ${isSelected ? 'text-blue-400' : 'text-slate-300'}`}>
                        {opt.label}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono">
                        {opt.badge}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 line-clamp-1">{opt.description}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </form>

        {errorMessage && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs sm:text-sm flex items-start gap-2">
            <span>{errorMessage}</span>
          </div>
        )}
      </div>

      {/* Example Prompts */}
      <div className="w-full max-w-3xl mb-12">
        <div className="flex items-center gap-2 mb-3 px-1">
          <Zap className="w-4 h-4 text-amber-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Suggested Research Inquiries
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {EXAMPLE_PROMPTS.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuestion(item.prompt);
                handleStartResearch(item.prompt);
              }}
              className="text-left p-4 rounded-xl glass-card hover:bg-slate-800/60 hover:border-slate-600/60 transition-all group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                    {item.title}
                  </span>
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/60">
                    {item.tag}
                  </span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {item.prompt}
                </p>
              </div>
              <div className="mt-3 flex items-center gap-1 text-[11px] text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
                <span>Start research</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Feature Badges / Trust Markers */}
      <div className="w-full max-w-4xl grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6 border-t border-slate-800/80">
        <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/30 border border-slate-800/60">
          <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-200 mb-0.5">Multi-Agent RAG</h4>
            <p className="text-xs text-slate-400">Autonomous planner, searcher, extractor, and critic pipeline.</p>
          </div>
        </div>

        <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/30 border border-slate-800/60">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-200 mb-0.5">Evidence Extraction</h4>
            <p className="text-xs text-slate-400">pgvector embedding search extracts verified claims and confidence scores.</p>
          </div>
        </div>

        <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/30 border border-slate-800/60">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-200 mb-0.5">Verified Citations</h4>
            <p className="text-xs text-slate-400">Post-generation verification ensures every claim maps to an authentic source.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

