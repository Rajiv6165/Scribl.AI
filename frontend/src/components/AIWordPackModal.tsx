'use client';

import React, { useState } from 'react';
import { Sparkles, Wand2, X } from 'lucide-react';

interface AIWordPackModalProps {
  currentTheme: string;
  onGenerateTheme: (theme: string) => void;
  onClose: () => void;
}

export const AIWordPackModal: React.FC<AIWordPackModalProps> = ({
  currentTheme,
  onGenerateTheme,
  onClose,
}) => {
  const [themeInput, setThemeInput] = useState(currentTheme || '');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!themeInput.trim()) return;
    setLoading(true);
    onGenerateTheme(themeInput.trim());
    setTimeout(() => {
      setLoading(false);
      onClose();
    }, 1200);
  };

  const presetThemes = [
    'Bollywood Movies',
    'Startup Buzzwords',
    'Marvel Superheroes',
    '90s Cartoon Characters',
    'Video Game Bosses',
    'Famous World Landmarks',
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="glass-panel p-6 rounded-3xl max-w-md w-full shadow-2xl border border-brand-500/40 relative overflow-hidden">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Icon & Title */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-400 flex items-center justify-center text-white shadow-lg shadow-purple-500/30">
            <Wand2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xl font-extrabold text-white">AI Theme Word Pack</h3>
            <p className="text-xs text-slate-400">Generate ~30 themed drawing words with Gemini AI</p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
              Enter Custom Theme
            </label>
            <input
              type="text"
              required
              maxLength={40}
              value={themeInput}
              onChange={(e) => setThemeInput(e.target.value)}
              placeholder="e.g. Bollywood Movies"
              className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
            />
          </div>

          {/* Quick Presets */}
          <div>
            <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
              Popular Presets
            </span>
            <div className="flex flex-wrap gap-1.5">
              {presetThemes.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setThemeInput(preset)}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-purple-900/40 text-slate-300 hover:text-purple-200 text-xs font-semibold border border-slate-700/60 transition-colors"
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !themeInput.trim()}
            className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-extrabold text-sm shadow-xl shadow-purple-500/30 transition-all flex items-center justify-center gap-2 transform hover:-translate-y-0.5 disabled:opacity-50"
          >
            {loading ? (
              <span>Generating Words...</span>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate Word Pack</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
