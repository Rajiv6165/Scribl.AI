'use client';

import React, { useEffect, useState } from 'react';
import { Trophy, Sparkles, Clock } from 'lucide-react';
import { Player, GamePhase } from '../utils/types';

interface RoundEndModalProps {
  phase: GamePhase;
  revealedWord: string;
  players: Player[];
  timerStartMs: number;
  timerDurationSec: number;
}

export const RoundEndModal: React.FC<RoundEndModalProps> = ({
  phase,
  revealedWord,
  players,
  timerStartMs,
  timerDurationSec,
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
      }
    }, 200);

    return () => clearInterval(interval);
  }, [timerStartMs, timerDurationSec]);

  const sortedPlayers = [...players].sort((a, b) => (b.score || 0) - (a.score || 0));
  const winner = sortedPlayers[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="glass-panel p-8 rounded-3xl max-w-lg w-full shadow-2xl border border-brand-500/40 text-center relative overflow-hidden">
        <div className="absolute -top-12 -left-12 w-36 h-36 bg-brand-500/20 rounded-full blur-3xl pointer-events-none" />

        {phase === 'GAME_END' ? (
          <>
            <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-tr from-amber-500 to-orange-400 flex items-center justify-center text-white mb-4 shadow-xl shadow-amber-500/40">
              <Trophy className="w-8 h-8" />
            </div>

            <h2 className="text-3xl font-extrabold text-white mb-1">Game Over!</h2>
            <p className="text-slate-400 text-sm mb-6">
              🎉 <strong className="text-amber-300">{winner?.nickname || 'Player'}</strong> wins the game with{' '}
              <strong className="text-white">{winner?.score || 0} pts</strong>!
            </p>
          </>
        ) : (
          <>
            <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-400 flex items-center justify-center text-white mb-4 shadow-lg shadow-brand-500/40">
              <Sparkles className="w-7 h-7" />
            </div>

            <h2 className="text-2xl font-extrabold text-white mb-1">Round Ended!</h2>
            <p className="text-slate-400 text-sm mb-2">The secret word was:</p>
            <div className="inline-block bg-brand-950/80 px-6 py-2 rounded-2xl border border-brand-500/40 text-2xl font-black text-amber-300 tracking-widest font-mono uppercase mb-6 shadow-inner">
              {revealedWord || '---'}
            </div>
          </>
        )}

        {/* Current Leaderboard Standings */}
        <div className="bg-slate-900/60 rounded-2xl p-4 border border-slate-800 mb-6 text-left max-h-48 overflow-y-auto">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Current Standings</h4>
          <div className="space-y-2">
            {sortedPlayers.map((player, idx) => (
              <div
                key={player.nickname}
                className="flex items-center justify-between text-xs py-1.5 px-3 rounded-xl bg-slate-800/50 border border-slate-700/40"
              >
                <div className="flex items-center gap-2">
                  <span className="font-bold text-amber-400">#{idx + 1}</span>
                  <span className="font-semibold text-slate-200">{player.nickname}</span>
                </div>
                <span className="font-extrabold text-brand-300">{player.score || 0} pts</span>
              </div>
            ))}
          </div>
        </div>

        {/* Timer Bar */}
        {phase === 'ROUND_END' && (
          <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
            <span className="flex items-center gap-1.5 text-brand-400">
              <Clock className="w-4 h-4" />
              Next turn starting in {timeLeft}s
            </span>
            <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-500 transition-all duration-300 ease-linear"
                style={{ width: `${(timeLeft / (timerDurationSec || 1)) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
