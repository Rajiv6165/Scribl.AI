from channels.db import database_sync_to_async
from django.db import transaction
from django.utils import timezone
from .models import Room, Player, StrokeEvent, Round


class RoomService:
    @staticmethod
    def create_room(host_nickname: str, max_players: int = 10) -> dict:
        """Create a new room and assign host player."""
        host_nickname = host_nickname.strip()
        if not host_nickname:
            raise ValueError("Host nickname cannot be empty.")

        with transaction.atomic():
            room = Room.objects.create(
                host_name=host_nickname,
                max_players=max_players,
                status=Room.STATUS_LOBBY
            )
            player = Player.objects.create(
                room=room,
                nickname=host_nickname,
                session_id=f"host_{room.code}",
                is_host=True,
                is_connected=True
            )
            return {
                "room_code": room.code,
                "host_nickname": host_nickname,
                "status": room.status,
                "max_players": room.max_players,
                "created_at": room.created_at.isoformat(),
            }

    @staticmethod
    def join_room(room_code: str, player_nickname: str, session_id: str) -> dict:
        """Join an existing room or update connection status."""
        room_code = room_code.upper().strip()
        player_nickname = player_nickname.strip()

        if not player_nickname:
            raise ValueError("Player nickname cannot be empty.")

        try:
            room = Room.objects.get(code=room_code)
        except Room.DoesNotExist:
            raise ValueError(f"Room {room_code} does not exist.")

        player, created = Player.objects.get_or_create(
            room=room,
            nickname=player_nickname,
            defaults={
                'session_id': session_id,
                'is_host': False,
                'is_connected': True,
            }
        )

        if not created:
            player.session_id = session_id
            player.is_connected = True
            player.last_seen = timezone.now()
            player.save(update_fields=['session_id', 'is_connected', 'last_seen'])

        players_list = RoomService.get_room_players_sync(room)

        return {
            "room_code": room.code,
            "player_nickname": player.nickname,
            "is_host": player.is_host,
            "status": room.status,
            "players": players_list,
        }

    @staticmethod
    def leave_room(room_code: str, player_nickname: str) -> dict:
        """Mark player disconnected in room."""
        try:
            room = Room.objects.get(code=room_code.upper())
            player = Player.objects.filter(room=room, nickname=player_nickname).first()
            if player:
                player.is_connected = False
                player.save(update_fields=['is_connected'])
            players_list = RoomService.get_room_players_sync(room)
            return {
                "room_code": room.code,
                "player_nickname": player_nickname,
                "players": players_list,
            }
        except Room.DoesNotExist:
            return {"room_code": room_code, "player_nickname": player_nickname, "players": []}

    @staticmethod
    def get_room_players_sync(room: Room) -> list:
        """Fetch current players list for room."""
        players = Player.objects.filter(room=room).order_by('joined_at')
        return [
            {
                "nickname": p.nickname,
                "is_host": p.is_host,
                "is_connected": p.is_connected,
            }
            for p in players
        ]

    @staticmethod
    def record_stroke_event(room_code: str, player_nickname: str, action_type: str, payload: dict) -> dict:
        """Record stroke event to PostgreSQL for replay & sync."""
        try:
            room = Room.objects.get(code=room_code.upper())
            active_round = room.rounds.filter(status=Round.STATUS_ACTIVE).last()
            
            # Auto-increment sequence number per room
            last_event = StrokeEvent.objects.filter(room=room).order_by('-sequence_number').first()
            next_seq = (last_event.sequence_number + 1) if last_event else 1

            stroke = StrokeEvent.objects.create(
                room=room,
                round=active_round,
                sequence_number=next_seq,
                player_nickname=player_nickname,
                action_type=action_type,
                payload=payload
            )
            return {
                "sequence_number": stroke.sequence_number,
                "player_nickname": stroke.player_nickname,
                "action_type": stroke.action_type,
                "payload": stroke.payload,
                "created_at": stroke.created_at.isoformat(),
            }
        except Room.DoesNotExist:
            raise ValueError(f"Room {room_code} not found.")

    @staticmethod
    def get_canvas_history(room_code: str) -> list:
        """Fetch all canvas stroke events for initial state sync."""
        try:
            room = Room.objects.get(code=room_code.upper())
            strokes = StrokeEvent.objects.filter(room=room).order_by('sequence_number')
            return [
                {
                    "sequence_number": s.sequence_number,
                    "player_nickname": s.player_nickname,
                    "action_type": s.action_type,
                    "payload": s.payload,
                    "created_at": s.created_at.isoformat(),
                }
                for s in strokes
            ]
        except Room.DoesNotExist:
            return []

    @staticmethod
    def get_replay_data(room_code: str) -> dict:
        """Fetch complete replay payload for a room session."""
        try:
            room = Room.objects.get(code=room_code.upper())
            strokes = StrokeEvent.objects.filter(room=room).order_by('sequence_number')
            return {
                "room_code": room.code,
                "host_name": room.host_name,
                "status": room.status,
                "created_at": room.created_at.isoformat(),
                "total_strokes": strokes.count(),
                "events": [
                    {
                        "sequence_number": s.sequence_number,
                        "player_nickname": s.player_nickname,
                        "action_type": s.action_type,
                        "payload": s.payload,
                        "created_at": s.created_at.isoformat(),
                    }
                    for s in strokes
                ]
            }
        except Room.DoesNotExist:
            raise ValueError(f"Room {room_code} does not exist.")


# Async helpers for Channels Consumer
async_create_room = database_sync_to_async(RoomService.create_room)
async_join_room = database_sync_to_async(RoomService.join_room)
async_leave_room = database_sync_to_async(RoomService.leave_room)
async_record_stroke_event = database_sync_to_async(RoomService.record_stroke_event)
async_get_canvas_history = database_sync_to_async(RoomService.get_canvas_history)
