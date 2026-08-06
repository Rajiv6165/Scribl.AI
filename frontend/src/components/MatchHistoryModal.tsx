'use client';

import React, { useEffect, useRef } from 'react';
import { X, Play, Trophy, Users, CheckCircle2, Paintbrush, Calendar } from 'lucide-react';
import { MatchHistoryData, RoundSummary, StrokePayload } from '../utils/types';
import { drawSmoothStroke } from '../utils/strokeSmoothing';

interface MatchHistoryModalProps {
  historyData: MatchHistoryData;
  onSelectRoundReplay: (roundId: number) => void;
  onClose: () => void;
}

const ThumbnailCanvas: React.FC<{ events: any[] }> = ({ events }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Fixed internal size for crisp thumbnail preview
    canvas.width = 300;
    canvas.height = 200;

    ctx.save();
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.restore();

    const strokes: StrokePayload[] = [];
    (events || []).forEach((ev) => {
      if (ev.action_type === 'stroke' && ev.payload) {
        strokes.push(ev.payload);
      } else if (ev.action_type === 'clear') {
        strokes.length = 0;
      } else if (ev.action_type === 'undo') {
        strokes.pop();
      }
    });

    strokes.forEach((stroke) => {
      drawSmoothStroke(ctx, stroke);
    });
  }, [events]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-32 object-contain bg-white rounded-xl border border-slate-700 shadow-sm"
    />
  );
};

export const MatchHistoryModal: React.FC<MatchHistoryModalProps> = ({
  historyData,
  onSelectRoundReplay,
  onClose,
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/90 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="glass-panel p-6 rounded-3xl max-w-4xl w-full shadow-2xl border border-brand-500/40 relative flex flex-col max-h-[85vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-amber-400 flex items-center justify-center text-white shadow-lg shadow-brand-500/30">
              <Trophy className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-white">Match History & Replays</h2>
              <p className="text-slate-400 text-xs mt-0.5">
                Room <strong className="text-brand-300">{historyData.room_code}</strong> • {historyData.rounds?.length || 0} Rounds Played
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-2xl bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Rounds Grid List */}
        <div className="overflow-y-auto pr-1 space-y-4 max-h-[60vh]">
          {(!historyData.rounds || historyData.rounds.length === 0) ? (
            <div className="p-8 text-center bg-slate-900/60 rounded-2xl border border-slate-800">
              <Paintbrush className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-slate-400 text-sm">No round history available for this match yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {historyData.rounds.map((round: RoundSummary) => (
                <div
                  key={round.round_id}
                  className="bg-slate-900/80 rounded-2xl p-4 border border-slate-800 hover:border-brand-500/50 transition shadow-lg flex flex-col justify-between"
                >
                  <div>
                    {/* Thumbnail drawing */}
                    <div className="relative mb-3 group cursor-pointer" onClick={() => onSelectRoundReplay(round.round_id)}>
                      <ThumbnailCanvas events={round.events} />
                      <div className="absolute inset-0 bg-slate-950/40 rounded-xl opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                        <span className="bg-brand-500 text-white px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-lg">
                          <Play className="w-3.5 h-3.5" /> Watch Replay
                        </span>
                      </div>
                    </div>

                    {/* Info */}
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold bg-brand-950/80 text-brand-300 border border-brand-500/30 px-2.5 py-0.5 rounded-full">
                        Round {round.round_number}
                      </span>
                      <span className="text-sm font-black text-amber-300 tracking-wide uppercase font-mono">
                        "{round.word}"
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 mb-2 flex items-center gap-1.5">
                      <Paintbrush className="w-3.5 h-3.5 text-brand-400" />
                      Artist: <strong className="text-slate-200">{round.drawer || 'Unknown'}</strong>
                    </div>

                    {/* Correct Guessers */}
                    <div className="text-xs text-slate-400">
                      <span className="font-semibold text-slate-300 block mb-1 flex items-center gap-1">
                        <Users className="w-3.5 h-3.5 text-emerald-400" /> Correct Guessers ({round.correct_guessers?.length || 0}):
                      </span>
                      {round.correct_guessers && round.correct_guessers.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {round.correct_guessers.map((g, idx) => (
                            <span
                              key={idx}
                              className="bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 text-[10px] px-2 py-0.5 rounded-md font-semibold flex items-center gap-1"
                            >
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                              {g}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-500 italic text-[11px]">No correct guesses this round</span>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => onSelectRoundReplay(round.round_id)}
                    className="mt-4 w-full py-2 rounded-xl bg-slate-800 hover:bg-brand-500 text-slate-300 hover:text-white transition font-semibold text-xs flex items-center justify-center gap-1.5 border border-slate-700"
                  >
                    <Play className="w-3.5 h-3.5" /> Launch Scrubbable Replay
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
