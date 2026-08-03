import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .services import (
    async_join_room,
    async_leave_room,
    async_record_stroke_event,
    async_get_canvas_history,
)

logger = logging.getLogger(__name__)


class RoomConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_code = None
        self.room_group_name = None
        self.nickname = None

    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code'].upper()
        self.room_group_name = f'room_{self.room_code}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"WebSocket connected for room {self.room_code} on channel {self.channel_name}")

    async def disconnect(self, close_code):
        if self.room_group_name and self.nickname:
            # Notify service of disconnection
            result = await async_leave_room(self.room_code, self.nickname)
            
            # Broadcast player departure to channel group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_left_event',
                    'nickname': self.nickname,
                    'players': result.get('players', []),
                }
            )

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        logger.info(f"WebSocket disconnected for room {self.room_code}")

    async def receive_json(self, content):
        action_type = content.get('type')
        nickname = content.get('nickname', self.nickname)

        if not action_type:
            await self.send_json({"error": "Missing event type"})
            return

        if action_type == 'join_room':
            await self.handle_join_room(content)
        elif action_type == 'draw_stroke':
            await self.handle_draw_stroke(content)
        elif action_type == 'clear_canvas':
            await self.handle_clear_canvas(content)
        elif action_type == 'undo_stroke':
            await self.handle_undo_stroke(content)
        else:
            await self.send_json({"error": f"Unknown event type: {action_type}"})

    async def handle_join_room(self, content):
        nickname = content.get('nickname', 'Anonymous')
        self.nickname = nickname

        # Register join with service layer
        join_data = await async_join_room(self.room_code, nickname, self.channel_name)

        # Fetch canvas history for initial state sync
        history = await async_get_canvas_history(self.room_code)

        # 1. Send state directly to joining client
        await self.send_json({
            'type': 'room_state',
            'room_code': self.room_code,
            'nickname': self.nickname,
            'is_host': join_data.get('is_host', False),
            'players': join_data.get('players', []),
            'canvas_history': history,
        })

        # 2. Broadcast join event to all room members
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_joined_event',
                'nickname': nickname,
                'players': join_data.get('players', []),
            }
        )

    async def handle_draw_stroke(self, content):
        payload = content.get('payload', {})
        nickname = content.get('nickname', self.nickname or 'Anonymous')

        # Persist stroke via service layer
        saved_stroke = await async_record_stroke_event(
            room_code=self.room_code,
            player_nickname=nickname,
            action_type='stroke',
            payload=payload
        )

        # Broadcast stroke event to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'draw_stroke_event',
                'nickname': nickname,
                'sequence_number': saved_stroke['sequence_number'],
                'payload': payload,
            }
        )

    async def handle_clear_canvas(self, content):
        nickname = content.get('nickname', self.nickname or 'Anonymous')

        saved_event = await async_record_stroke_event(
            room_code=self.room_code,
            player_nickname=nickname,
            action_type='clear',
            payload={}
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'clear_canvas_event',
                'nickname': nickname,
                'sequence_number': saved_event['sequence_number'],
            }
        )

    async def handle_undo_stroke(self, content):
        nickname = content.get('nickname', self.nickname or 'Anonymous')

        saved_event = await async_record_stroke_event(
            room_code=self.room_code,
            player_nickname=nickname,
            action_type='undo',
            payload={}
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'undo_stroke_event',
                'nickname': nickname,
                'sequence_number': saved_event['sequence_number'],
            }
        )

    # Redis Group Broadcast Handlers
    async def player_joined_event(self, event):
        await self.send_json({
            'type': 'player_joined',
            'nickname': event['nickname'],
            'players': event['players'],
        })

    async def player_left_event(self, event):
        await self.send_json({
            'type': 'player_left',
            'nickname': event['nickname'],
            'players': event['players'],
        })

    async def draw_stroke_event(self, event):
        await self.send_json({
            'type': 'draw_stroke',
            'nickname': event['nickname'],
            'sequence_number': event['sequence_number'],
            'payload': event['payload'],
        })

    async def clear_canvas_event(self, event):
        await self.send_json({
            'type': 'clear_canvas',
            'nickname': event['nickname'],
            'sequence_number': event['sequence_number'],
        })

    async def undo_stroke_event(self, event):
        await self.send_json({
            'type': 'undo_stroke',
            'nickname': event['nickname'],
            'sequence_number': event['sequence_number'],
        })
