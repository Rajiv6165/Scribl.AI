export type GamePhase = 'LOBBY' | 'WORD_SELECT' | 'DRAWING' | 'ROUND_END' | 'GAME_END';

export interface Point {
  x: number;
  y: number;
  pressure?: number;
  timestamp: number;
}

export interface StrokePayload {
  color: string;
  brushSize: number;
  isEraser: boolean;
  points: Point[];
}

export interface StrokeEventData {
  sequence_number?: number;
  nickname: string;
  action_type: 'stroke' | 'clear' | 'undo';
  payload: StrokePayload;
  created_at?: string;
}

export interface Player {
  nickname: string;
  is_host: boolean;
  is_connected: boolean;
  score: number;
  has_guessed: boolean;
}

export interface ChatMessage {
  id?: string;
  nickname: string;
  text: string;
  is_system: boolean;
  timestamp: number;
}

export type WSMessageType =
  | 'room_state'
  | 'player_joined'
  | 'player_left'
  | 'game_phase_change'
  | 'chat_message'
  | 'correct_guess'
  | 'draw_stroke'
  | 'clear_canvas'
  | 'undo_stroke';

export interface RoomStateMessage {
  type: 'room_state';
  room_code: string;
  nickname: string;
  is_host: boolean;
  phase: GamePhase;
  current_round_num: number;
  total_rounds: number;
  current_drawer: string;
  word_hint: string;
  timer_start_ms: number;
  timer_duration_sec: number;
  players: Player[];
  canvas_history: StrokeEventData[];
}

export interface GamePhaseChangeMessage {
  type: 'game_phase_change';
  room_code: string;
  phase: GamePhase;
  current_round_num: number;
  total_rounds: number;
  current_drawer: string;
  word_choices?: string[];
  word_hint?: string;
  revealed_word?: string;
  timer_start_ms: number;
  timer_duration_sec: number;
  players: Player[];
}

export interface ChatMessageEvent {
  type: 'chat_message';
  nickname: string;
  text: string;
  is_system: boolean;
}

export interface CorrectGuessEvent {
  type: 'correct_guess';
  nickname: string;
  guesser_points: number;
  players: Player[];
}

export interface PlayerJoinedMessage {
  type: 'player_joined';
  nickname: string;
  players: Player[];
}

export interface PlayerLeftMessage {
  type: 'player_left';
  nickname: string;
  players: Player[];
}

export interface DrawStrokeMessage {
  type: 'draw_stroke';
  nickname: string;
  sequence_number: number;
  payload: StrokePayload;
}

export interface ClearCanvasMessage {
  type: 'clear_canvas';
  nickname: string;
  sequence_number: number;
}

export interface UndoStrokeMessage {
  type: 'undo_stroke';
  nickname: string;
  sequence_number: number;
}

export type IncomingWSMessage =
  | RoomStateMessage
  | GamePhaseChangeMessage
  | ChatMessageEvent
  | CorrectGuessEvent
  | PlayerJoinedMessage
  | PlayerLeftMessage
  | DrawStrokeMessage
  | ClearCanvasMessage
  | UndoStrokeMessage;
