import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import ResearchSession from './pages/ResearchSession';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-slate-200 font-sans">
        <header className="border-b border-slate-700 bg-surface">
          <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
              Autonomous AI Research
            </h1>
          </div>
        </header>
        
        <main className="max-w-6xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/research/:id" element={<ResearchSession />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
