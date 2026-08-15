'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, Users, Palette, ArrowRight, PlusCircle, LogIn } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  const [nickname, setNickname] = useState('');
  const [roomCode, setRoomCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'create' | 'join'>('create');

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nickname.trim()) {
      setError('Please enter a nickname.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${apiUrl}/api/rooms/create/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname: nickname.trim() }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Failed to create room.');
      }

      // Store nickname locally for persistence
      sessionStorage.setItem('scribl_nickname', nickname.trim());
      router.push(`/room/${data.room_code}?nickname=${encodeURIComponent(nickname.trim())}`);
    } catch (err: any) {
      setError(err.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  const handleJoinRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nickname.trim()) {
      setError('Please enter a nickname.');
      return;
    }
    if (!roomCode.trim()) {
      setError('Please enter a room code.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const code = roomCode.trim().toUpperCase();
      const res = await fetch(`${apiUrl}/api/rooms/join/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_code: code, nickname: nickname.trim() }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Room not found or unable to join.');
      }

      sessionStorage.setItem('scribl_nickname', nickname.trim());
      router.push(`/room/${code}?nickname=${encodeURIComponent(nickname.trim())}`);
    } catch (err: any) {
      setError(err.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  const handleSpectateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roomCode.trim()) {
      setError('Please enter a room code to watch.');
      return;
    }

    const name = nickname.trim() || `Spectator_${Math.floor(100 + Math.random() * 900)}`;
    const code = roomCode.trim().toUpperCase();
    sessionStorage.setItem('scribl_nickname', name);
    router.push(`/room/${code}?nickname=${encodeURIComponent(name)}&spectate=true`);
  };

  return (
    <main className="min-h-screen relative flex items-center justify-center p-6 overflow-hidden">
      {/* Dynamic Background Glow Elements */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-brand-600/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Logo & Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-400 text-white mb-4 shadow-2xl shadow-brand-500/40">
            <Sparkles className="w-8 h-8" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">
            Scribl<span className="text-brand-400">.AI</span>
          </h1>
          <p className="text-slate-400 text-sm">
            Real-time multiplayer drawing & guessing built for production performance.
          </p>
        </div>

        {/* Form Container */}
        <div className="glass-panel p-6 rounded-3xl shadow-2xl border border-slate-700/60 backdrop-blur-xl">
          {/* Tab Selector */}
          <div className="grid grid-cols-2 gap-2 bg-slate-900/80 p-1.5 rounded-2xl border border-slate-800 mb-6">
            <button
              type="button"
              onClick={() => setActiveTab('create')}
              className={`flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'create'
                  ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Room</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('join')}
              className={`flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'join'
                  ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <LogIn className="w-4 h-4" />
              <span>Join Room</span>
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs font-semibold">
              {error}
            </div>
          )}

          {activeTab === 'create' ? (
            <form onSubmit={handleCreateRoom} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
                  Your Nickname
                </label>
                <input
                  type="text"
                  required
                  maxLength={20}
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="e.g. Picasso"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold text-sm shadow-xl shadow-brand-500/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <span>{loading ? 'Creating Room...' : 'Create New Room'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          ) : (
            <form onSubmit={handleJoinRoom} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
                  Your Nickname (Optional for Spectators)
                </label>
                <input
                  type="text"
                  maxLength={20}
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="e.g. Leonardo (or leave blank to watch)"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
                  Room Code
                </label>
                <input
                  type="text"
                  required
                  maxLength={8}
                  value={roomCode}
                  onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                  placeholder="e.g. AB12CD"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 font-mono tracking-widest uppercase focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold text-xs shadow-xl shadow-brand-500/25 transition-all flex items-center justify-center gap-1.5"
                >
                  <span>{loading ? 'Joining...' : 'Join Game'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                <button
                  type="button"
                  onClick={handleSpectateRoom}
                  disabled={loading}
                  className="w-full py-3 px-4 rounded-xl bg-purple-900/40 hover:bg-purple-800/60 border border-purple-500/40 text-purple-200 font-bold text-xs shadow-lg transition-all flex items-center justify-center gap-1.5"
                >
                  <span>Watch Spectator</span>
                  <span className="text-base">👁️</span>
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer Feature Badges */}
        <div className="mt-8 grid grid-cols-2 gap-3 text-center text-xs font-medium text-slate-400">
          <div className="flex items-center justify-center gap-1.5 bg-slate-900/40 py-2 px-3 rounded-xl border border-slate-800/60">
            <Palette className="w-3.5 h-3.5 text-brand-400" />
            <span>Smooth Canvas</span>
          </div>
          <div className="flex items-center justify-center gap-1.5 bg-slate-900/40 py-2 px-3 rounded-xl border border-slate-800/60">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            <span>Multiplayer Lobby</span>
          </div>
        </div>
      </div>
    </main>
  );
}
