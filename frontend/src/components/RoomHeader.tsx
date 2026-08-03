'use client';

import React, { useState } from 'react';
import { Copy, Check, Sparkles, Wifi, WifiOff } from 'lucide-react';

interface RoomHeaderProps {
  roomCode: string;
  connected: boolean;
}

export const RoomHeader: React.FC<RoomHeaderProps> = ({ roomCode, connected }) => {
  const [copied, setCopied] = useState(false);

  const handleCopyLink = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <header className="glass-panel px-6 py-3.5 rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xl border border-slate-700/50">
      {/* Brand Title */}
      <div className="flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-400 flex items-center justify-center text-white shadow-lg shadow-brand-500/30">
          <Sparkles className="w-5 h-5" />
        </div>
        <h1 className="text-xl font-extrabold tracking-tight text-white flex items-center gap-1.5">
          Scribl<span className="text-brand-400">.AI</span>
        </h1>
      </div>

      {/* Room Code & Invite Copy */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-slate-900/80 px-3.5 py-1.5 rounded-xl border border-slate-700/80">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Room Code:</span>
          <span className="text-base font-extrabold text-brand-300 tracking-widest font-mono">
            {roomCode}
          </span>
          <button
            type="button"
            onClick={handleCopyLink}
            className="ml-1.5 p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Copy Invite Link"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>

        {/* Connection Status Pill */}
        <div
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-colors ${
            connected
              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/50'
              : 'bg-amber-950/60 text-amber-300 border-amber-800/50'
          }`}
        >
          {connected ? (
            <>
              <Wifi className="w-3.5 h-3.5 text-emerald-400" />
              <span>Live</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-amber-400" />
              <span>Connecting...</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
