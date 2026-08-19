import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getResearchStreamUrl } from '../services/api';
import { Loader2, CheckCircle2, Circle } from 'lucide-react';

const STAGES = [
  { id: 'planning', label: 'Creating research plan' },
  { id: 'searching', label: 'Searching sources' },
  { id: 'extracting', label: 'Extracting evidence' },
  { id: 'generating', label: 'Generating report' },
  { id: 'completed', label: 'Completed' },
];

const ResearchSession = () => {
  const { id } = useParams<{ id: string }>();
  const [currentStatus, setCurrentStatus] = useState<string>('planning');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    
    const url = getResearchStreamUrl(id);
    const eventSource = new EventSource(url);
    
    eventSource.addEventListener('status', (e) => {
      setCurrentStatus(e.data);
      if (e.data === 'completed' || e.data === 'failed') {
        eventSource.close();
      }
    });

    eventSource.addEventListener('error', (e) => {
      console.error('SSE Error', e);
      setError('Connection lost or job failed.');
      eventSource.close();
    });

    return () => {
      eventSource.close();
    };
  }, [id]);

  const getStageState = (stageId: string) => {
    const currentIndex = STAGES.findIndex(s => s.id === currentStatus);
    const stageIndex = STAGES.findIndex(s => s.id === stageId);
    
    if (currentStatus === 'failed') return 'failed';
    if (stageIndex < currentIndex) return 'done';
    if (stageIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-surface rounded-2xl p-8 border border-slate-700 mb-8">
        <h2 className="text-2xl font-bold mb-6">Live Research Progress</h2>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded-xl mb-6">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {STAGES.map((stage) => {
            const state = getStageState(stage.id);
            return (
              <div key={stage.id} className="flex items-center gap-4">
                {state === 'done' && <CheckCircle2 className="w-6 h-6 text-green-500" />}
                {state === 'active' && <Loader2 className="w-6 h-6 text-primary animate-spin" />}
                {state === 'pending' && <Circle className="w-6 h-6 text-slate-600" />}
                <span className={`text-lg ${state === 'active' ? 'text-primary font-medium' : state === 'done' ? 'text-slate-300' : 'text-slate-500'}`}>
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      
      {currentStatus === 'completed' && (
        <div className="bg-surface rounded-2xl p-8 border border-slate-700">
          <h2 className="text-2xl font-bold mb-6">Research Report</h2>
          <div className="prose prose-invert max-w-none">
            <p className="text-slate-400 italic">Report content will be rendered here...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResearchSession;
