'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useRoomSocket } from '../../../hooks/useRoomSocket';
import { Canvas, CanvasRef } from '../../../components/Canvas';
import { Toolbar } from '../../../components/Toolbar';
import { PlayerList } from '../../../components/PlayerList';
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

  // Retrieve stored nickname or redirect home if missing
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

  const { connected, players, isHost, sendStroke, sendClear, sendUndo } = useRoomSocket({
    roomCode,
    nickname,
    onStrokeReceived: handleRemoteStroke,
    onClearReceived: handleRemoteClear,
    onUndoReceived: handleRemoteUndo,
    onStateSynced: handleStateSynced,
  });

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
      <div className="min-h-screen flex items-center justify-center text-slate-400">
        Loading room...
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-6 flex flex-col gap-4 max-w-7xl mx-auto">
      {/* Header Bar */}
      <RoomHeader roomCode={roomCode} connected={connected} />

      {/* Main Game Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 flex-1 min-h-[600px]">
        {/* Left / Main Canvas Area (3 cols) */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          <div className="flex-1 min-h-[480px]">
            <Canvas
              ref={canvasRef}
              color={color}
              brushSize={brushSize}
              isEraser={isEraser}
              onStrokeComplete={handleLocalStrokeComplete}
            />
          </div>

          {/* Drawing Tools Bar */}
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
        </div>

        {/* Right Sidebar - Players List & Lobby (1 col) */}
        <div className="lg:col-span-1 h-full min-h-[300px]">
          <PlayerList players={players} currentNickname={nickname} />
        </div>
      </div>
    </div>
  );
}
