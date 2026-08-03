import { useEffect, useRef, useState, useCallback } from 'react';
import { Player, StrokePayload, StrokeEventData, IncomingWSMessage } from '../utils/types';

interface UseRoomSocketOptions {
  roomCode: string;
  nickname: string;
  onStrokeReceived?: (data: { nickname: string; payload: StrokePayload }) => void;
  onClearReceived?: (nickname: string) => void;
  onUndoReceived?: (nickname: string) => void;
  onStateSynced?: (history: StrokeEventData[]) => void;
}

export function useRoomSocket({
  roomCode,
  nickname,
  onStrokeReceived,
  onClearReceived,
  onUndoReceived,
  onStateSynced,
}: UseRoomSocketOptions) {
  const [connected, setConnected] = useState(false);
  const [players, setPlayers] = useState<Player[]>([]);
  const [isHost, setIsHost] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (!roomCode || !nickname) return;

    const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const wsUrl = `${wsBaseUrl}/ws/room/${roomCode.toUpperCase()}/`;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
      // Handshake join event
      socket.send(
        JSON.stringify({
          type: 'join_room',
          nickname: nickname,
        })
      );
    };

    socket.onmessage = (event) => {
      try {
        const data: IncomingWSMessage = JSON.parse(event.data);

        switch (data.type) {
          case 'room_state':
            setIsHost(data.is_host);
            setPlayers(data.players || []);
            if (onStateSynced) {
              onStateSynced(data.canvas_history || []);
            }
            break;

          case 'player_joined':
          case 'player_left':
            setPlayers(data.players || []);
            break;

          case 'draw_stroke':
            if (onStrokeReceived) {
              onStrokeReceived({ nickname: data.nickname, payload: data.payload });
            }
            break;

          case 'clear_canvas':
            if (onClearReceived) {
              onClearReceived(data.nickname);
            }
            break;

          case 'undo_stroke':
            if (onUndoReceived) {
              onUndoReceived(data.nickname);
            }
            break;

          default:
            break;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    socket.onclose = () => {
      setConnected(false);
      // Auto-reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    socket.onerror = (err) => {
      console.error('WebSocket error:', err);
      socket.close();
    };
  }, [roomCode, nickname, onStrokeReceived, onClearReceived, onUndoReceived, onStateSynced]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  const sendStroke = useCallback((payload: StrokePayload) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'draw_stroke',
          nickname,
          payload,
        })
      );
    }
  }, [nickname]);

  const sendClear = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'clear_canvas',
          nickname,
        })
      );
    }
  }, [nickname]);

  const sendUndo = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'undo_stroke',
          nickname,
        })
      );
    }
  }, [nickname]);

  return {
    connected,
    players,
    isHost,
    sendStroke,
    sendClear,
    sendUndo,
  };
}
