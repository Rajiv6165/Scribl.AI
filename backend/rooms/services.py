import time
import random
from channels.db import database_sync_to_async
from django.db import transaction
from django.utils import timezone
from .models import Room, Player, StrokeEvent, Round, Word
from .word_bank import STARTER_WORDS
from .ai_service import AIService


class RoomService:

    @staticmethod
    def seed_word_bank():
        """Ensure initial word bank is populated in DB."""
        if Word.objects.filter(room=None).count() < 50:
            for item in STARTER_WORDS:
                Word.objects.get_or_create(
                    word=item["word"],
                    room=None,
                    defaults={
                        "difficulty": item["difficulty"],
                        "category": item["category"]
                    }
                )

    @staticmethod
    def create_room(host_nickname: str, max_players: int = 10, total_rounds: int = 3, smart_ai_enabled: bool = True, roast_mode_enabled: bool = True) -> dict:
        """Create a new room and assign host player."""
        host_nickname = host_nickname.strip()
        if not host_nickname:
            raise ValueError("Host nickname cannot be empty.")

        RoomService.seed_word_bank()

        with transaction.atomic():
            room = Room.objects.create(
                host_name=host_nickname,
                max_players=max_players,
                total_rounds=total_rounds,
                smart_ai_enabled=smart_ai_enabled,
                roast_mode_enabled=roast_mode_enabled,
                phase=Room.PHASE_LOBBY
            )
            player = Player.objects.create(
                room=room,
                nickname=host_nickname,
                session_id=f"host_{room.code}",
                is_host=True,
                is_connected=True,
                is_ai=False
            )

            if smart_ai_enabled:
                RoomService.add_ai_player_sync(room)

            return {
                "room_code": room.code,
                "host_nickname": host_nickname,
                "status": room.phase,
                "phase": room.phase,
                "max_players": room.max_players,
                "total_rounds": room.total_rounds,
                "smart_ai_enabled": room.smart_ai_enabled,
                "roast_mode_enabled": room.roast_mode_enabled,
                "custom_theme": room.custom_theme,
                "created_at": room.created_at.isoformat(),
            }

    @staticmethod
    def add_ai_player_sync(room: Room) -> Player:
        """Add Scribl-Bot AI player to room."""
        ai_player, _ = Player.objects.get_or_create(
            room=room,
            nickname="Scribl-Bot",
            defaults={
                "session_id": f"bot_{room.code}",
                "is_host": False,
                "is_connected": True,
                "is_ai": True,
            }
        )
        return ai_player

    @staticmethod
    def toggle_smart_ai(room_code: str, enabled: bool) -> dict:
        """Toggle AI player in room."""
        room = Room.objects.get(code=room_code.upper())
        room.smart_ai_enabled = enabled
        room.save(update_fields=['smart_ai_enabled'])

        if enabled:
            RoomService.add_ai_player_sync(room)
        else:
            Player.objects.filter(room=room, is_ai=True).delete()

        return {
            "room_code": room.code,
            "smart_ai_enabled": room.smart_ai_enabled,
            "players": RoomService.get_room_players_sync(room)
        }

    @staticmethod
    def toggle_roast_mode(room_code: str, enabled: bool) -> dict:
        """Toggle AI Roast Mode in room."""
        room = Room.objects.get(code=room_code.upper())
        room.roast_mode_enabled = enabled
        room.save(update_fields=['roast_mode_enabled'])
        return {
            "room_code": room.code,
            "roast_mode_enabled": room.roast_mode_enabled,
        }

    @staticmethod
    def generate_and_apply_custom_word_pack(room_code: str, theme: str) -> dict:
        """Generates custom AI themed word pack and attaches it to room session."""
        room = Room.objects.get(code=room_code.upper())
        theme_clean = theme.strip()

        if not theme_clean:
            raise ValueError("Theme cannot be empty.")

        word_list = AIService.generate_theme_word_pack(theme_clean)

        with transaction.atomic():
            Word.objects.filter(room=room).delete()

            for w in word_list:
                Word.objects.create(
                    word=w,
                    room=room,
                    difficulty='medium',
                    category=theme_clean
                )

            room.custom_theme = theme_clean
            room.save(update_fields=['custom_theme'])

        return {
            "room_code": room.code,
            "custom_theme": room.custom_theme,
            "word_count": len(word_list),
            "words": word_list,
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
                'is_ai': False,
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
            "status": room.phase,
            "phase": room.phase,
            "smart_ai_enabled": room.smart_ai_enabled,
            "roast_mode_enabled": room.roast_mode_enabled,
            "custom_theme": room.custom_theme,
            "current_round_num": room.current_round_num,
            "total_rounds": room.total_rounds,
            "current_drawer": room.current_drawer_nickname,
            "word_hint": room.word_hint,
            "timer_start_ms": room.timer_start_ms,
            "timer_duration_sec": room.timer_duration_sec,
            "players": players_list,
        }

    @staticmethod
    def leave_room(room_code: str, player_nickname: str) -> dict:
        """Mark player disconnected in room."""
        try:
            room = Room.objects.get(code=room_code.upper())
            player = Player.objects.filter(room=room, nickname=player_nickname).first()
            if player and not player.is_ai:
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
        """Fetch current players list for room ordered by score."""
        players = Player.objects.filter(room=room).order_by('-score', 'joined_at')
        return [
            {
                "nickname": p.nickname,
                "is_host": p.is_host,
                "is_connected": p.is_connected,
                "is_ai": p.is_ai,
                "score": p.score,
                "has_guessed": p.has_guessed,
            }
            for p in players
        ]

    @staticmethod
    def start_game(room_code: str, host_nickname: str) -> dict:
        """Host starts game loop from LOBBY."""
        room = Room.objects.get(code=room_code.upper())
        if room.host_name.lower() != host_nickname.lower():
            raise ValueError("Only the host can start the game.")

        connected_players = list(
            Player.objects.filter(room=room, is_connected=True)
            .values_list('nickname', flat=True)
        )

        if not connected_players:
            raise ValueError("No connected players in room.")

        random.shuffle(connected_players)

        Player.objects.filter(room=room).update(score=0, has_guessed=False, guess_order=0)

        room.turn_order = connected_players
        room.current_turn_index = 0
        room.current_round_num = 1
        room.save(update_fields=['turn_order', 'current_turn_index', 'current_round_num'])

        return RoomService.start_word_selection(room_code)

    @staticmethod
    def start_word_selection(room_code: str) -> dict:
        """Begin word selection phase for current turn's drawer."""
        room = Room.objects.get(code=room_code.upper())
        turn_order = room.turn_order or []

        if not turn_order or room.current_turn_index >= len(turn_order):
            room.current_turn_index = 0

        drawer_nickname = turn_order[room.current_turn_index]
        room.current_drawer_nickname = drawer_nickname
        room.phase = Room.PHASE_WORD_SELECT
        room.current_word = ''
        room.word_hint = ''
        room.timer_start_ms = int(time.time() * 1000)
        room.timer_duration_sec = 10
        room.save(update_fields=[
            'current_drawer_nickname', 'phase', 'current_word',
            'word_hint', 'timer_start_ms', 'timer_duration_sec', 'current_turn_index'
        ])

        Player.objects.filter(room=room).update(has_guessed=False, guess_order=0)
        StrokeEvent.objects.filter(room=room).delete()

        custom_words = list(Word.objects.filter(room=room).values_list('word', flat=True))
        if len(custom_words) >= 3:
            choices = random.sample(custom_words, 3)
        else:
            words = list(Word.objects.filter(room=None).values_list('word', flat=True))
            if len(words) < 3:
                words = ["CAT", "HOUSE", "ELEPHANT"]
            choices = random.sample(words, 3)

        return {
            "room_code": room.code,
            "phase": room.phase,
            "current_round_num": room.current_round_num,
            "total_rounds": room.total_rounds,
            "current_drawer": drawer_nickname,
            "word_choices": choices,
            "timer_start_ms": room.timer_start_ms,
            "timer_duration_sec": room.timer_duration_sec,
            "players": RoomService.get_room_players_sync(room),
        }

    @staticmethod
    def select_word(room_code: str, drawer_nickname: str, chosen_word: str) -> dict:
        """Drawer picks word to begin drawing phase."""
        room = Room.objects.get(code=room_code.upper())

        if room.current_drawer_nickname.lower() != drawer_nickname.lower():
            raise ValueError("Only the current drawer can select the word.")

        word_clean = chosen_word.upper().strip()
        room.current_word = word_clean
        
        hint_chars = []
        for char in word_clean:
            if char.isalpha():
                hint_chars.append('_')
            else:
                hint_chars.append(char)
        room.word_hint = ' '.join(hint_chars)

        room.phase = Room.PHASE_DRAWING
        room.timer_start_ms = int(time.time() * 1000)
        room.timer_duration_sec = 80
        room.save(update_fields=['current_word', 'word_hint', 'phase', 'timer_start_ms', 'timer_duration_sec'])

        return {
            "room_code": room.code,
            "phase": room.phase,
            "current_round_num": room.current_round_num,
            "total_rounds": room.total_rounds,
            "current_drawer": room.current_drawer_nickname,
            "word_hint": room.word_hint,
            "word_length": len(word_clean),
            "timer_start_ms": room.timer_start_ms,
            "timer_duration_sec": room.timer_duration_sec,
            "players": RoomService.get_room_players_sync(room),
        }

    @staticmethod
    def submit_guess(room_code: str, player_nickname: str, text: str) -> dict:
        """Validate player guess against current secret word."""
        room = Room.objects.get(code=room_code.upper())

        if room.phase != Room.PHASE_DRAWING:
            return {"is_correct": False, "reason": "Not in drawing phase."}

        player = Player.objects.filter(room=room, nickname=player_nickname).first()
        if not player:
            raise ValueError(f"Player {player_nickname} not found.")

        if player_nickname.lower() == room.current_drawer_nickname.lower() or player.has_guessed:
            return {"is_correct": False, "reason": "Drawer or already guessed."}

        clean_text = text.strip().upper()
        target_word = room.current_word.upper().strip()

        if clean_text == target_word:
            now_ms = int(time.time() * 1000)
            elapsed_sec = max(0, (now_ms - room.timer_start_ms) / 1000.0)
            time_left_sec = max(0.0, room.timer_duration_sec - elapsed_sec)

            time_ratio = time_left_sec / float(room.timer_duration_sec)
            guesser_pts = 500 + int(time_ratio * 500)

            player.score += guesser_pts
            player.has_guessed = True
            
            previous_guessers = Player.objects.filter(room=room, has_guessed=True).count()
            player.guess_order = previous_guessers + 1
            player.save(update_fields=['score', 'has_guessed', 'guess_order'])

            drawer = Player.objects.filter(room=room, nickname=room.current_drawer_nickname).first()
            if drawer:
                drawer.score += 100
                drawer.save(update_fields=['score'])

            non_drawers = Player.objects.filter(room=room, is_connected=True).exclude(nickname=room.current_drawer_nickname)
            all_guessed = non_drawers.filter(has_guessed=False).count() == 0

            return {
                "is_correct": True,
                "player_nickname": player.nickname,
                "guesser_points": guesser_pts,
                "total_score": player.score,
                "all_guessed": all_guessed,
                "players": RoomService.get_room_players_sync(room),
            }

        return {"is_correct": False, "text": text}

    @staticmethod
    def execute_ai_guess_attempt(room_code: str) -> dict:
        """Executes a non-cheat AI guess attempt via Gemini Vision & Pillow rendering."""
        try:
            room = Room.objects.get(code=room_code.upper())
            if not room.smart_ai_enabled or room.phase != Room.PHASE_DRAWING:
                return {"executed": False, "reason": "AI disabled or not in drawing phase."}

            bot = Player.objects.filter(room=room, is_ai=True, is_connected=True).first()
            if not bot or bot.has_guessed or bot.nickname.lower() == room.current_drawer_nickname.lower():
                return {"executed": False, "reason": "Bot drawing or already guessed."}

            strokes = StrokeEvent.objects.filter(room=room).order_by('sequence_number')
            if strokes.count() == 0:
                return {"executed": False, "reason": "Empty canvas."}

            stroke_data = [
                {
                    "action_type": s.action_type,
                    "payload": s.payload
                }
                for s in strokes
            ]

            guess_candidates = AIService.predict_drawing_guess(
                stroke_events=stroke_data,
                word_hint=room.word_hint
            )

            results = []
            for candidate in guess_candidates:
                res = RoomService.submit_guess(room_code=room.code, player_nickname="Scribl-Bot", text=candidate)
                results.append(res)
                if res.get('is_correct'):
                    return {
                        "executed": True,
                        "is_correct": True,
                        "guessed_word": candidate,
                        "submit_result": res,
                    }

            return {
                "executed": True,
                "is_correct": False,
                "guesses_attempted": guess_candidates,
            }
        except Exception as err:
            return {"executed": False, "error": str(err)}

    @staticmethod
    def generate_round_roast(room_code: str) -> dict:
        """Generates AI drawing roast asynchronously for round end summary."""
        try:
            room = Room.objects.get(code=room_code.upper())
            if not room.roast_mode_enabled:
                return {"roast": ""}

            strokes = StrokeEvent.objects.filter(room=room).order_by('sequence_number')
            stroke_data = [{"action_type": s.action_type, "payload": s.payload} for s in strokes]

            roast_text = AIService.generate_drawing_roast(
                stroke_events=stroke_data,
                revealed_word=room.current_word
            )
            return {"room_code": room.code, "roast": roast_text, "drawer": room.current_drawer_nickname}
        except Exception as err:
            return {"room_code": room_code, "roast": "A bold minimalist creation!", "error": str(err)}

    @staticmethod
    def generate_match_recap(room_code: str) -> dict:
        """Generates AI match highlight recap for game end results screen."""
        try:
            room = Room.objects.get(code=room_code.upper())
            recap_text = AIService.generate_match_highlight_recap(
                revealed_word=room.current_word or "Creative Masterpiece",
                drawer_nickname=room.current_drawer_nickname or "Top Artist"
            )
            return {"room_code": room.code, "recap": recap_text}
        except Exception as err:
            return {"room_code": room_code, "recap": "Match Highlight: Outstanding creativity across all rounds!", "error": str(err)}

    @staticmethod
    def end_round(room_code: str) -> dict:
        """End current drawing round, reveal word, and show round summary."""
        room = Room.objects.get(code=room_code.upper())
        room.phase = Room.PHASE_ROUND_END
        room.timer_start_ms = int(time.time() * 1000)
        room.timer_duration_sec = 10
        room.save(update_fields=['phase', 'timer_start_ms', 'timer_duration_sec'])

        players_list = RoomService.get_room_players_sync(room)

        return {
            "room_code": room.code,
            "phase": room.phase,
            "roast_mode_enabled": room.roast_mode_enabled,
            "revealed_word": room.current_word,
            "current_drawer": room.current_drawer_nickname,
            "timer_start_ms": room.timer_start_ms,
            "timer_duration_sec": room.timer_duration_sec,
            "players": players_list,
        }

    @staticmethod
    def next_turn(room_code: str) -> dict:
        """Rotate to next drawer or increment round / end game."""
        room = Room.objects.get(code=room_code.upper())
        turn_order = room.turn_order or []

        next_turn_idx = room.current_turn_index + 1

        if next_turn_idx >= len(turn_order):
            next_turn_idx = 0
            room.current_round_num += 1

        if room.current_round_num > room.total_rounds:
            room.phase = Room.PHASE_GAME_END
            room.save(update_fields=['phase', 'current_round_num'])
            return {
                "room_code": room.code,
                "phase": room.phase,
                "players": RoomService.get_room_players_sync(room),
            }

        room.current_turn_index = next_turn_idx
        room.save(update_fields=['current_turn_index', 'current_round_num'])

        return RoomService.start_word_selection(room_code)

    @staticmethod
    def record_stroke_event(room_code: str, player_nickname: str, action_type: str, payload: dict) -> dict:
        """Record stroke event to PostgreSQL for replay & sync."""
        try:
            room = Room.objects.get(code=room_code.upper())
            active_round = room.rounds.filter(status=Round.STATUS_ACTIVE).last()
            
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
        """Fetch canvas stroke events for current turn."""
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
        """Fetch complete replay payload for room session."""
        try:
            room = Room.objects.get(code=room_code.upper())
            strokes = StrokeEvent.objects.filter(room=room).order_by('sequence_number')
            return {
                "room_code": room.code,
                "host_name": room.host_name,
                "status": room.phase,
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


# Async database wrappers for Channels Consumer
async_create_room = database_sync_to_async(RoomService.create_room)
async_join_room = database_sync_to_async(RoomService.join_room)
async_leave_room = database_sync_to_async(RoomService.leave_room)
async_toggle_smart_ai = database_sync_to_async(RoomService.toggle_smart_ai)
async_toggle_roast_mode = database_sync_to_async(RoomService.toggle_roast_mode)
async_generate_and_apply_custom_word_pack = database_sync_to_async(RoomService.generate_and_apply_custom_word_pack)
async_start_game = database_sync_to_async(RoomService.start_game)
async_start_word_selection = database_sync_to_async(RoomService.start_word_selection)
async_select_word = database_sync_to_async(RoomService.select_word)
async_submit_guess = database_sync_to_async(RoomService.submit_guess)
async_execute_ai_guess_attempt = database_sync_to_async(RoomService.execute_ai_guess_attempt)
async_generate_round_roast = database_sync_to_async(RoomService.generate_round_roast)
async_generate_match_recap = database_sync_to_async(RoomService.generate_match_recap)
async_end_round = database_sync_to_async(RoomService.end_round)
async_next_turn = database_sync_to_async(RoomService.next_turn)
async_record_stroke_event = database_sync_to_async(RoomService.record_stroke_event)
async_get_canvas_history = database_sync_to_async(RoomService.get_canvas_history)
