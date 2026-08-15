'use client';

import React from 'react';
import { Player } from '../utils/types';
import { Crown, User, Wifi, WifiOff, AlertTriangle } from 'lucide-react';

interface PlayerListProps {
  players: Player[];
  currentNickname: string;
  isHost?: boolean;
}

// Generate consistent avatar colors from nickname string
function getAvatarColor(name: string): string {
  const colors = [
    'from-indigo-500 to-purple-600',
    'from-pink-500 to-rose-600',
    'from-amber-500 to-orange-600',
    'from-emerald-500 to-teal-600',
    'from-cyan-500 to-blue-600',
    'from-violet-500 to-fuchsia-600',
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % colors.length;
  return colors[index];
}

export const PlayerList: React.FC<PlayerListProps> = ({ players, currentNickname, isHost = false }) => {
  return (
    <div className="glass-panel p-4 rounded-2xl flex flex-col gap-3 border border-slate-700/50 h-full">
      <div className="flex items-center justify-between border-b border-slate-700/50 pb-2">
        <h3 className="font-bold text-slate-200 text-sm tracking-wide uppercase flex items-center gap-2">
          <User className="w-4 h-4 text-brand-400" />
          <span>Connected Players ({players.length})</span>
        </h3>
      </div>

      <div className="flex flex-col gap-2 overflow-y-auto max-h-[500px] pr-1">
        {players.length === 0 ? (
          <p className="text-xs text-slate-400 italic py-2">Waiting for players...</p>
        ) : (
          players.map((player) => {
            const isMe = player.nickname.toLowerCase() === currentNickname.toLowerCase();
            const avatarGradient = getAvatarColor(player.nickname);

            return (
              <div
                key={player.nickname}
                className={`flex items-center justify-between p-2.5 rounded-xl border transition-all ${
                  isMe
                    ? 'bg-brand-900/40 border-brand-500/50 text-white'
                    : 'bg-slate-800/40 border-slate-700/40 text-slate-300'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  {/* Player Avatar */}
                  <div
                    className={`w-8 h-8 rounded-lg bg-gradient-to-br ${avatarGradient} flex items-center justify-center font-bold text-xs text-white shadow-md`}
                  >
                    {player.nickname.substring(0, 2).toUpperCase()}
                  </div>

                  <div className="flex flex-col">
                    <span className="text-sm font-semibold flex items-center gap-1.5">
                      {player.nickname}
                      {player.is_ai && (
                        <span className="text-[10px] bg-purple-500/30 text-purple-300 border border-purple-400/40 px-1.5 py-0.5 rounded font-mono font-bold flex items-center gap-0.5">
                          BOT
                        </span>
                      )}
                      {isMe && (
                        <span className="text-[10px] bg-brand-500/30 text-brand-300 px-1.5 py-0.5 rounded font-mono">
                          You
                        </span>
                      )}
                      {/* Host-only Anti-Cheat Flagged Badge */}
                      {isHost && player.is_flagged && (
                        <span
                          className="flex items-center gap-1 text-[10px] font-bold text-amber-400 bg-amber-500/20 px-1.5 py-0.5 rounded border border-amber-500/40 cursor-help"
                          title={`Anti-cheat flagged suspicious drawing patterns (${Math.round((player.anomaly_score || 0.7) * 100)}% confidence)`}
                        >
                          <AlertTriangle className="w-3 h-3 text-amber-400" />
                          Flagged
                        </span>
                      )}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {player.is_host && (
                    <span className="flex items-center gap-1 text-[11px] font-bold text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded-full border border-amber-400/20">
                      <Crown className="w-3 h-3" />
                      Host
                    </span>
                  )}

                  {player.is_connected ? (
                    <span className="flex items-center text-emerald-400" title="Connected">
                      <Wifi className="w-3.5 h-3.5" />
                    </span>
                  ) : (
                    <span className="flex items-center text-slate-500" title="Disconnected">
                      <WifiOff className="w-3.5 h-3.5" />
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
