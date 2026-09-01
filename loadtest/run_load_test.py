import asyncio
import websockets
import json
import time
import argparse
import random
import statistics
from aiohttp import ClientSession

async def create_rooms(api_url, num_rooms):
    rooms = []
    async with ClientSession() as session:
        for i in range(num_rooms):
            try:
                async with session.post(f"{api_url}/rooms/create/", json={
                    "nickname": f"Host_{i}",
                    "max_players": 15,
                    "smart_ai_enabled": False
                }) as resp:
                    if resp.status == 201:
                        data = await resp.json()
                        rooms.append(data['room_code'])
                    else:
                        print(f"Failed to create room: {resp.status} {await resp.text()}")
            except Exception as e:
                print(f"Error creating room: {e}")
    return rooms

class LoadTestHarness:
    def __init__(self, args, rooms):
        self.ws_url = args.ws_url
        self.rooms = rooms
        self.players_per_room = args.players_per_room
        self.duration = args.duration
        
        self.latencies = []
        self.errors = 0
        self.connected = 0
        self.failed_connections = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.running = True

    async def player_task(self, room_code, player_id, is_drawer):
        nickname = f"Player_{player_id}"
        uri = f"{self.ws_url}/rooms/{room_code}/"
        
        try:
            async with websockets.connect(uri) as websocket:
                self.connected += 1
                
                # Join room
                await websocket.send(json.dumps({
                    "type": "join_room",
                    "nickname": nickname,
                    "is_spectator": False
                }))
                self.messages_sent += 1
                
                start_time = time.time()
                
                async def send_loop():
                    while self.running and (time.time() - start_time) < self.duration:
                        if is_drawer:
                            # Send stroke every 100ms
                            ts = time.time()
                            await websocket.send(json.dumps({
                                "type": "draw_stroke",
                                "nickname": nickname,
                                "payload": {"x": random.randint(0, 100), "y": random.randint(0, 100), "ts": ts}
                            }))
                            self.messages_sent += 1
                            await asyncio.sleep(0.1)
                        else:
                            # Send guess every 5-10 seconds
                            await asyncio.sleep(random.uniform(5.0, 10.0))
                            await websocket.send(json.dumps({
                                "type": "submit_guess",
                                "text": f"guess_{random.randint(1,100)}"
                            }))
                            self.messages_sent += 1

                async def recv_loop():
                    while self.running and (time.time() - start_time) < self.duration:
                        try:
                            msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            self.messages_received += 1
                            data = json.loads(msg)
                            
                            # Only calculate latency for guessers when they receive a stroke
                            if not is_drawer and data.get("type") == "draw_stroke":
                                payload = data.get("payload", {})
                                if "ts" in payload:
                                    latency = (time.time() - payload["ts"]) * 1000
                                    self.latencies.append(latency)
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            self.errors += 1
                            break

                await asyncio.gather(send_loop(), recv_loop())
                
        except Exception as e:
            self.failed_connections += 1

    async def run(self):
        tasks = []
        for i, room in enumerate(self.rooms):
            for j in range(self.players_per_room):
                is_drawer = (j == 0)
                tasks.append(asyncio.create_task(self.player_task(room, i * self.players_per_room + j, is_drawer)))
                
        print(f"Started {len(tasks)} virtual players across {len(self.rooms)} rooms. Running for {self.duration}s...")
        await asyncio.sleep(self.duration)
        self.running = False
        print("Stopping tasks...")
        await asyncio.gather(*tasks, return_exceptions=True)
        self.report()

    def report(self):
        print("\n" + "="*50)
        print("LOAD TEST RESULTS")
        print("="*50)
        print(f"Total Virtual Players : {self.players_per_room * len(self.rooms)}")
        print(f"Successful Connections: {self.connected}")
        print(f"Failed Connections    : {self.failed_connections}")
        print(f"Messages Sent         : {self.messages_sent}")
        print(f"Messages Received     : {self.messages_received}")
        print(f"Errors Caught         : {self.errors}")
        
        if self.latencies:
            print("\nLATENCY (Broadcast draw_stroke to guessers)")
            print(f"Count                 : {len(self.latencies)}")
            print(f"Min Latency           : {min(self.latencies):.2f} ms")
            print(f"Max Latency           : {max(self.latencies):.2f} ms")
            print(f"Average Latency       : {statistics.mean(self.latencies):.2f} ms")
            if len(self.latencies) > 1:
                print(f"P95 Latency           : {statistics.quantiles(self.latencies, n=100)[94]:.2f} ms")
                print(f"P99 Latency           : {statistics.quantiles(self.latencies, n=100)[98]:.2f} ms")
        else:
            print("\nLATENCY: No valid latency metrics collected.")
        print("="*50 + "\n")

async def main():
    parser = argparse.ArgumentParser(description="Scribl.AI Load Tester")
    parser.add_argument("--rooms", type=int, default=10, help="Number of rooms")
    parser.add_argument("--players-per-room", type=int, default=8, help="Players per room")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000/api", help="Backend REST API URL")
    parser.add_argument("--ws-url", type=str, default="ws://localhost:8000/ws", help="Backend WS API URL")
    
    args = parser.parse_args()
    
    print(f"Creating {args.rooms} rooms via {args.api_url}...")
    rooms = await create_rooms(args.api_url, args.rooms)
    
    if not rooms:
        print("No rooms created. Exiting.")
        return
        
    print(f"Created {len(rooms)} rooms.")
    
    harness = LoadTestHarness(args, rooms)
    await harness.run()

if __name__ == "__main__":
    asyncio.run(main())
