import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  getResearchStreamUrl, 
  getResearchJob, 
  getResearchReport, 
  getResearchSources, 
  getResearchClaims,
} from '../services/api';
import type {
  ResearchJob,
  Report,
  Source,
  Claim
} from '../services/api';
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Compass, 
  Search, 
  FileText, 
  Layers, 
  Cpu, 
  ShieldCheck, 
  ExternalLink, 
  Copy, 
  Check, 
  Download, 
  Clock, 
  ArrowLeft,
  ChevronRight,
  Database,
  Sparkles
} from 'lucide-react';

interface StageConfig {
  id: string;
  label: string;
  description: string;
  icon: any;
}

const STAGES: StageConfig[] = [
  {
    id: 'planning',
    label: 'Research Planning',
    description: 'Decomposing inquiry into sub-questions and key dimensions',
    icon: Compass
  },
  {
    id: 'searching',
    label: 'Targeted Web Search',
    description: 'Generating optimized queries and searching via Tavily',
    icon: Search
  },
  {
    id: 'extracting',
    label: 'Extraction & Vector Embedding',
    description: 'Scraping web sources, chunking text, generating embeddings',
    icon: Layers
  },
  {
    id: 'critiquing',
    label: 'Evidence Critic',
    description: 'Evaluating sufficiency, identifying gaps and contradictions',
    icon: Cpu
  },
  {
    id: 'generating',
    label: 'Report Synthesis',
    description: 'Structuring multidimensional findings with citations',
    icon: FileText
  },
  {
    id: 'verifying',
    label: 'Citation Verification',
    description: 'Cross-checking all claims against factual source evidence',
    icon: ShieldCheck
  },
  {
    id: 'completed',
    label: 'Research Completed',
    description: 'Comprehensive citation-backed report ready',
    icon: CheckCircle2
  }
];

// Helper to normalize status strings
const normalizeStatus = (statusStr: string): string => {
  const map: Record<string, string> = {
    'pending': 'planning',
    'planning_started': 'planning',
    'queries_generated': 'searching',
    'search_started': 'searching',
    'sources_found': 'searching',
    'source_extraction_started': 'extracting',
    'embedding_started': 'extracting',
    'source_extraction_completed': 'extracting',
    'evidence_extracted': 'critiquing',
    'critic_started': 'critiquing',
    'additional_research_required': 'searching',
    'report_generation_started': 'generating',
    'citation_verification_started': 'verifying',
    'research_completed': 'completed',
    'research_failed': 'failed',
    'failed': 'failed'
  };
  return map[statusStr] || statusStr;
};

