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
}

export type WSMessageType =
  | 'room_state'
  | 'player_joined'
  | 'player_left'
  | 'draw_stroke'
  | 'clear_canvas'
  | 'undo_stroke';

export interface RoomStateMessage {
  type: 'room_state';
  room_code: string;
  nickname: string;
  is_host: boolean;
  players: Player[];
  canvas_history: StrokeEventData[];
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
  | PlayerJoinedMessage
  | PlayerLeftMessage
  | DrawStrokeMessage
  | ClearCanvasMessage
  | UndoStrokeMessage;
