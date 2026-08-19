import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startResearch } from '../services/api';
import { Search } from 'lucide-react';

const Dashboard = () => {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    
    setIsLoading(true);
    try {
      const job = await startResearch({ user_question: question });
      navigate(`/research/${job.id}`);
    } catch (error) {
      console.error(error);
      alert('Failed to start research.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center pt-20">
      <div className="w-full max-w-3xl text-center mb-10">
        <h1 className="text-5xl font-extrabold mb-6">Ask Anything.</h1>
        <p className="text-xl text-slate-400">
          Autonomous agents will research, analyze, and synthesize a comprehensive report for you.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="w-full max-w-3xl relative">
        <div className="relative flex items-center">
          <Search className="absolute left-4 text-slate-400 w-6 h-6" />
          <input
            type="text"
            className="w-full bg-surface border border-slate-700 rounded-2xl py-5 pl-14 pr-32 text-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xl transition-all"
            placeholder="e.g. Compare the AI infrastructure strategies of AWS and Google Cloud..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !question.trim()}
            className="absolute right-3 bg-primary hover:bg-blue-600 text-white font-medium py-2.5 px-6 rounded-xl transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Starting...' : 'Research'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Dashboard;
