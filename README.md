# Scribl.AI — Real-Time Multiplayer Drawing & Guessing App

Scribl.AI is a high-performance, production-grade real-time multiplayer drawing and guessing game. Built with a decoupled monorepo architecture, it features real-time canvas synchronization, time-based competitive scoring, server-side anti-cheat word validation, stroke-by-stroke replay data storage, and scalable Redis pub/sub.

---

## 🎮 Game Flow & Core Features

### 1. Turn & Round Management
- **Round Cycle**: Games default to 3 total rounds. Each round rotates drawing turns across all connected players.
- **Phases**: `LOBBY` ➔ `WORD_SELECT` ➔ `DRAWING` ➔ `ROUND_END` ➔ `GAME_END`.

### 2. Word Selection & Word Bank
- **Word Bank**: Pre-seeded with ~150 curated drawing words across Animals, Nature, Objects, Food, Clothing, Places, and Fantasy categories.
- **Selection**: When a turn starts, the active drawer gets 3 random word choices with a 10-second countdown. If no choice is made, a word is automatically selected.

### 3. Server-Side Guessing & Anti-Cheat
- **Anti-Cheat**: The secret word is stored strictly on the server and is **never** broadcast to non-drawing clients until the round concludes. Guessers only see masked hints e.g. `_ _ _ _ _ _ _ _`.
- **Chat & Guesses**: Non-drawer players submit text guesses via the live chat.
- **Dynamic Scoring**:
  - **Guesser Points**: `500 (Base) + (Time Left % × 500)`. Faster guesses yield higher scores (up to 1,000 pts per round).
  - **Drawer Bonus**: The drawer receives `+100 pts` bonus for every player who guesses correctly.
- **Auto Round Completion**: When all non-drawing players guess correctly, the round ends automatically.

### 4. Synced Backend Timers
- Server emits `timer_start_ms` (epoch) and `timer_duration_sec`. Clients compute remaining time locally to eliminate network latency drift.

### 5. Replay Data Model
- Every stroke event, coordinate, pressure, tool action, and timestamp is stored in PostgreSQL for stroke-by-stroke timeline scrubbing.

---

## 🏗 Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, HTML5 Canvas API.
- **Backend**: Django 5.x, Django Channels (ASGI), Daphne.
- **Real-Time Channel Layer**: Redis (Pub/Sub for WebSocket group broadcasting).
- **Database**: PostgreSQL 15 (Rooms, Players, Rounds, Words, Stroke Events).
- **Containerization**: Docker & Docker Compose.

---

## 🚀 Quick Start with Docker Compose

### 1. Clone & Setup Environment
```bash
cp .env.example .env
```

### 2. Launch Application Services
```bash
docker-compose up --build
```

Access Next.js Frontend at: **`http://localhost:3000`**

### 3. Playing the Game
1. Open Browser Window A (`http://localhost:3000`), enter a nickname and click **Create Room**.
2. Copy the generated **Room Code**.
3. Open Browser Window B (incognito tab), enter a nickname and the Room Code to join.
4. Host clicks **Start Game**.
5. The drawer picks a word from the modal, draws on the canvas, and the guesser types the answer in the live chat to earn points!

---

## 🧪 Local Automated Testing

### Backend Unit Tests
```bash
cd backend
python manage.py test
```
Tests cover:
- Room creation and player joining
- Game initialization and turn rotation
- Word selection & hint generation
- Guess validation, time-based scoring calculation, and drawer bonuses
- Stroke recording & replay serialization

### Frontend Production Build
```bash
cd frontend
npm run dev # for dev server
# Or for static type checking & production build:
node node_modules/next/dist/bin/next build
```
