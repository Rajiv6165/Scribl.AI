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
import { RoomHeader } from '../../../components/RoomHeader';
import { StrokePayload, StrokeEventData } from '../../../utils/types';

export default function RoomPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const roomCode = (params.code as string)?.toUpperCase() || '';
  const searchNickname = searchParams.get('nickname') || '';

  const [nickname, setNickname] = useState<string>('');
  const [color, setColor] = useState<string>('#000000');
  const [brushSize, setBrushSize] = useState<number>(6);
  const [isEraser, setIsEraser] = useState<boolean>(false);

  const canvasRef = useRef<CanvasRef | null>(null);

  useEffect(() => {
    const stored = searchNickname || sessionStorage.getItem('scribl_nickname') || '';
    if (!stored) {
      router.push('/');
    } else {
      setNickname(stored);
    }
  }, [searchNickname, router]);

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
    phase,
    currentRoundNum,
    totalRounds,
    currentDrawer,
    wordChoices,
    wordHint,
    revealedWord,
    timerStartMs,
    timerDurationSec,
    chatMessages,
    startGame,
    selectWord,
    sendGuess,
    notifyTimerExpired,
    sendStroke,
    sendClear,
    sendUndo,
  } = useRoomSocket({
    roomCode,
    nickname,
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
      <RoomHeader roomCode={roomCode} connected={connected} />

      {/* Word Hint & Timer Bar (Active during Word Select & Drawing) */}
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
          onTimerExpired={notifyTimerExpired}
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

        {/* Middle Column (6 cols): Drawing Canvas & Toolbar */}
        <div className="lg:col-span-6 flex flex-col gap-4">
          <div className="flex-1 min-h-[460px]">
            <Canvas
              ref={canvasRef}
              color={color}
              brushSize={brushSize}
              isEraser={isEraser}
              isReadOnly={!isDrawer || phase !== 'DRAWING'}
              onStrokeComplete={handleLocalStrokeComplete}
            />
          </div>

          {/* Controls toolbar enabled for active drawer during DRAWING phase */}
          {isDrawer && phase === 'DRAWING' && (
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
            onSendGuess={sendGuess}
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

      {/* Round End / Game Over Summary Modal */}
      {(phase === 'ROUND_END' || phase === 'GAME_END') && (
        <RoundEndModal
          phase={phase}
          revealedWord={revealedWord}
          players={players}
          timerStartMs={timerStartMs}
          timerDurationSec={timerDurationSec}
        />
      )}
    </div>
  );
}
