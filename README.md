# Scribl.AI — Real-Time Multiplayer Drawing & Guessing App

Scribl.AI is a high-performance, production-grade real-time multiplayer drawing and guessing game featuring an intelligent AI Player layer, AI-powered theme word pack generation, real-time canvas synchronization, time-based competitive scoring, server-side anti-cheat word validation, stroke-by-stroke replay data storage, and scalable Redis pub/sub.

---

## 🤖 Phase 3: AI Player & Word Pack Features

### 1. Smart AI Player Bot ("Scribl-Bot")
- **Human-Like AI Peer**: Scribl-Bot joins rooms as an active player (badged as `BOT`) and guesses what is drawn on canvas using Pillow headless image rendering and Gemini Vision API.
- **No-Cheat Architecture**: Scribl-Bot has **zero access** to the secret word in the database. It receives only the rendered PNG image of stroke events and the hint length (`_ _ _ _ _`). All AI guesses pass through the exact same `RoomService.submit_guess()` validation path as human players.
- **Dynamic Difficulty Scaling**: Scribl-Bot adjusts its guess delay and accuracy dynamically based on human player performance:
  - If humans are struggling / haven't guessed yet, Scribl-Bot delays 14–20 seconds to prevent spoiling the round.
  - If humans are guessing fast, Scribl-Bot responds in 6–9 seconds.

### 2. AI Theme Word Pack Generator
- **Custom Themes**: Host players can enter any custom theme (e.g. *"Bollywood Movies"*, *"Startup Buzzwords"*, *"Superhero Gadgets"*, *"Retro 90s"*).
- **Gemini Word Pack Service**: The backend prompts Gemini AI to generate, filter, and validate 30 theme-matched drawing words, attaching them to the active game room.

---

## 🎮 Game Flow & Core Features

### 1. Turn & Round Management
- **Round Cycle**: Games default to 3 total rounds. Each round rotates drawing turns across all connected players (including Scribl-Bot).
- **Phases**: `LOBBY` ➔ `WORD_SELECT` ➔ `DRAWING` ➔ `ROUND_END` ➔ `GAME_END`.

### 2. Server-Side Guessing & Anti-Cheat
- **Anti-Cheat**: Secret words are hidden server-side. Guessers only see hint underscores e.g. `_ _ _ _ _ _ _ _`.
- **Dynamic Scoring**:
  - **Guesser Points**: `500 (Base) + (Time Left % × 500)`. Faster guesses yield up to 1,000 pts per round.
  - **Drawer Bonus**: `+100 pts` bonus awarded to the drawer per correct guesser.

---

## 🏗 Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, HTML5 Canvas API, Lucide Icons.
- **Backend**: Django 5.x, Django Channels (ASGI), Daphne, Pillow (PIL), Google Generative AI SDK (Gemini Vision).
- **Real-Time Layer**: Redis (Pub/Sub for WebSocket group broadcasting).
- **Database**: PostgreSQL 15 (Rooms, Players, Rounds, Words, Stroke Events).
- **Containerization**: Docker & Docker Compose.

---

## 🚀 Quick Start with Docker Compose

### 1. Setup Environment Variables
```bash
cp .env.example .env
```
*(Optionally add your `GEMINI_API_KEY` to `.env` to enable live Gemini Vision guessing and AI word pack generation. If unconfigured, Scribl-Bot operates with resilient fallback guessing.)*

### 2. Launch Application Services
```bash
docker-compose up --build
```

Access Next.js Frontend at: **`http://localhost:3000`**

### 3. Playing with the AI Bot
1. Open Browser Window A (`http://localhost:3000`), enter a nickname and click **Create Room**.
2. Notice `Scribl-Bot` (badged `BOT`) in the connected players list. Host can toggle AI on/off or generate custom AI theme word packs.
3. Host clicks **Start Game**.
4. When you draw, Scribl-Bot renders your canvas strokes in real time and submits guesses into the live chat!

---

## 🧪 Local Automated Testing

### Backend Unit Tests
```bash
cd backend
python manage.py test
```
Tests cover:
- AI player creation, toggling, and joining
- Pillow headless canvas image rendering from stroke coordinates
- AI guess submission through the exact same `submit_guess()` validation path
- AI theme word pack generation and filtering
- Simulated Gemini API 500 error / missing key resilience

### Frontend Production Build
```bash
cd frontend
node node_modules/next/dist/bin/next build
```
