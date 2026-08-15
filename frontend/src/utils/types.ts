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
  is_ai?: boolean;
  is_spectator?: boolean;
  is_flagged?: boolean;
  anomaly_score?: number;
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
  | 'drawing_roast'
  | 'match_recap'
  | 'spectator_commentary'
  | 'player_flagged'
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
  is_spectator?: boolean;
  phase: GamePhase;
  smart_ai_enabled: boolean;
  roast_mode_enabled: boolean;
  custom_theme: string;
  current_round_num: number;
  total_rounds: number;
  current_drawer: string;
  word_hint: string;
  timer_start_ms: number;
  timer_duration_sec: number;
  players: Player[];
  spectator_count?: number;
  canvas_history: StrokeEventData[];
}

export interface GamePhaseChangeMessage {
  type: 'game_phase_change';
  room_code: string;
  phase: GamePhase;
  smart_ai_enabled: boolean;
  roast_mode_enabled: boolean;
  custom_theme: string;
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

export interface DrawingRoastEvent {
  type: 'drawing_roast';
  roast: string;
}

export interface MatchRecapEvent {
  type: 'match_recap';
  recap: string;
}

export interface SpectatorCommentaryEvent {
  type: 'spectator_commentary';
  commentary: string;
  event_type: string;
}

export interface PlayerFlaggedEvent {
  type: 'player_flagged';
  nickname: string;
  anomaly_score: number;
  reasons: string[];
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
  is_spectator?: boolean;
  players: Player[];
  spectator_count?: number;
}

export interface PlayerLeftMessage {
  type: 'player_left';
  nickname: string;
  is_spectator?: boolean;
  players: Player[];
  spectator_count?: number;
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
  | DrawingRoastEvent
  | MatchRecapEvent
  | SpectatorCommentaryEvent
  | PlayerFlaggedEvent
  | ChatMessageEvent
  | CorrectGuessEvent
  | PlayerJoinedMessage
  | PlayerLeftMessage
  | DrawStrokeMessage
  | ClearCanvasMessage
  | UndoStrokeMessage;

export interface ReplayGuess {
  nickname: string;
  text: string;
  is_correct: boolean;
  points_awarded?: number;
  created_at?: string;
  timestamp_ms: number;
}

export interface ReplayData {
  round_id: number;
  round_number: number;
  room_code: string;
  word: string;
  drawer: string;
  status: string;
  started_at?: string;
  ended_at?: string;
  duration: number;
  guessers: ReplayGuess[];
  total_strokes: number;
  events: StrokeEventData[];
}

export interface RoundSummary {
  round_id: number;
  round_number: number;
  drawer: string;
  word: string;
  status: string;
  started_at?: string;
  ended_at?: string;
  correct_guessers: string[];
  total_strokes: number;
  events: StrokeEventData[];
}

export interface MatchHistoryData {
  room_code: string;
  host_name: string;
  phase: string;
  total_rounds: number;
  rounds: RoundSummary[];
}

