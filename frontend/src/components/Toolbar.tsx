'use client';

import React from 'react';
import { Paintbrush, Eraser, RotateCcw, Trash2 } from 'lucide-react';

interface ToolbarProps {
  color: string;
  setColor: (color: string) => void;
  brushSize: number;
  setBrushSize: (size: number) => void;
  isEraser: boolean;
  setIsEraser: (isEraser: boolean) => void;
  onUndo: () => void;
  onClear: () => void;
}

const PRESET_COLORS = [
  '#000000', // Black
  '#ffffff', // White
  '#ef4444', // Red
  '#f97316', // Orange
  '#eab308', // Yellow
  '#22c55e', // Green
  '#06b6d4', // Cyan
  '#3b82f6', // Blue
  '#a855f7', // Purple
  '#ec4899', // Pink
  '#78350f', // Brown
  '#64748b', // Slate
];

export const Toolbar: React.FC<ToolbarProps> = ({
  color,
  setColor,
  brushSize,
  setBrushSize,
  isEraser,
  setIsEraser,
  onUndo,
  onClear,
}) => {
  return (
    <div className="glass-panel p-4 rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xl border border-slate-700/50">
      {/* Tools & Drawing Mode */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setIsEraser(false)}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
            !isEraser
              ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/30 scale-105'
              : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
          }`}
        >
          <Paintbrush className="w-4 h-4" />
          <span>Brush</span>
        </button>

        <button
          type="button"
          onClick={() => setIsEraser(true)}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
            isEraser
              ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/30 scale-105'
              : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
          }`}
        >
          <Eraser className="w-4 h-4" />
          <span>Eraser</span>
        </button>
      </div>

      {/* Color Palette & Custom Picker */}
      <div className="flex items-center gap-2 bg-slate-900/60 p-2 rounded-xl border border-slate-800">
        <div className="flex items-center gap-1.5 flex-wrap">
          {PRESET_COLORS.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => {
                setColor(c);
                setIsEraser(false);
              }}
              style={{ backgroundColor: c }}
              className={`w-6 h-6 rounded-full transition-transform duration-150 hover:scale-125 border ${
                color === c && !isEraser
                  ? 'ring-2 ring-brand-500 ring-offset-2 ring-offset-slate-900 scale-110 border-white'
                  : 'border-slate-700/60'
              }`}
              title={c}
            />
          ))}
        </div>

        {/* Custom Color Input */}
        <div className="relative flex items-center justify-center w-7 h-7 rounded-full overflow-hidden border border-slate-700 cursor-pointer hover:scale-105 transition-transform">
          <input
            type="color"
            value={color}
            onChange={(e) => {
              setColor(e.target.value);
              setIsEraser(false);
            }}
            className="absolute -top-2 -left-2 w-12 h-12 cursor-pointer opacity-0"
            title="Choose custom color"
          />
          <div
            className="w-full h-full"
            style={{ backgroundColor: color }}
          />
        </div>
      </div>

      {/* Brush Size Slider */}
      <div className="flex items-center gap-3 bg-slate-900/60 px-3 py-2 rounded-xl border border-slate-800 min-w-[180px]">
        <span className="text-xs font-semibold text-slate-400">Size</span>
        <input
          type="range"
          min="2"
          max="40"
          value={brushSize}
          onChange={(e) => setBrushSize(Number(e.target.value))}
          className="w-24 accent-brand-500 cursor-pointer"
        />
        {/* Preview Circle */}
        <div className="flex items-center justify-center w-7 h-7">
          <div
            className="rounded-full bg-white transition-all"
            style={{
              width: `${Math.min(brushSize, 24)}px`,
              height: `${Math.min(brushSize, 24)}px`,
              backgroundColor: isEraser ? '#94a3b8' : color,
            }}
          />
        </div>
      </div>

      {/* Action Buttons: Undo & Clear */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onUndo}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold text-slate-300 bg-slate-800 hover:bg-slate-700 hover:text-white transition-all border border-slate-700"
          title="Undo last stroke"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Undo</span>
        </button>

        <button
          type="button"
          onClick={onClear}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold text-rose-300 bg-rose-950/40 hover:bg-rose-900/60 hover:text-rose-100 transition-all border border-rose-800/40"
          title="Clear canvas"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear</span>
        </button>
      </div>
    </div>
  );
};
