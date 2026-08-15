'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useRoomSocket } from '../../../hooks/useRoomSocket';
import { Canvas, CanvasRef } from '../../../components/Canvas';
import { Toolbar } from '../../../components/Toolbar';
import { Scoreboard } from '../../../components/Scoreboard';
import { ChatPanel } from '../../../components/ChatPanel';
import { WordHintDisplay } from '../../../components/WordHintDisplay';
import { WordSelectModal } from '../../../components/WordSelectModal';
import { RoundEndModal } from '../../../components/RoundEndModal';
import { AIWordPackModal } from '../../../components/AIWordPackModal';
import { ReplayPlayer } from '../../../components/ReplayPlayer';
import { MatchHistoryModal } from '../../../components/MatchHistoryModal';
import { RoomHeader } from '../../../components/RoomHeader';
import { SpectatorCommentary } from '../../../components/SpectatorCommentary';
import { StrokePayload, StrokeEventData, ReplayData, MatchHistoryData } from '../../../utils/types';
import { Bot, Wand2, Flame, History, Play } from 'lucide-react';

export default function RoomPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const roomCode = (params.code as string)?.toUpperCase() || '';
  const searchNickname = searchParams.get('nickname') || '';
  const isSpectatorParam = searchParams.get('spectate') === 'true';

  const [nickname, setNickname] = useState<string>('');
  const [color, setColor] = useState<string>('#000000');
  const [brushSize, setBrushSize] = useState<number>(6);
  const [isEraser, setIsEraser] = useState<boolean>(false);
  const [showThemeModal, setShowThemeModal] = useState<boolean>(false);

  const [activeReplayData, setActiveReplayData] = useState<ReplayData | null>(null);
  const [activeMatchHistory, setActiveMatchHistory] = useState<MatchHistoryData | null>(null);
  const [isLoadingReplay, setIsLoadingReplay] = useState<boolean>(false);

  const canvasRef = useRef<CanvasRef | null>(null);

  useEffect(() => {
    const stored = searchNickname || sessionStorage.getItem('scribl_nickname') || '';
    if (!stored) {
      router.push('/');
    } else {
      setNickname(stored);
    }
  }, [searchNickname, router]);

  const handleFetchRoundReplay = async (roundId?: number) => {
    try {
      setIsLoadingReplay(true);
      const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      let url = `${apiHost}/api/rooms/${roomCode}/replay/`;
      if (roundId) {
        url = `${apiHost}/api/rooms/${roomCode}/rounds/${roundId}/replay/`;
      }
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch replay data');
      const data: ReplayData = await res.json();
      setActiveReplayData(data);
    } catch (err) {
      console.error('Error fetching replay data:', err);
    } finally {
      setIsLoadingReplay(false);
    }
  };

  const handleFetchMatchHistory = async () => {
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiHost}/api/rooms/${roomCode}/rounds/`);
      if (!res.ok) throw new Error('Failed to fetch match history');
      const data: MatchHistoryData = await res.json();
      setActiveMatchHistory(data);
    } catch (err) {
      console.error('Error fetching match history:', err);
    }
  };

  const handleRemoteStroke = (data: { nickname: string; payload: StrokePayload }) => {
    if (data.nickname !== nickname) {
      canvasRef.current?.drawRemoteStroke(data.payload);
    }
  };

  const handleRemoteClear = (remoteNickname: string) => {
    canvasRef.current?.clearCanvasLocal();
  };

  const handleRemoteUndo = (remoteNickname: string) => {
    canvasRef.current?.undoLocal();
  };

  const handleStateSynced = (history: StrokeEventData[]) => {
    canvasRef.current?.syncHistory(history);
  };

  const {
    connected,
    players,
    isHost,
    isSpectatorMode,
    spectatorCount,
    commentaryFeed,
    phase,
    smartAIEnabled,
    roastModeEnabled,
    customTheme,
    drawingRoast,
    matchRecap,
    currentRoundNum,
    totalRounds,
    currentDrawer,
    wordChoices,
    wordHint,
    revealedWord,
    timerStartMs,
    timerDurationSec,
    chatMessages,
    toggleSmartAI,
    toggleRoastMode,
    generateWordPack,
    startGame,
    selectWord,
    submitGuess,
    sendTimerExpired,
    sendStroke,
    sendClear,
    sendUndo,
  } = useRoomSocket({
    roomCode,
    nickname,
    isSpectator: isSpectatorParam,
    onStrokeReceived: handleRemoteStroke,
    onClearReceived: handleRemoteClear,
    onUndoReceived: handleRemoteUndo,
    onStateSynced: handleStateSynced,
  });

  const isDrawer = nickname.toLowerCase() === currentDrawer.toLowerCase();
  const currentPlayer = players.find((p) => p.nickname.toLowerCase() === nickname.toLowerCase());
  const hasGuessed = currentPlayer?.has_guessed || false;

  const handleLocalStrokeComplete = (payload: StrokePayload) => {
    sendStroke(payload);
  };

  const handleLocalClear = () => {
    canvasRef.current?.clearCanvasLocal();
    sendClear();
  };

  const handleLocalUndo = () => {
    canvasRef.current?.undoLocal();
    sendUndo();
  };

  if (!nickname) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400 font-semibold">
        Joining game room...
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-6 flex flex-col gap-4 max-w-7xl mx-auto">
      {/* Header Bar */}
      <RoomHeader
        roomCode={roomCode}
        connected={connected}
        spectatorCount={spectatorCount}
        isSpectatorMode={isSpectatorMode}
      />

      {/* Host AI & Custom Theme Toolbar (Visible in LOBBY for Host) */}
      {phase === 'LOBBY' && isHost && (
        <div className="glass-panel px-4 py-3 rounded-2xl flex flex-wrap items-center justify-between gap-3 border border-purple-500/30">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <Bot className="w-4 h-4 text-purple-400" />
                <span>Smart AI Bot:</span>
              </span>
              <button
                type="button"
                onClick={() => toggleSmartAI(!smartAIEnabled)}
                className={`px-3 py-1 rounded-xl text-xs font-extrabold transition-all ${
                  smartAIEnabled
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-500/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                {smartAIEnabled ? 'ENABLED' : 'DISABLED'}
              </button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <Flame className="w-4 h-4 text-rose-400" />
                <span>AI Roast Mode:</span>
              </span>
              <button
                type="button"
                onClick={() => toggleRoastMode(!roastModeEnabled)}
                className={`px-3 py-1 rounded-xl text-xs font-extrabold transition-all ${
                  roastModeEnabled
                    ? 'bg-rose-600 text-white shadow-md shadow-rose-500/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                {roastModeEnabled ? 'ENABLED' : 'DISABLED'}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleFetchMatchHistory}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-all"
            >
              <History className="w-3.5 h-3.5" />
              <span>Match History</span>
            </button>

            {customTheme && (
              <span className="text-xs font-semibold text-purple-300 bg-purple-950/60 px-3 py-1 rounded-xl border border-purple-800/50">
                Theme: <strong>{customTheme}</strong>
              </span>
            )}

            <button
              type="button"
              onClick={() => setShowThemeModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-extrabold shadow-md shadow-purple-500/20 transition-all"
            >
              <Wand2 className="w-3.5 h-3.5" />
              <span>{customTheme ? 'Change AI Word Pack' : 'Generate AI Theme Pack'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Word Hint & Timer Bar */}
      {phase !== 'LOBBY' && (
        <WordHintDisplay
          phase={phase}
          wordHint={wordHint}
          isDrawer={isDrawer}
          currentDrawer={currentDrawer}
          currentRoundNum={currentRoundNum}
          totalRounds={totalRounds}
          timerStartMs={timerStartMs}
          timerDurationSec={timerDurationSec}
          onTimerExpired={sendTimerExpired}
        />
      )}

      {/* Main Game Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-[600px]">
        {/* Left Column (3 cols): Scoreboard */}
        <div className="lg:col-span-3 h-full">
          <Scoreboard
            players={players}
            currentNickname={nickname}
            currentDrawer={currentDrawer}
            phase={phase}
            isHost={isHost}
            onStartGame={startGame}
          />
        </div>

        {/* Middle Column (6 cols): Drawing Canvas, Live Spectator Commentary & Toolbar */}
        <div className="lg:col-span-6 flex flex-col gap-4">
          {/* Live AI Spectator Shoutcast Feed (Visible ONLY for Spectators) */}
          {isSpectatorMode && (
            <SpectatorCommentary commentaryFeed={commentaryFeed} />
          )}

          <div className="flex-1 min-h-[460px]">
            <Canvas
              ref={canvasRef}
              color={color}
              brushSize={brushSize}
              isEraser={isEraser}
              isReadOnly={isSpectatorMode || (!isDrawer || phase !== 'DRAWING')}
              onStrokeComplete={handleLocalStrokeComplete}
            />
          </div>

          {/* Controls toolbar enabled for active drawer during DRAWING phase */}
          {!isSpectatorMode && isDrawer && phase === 'DRAWING' && (
            <Toolbar
              color={color}
              setColor={setColor}
              brushSize={brushSize}
              setBrushSize={setBrushSize}
              isEraser={isEraser}
              setIsEraser={setIsEraser}
              onUndo={handleLocalUndo}
              onClear={handleLocalClear}
            />
          )}
        </div>

        {/* Right Column (3 cols): Chat & Guess Panel */}
        <div className="lg:col-span-3 h-full">
          <ChatPanel
            chatMessages={chatMessages}
            currentNickname={nickname}
            isDrawer={isDrawer}
            hasGuessed={hasGuessed}
            isSpectator={isSpectatorMode}
            onSendGuess={submitGuess}
          />
        </div>
      </div>

      {/* Word Selection Modal Overlay for Active Drawer */}
      {phase === 'WORD_SELECT' && isDrawer && wordChoices.length > 0 && (
        <WordSelectModal
          wordChoices={wordChoices}
          timerStartMs={timerStartMs}
          timerDurationSec={timerDurationSec}
          onSelectWord={selectWord}
        />
      )}

      {/* AI Theme Word Pack Modal */}
      {showThemeModal && (
        <AIWordPackModal
          currentTheme={customTheme}
          onGenerateTheme={generateWordPack}
          onClose={() => setShowThemeModal(false)}
        />
      )}

      {/* Round End / Game Over Summary Modal */}
      {(phase === 'ROUND_END' || phase === 'GAME_END') && (
        <RoundEndModal
          phase={phase}
          revealedWord={revealedWord}
          drawingRoast={drawingRoast}
          matchRecap={matchRecap}
          players={players}
          timerStartMs={timerStartMs}
          timerDurationSec={timerDurationSec}
          onWatchReplay={() => handleFetchRoundReplay()}
          onOpenMatchHistory={handleFetchMatchHistory}
        />
      )}

      {/* Replay Player Modal */}
      {activeReplayData && (
        <ReplayPlayer
          replayData={activeReplayData}
          onClose={() => setActiveReplayData(null)}
        />
      )}

      {/* Match History Modal */}
      {activeMatchHistory && (
        <MatchHistoryModal
          historyData={activeMatchHistory}
          onSelectRoundReplay={(roundId) => handleFetchRoundReplay(roundId)}
          onClose={() => setActiveMatchHistory(null)}
        />
      )}
    </div>
  );
}

