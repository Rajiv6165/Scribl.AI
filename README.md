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

---

## ☁️ Production Deployment

The application is structured to be deployed across three main services:
1. **Next.js Frontend** (Recommended: Vercel)
2. **Django Backend + ASGI** (Recommended: Render or Railway)
3. **PostgreSQL & Redis** (Render/Railway managed instances)

### Environment Variables Required

#### Backend (Render/Railway)
| Variable | Description |
|----------|-------------|
| `DJANGO_SETTINGS_MODULE` | Must be set to `scribl_backend.settings.prod` |
| `SECRET_KEY` | A long, secure random string for Django |
| `ALLOWED_HOSTS` | Comma-separated list of your backend domains (e.g. `api.yoursite.com,backend.onrender.com`) |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend domains (e.g. `https://yoursite.com`) |
| `CSRF_TRUSTED_ORIGINS` | Same as CORS origins |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string (e.g. `redis://...`) |
| `GEMINI_API_KEY` | (Optional) Your Google Gemini API Key |

#### Frontend (Vercel)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL of your deployed backend (e.g. `https://backend.onrender.com`) |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL of your deployed backend (e.g. `wss://backend.onrender.com`) |

### Deployment Steps

#### 1. Database and Redis (Render/Railway)
- Provision a PostgreSQL database and a Redis instance on your chosen platform.
- Save the Internal or External Connection Strings for the backend setup.

#### 2. Backend Deployment (Render/Railway)
- Create a new Web Service pointing to your GitHub repository's `backend` directory.
- Build Command: `pip install -r requirements.txt`
- Start Command: `daphne -b 0.0.0.0 -p $PORT scribl_backend.asgi:application`
- **Important**: Add a release phase or run migrations manually: `python manage.py migrate`
- Set all required backend environment variables.

#### 3. Frontend Deployment (Vercel)
- Import your GitHub repository in Vercel.
- Set the Root Directory to `frontend`.
- Set the `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` environment variables pointing to your deployed backend.
- Deploy!

### ⚠️ Common Pitfalls (CORS & WebSockets)
- Ensure your `NEXT_PUBLIC_WS_URL` uses `wss://` (secure WebSocket) in production, not `ws://`.
- If the frontend fails to connect to the backend API, double-check that your Vercel domain is strictly matched in `CORS_ALLOWED_ORIGINS` (with `https://` and no trailing slash).
