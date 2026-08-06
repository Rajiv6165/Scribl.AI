'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Play, Pause, RotateCcw, X, FastForward, CheckCircle2, MessageSquare, Sparkles, User } from 'lucide-react';
import { ReplayData, StrokePayload, StrokeEventData, ReplayGuess } from '../utils/types';
import { drawSmoothStroke } from '../utils/strokeSmoothing';

interface ReplayPlayerProps {
  replayData: ReplayData;
  onClose: () => void;
}

export const ReplayPlayer: React.FC<ReplayPlayerProps> = ({ replayData, onClose }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [progress, setProgress] = useState<number>(0); // 0 to 1
  const [hoveredGuess, setHoveredGuess] = useState<ReplayGuess | null>(null);

  // Time & Animation references
  const animFrameIdRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number | null>(null);
  const totalDurationMsRef = useRef<number>(80000); // Default 80 seconds max duration

  // Computed time offset for timeline progress
  const currentTimeMsRef = useRef<number>(0);

  // Calculate total round time duration in ms based on stroke timestamps or default
  useEffect(() => {
    const events = replayData.events || [];
    let maxTimeMs = (replayData.duration || 80) * 1000;

    if (events.length > 0) {
      const firstTimestamp = events[0].payload?.points?.[0]?.timestamp || 0;
      const lastEvent = events[events.length - 1];
      const lastPoints = lastEvent.payload?.points || [];
      const lastTimestamp = lastPoints.length > 0 ? lastPoints[lastPoints.length - 1].timestamp || 0 : 0;

      if (firstTimestamp > 0 && lastTimestamp > firstTimestamp) {
        maxTimeMs = Math.max(maxTimeMs, lastTimestamp - firstTimestamp + 2000);
      }
    }

    totalDurationMsRef.current = maxTimeMs;
  }, [replayData]);

  // Helper to redraw strokes up to current progress ratio or time
  const renderCanvasAtTime = useCallback((progressRatio: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const events = replayData.events || [];
    if (events.length === 0) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      return;
    }

    // Determine target index of events to draw based on progressRatio
    const targetCount = Math.floor(progressRatio * events.length);
    const visibleEvents = events.slice(0, targetCount);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // White background
    ctx.save();
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.restore();

    // Batch stroke rendering progressive state
    const currentStrokes: StrokePayload[] = [];
    visibleEvents.forEach((ev) => {
      if (ev.action_type === 'stroke' && ev.payload) {
        currentStrokes.push(ev.payload);
      } else if (ev.action_type === 'clear') {
        currentStrokes.length = 0;
      } else if (ev.action_type === 'undo') {
        currentStrokes.pop();
      }
    });

    // Draw batched strokes
    currentStrokes.forEach((stroke) => {
      drawSmoothStroke(ctx, stroke);
    });
  }, [replayData]);

  // Canvas DPI scaling and initial render
  const handleResize = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.scale(dpr, dpr);
    }

    renderCanvasAtTime(progress);
  }, [renderCanvasAtTime, progress]);

  useEffect(() => {
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [handleResize]);

  // Progressive batched rAF Animation loop
  useEffect(() => {
    if (!isPlaying) {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
      lastTimeRef.current = null;
      return;
    }

    const step = (timestamp: number) => {
      if (!lastTimeRef.current) {
        lastTimeRef.current = timestamp;
      }

      const deltaMs = (timestamp - lastTimeRef.current) * playbackSpeed;
      lastTimeRef.current = timestamp;

      const newTimeMs = currentTimeMsRef.current + deltaMs;
      const totalMs = totalDurationMsRef.current;

      if (newTimeMs >= totalMs) {
        currentTimeMsRef.current = totalMs;
        setProgress(1);
        renderCanvasAtTime(1);
        setIsPlaying(false);
        return;
      }

      currentTimeMsRef.current = newTimeMs;
      const newRatio = newTimeMs / totalMs;
      setProgress(newRatio);
      renderCanvasAtTime(newRatio);

      animFrameIdRef.current = requestAnimationFrame(step);
    };

    animFrameIdRef.current = requestAnimationFrame(step);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, renderCanvasAtTime]);

  const handlePlayPause = () => {
    if (progress >= 1) {
      // Restart from beginning if at the end
      currentTimeMsRef.current = 0;
      setProgress(0);
      renderCanvasAtTime(0);
    }
    setIsPlaying((prev) => !prev);
  };

  const handleRestart = () => {
    setIsPlaying(false);
    currentTimeMsRef.current = 0;
    setProgress(0);
    renderCanvasAtTime(0);
  };

  const handleScrubChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setProgress(val);
    currentTimeMsRef.current = val * totalDurationMsRef.current;
    renderCanvasAtTime(val);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/90 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="glass-panel p-6 rounded-3xl max-w-3xl w-full shadow-2xl border border-brand-500/40 relative flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-brand-500/20 text-brand-300 border border-brand-500/40 text-xs px-2.5 py-0.5 rounded-full font-semibold">
                Round {replayData.round_number || 1} Replay
              </span>
              <h2 className="text-xl font-black text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-400" />
                {replayData.word}
              </h2>
            </div>
            <p className="text-slate-400 text-xs mt-1 flex items-center gap-3">
              <span className="flex items-center gap-1">
                <User className="w-3.5 h-3.5 text-brand-400" />
                Drawn by: <strong className="text-slate-200">{replayData.drawer || 'Unknown'}</strong>
              </span>
              <span>•</span>
              <span>{replayData.total_strokes || 0} stroke actions</span>
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-2xl bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawing Canvas Area */}
        <div
          ref={containerRef}
          className="relative w-full h-[360px] bg-white rounded-2xl overflow-hidden shadow-inner border border-slate-700 mb-4 flex items-center justify-center"
        >
          <canvas ref={canvasRef} className="w-full h-full block touch-none" />

          {/* Hovered Guess Tooltip Preview */}
          {hoveredGuess && (
            <div className="absolute top-4 left-4 bg-slate-900/90 text-white px-3 py-2 rounded-xl text-xs border border-slate-700 shadow-xl flex items-center gap-2 animate-in fade-in">
              <MessageSquare className="w-4 h-4 text-brand-400" />
              <div>
                <span className="font-bold">{hoveredGuess.nickname}: </span>
                <span className={hoveredGuess.is_correct ? 'text-emerald-400 font-bold' : 'text-slate-300'}>
                  "{hoveredGuess.text}"
                </span>
                {hoveredGuess.is_correct && <span className="ml-1 text-emerald-400">✓ Correct</span>}
              </div>
            </div>
          )}
        </div>

        {/* Timeline & Controls */}
        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 space-y-4">
          
          {/* Draggable Scrub Bar with Guess Markers */}
          <div className="relative w-full pt-2">
            
            {/* Timeline guess markers */}
            <div className="absolute top-0 left-0 right-0 h-2 pointer-events-none">
              {(replayData.guessers || []).map((guess, idx) => {
                const totalMs = totalDurationMsRef.current || 80000;
                const posPercent = Math.min(100, Math.max(0, (guess.timestamp_ms / totalMs) * 100));

                return (
                  <div
                    key={idx}
                    className={`absolute top-0 w-2.5 h-2.5 rounded-full -translate-x-1/2 cursor-pointer pointer-events-auto transition-transform hover:scale-150 ${
                      guess.is_correct
                        ? 'bg-emerald-400 shadow-lg shadow-emerald-500/50 ring-2 ring-emerald-300'
                        : 'bg-slate-500 hover:bg-amber-400'
                    }`}
                    style={{ left: `${posPercent}%` }}
                    onMouseEnter={() => setHoveredGuess(guess)}
                    onMouseLeave={() => setHoveredGuess(null)}
                  />
                );
              })}
            </div>

            <input
              type="range"
              min="0"
              max="1"
              step="0.001"
              value={progress}
              onChange={handleScrubChange}
              className="w-full accent-brand-500 cursor-pointer h-2 bg-slate-800 rounded-lg appearance-none"
            />
          </div>

          {/* Controls Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={handlePlayPause}
                className="w-10 h-10 rounded-xl bg-brand-500 hover:bg-brand-400 text-white flex items-center justify-center shadow-lg shadow-brand-500/30 transition font-bold"
              >
                {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
              </button>

              <button
                onClick={handleRestart}
                className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                title="Restart Replay"
              >
                <RotateCcw className="w-4 h-4" />
              </button>

              <span className="text-xs font-mono text-slate-400 ml-2">
                {Math.floor((progress * totalDurationMsRef.current) / 1000)}s /{' '}
                {Math.floor(totalDurationMsRef.current / 1000)}s
              </span>
            </div>

            {/* Playback Speed Selectors */}
            <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
              {[0.5, 1, 2, 4].map((spd) => (
                <button
                  key={spd}
                  onClick={() => setPlaybackSpeed(spd)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition ${
                    playbackSpeed === spd
                      ? 'bg-brand-500 text-white shadow-md'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {spd}x
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Guesses Log Footer */}
        {(replayData.guessers || []).length > 0 && (
          <div className="mt-4 pt-3 border-t border-slate-800 overflow-hidden">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Round Guesses Timeline</h4>
            <div className="flex items-center gap-2 overflow-x-auto pb-1 max-w-full">
              {replayData.guessers.map((g, idx) => (
                <div
                  key={idx}
                  className={`text-xs px-2.5 py-1 rounded-xl whitespace-nowrap border flex items-center gap-1.5 ${
                    g.is_correct
                      ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300 font-semibold'
                      : 'bg-slate-800/60 border-slate-700/40 text-slate-300'
                  }`}
                >
                  {g.is_correct && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                  <span>{g.nickname}:</span>
                  <span className="font-mono">"{g.text}"</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
