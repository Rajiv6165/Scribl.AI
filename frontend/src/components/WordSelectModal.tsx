'use client';

import React, { useEffect, useState } from 'react';
import { Sparkles, Clock } from 'lucide-react';

interface WordSelectModalProps {
  wordChoices: string[];
  timerStartMs: number;
  timerDurationSec: number;
  onSelectWord: (word: string) => void;
}

export const WordSelectModal: React.FC<WordSelectModalProps> = ({
  wordChoices,
  timerStartMs,
  timerDurationSec,
  onSelectWord,
}) => {
  const [timeLeft, setTimeLeft] = useState<number>(timerDurationSec);

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - timerStartMs) / 1000);
      const remaining = Math.max(0, timerDurationSec - elapsed);
      setTimeLeft(remaining);

      // Auto-select first word if time runs out
      if (remaining === 0 && wordChoices.length > 0) {
        clearInterval(interval);
        onSelectWord(wordChoices[0]);
      }
    }, 200);

    return () => clearInterval(interval);
  }, [timerStartMs, timerDurationSec, wordChoices, onSelectWord]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="glass-panel p-8 rounded-3xl max-w-lg w-full shadow-2xl border border-brand-500/30 text-center relative overflow-hidden">
        <div className="absolute -top-12 -left-12 w-32 h-32 bg-brand-500/20 rounded-full blur-2xl pointer-events-none" />
        
        {/* Header Icon */}
        <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-400 flex items-center justify-center text-white mb-4 shadow-lg shadow-brand-500/40">
          <Sparkles className="w-7 h-7" />
        </div>

        <h2 className="text-2xl font-extrabold text-white mb-1">It's Your Turn to Draw!</h2>
        <p className="text-slate-400 text-sm mb-6">Pick a word to start drawing for the room:</p>

        {/* Word Options */}
        <div className="grid grid-cols-1 gap-3 mb-6">
          {wordChoices.map((word) => (
            <button
              key={word}
              type="button"
              onClick={() => onSelectWord(word)}
              className="py-4 px-6 rounded-2xl bg-slate-900/90 hover:bg-brand-600 text-white font-extrabold text-lg tracking-wider border border-slate-700 hover:border-brand-400 shadow-lg hover:shadow-brand-500/30 transition-all transform hover:-translate-y-0.5 active:translate-y-0 uppercase"
            >
              {word}
            </button>
          ))}
        </div>

        {/* Timer Bar */}
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
          <span className="flex items-center gap-1.5 text-amber-400">
            <Clock className="w-4 h-4" />
            Auto-selecting in {timeLeft}s
          </span>
          <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-400 transition-all duration-300 ease-linear"
              style={{ width: `${(timeLeft / timerDurationSec) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
