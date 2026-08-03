# Scribl.AI — Real-Time Multiplayer Drawing & Guessing App

Scribl.AI is a high-performance, production-grade real-time multiplayer drawing and guessing game featuring Voice-Powered Guessing (Web Speech API), an AI Post-Round Drawing Roast Mode (Gemini Vision), AI Match Highlight Recaps, an intelligent AI Player layer, AI-powered theme word pack generation, real-time canvas synchronization, time-based competitive scoring, server-side anti-cheat word validation, stroke-by-stroke replay data storage, and scalable Redis pub/sub.

---

## 🎙 Phase 4: Voice Guessing & AI Roast Mode Features

### 1. Voice-Powered Guessing (Web Speech API)
- **Hands-Free Guessing**: Guessers can click the **Voice** button in the chat panel to speak their guess using Chromium/Edge `Web Speech API`.
- **Live Preview & Indicators**: Features a pulsing red recording status badge and a live transcript banner e.g. `Listening: "elephant"`.
- **Identical Submission Path**: Transcribed speech is submitted through the exact same `sendGuess()` / `submit_guess()` validation path as typed text, maintaining identical scoring rules.

### 2. AI Post-Round Roast Mode
- **Good-Natured Art Critique**: After each drawing round ends, Gemini Vision examines the final canvas PNG and generates a short (2-sentence), PG-rated, friendly roast/critique of the drawing.
- **Non-Blocking Async Delivery**: Roast generation runs asynchronously in the background so round transition modals open instantly without waiting for network calls.
- **Host Toggle**: Host players can toggle AI Roast Mode ON/OFF in the lobby setting toolbar.

### 3. AI Match Highlight Recap
- **Final Results Highlights**: When a match concludes (`GAME_END`), AI selects a match highlight drawing and generates a fun 2-sentence highlight summary card e.g. *"✨ Match Highlight: Picasso of the day award goes to Alice's drawing of ELEPHANT for its sheer abstract bravery!"*.

---

## 🤖 Phase 3: AI Player & Word Pack Features

### 1. Smart AI Player Bot ("Scribl-Bot")
- **Human-Like AI Peer**: Scribl-Bot joins rooms as an active player (badged as `BOT`) and guesses what is drawn on canvas using Pillow headless image rendering and Gemini Vision API.
- **No-Cheat Architecture**: Scribl-Bot has **zero access** to the secret word in the database. It receives only the rendered PNG image of stroke events and the hint length (`_ _ _ _ _`). All AI guesses pass through `RoomService.submit_guess()`.
- **Dynamic Difficulty Scaling**: Scribl-Bot adjusts its guess delay dynamically based on human player performance (14–20s when humans struggle vs 6–9s when humans are fast).

### 2. AI Theme Word Pack Generator
- **Custom Themes**: Host players can enter any custom theme (e.g. *"Bollywood Movies"*, *"Startup Buzzwords"*, *"Superhero Gadgets"*, *"Retro 90s"*).

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

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, HTML5 Canvas API, Web Speech API, Lucide Icons.
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
*(Optionally add your `GEMINI_API_KEY` to `.env` to enable live Gemini Vision guessing, AI roasts, and AI word pack generation. If unconfigured, Scribl-Bot and Roast Mode operate with resilient fallback responses.)*

### 2. Launch Application Services
```bash
docker-compose up --build
```

Access Next.js Frontend at: **`http://localhost:3000`**

### 3. Voice Guessing & Game Testing
1. Open Chrome/Edge at `http://localhost:3000`, enter a nickname and click **Create Room**.
2. Start Game -> when you are guessing, click the **Voice** button in the chat panel and allow microphone access.
3. Speak your guess into the mic to watch it transcribe and submit automatically!

---

## 🧪 Local Automated Testing

### Backend Unit Tests
```bash
cd backend
python manage.py test
```
Tests cover:
- Voice & typed guess validation through `submit_guess()`
- AI drawing roast generation & failure fallback non-blocking execution
- Match highlight recap generation & failure fallback non-blocking execution
- AI player creation, toggling, Pillow canvas rendering, and Gemini Vision API failure resilience

### Frontend Production Build
```bash
cd frontend
node node_modules/next/dist/bin/next build
```
