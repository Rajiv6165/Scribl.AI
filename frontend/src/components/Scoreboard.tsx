'use client';

import React from 'react';
import { Player, GamePhase } from '../utils/types';
import { Crown, Paintbrush, CheckCircle2, Play, Trophy, AlertTriangle } from 'lucide-react';

interface ScoreboardProps {
  players: Player[];
  currentNickname: string;
  currentDrawer: string;
  phase: GamePhase;
  isHost: boolean;
  onStartGame: () => void;
}

export const Scoreboard: React.FC<ScoreboardProps> = ({
  players,
  currentNickname,
  currentDrawer,
  phase,
  isHost,
  onStartGame,
}) => {
  // Sort players by score descending
  const sortedPlayers = [...players].sort((a, b) => (b.score || 0) - (a.score || 0));

  return (
    <div className="glass-panel p-4 rounded-2xl flex flex-col gap-3 border border-slate-700/50 h-full">
      <div className="flex items-center justify-between border-b border-slate-700/50 pb-2">
        <h3 className="font-bold text-slate-200 text-sm tracking-wide uppercase flex items-center gap-2">
          <Trophy className="w-4 h-4 text-amber-400" />
          <span>Scoreboard</span>
        </h3>
      </div>

      {/* Start Game button for Host in LOBBY */}
      {phase === 'LOBBY' && isHost && (
        <button
          type="button"
          onClick={onStartGame}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-extrabold text-sm shadow-xl shadow-brand-500/30 transition-all flex items-center justify-center gap-2 transform hover:-translate-y-0.5"
        >
          <Play className="w-4 h-4 fill-white" />
          <span>Start Game</span>
        </button>
      )}

      {/* Players Ranking List */}
      <div className="flex flex-col gap-2 overflow-y-auto max-h-[380px] pr-1">
        {sortedPlayers.map((player, idx) => {
          const isMe = player.nickname.toLowerCase() === currentNickname.toLowerCase();
          const isDrawing = player.nickname.toLowerCase() === currentDrawer.toLowerCase();

          // Rank badges
          const rank = idx + 1;
          let rankColor = 'bg-slate-800 text-slate-400 border-slate-700';
          if (rank === 1) rankColor = 'bg-amber-500/20 text-amber-300 border-amber-500/40';
          else if (rank === 2) rankColor = 'bg-slate-300/20 text-slate-200 border-slate-400/40';
          else if (rank === 3) rankColor = 'bg-amber-700/20 text-amber-500 border-amber-700/40';

          return (
            <div
              key={player.nickname}
              className={`flex items-center justify-between p-2.5 rounded-xl border transition-all ${
                isMe
                  ? 'bg-brand-950/60 border-brand-500/50 text-white shadow-md'
                  : 'bg-slate-900/50 border-slate-800 text-slate-300'
              }`}
            >
              <div className="flex items-center gap-2.5">
                {/* Rank Number */}
                <div
                  className={`w-6 h-6 rounded-lg font-bold text-xs flex items-center justify-center border ${rankColor}`}
                >
                  #{rank}
                </div>

                <div className="flex flex-col">
                  <span className="text-xs font-bold flex items-center gap-1.5">
                    {player.nickname}
                    {player.is_ai && (
                      <span className="text-[9px] bg-purple-500/30 text-purple-300 border border-purple-400/40 px-1 py-0.2 rounded font-mono font-bold">
                        BOT
                      </span>
                    )}
                    {player.is_host && <Crown className="w-3 h-3 text-amber-400" />}
                  </span>
                  <span className="text-[11px] font-extrabold text-brand-400">
                    {player.score || 0} pts
                  </span>
                </div>
              </div>

              {/* Status Badges */}
              <div className="flex items-center gap-1.5">
                {isHost && player.is_flagged && (
                  <span
                    className="p-1 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/40 cursor-help"
                    title={`Anti-cheat flagged suspicious drawing patterns (${Math.round((player.anomaly_score || 0.7) * 100)}% confidence)`}
                  >
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  </span>
                )}
                {isDrawing && (
                  <span className="p-1 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30" title="Currently Drawing">
                    <Paintbrush className="w-3.5 h-3.5" />
                  </span>
                )}
                {player.has_guessed && !isDrawing && (
                  <span className="p-1 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" title="Guessed Correctly!">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
