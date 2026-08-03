'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageSquare, CheckCircle2 } from 'lucide-react';
import { ChatMessage } from '../utils/types';

interface ChatPanelProps {
  chatMessages: ChatMessage[];
  currentNickname: string;
  isDrawer: boolean;
  hasGuessed: boolean;
  onSendGuess: (text: string) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  chatMessages,
  currentNickname,
  isDrawer,
  hasGuessed,
  onSendGuess,
}) => {
  const [text, setText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isDrawer || hasGuessed) return;
    onSendGuess(text.trim());
    setText('');
  };

  const isDisabled = isDrawer || hasGuessed;

  return (
    <div className="glass-panel p-4 rounded-2xl flex flex-col gap-3 border border-slate-700/50 h-full max-h-[500px]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-700/50 pb-2">
        <h3 className="font-bold text-slate-200 text-sm tracking-wide uppercase flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-brand-400" />
          <span>Live Chat & Guesses</span>
        </h3>
      </div>

      {/* Messages Scroll View */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1 min-h-[220px]">
        {chatMessages.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4 text-center">
            Type your guess below when drawing starts!
          </p>
        ) : (
          chatMessages.map((msg) => {
            const isMe = msg.nickname.toLowerCase() === currentNickname.toLowerCase();

            if (msg.is_system) {
              return (
                <div
                  key={msg.id}
                  className="bg-emerald-950/60 border border-emerald-800/50 text-emerald-300 px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 animate-in fade-in"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>{msg.text}</span>
                </div>
              );
            }

            return (
              <div
                key={msg.id}
                className={`text-xs p-2 rounded-xl border ${
                  isMe
                    ? 'bg-brand-900/30 border-brand-500/40 text-slate-200 ml-4'
                    : 'bg-slate-900/60 border-slate-800 text-slate-300 mr-4'
                }`}
              >
                <span className="font-bold text-brand-300 mr-1.5">{msg.nickname}:</span>
                <span className="break-words">{msg.text}</span>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Guess Input Form */}
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={text}
          disabled={isDisabled}
          onChange={(e) => setText(e.target.value)}
          placeholder={
            isDrawer
              ? 'You are drawing! Cannot guess.'
              : hasGuessed
              ? 'You guessed correctly!'
              : 'Type your guess here...'
          }
          className="w-full pl-3.5 pr-10 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={isDisabled || !text.trim()}
          className="absolute right-1.5 top-1.5 p-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white disabled:opacity-40 transition-colors"
          title="Send Guess"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
};