const ResearchSession = () => {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  
  const [currentStatus, setCurrentStatus] = useState<string>('planning');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'report' | 'evidence' | 'sources'>('report');
  const [copied, setCopied] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Poll timer during in-progress research
  useEffect(() => {
    let timer: any = null;
    const isFinished = currentStatus === 'completed' || currentStatus === 'failed';
    if (!isFinished) {
      timer = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [currentStatus]);

  // Initial fetch for job metadata
  useEffect(() => {
    if (!id) return;
    getResearchJob(id)
      .then((data) => {
        setJob(data);
        if (data.status) {
          const norm = normalizeStatus(data.status);
          setCurrentStatus(norm);
          if (norm === 'failed') {
            setErrorMessage(data.error_message || 'Research pipeline encountered a failure.');
          }
        }
      })
      .catch((err) => {
        console.error('Error fetching research job:', err);
      });
  }, [id]);

  // Connect to SSE stream
  useEffect(() => {
    if (!id) return;
    
    const streamUrl = getResearchStreamUrl(id);
    const eventSource = new EventSource(streamUrl);

    eventSource.addEventListener('status', (e: MessageEvent) => {
      const rawStatus = e.data;
      const normalized = normalizeStatus(rawStatus);
      setCurrentStatus(normalized);
      if (normalized === 'completed' || normalized === 'failed') {
        eventSource.close();
      }
    });

    eventSource.addEventListener('progress', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        if (data.status) {
          const normalized = normalizeStatus(data.status);
          setCurrentStatus(normalized);
          if (data.error_message) {
            setErrorMessage(data.error_message);
          }
        }
      } catch (err) {
        console.error('Failed to parse progress SSE event:', err);
      }
    });

    eventSource.addEventListener('done', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        const normalized = normalizeStatus(data.status);
        setCurrentStatus(normalized);
        if (data.error) {
          setErrorMessage(data.error);
        }
      } catch (err) {
        // fallback
      }
      eventSource.close();
    });

    eventSource.addEventListener('error', (e) => {
      console.warn('SSE disconnected or closed:', e);
      // Fallback: poll job endpoint once to see if it completed or failed
      getResearchJob(id).then((j) => {
        if (j) {
          setJob(j);
          const norm = normalizeStatus(j.status);
          setCurrentStatus(norm);
          if (norm === 'failed') {
            setErrorMessage(j.error_message || 'Research pipeline encountered an error.');
          }
        }
      }).catch(() => {});
      eventSource.close();
    });

    return () => {
      eventSource.close();
    };
  }, [id]);

  // When status becomes completed, fetch report, sources, and claims
  useEffect(() => {
    if (!id || currentStatus !== 'completed') return;

    // Fetch full results
    Promise.allSettled([
      getResearchJob(id),
      getResearchReport(id),
      getResearchSources(id),
      getResearchClaims(id)
    ]).then(([jobRes, reportRes, sourcesRes, claimsRes]) => {
      if (jobRes.status === 'fulfilled') setJob(jobRes.value);
      if (reportRes.status === 'fulfilled') setReport(reportRes.value);
      if (sourcesRes.status === 'fulfilled') setSources(sourcesRes.value);
      if (claimsRes.status === 'fulfilled') setClaims(claimsRes.value);
    });
  }, [id, currentStatus]);

  // Stage state calculation
  const getStageState = (stageId: string) => {
    if (currentStatus === 'failed') return 'failed';
    if (currentStatus === 'completed') return 'done';

    const currentIndex = STAGES.findIndex(s => s.id === currentStatus);
    const stageIndex = STAGES.findIndex(s => s.id === stageId);

    if (stageIndex < currentIndex) return 'done';
    if (stageIndex === currentIndex) return 'active';
    return 'pending';
  };

  const handleCopyReport = () => {
    if (!report?.content) return;
    navigator.clipboard.writeText(report.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadReport = () => {
    if (!report?.content) return;
    const blob = new Blob([report.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research-report-${id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Format markdown content for clean readability
  const formattedReportContent = useMemo(() => {
    if (!report?.content) return '';
    return report.content;
  }, [report]);

  const isCompleted = currentStatus === 'completed' && report !== null;

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16">
      {/* Top Breadcrumb & Question Header */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-700/60 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <Link 
            to="/" 
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-blue-400 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Research Inquiries</span>
          </Link>
          
          <div className="flex items-center gap-3">
            {job?.research_depth && (
              <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-medium capitalize">
                {job.research_depth} Research
              </span>
            )}
            
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>
                {isCompleted 
                  ? 'Completed' 
                  : currentStatus === 'failed' 
                    ? 'Failed' 
                    : `Running: ${elapsedSeconds}s`}
              </span>
            </div>
          </div>
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
          {job?.user_question || 'Research Inquiry'}
        </h1>
        <p className="text-xs text-slate-400 font-mono">
          Session ID: <span className="text-slate-300">{id}</span>
        </p>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="glass-card rounded-2xl p-6 border border-red-500/40 bg-red-950/20 text-red-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-red-300 mb-1">Research Pipeline Interrupted</h3>
              <p className="text-xs text-red-300/80 leading-relaxed">{errorMessage}</p>
            </div>
          </div>
          <Link
            to="/"
            className="px-4 py-2 rounded-xl bg-red-600/30 hover:bg-red-600/50 border border-red-500/50 text-xs font-semibold text-white transition-colors shrink-0"
          >
            Try Another Query
          </Link>
        </div>
      )}

      {/* Live Agent Stepper (Always shown when active or expandable) */}
      {!isCompleted && (
        <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-700/60 shadow-xl glow-subtle">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-blue-500 animate-ping" />
              <h2 className="text-lg font-bold text-white tracking-tight">Autonomous Agent Execution</h2>
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">
              {currentStatus}
            </span>
          </div>

          <div className="space-y-4">
            {STAGES.map((stage, idx) => {
              const state = getStageState(stage.id);
              const Icon = stage.icon;

              return (
                <div 
                  key={stage.id} 
                  className={`flex items-start gap-4 p-4 rounded-xl border transition-all ${
                    state === 'active' 
                      ? 'bg-blue-600/10 border-blue-500/50 shadow-md ring-1 ring-blue-500/20' 
                      : state === 'done'
                        ? 'bg-slate-900/40 border-slate-800/80 opacity-90'
                        : state === 'failed'
                          ? 'bg-red-950/20 border-red-800/40 opacity-75'
                          : 'bg-slate-950/20 border-transparent opacity-40'
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    {state === 'done' && (
                      <div className="w-7 h-7 rounded-full bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      </div>
                    )}
                    {state === 'active' && (
                      <div className="w-7 h-7 rounded-full bg-blue-500/20 border border-blue-500/60 flex items-center justify-center animate-pulse">
                        <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                      </div>
                    )}
                    {state === 'pending' && (
                      <div className="w-7 h-7 rounded-full bg-slate-800/60 border border-slate-700/60 flex items-center justify-center">
                        <Icon className="w-3.5 h-3.5 text-slate-500" />
                      </div>
                    )}
                    {state === 'failed' && (
                      <div className="w-7 h-7 rounded-full bg-red-500/20 border border-red-500/50 flex items-center justify-center">
                        <AlertCircle className="w-4 h-4 text-red-400" />
                      </div>
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-mono text-slate-500">0{idx + 1}.</span>
                      <h3 className={`text-sm font-semibold ${
                        state === 'active' ? 'text-blue-300' : state === 'done' ? 'text-slate-200' : 'text-slate-400'
                      }`}>
                        {stage.label}
                      </h3>
                    </div>
                    <p className="text-xs text-slate-400">{stage.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Completed Research Workspace */}
      {isCompleted && (
        <div className="space-y-6">
          {/* Action Tabs & Controls */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-2 rounded-2xl glass-panel border border-slate-700/60">
            <div className="flex items-center gap-1.5 p-1 bg-slate-900/80 rounded-xl border border-slate-800">
              <button
                type="button"
                onClick={() => setActiveTab('report')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'report'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Synthesis Report</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('evidence')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'evidence'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                <span>Evidence Explorer ({claims.length})</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('sources')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'sources'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Sources ({sources.length})</span>
              </button>
            </div>

            <div className="flex items-center gap-2 px-2">
              <button
                type="button"
                onClick={handleCopyReport}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors"
                title="Copy Markdown"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
              </button>

              <button
                type="button"
                onClick={handleDownloadReport}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors"
                title="Download Report (.md)"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export</span>
              </button>
            </div>
          </div>

          {/* Tab 1: Synthesis Report */}
          {activeTab === 'report' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
              {/* Main Report Column */}
              <div className="lg:col-span-2 glass-panel rounded-2xl p-6 sm:p-10 border border-slate-700/60 shadow-2xl">
                <div className="flex items-center gap-2 pb-4 mb-6 border-b border-slate-800 text-xs text-slate-400">
                  <Sparkles className="w-4 h-4 text-blue-400" />
                  <span>Synthesized & Verified Autonomous Research Report</span>
                </div>

                <div className="prose-report text-slate-300">
                  <div className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                    {formattedReportContent}
                  </div>
                </div>
              </div>

              {/* Side Summary & Evidence Widget */}
              <div className="space-y-6">
                {/* Evidence Snapshot */}
                <div className="glass-panel rounded-2xl p-6 border border-slate-700/60 shadow-xl">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Database className="w-4 h-4 text-blue-400" />
                      <span>Evidence Summary</span>
                    </h3>
                    <button 
                      type="button" 
                      onClick={() => setActiveTab('evidence')}
                      className="text-xs text-blue-400 hover:underline flex items-center gap-0.5"
                    >
                      <span>View all</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>

                  <div className="space-y-3">
                    {claims.slice(0, 4).map((c, i) => (
                      <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] uppercase font-semibold text-slate-400">Claim {i + 1}</span>
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                            {Math.round(c.confidence * 100)}% Confidence
                          </span>
                        </div>
                        <p className="text-slate-300 line-clamp-2">{c.claim}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Primary Sources Widget */}
                <div className="glass-panel rounded-2xl p-6 border border-slate-700/60 shadow-xl">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Layers className="w-4 h-4 text-indigo-400" />
                      <span>Cited Sources</span>
                    </h3>
                    <button 
                      type="button" 
                      onClick={() => setActiveTab('sources')}
                      className="text-xs text-blue-400 hover:underline flex items-center gap-0.5"
                    >
                      <span>View all</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>

                  <div className="space-y-2.5">
                    {sources.slice(0, 5).map((src, i) => (
                      <a
                        key={i}
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        className="block p-2.5 rounded-xl bg-slate-900/40 hover:bg-slate-800/70 border border-slate-800/80 transition-colors group"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-medium text-slate-300 group-hover:text-blue-400 transition-colors truncate">
                            {src.title || src.url}
                          </span>
                          <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-blue-400 shrink-0" />
                        </div>
                        {src.publisher && (
                          <span className="text-[10px] text-slate-500">{src.publisher}</span>
                        )}
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Evidence Explorer */}
          {activeTab === 'evidence' && (
            <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-700/60 shadow-2xl space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div>
                  <h2 className="text-xl font-bold text-white">Extracted Evidence Claims</h2>
                  <p className="text-xs text-slate-400">
                    Factual statements verified by embedding similarity and autonomous critics.
                  </p>
                </div>
                <span className="text-xs px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 font-semibold">
                  {claims.length} Claims Identified
                </span>
              </div>

              {claims.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-sm">
                  No extracted claims recorded for this research session.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {claims.map((claimItem, idx) => (
                    <div 
                      key={idx} 
                      className="glass-card rounded-2xl p-5 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="text-xs font-mono font-bold text-slate-400">
                            Claim #{idx + 1}
                          </span>
                          <div className="flex items-center gap-1.5">
                            <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                              <div 
                                className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 rounded-full"
                                style={{ width: `${Math.min(100, Math.max(10, claimItem.confidence * 100))}%` }}
                              />
                            </div>
                            <span className="text-xs font-bold text-emerald-400">
                              {Math.round(claimItem.confidence * 100)}%
                            </span>
                          </div>
                        </div>

                        <p className="text-sm font-medium text-slate-100 mb-3 leading-snug">
                          {claimItem.claim}
                        </p>

                        {claimItem.evidence && claimItem.evidence.length > 0 && (
                          <div className="space-y-2 mt-3 pt-3 border-t border-slate-800/80">
                            {claimItem.evidence.map((ev, evIdx) => (
                              <div key={evIdx} className="text-xs text-slate-400 bg-slate-950/40 p-2.5 rounded-lg border border-slate-900">
                                <p className="italic text-slate-300 mb-1.5">"{ev.text}"</p>
                                {ev.source?.url && (
                                  <a 
                                    href={ev.source.url} 
                                    target="_blank" 
                                    rel="noreferrer"
                                    className="text-[11px] text-blue-400 hover:underline inline-flex items-center gap-1"
                                  >
                                    <span>Source: {ev.source.publisher || ev.source.title || ev.source.url}</span>
                                    <ExternalLink className="w-2.5 h-2.5" />
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Sources */}
          {activeTab === 'sources' && (
            <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-700/60 shadow-2xl space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div>
                  <h2 className="text-xl font-bold text-white">Analyzed Web Sources</h2>
                  <p className="text-xs text-slate-400">
                    Authority web pages retrieved and parsed during this investigation.
                  </p>
                </div>
                <span className="text-xs px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-semibold">
                  {sources.length} Total Sources
                </span>
              </div>

              {sources.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-sm">
                  No sources recorded for this research session.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {sources.map((sourceItem, idx) => (
                    <div 
                      key={idx}
                      className="glass-card rounded-2xl p-5 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                            {sourceItem.publisher || 'Web Page'}
                          </span>
                          {sourceItem.relevance_score && (
                            <span className="text-[10px] text-slate-400">
                              Relevance: {(sourceItem.relevance_score * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>

                        <h4 className="text-sm font-bold text-white mb-2 line-clamp-2">
                          {sourceItem.title || sourceItem.url}
                        </h4>

                        {sourceItem.published_at && (
                          <p className="text-xs text-slate-500 mb-2">
                            Published: {sourceItem.published_at}
                          </p>
                        )}
                      </div>

                      <div className="mt-4 pt-3 border-t border-slate-800/80">
                        <a
                          href={sourceItem.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-blue-400 hover:text-blue-300 inline-flex items-center gap-1.5 font-medium transition-colors"
                        >
                          <span className="truncate max-w-xs">{sourceItem.url}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ResearchSession;

