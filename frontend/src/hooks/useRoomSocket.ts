import { useEffect, useRef, useState, useCallback } from 'react';
import {
  Player,
  GamePhase,
  ChatMessage,
  StrokePayload,
  StrokeEventData,
  IncomingWSMessage,
} from '../utils/types';

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

  // Game Loop, AI, & Roast State
  const [phase, setPhase] = useState<GamePhase>('LOBBY');
  const [smartAIEnabled, setSmartAIEnabled] = useState<boolean>(true);
  const [roastModeEnabled, setRoastModeEnabled] = useState<boolean>(true);
  const [customTheme, setCustomTheme] = useState<string>('');
  const [drawingRoast, setDrawingRoast] = useState<string>('');
  const [matchRecap, setMatchRecap] = useState<string>('');
  const [currentRoundNum, setCurrentRoundNum] = useState<number>(0);
  const [totalRounds, setTotalRounds] = useState<number>(3);
  const [currentDrawer, setCurrentDrawer] = useState<string>('');
  const [wordChoices, setWordChoices] = useState<string[]>([]);
  const [wordHint, setWordHint] = useState<string>('');
  const [revealedWord, setRevealedWord] = useState<string>('');
  const [timerStartMs, setTimerStartMs] = useState<number>(0);
  const [timerDurationSec, setTimerDurationSec] = useState<number>(80);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

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
            setPhase(data.phase || 'LOBBY');
            setSmartAIEnabled(data.smart_ai_enabled ?? true);
            setRoastModeEnabled(data.roast_mode_enabled ?? true);
            setCustomTheme(data.custom_theme || '');
            setCurrentRoundNum(data.current_round_num || 0);
            setTotalRounds(data.total_rounds || 3);
            setCurrentDrawer(data.current_drawer || '');
            setWordHint(data.word_hint || '');
            setTimerStartMs(data.timer_start_ms || 0);
            setTimerDurationSec(data.timer_duration_sec || 80);
            setPlayers(data.players || []);
            if (onStateSynced) {
              onStateSynced(data.canvas_history || []);
            }
            break;

          case 'game_phase_change':
            setPhase(data.phase);
            if (data.smart_ai_enabled !== undefined) {
              setSmartAIEnabled(data.smart_ai_enabled);
            }
            if (data.roast_mode_enabled !== undefined) {
              setRoastModeEnabled(data.roast_mode_enabled);
            }
            if (data.custom_theme !== undefined) {
              setCustomTheme(data.custom_theme);
            }
            setCurrentRoundNum(data.current_round_num);
            setTotalRounds(data.total_rounds);
            setCurrentDrawer(data.current_drawer || '');
            setTimerStartMs(data.timer_start_ms || 0);
            setTimerDurationSec(data.timer_duration_sec || 80);
            setPlayers(data.players || []);

            if (data.word_choices) {
              setWordChoices(data.word_choices);
            } else {
              setWordChoices([]);
            }

            if (data.word_hint) {
              setWordHint(data.word_hint);
            }

            if (data.revealed_word) {
              setRevealedWord(data.revealed_word);
            }

            if (data.phase === 'WORD_SELECT') {
              setDrawingRoast('');
              if (onStateSynced) {
                onStateSynced([]);
              }
            }
            break;

          case 'drawing_roast':
            setDrawingRoast(data.roast);
            break;

          case 'match_recap':
            setMatchRecap(data.recap);
            break;

          case 'chat_message':
            setChatMessages((prev) => [
              ...prev,
              {
                id: `${Date.now()}-${Math.random()}`,
                nickname: data.nickname,
                text: data.text,
                is_system: data.is_system,
                timestamp: Date.now(),
              },
            ]);
            break;

          case 'correct_guess':
            setPlayers(data.players || []);
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

  const toggleAI = useCallback((enabled: boolean) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'toggle_ai',
          nickname,
          enabled,
        })
      );
    }
  }, [nickname]);

  const toggleRoastMode = useCallback((enabled: boolean) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'toggle_roast_mode',
          nickname,
          enabled,
        })
      );
    }
  }, [nickname]);

  const generateWordPack = useCallback((theme: string) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'generate_word_pack',
          nickname,
          theme,
        })
      );
    }
  }, [nickname]);

  const startGame = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'start_game',
          nickname,
        })
      );
    }
  }, [nickname]);

  const selectWord = useCallback((word: string) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'select_word',
          nickname,
          word,
        })
      );
    }
  }, [nickname]);

  const sendGuess = useCallback((text: string) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'submit_guess',
          nickname,
          text,
        })
      );
    }
  }, [nickname]);

  const notifyTimerExpired = useCallback((currentPhase: GamePhase) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'timer_expired',
          nickname,
          phase: currentPhase,
        })
      );
    }
  }, [nickname]);

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
    toggleAI,
    toggleRoastMode,
    generateWordPack,
    startGame,
    selectWord,
    sendGuess,
    notifyTimerExpired,
    sendStroke,
    sendClear,
    sendUndo,
  };
}
