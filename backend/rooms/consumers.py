import asyncio
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .services import (
    async_join_room,
    async_leave_room,
    async_toggle_smart_ai,
    async_generate_and_apply_custom_word_pack,
    async_start_game,
    async_start_word_selection,
    async_select_word,
    async_submit_guess,
    async_execute_ai_guess_attempt,
    async_end_round,
    async_next_turn,
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
        self.ai_task = None

    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code'].upper()
        self.room_group_name = f'room_{self.room_code}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"WebSocket connected for room {self.room_code}")

    async def disconnect(self, close_code):
        if self.room_group_name and self.nickname:
            result = await async_leave_room(self.room_code, self.nickname)
            
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
        if not action_type:
            await self.send_json({"error": "Missing event type"})
            return

        if action_type == 'join_room':
            await self.handle_join_room(content)
        elif action_type == 'toggle_ai':
            await self.handle_toggle_ai(content)
        elif action_type == 'generate_word_pack':
            await self.handle_generate_word_pack(content)
        elif action_type == 'start_game':
            await self.handle_start_game(content)
        elif action_type == 'select_word':
            await self.handle_select_word(content)
        elif action_type == 'submit_guess':
            await self.handle_submit_guess(content)
        elif action_type == 'timer_expired':
            await self.handle_timer_expired(content)
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

        join_data = await async_join_room(self.room_code, nickname, self.channel_name)
        history = await async_get_canvas_history(self.room_code)

        await self.send_json({
            'type': 'room_state',
            'room_code': self.room_code,
            'nickname': self.nickname,
            'is_host': join_data.get('is_host', False),
            'phase': join_data.get('phase', 'LOBBY'),
            'smart_ai_enabled': join_data.get('smart_ai_enabled', True),
            'custom_theme': join_data.get('custom_theme', ''),
            'current_round_num': join_data.get('current_round_num', 0),
            'total_rounds': join_data.get('total_rounds', 3),
            'current_drawer': join_data.get('current_drawer', ''),
            'word_hint': join_data.get('word_hint', ''),
            'timer_start_ms': join_data.get('timer_start_ms', 0),
            'timer_duration_sec': join_data.get('timer_duration_sec', 80),
            'players': join_data.get('players', []),
            'canvas_history': history,
        })

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_joined_event',
                'nickname': nickname,
                'players': join_data.get('players', []),
            }
        )

    async def handle_toggle_ai(self, content):
        enabled = content.get('enabled', True)
        result = await async_toggle_smart_ai(self.room_code, enabled)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_joined_event',
                'nickname': 'System',
                'players': result.get('players', []),
            }
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message_event',
                'nickname': 'System',
                'text': f"🤖 Smart AI Bot {'enabled' if enabled else 'disabled'}.",
                'is_system': True,
            }
        )

    async def handle_generate_word_pack(self, content):
        theme = content.get('theme', '')
        try:
            result = await async_generate_and_apply_custom_word_pack(self.room_code, theme)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_event',
                    'nickname': 'System',
                    'text': f"✨ AI Word Pack generated for theme '{result['custom_theme']}' ({result['word_count']} words)!",
                    'is_system': True,
                }
            )
        except Exception as err:
            await self.send_json({"error": str(err)})

    async def handle_start_game(self, content):
        try:
            result = await async_start_game(self.room_code, self.nickname)
            await self.broadcast_phase_update(result)
        except Exception as err:
            await self.send_json({"error": str(err)})

    async def handle_select_word(self, content):
        chosen_word = content.get('word', '')
        try:
            result = await async_select_word(self.room_code, self.nickname, chosen_word)
            await self.broadcast_phase_update(result)
        except Exception as err:
            await self.send_json({"error": str(err)})

    async def handle_submit_guess(self, content):
        text = content.get('text', '')
        if not text.strip():
            return

        result = await async_submit_guess(self.room_code, self.nickname, text)

        if result.get('is_correct'):
            guesser_nickname = result['player_nickname']
            pts = result['guesser_points']

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'correct_guess_event',
                    'nickname': guesser_nickname,
                    'guesser_points': pts,
                    'players': result['players'],
                }
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_event',
                    'nickname': 'System',
                    'text': f"🎉 {guesser_nickname} guessed the word! (+{pts} pts)",
                    'is_system': True,
                }
            )

            if result.get('all_guessed'):
                end_res = await async_end_round(self.room_code)
                await self.broadcast_phase_update(end_res)

        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_event',
                    'nickname': self.nickname,
                    'text': text,
                    'is_system': False,
                }
            )

    async def handle_timer_expired(self, content):
        phase = content.get('phase', '')
        if phase == 'WORD_SELECT':
            try:
                result = await async_select_word(self.room_code, self.nickname, "CAT")
                await self.broadcast_phase_update(result)
            except Exception:
                pass
        elif phase == 'DRAWING':
            end_res = await async_end_round(self.room_code)
            await self.broadcast_phase_update(end_res)
        elif phase == 'ROUND_END':
            next_res = await async_next_turn(self.room_code)
            await self.broadcast_phase_update(next_res)

    async def broadcast_phase_update(self, phase_data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_phase_event',
                'phase_data': phase_data,
            }
        )

    async def handle_draw_stroke(self, content):
        payload = content.get('payload', {})
        nickname = content.get('nickname', self.nickname or 'Anonymous')

        saved_stroke = await async_record_stroke_event(
            room_code=self.room_code,
            player_nickname=nickname,
            action_type='stroke',
            payload=payload
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'draw_stroke_event',
                'nickname': nickname,
                'sequence_number': saved_stroke['sequence_number'],
                'payload': payload,
            }
        )

        # Trigger background AI guess attempt silently
        asyncio.create_task(self.trigger_background_ai_guess())

    async def trigger_background_ai_guess(self):
        """Asynchronously attempts an AI player guess without blocking WS draw messages."""
        try:
            ai_res = await async_execute_ai_guess_attempt(self.room_code)
            if ai_res.get('executed') and ai_res.get('is_correct'):
                sub_res = ai_res.get('submit_result', {})
                guesser_nickname = sub_res.get('player_nickname', 'Scribl-Bot')
                pts = sub_res.get('guesser_points', 500)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'correct_guess_event',
                        'nickname': guesser_nickname,
                        'guesser_points': pts,
                        'players': sub_res.get('players', []),
                    }
                )

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message_event',
                        'nickname': 'System',
                        'text': f"🤖 Scribl-Bot guessed the word! (+{pts} pts)",
                        'is_system': True,
                    }
                )

                if sub_res.get('all_guessed'):
                    end_res = await async_end_round(self.room_code)
                    await self.broadcast_phase_update(end_res)

        except Exception as err:
            logger.error(f"Background AI guess error: {err}")

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

    # Redis Group Handlers
    async def game_phase_event(self, event):
        phase_data = dict(event['phase_data'])
        drawer = phase_data.get('current_drawer', '')

        if self.nickname.lower() != drawer.lower():
            phase_data.pop('word_choices', None)

        await self.send_json({
            'type': 'game_phase_change',
            **phase_data
        })

    async def chat_message_event(self, event):
        await self.send_json({
            'type': 'chat_message',
            'nickname': event['nickname'],
            'text': event['text'],
            'is_system': event['is_system'],
        })

    async def correct_guess_event(self, event):
        await self.send_json({
            'type': 'correct_guess',
            'nickname': event['nickname'],
            'guesser_points': event['guesser_points'],
            'players': event['players'],
        })

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
