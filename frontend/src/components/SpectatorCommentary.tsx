import React from 'react';
import { CommentaryItem } from '../hooks/useRoomSocket';

interface SpectatorCommentaryProps {
  commentaryFeed: CommentaryItem[];
}

export const SpectatorCommentary: React.FC<SpectatorCommentaryProps> = ({ commentaryFeed }) => {
  if (!commentaryFeed || commentaryFeed.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-indigo-500/20 backdrop-blur-md rounded-xl p-4 text-slate-400 text-xs text-center shadow-lg">
        <div className="flex items-center justify-center gap-2 mb-1 text-indigo-400 font-semibold uppercase tracking-wider text-[11px]">
          <span className="animate-pulse">🎙️</span> AI Live Commentary
        </div>
        <p className="text-slate-400 italic">Waiting for live drawing action beat...</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/70 border border-indigo-500/30 backdrop-blur-md rounded-xl p-4 shadow-xl flex flex-col gap-3 max-h-48 overflow-y-auto custom-scrollbar">
      <div className="flex items-center justify-between border-b border-indigo-500/20 pb-2">
        <div className="flex items-center gap-2 text-indigo-300 font-bold text-xs uppercase tracking-wider">
          <span className="text-base animate-bounce">🎙️</span> Spectator Shoutcast
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono">
          LIVE BEAT
        </span>
      </div>

      <div className="space-y-2">
        {commentaryFeed.map((item, idx) => (
          <div
            key={item.id}
            className={`p-2.5 rounded-lg border text-xs transition-all duration-300 ${
              idx === 0
                ? 'bg-indigo-950/80 border-indigo-500/50 text-indigo-100 shadow-md animate-fade-in font-medium scale-[1.01]'
                : 'bg-slate-800/40 border-slate-700/30 text-slate-300 opacity-80'
            }`}
          >
            <div className="flex items-start gap-2">
              <span className="text-indigo-400 font-bold shrink-0">{item.commentary}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
