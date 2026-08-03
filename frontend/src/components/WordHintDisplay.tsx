'use client';

import React, { useEffect, useState } from 'react';
import { Clock, Paintbrush } from 'lucide-react';
import { GamePhase } from '../utils/types';

interface WordHintDisplayProps {
  phase: GamePhase;
  wordHint: string;
  isDrawer: boolean;
  currentDrawer: string;
  currentRoundNum: number;
  totalRounds: number;
  timerStartMs: number;
  timerDurationSec: number;
  onTimerExpired: (phase: GamePhase) => void;
}

export const WordHintDisplay: React.FC<WordHintDisplayProps> = ({
  phase,
  wordHint,
  isDrawer,
  currentDrawer,
  currentRoundNum,
  totalRounds,
  timerStartMs,
  timerDurationSec,
  onTimerExpired,
}) => {
  const [timeLeft, setTimeLeft] = useState<number>(timerDurationSec);

  useEffect(() => {
    if (!timerStartMs || timerDurationSec <= 0) return;

    const interval = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - timerStartMs) / 1000);
      const remaining = Math.max(0, timerDurationSec - elapsed);
      setTimeLeft(remaining);

      if (remaining === 0) {
        clearInterval(interval);
        if (isDrawer) {
          onTimerExpired(phase);
        }
      }
    }, 200);

    return () => clearInterval(interval);
  }, [timerStartMs, timerDurationSec, phase, isDrawer, onTimerExpired]);

  const timePct = Math.max(0, Math.min(100, (timeLeft / (timerDurationSec || 1)) * 100));

  return (
    <div className="glass-panel p-4 rounded-2xl flex flex-col gap-3 shadow-xl border border-slate-700/50">
      <div className="flex items-center justify-between gap-4">
        {/* Round Badge & Drawer info */}
        <div className="flex items-center gap-3">
          <span className="bg-brand-900/60 text-brand-300 text-xs font-extrabold px-3 py-1.5 rounded-xl border border-brand-500/40 uppercase tracking-wider">
            Round {currentRoundNum || 1} / {totalRounds || 3}
          </span>
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Paintbrush className="w-3.5 h-3.5 text-brand-400" />
            {isDrawer ? (
              <span className="text-amber-400 font-bold">You are drawing!</span>
            ) : (
              <span>
                <strong className="text-white">{currentDrawer || 'Someone'}</strong> is drawing
              </span>
            )}
          </span>
        </div>

        {/* Synced Timer */}
        <div className="flex items-center gap-2">
          <Clock className={`w-4 h-4 ${timeLeft <= 10 ? 'text-rose-400 animate-pulse' : 'text-slate-400'}`} />
          <span className={`text-lg font-black font-mono ${timeLeft <= 10 ? 'text-rose-400' : 'text-white'}`}>
            {timeLeft}s
          </span>
        </div>
      </div>

      {/* Word Hint Display / Underscores */}
      <div className="bg-slate-950/80 py-3 px-6 rounded-xl border border-slate-800 text-center relative overflow-hidden">
        {phase === 'WORD_SELECT' ? (
          <p className="text-xs font-semibold text-slate-400 italic animate-pulse">
            {currentDrawer} is selecting a word...
          </p>
        ) : (
          <span className="text-2xl md:text-3xl font-extrabold tracking-[0.3em] font-mono text-amber-300 uppercase select-none">
            {wordHint || '_ _ _ _ _'}
          </span>
        )}
      </div>

      {/* Timer Progress Bar */}
      <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ease-linear ${
            timePct <= 20 ? 'bg-rose-500' : timePct <= 50 ? 'bg-amber-400' : 'bg-brand-500'
          }`}
          style={{ width: `${timePct}%` }}
        />
      </div>
    </div>
  );
};
