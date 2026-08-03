# Scribl.AI — Real-Time Multiplayer Drawing & Guessing App

Scribl.AI is a high-performance, production-grade real-time multiplayer drawing application. Built with a decoupled monorepo architecture, this phase delivers real-time canvas synchronization, stroke-by-stroke replay data storage, player room lobbies, and scalable Redis pub/sub.

---

## 🎨 Features (Foundation Phase)

- **Real-Time Multiplayer Canvas**: Synchronized drawing across multiple clients using WebSockets and Django Channels.
- **Client-Side Stroke Smoothing**: Quadratic Bezier curve point interpolation for smooth rendering regardless of network jitter.
- **Tools & Palette**: Support for custom color picker, pre-set palette, dynamic brush sizing, eraser, stroke undo, and canvas clear.
- **Mouse & Touch Support**: Fluid experience on desktops, tablets, and mobile browsers.
- **Scalable Architecture**: Decoupled service layer (`RoomService`) separate from WebSockets consumers, powered by Redis Channel Layer for scaling behind load balancers.
- **Replay Data Model**: Every stroke, coordinate, pressure, tool action, and timestamp is stored in PostgreSQL for stroke-by-stroke timeline scrubbing.
- **Room Lifecycle & Lobby**: Create room, join room via 6-character room code, real-time connected player list.

---

## 🏗 Tech Stack

- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, HTML5 Canvas API.
- **Backend**: Django 5.x, Django Channels (ASGI), Daphne.
- **Real-Time Channel Layer**: Redis (Pub/Sub for WebSocket group broadcasting).
- **Database**: PostgreSQL 15 (Rooms, Players, Rounds, Stroke Events).
- **Containerization**: Docker & Docker Compose.

---

## 🚀 Quick Start with Docker Compose

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 1. Clone & Setup Environment
```bash
cp .env.example .env
```

### 2. Launch Application Services
```bash
docker-compose up --build
```

This will spin up:
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Django Backend (Daphne ASGI)**: `http://localhost:8000`
- **Next.js Frontend**: `http://localhost:3000`

### 3. Accessing the App
Open your browser and navigate to:
👉 **`http://localhost:3000`**

1. Enter your nickname and click **Create Room**.
2. Copy the generated **Room Code** (or room URL).
3. Open a second browser window (or incognito tab), navigate to `http://localhost:3000`, enter a second nickname and the Room Code to join.
4. Draw on one screen and watch strokes sync in real time on the second screen!

---

## 🧪 Local Manual & Automated Testing (Without Docker)

### Backend Setup & Tests
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Run migrations (ensure PostgreSQL and Redis are running locally if not using SQLite/in-memory)
python manage.py migrate
python manage.py test
```

### Frontend Setup & Tests
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 Replay Data Model Endpoint

To inspect stroke timeline data recorded during drawing sessions:
```http
GET http://localhost:8000/api/rooms/<ROOM_CODE>/replay/
```
Response format:
```json
{
  "room_code": "AB12CD",
  "total_strokes": 42,
  "events": [
    {
      "sequence_number": 1,
      "player_nickname": "Artist",
      "action_type": "stroke",
      "payload": {
        "color": "#4f46e5",
        "brushSize": 8,
        "isEraser": false,
        "points": [
          {"x": 120.5, "y": 200.1, "pressure": 0.5, "timestamp": 1722718800000},
          {"x": 125.0, "y": 205.3, "pressure": 0.7, "timestamp": 1722718800016}
        ]
      },
      "created_at": "2026-08-03T21:03:00Z"
    }
  ]
}
```
