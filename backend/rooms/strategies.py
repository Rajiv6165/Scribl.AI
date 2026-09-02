import random
import time
from django.utils import timezone
from .models import Room, Player, Round, Word, Guess, StrokeEvent, ChainDrawStep

class GameModeStrategy:
    def get_timer_duration(self, phase: str) -> int:
        raise NotImplementedError

    def start_game(self, room: Room) -> dict:
        raise NotImplementedError

    def start_word_selection(self, room: Room) -> dict:
        raise NotImplementedError

    def select_word(self, room: Room, drawer_nickname: str, chosen_word: str) -> dict:
        raise NotImplementedError

    def submit_guess(self, room: Room, player: Player, text: str) -> dict:
        raise NotImplementedError

    def end_round(self, room: Room) -> dict:
        raise NotImplementedError

    def next_turn(self, room: Room) -> dict:
        raise NotImplementedError


def _get_room_players_sync(room: Room) -> list:
    players = Player.objects.filter(room=room, is_spectator=False).order_by('-score', 'joined_at')
    return [
        {
            "nickname": p.nickname,
            "is_host": p.is_host,
            "is_connected": p.is_connected,
            "is_ai": p.is_ai,
            "is_spectator": False,
            "is_flagged": p.is_flagged,
            "anomaly_score": p.anomaly_score,
            "score": p.score,
            "team": p.team,
            "has_guessed": p.has_guessed,
        }
        for p in players
    ]


class ClassicModeStrategy(GameModeStrategy):
    def get_timer_duration(self, phase: str) -> int:
        if phase == Room.PHASE_WORD_SELECT: return 10
        if phase == Room.PHASE_DRAWING: return 80
        if phase == Room.PHASE_ROUND_END: return 10
        return 0

    def start_game(self, room: Room) -> dict:
        connected_players = list(
            Player.objects.filter(room=room, is_connected=True, is_spectator=False)
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
        return self.start_word_selection(room)

    def start_word_selection(self, room: Room) -> dict:
        turn_order = room.turn_order or []
        if not turn_order or room.current_turn_index >= len(turn_order):
            room.current_turn_index = 0

        drawer_nickname = turn_order[room.current_turn_index]
        room.current_drawer_nickname = drawer_nickname
        room.phase = Room.PHASE_WORD_SELECT
        room.current_word = ''
        room.word_hint = ''
        room.timer_start_ms = int(time.time() * 1000)
        room.timer_duration_sec = self.get_timer_duration(Room.PHASE_WORD_SELECT)
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
            if len(words) < 3: words = ["CAT", "HOUSE", "ELEPHANT"]
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
            "players": _get_room_players_sync(room),
        }

    def select_word(self, room: Room, drawer_nickname: str, chosen_word: str) -> dict:
        if room.current_drawer_nickname.lower() != drawer_nickname.lower():
            raise ValueError("Only the current drawer can select the word.")

        word_clean = chosen_word.upper().strip()
        room.current_word = word_clean
        
        hint_chars = []
        for char in word_clean:
            if char.isalpha(): hint_chars.append('_')
            else: hint_chars.append(char)
        room.word_hint = ' '.join(hint_chars)

        room.phase = Room.PHASE_DRAWING
        room.timer_start_ms = int(time.time() * 1000)
        room.timer_duration_sec = self.get_timer_duration(Room.PHASE_DRAWING)
        room.save(update_fields=['current_word', 'word_hint', 'phase', 'timer_start_ms', 'timer_duration_sec'])

        Round.objects.filter(room=room, status=Round.STATUS_ACTIVE).update(
            status=Round.STATUS_COMPLETED, ended_at=timezone.now()
        )
        Round.objects.create(
            room=room, round_number=room.current_round_num,
            drawer_nickname=room.current_drawer_nickname,
            word=word_clean, status=Round.STATUS_ACTIVE, started_at=timezone.now()
        )

        return {
            "room_code": room.code, "phase": room.phase,
            "current_round_num": room.current_round_num, "total_rounds": room.total_rounds,
            "current_drawer": room.current_drawer_nickname, "word_hint": room.word_hint,
            "word_length": len(word_clean), "timer_start_ms": room.timer_start_ms,
            "timer_duration_sec": room.timer_duration_sec, "players": _get_room_players_sync(room),
        }

    def _calculate_score(self, room: Room, time_ratio: float) -> int:
        return 500 + int(time_ratio * 500)

    def submit_guess(self, room: Room, player: Player, text: str) -> dict:
        if room.phase != Room.PHASE_DRAWING:
            return {"is_correct": False, "reason": "Not in drawing phase."}

        if player.nickname.lower() == room.current_drawer_nickname.lower() or player.has_guessed:
            return {"is_correct": False, "reason": "Drawer or already guessed."}

        clean_text = text.strip().upper()
        target_word = room.current_word.upper().strip()
        is_correct = (clean_text == target_word)
        guesser_pts = 0

        active_round = room.rounds.filter(status=Round.STATUS_ACTIVE).last()

        if is_correct:
            now_ms = int(time.time() * 1000)
            elapsed_sec = max(0, (now_ms - room.timer_start_ms) / 1000.0)
            time_left_sec = max(0.0, room.timer_duration_sec - elapsed_sec)
            time_ratio = time_left_sec / float(room.timer_duration_sec)
            
            guesser_pts = self._calculate_score(room, time_ratio)
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

            if active_round:
                Guess.objects.create(
                    round=active_round, player_nickname=player.nickname, text=text,
                    is_correct=True, points_awarded=guesser_pts
                )

            return {
                "is_correct": True, "player_nickname": player.nickname,
                "guesser_points": guesser_pts, "total_score": player.score,
                "all_guessed": all_guessed, "players": _get_room_players_sync(room),
            }

        if active_round:
            Guess.objects.create(
                round=active_round, player_nickname=player.nickname,
                text=text, is_correct=False, points_awarded=0
            )

        return {"is_correct": False, "text": text}

    def end_round(self, room: Room) -> dict:
        room.phase = Room.PHASE_ROUND_END
        room.timer_start_ms = int(time.time() * 1000)
        room.timer_duration_sec = self.get_timer_duration(Room.PHASE_ROUND_END)
        room.save(update_fields=['phase', 'timer_start_ms', 'timer_duration_sec'])

        active_round = room.rounds.filter(status=Round.STATUS_ACTIVE).last()
        if active_round:
            active_round.status = Round.STATUS_COMPLETED
            active_round.ended_at = timezone.now()
            active_round.save(update_fields=['status', 'ended_at'])

        return {
            "room_code": room.code, "phase": room.phase,
            "roast_mode_enabled": room.roast_mode_enabled,
            "revealed_word": room.current_word, "current_drawer": room.current_drawer_nickname,
            "round_id": active_round.id if active_round else None,
            "timer_start_ms": room.timer_start_ms, "timer_duration_sec": room.timer_duration_sec,
            "players": _get_room_players_sync(room),
        }

    def next_turn(self, room: Room) -> dict:
        turn_order = room.turn_order or []
        next_turn_idx = room.current_turn_index + 1

        if next_turn_idx >= len(turn_order):
            next_turn_idx = 0
            room.current_round_num += 1

        if room.current_round_num > room.total_rounds:
            room.phase = Room.PHASE_GAME_END
            room.save(update_fields=['phase', 'current_round_num'])
            return {
                "room_code": room.code, "phase": room.phase,
                "players": _get_room_players_sync(room),
            }

        room.current_turn_index = next_turn_idx
        room.save(update_fields=['current_turn_index', 'current_round_num'])
        return self.start_word_selection(room)


class SpeedRoundModeStrategy(ClassicModeStrategy):
    def get_timer_duration(self, phase: str) -> int:
        if phase == Room.PHASE_WORD_SELECT: return 5
        if phase == Room.PHASE_DRAWING: return 40
        if phase == Room.PHASE_ROUND_END: return 10
        return 0

    def _calculate_score(self, room: Room, time_ratio: float) -> int:
        # Higher stakes scoring multiplier (decay faster)
        return 500 + int((time_ratio ** 2) * 1000)


class TeamModeStrategy(ClassicModeStrategy):
    def start_game(self, room: Room) -> dict:
        players = list(Player.objects.filter(room=room, is_connected=True, is_spectator=False))
        if not players:
            raise ValueError("No connected players in room.")
            
        team_a = [p for p in players if p.team == 'A']
        team_b = [p for p in players if p.team == 'B']
        unassigned = [p for p in players if not p.team]
        
        # Randomly assign remaining
        random.shuffle(unassigned)
        for p in unassigned:
            if len(team_a) <= len(team_b):
                p.team = 'A'
                team_a.append(p)
            else:
                p.team = 'B'
                team_b.append(p)
            p.save(update_fields=['team'])

        Player.objects.filter(room=room).update(score=0, has_guessed=False, guess_order=0)

        # Interleave turn order
        random.shuffle(team_a)
        random.shuffle(team_b)
        turn_order = []
        for i in range(max(len(team_a), len(team_b))):
            if i < len(team_a): turn_order.append(team_a[i].nickname)
            if i < len(team_b): turn_order.append(team_b[i].nickname)

        room.turn_order = turn_order
        room.current_turn_index = 0
        room.current_round_num = 1
        room.save(update_fields=['turn_order', 'current_turn_index', 'current_round_num'])
        
        return self.start_word_selection(room)

    def submit_guess(self, room: Room, player: Player, text: str) -> dict:
        drawer = Player.objects.filter(room=room, nickname=room.current_drawer_nickname).first()
        if drawer and drawer.team == player.team:
            return {"is_correct": False, "reason": "Cannot guess your own team's drawing."}
        
        return super().submit_guess(room, player, text)


class ChainDrawModeStrategy(GameModeStrategy):
    def get_timer_duration(self, phase: str) -> int:
        if phase == Room.PHASE_WORD_SELECT: return 15
        if phase == Room.PHASE_DRAWING: return 60
        if phase == Room.PHASE_ROUND_END: return 15
        return 0

    def start_game(self, room: Room) -> dict:
        connected_players = list(
            Player.objects.filter(room=room, is_connected=True, is_spectator=False)
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
        return self.start_word_selection(room)

    def start_word_selection(self, room: Room) -> dict:
        turn_order = room.turn_order or []
        if not turn_order or room.current_turn_index >= len(turn_order):
            room.current_turn_index = 0

        drawer_nickname = turn_order[room.current_turn_index]
        room.current_drawer_nickname = drawer_nickname
        room.phase = Room.PHASE_WORD_SELECT
        room.current_word = ''
        room.word_hint = ''
        room.timer_start_ms = int(time.time() * 1000)
        room.timer_duration_sec = self.get_timer_duration(Room.PHASE_WORD_SELECT)
        room.save(update_fields=[
            'current_drawer_nickname', 'phase', 'current_word',
            'word_hint', 'timer_start_ms', 'timer_duration_sec', 'current_turn_index'
        ])
        
        is_guess_turn = (room.current_turn_index % 2 == 1)
        
        if is_guess_turn:
            room.phase = Room.PHASE_DRAWING 
            room.timer_duration_sec = self.get_timer_duration(Room.PHASE_DRAWING)
            room.save(update_fields=['phase', 'timer_duration_sec'])
            
            active_round = room.rounds.filter(status=Round.STATUS_ACTIVE).last()
            if not active_round:
                 active_round = Round.objects.create(
                    room=room, round_number=room.current_round_num,
                    drawer_nickname=turn_order[0],
                    word="CHAIN", status=Round.STATUS_ACTIVE, started_at=timezone.now()
                )

            ChainDrawStep.objects.create(
                room=room, round=active_round, step_number=room.current_turn_index,
                player_nickname=drawer_nickname, step_type='guess'
            )
            
            return {
                "room_code": room.code,
                "phase": room.phase,
                "is_chain_guess_turn": True,
                "current_round_num": room.current_round_num,
                "total_rounds": room.total_rounds,
                "current_drawer": drawer_nickname,
                "timer_start_ms": room.timer_start_ms,
                "timer_duration_sec": room.timer_duration_sec,
                "players": _get_room_players_sync(room),
            }
        else:
            Player.objects.filter(room=room).update(has_guessed=False, guess_order=0)
            StrokeEvent.objects.filter(room=room).delete()
    
            custom_words = list(Word.objects.filter(room=room).values_list('word', flat=True))
            if len(custom_words) >= 3: choices = random.sample(custom_words, 3)
            else:
                words = list(Word.objects.filter(room=None).values_list('word', flat=True))
                if len(words) < 3: words = ["CAT", "HOUSE", "ELEPHANT"]
                choices = random.sample(words, 3)
    
            return {
                "room_code": room.code,
                "phase": room.phase,
                "is_chain_guess_turn": False,
                "current_round_num": room.current_round_num,
                "total_rounds": room.total_rounds,
                "current_drawer": drawer_nickname,
                "word_choices": choices,
                "timer_start_ms": room.timer_start_ms,
                "timer_duration_sec": room.timer_duration_sec,
                "players": _get_room_players_sync(room),
            }

    def select_word(self, room: Room, drawer_nickname: str, chosen_word: str) -> dict:
        if room.current_drawer_nickname.lower() != drawer_nickname.lower():
            raise ValueError("Only the current drawer can select the word.")

        word_clean = chosen_word.upper().strip()
        room.current_word = word_clean
        room.word_hint = word_clean

        room.phase = Room.PHASE_DRAWING
        room.timer_start_ms = int(time.time() * 1000)
        room.timer_duration_sec = self.get_timer_duration(Room.PHASE_DRAWING)
        room.save(update_fields=['current_word', 'word_hint', 'phase', 'timer_start_ms', 'timer_duration_sec'])

        Round.objects.filter(room=room, status=Round.STATUS_ACTIVE).update(
            status=Round.STATUS_COMPLETED, ended_at=timezone.now()
        )
        active_round = Round.objects.create(
            room=room, round_number=room.current_round_num,
            drawer_nickname=room.current_drawer_nickname,
            word=word_clean, status=Round.STATUS_ACTIVE, started_at=timezone.now()
        )
        
        ChainDrawStep.objects.create(
            room=room, round=active_round, step_number=room.current_turn_index,
            player_nickname=drawer_nickname, step_type='draw', word_to_draw=word_clean
        )

        return {
            "room_code": room.code, "phase": room.phase,
            "is_chain_guess_turn": False,
            "current_round_num": room.current_round_num, "total_rounds": room.total_rounds,
            "current_drawer": room.current_drawer_nickname, "word_hint": room.word_hint,
            "word_length": len(word_clean), "timer_start_ms": room.timer_start_ms,
            "timer_duration_sec": room.timer_duration_sec, "players": _get_room_players_sync(room),
        }

    def submit_guess(self, room: Room, player: Player, text: str) -> dict:
        if room.phase != Room.PHASE_DRAWING:
            return {"is_correct": False, "reason": "Not in drawing phase."}

        if player.nickname.lower() != room.current_drawer_nickname.lower():
            return {"is_correct": False, "reason": "Only the active chain player can guess."}

        clean_text = text.strip().upper()
        
        active_round = room.rounds.filter(status=Round.STATUS_ACTIVE).last()
        if active_round:
            step = ChainDrawStep.objects.filter(round=active_round, step_number=room.current_turn_index).last()
            if step and step.step_type == 'guess':
                step.guessed_word = clean_text
                step.save(update_fields=['guessed_word'])
                
                res = self.next_turn(room)
                if res.get('phase') == Room.PHASE_WORD_SELECT and not res.get('is_chain_guess_turn'):
                    res = self.select_word(room, room.current_drawer_nickname, clean_text)
                    
                return {
                    "is_correct": True,
                    "chain_advance": True,
                    "next_turn_data": res
                }
                
        return {"is_correct": False, "text": text}

    def end_round(self, room: Room) -> dict:
        room.phase = Room.PHASE_ROUND_END
        room.timer_start_ms = int(time.time() * 1000)
        room.timer_duration_sec = self.get_timer_duration(Room.PHASE_ROUND_END)
        room.save(update_fields=['phase', 'timer_start_ms', 'timer_duration_sec'])

        active_round = room.rounds.filter(status=Round.STATUS_ACTIVE).last()
        if active_round:
            active_round.status = Round.STATUS_COMPLETED
            active_round.ended_at = timezone.now()
            active_round.save(update_fields=['status', 'ended_at'])
            
        steps = []
        if active_round:
            for s in ChainDrawStep.objects.filter(round=active_round).order_by('step_number'):
                steps.append({
                    "step_number": s.step_number,
                    "player": s.player_nickname,
                    "type": s.step_type,
                    "word": s.word_to_draw or s.guessed_word
                })

        return {
            "room_code": room.code, "phase": room.phase,
            "revealed_word": room.current_word,
            "chain_steps": steps,
            "round_id": active_round.id if active_round else None,
            "timer_start_ms": room.timer_start_ms, "timer_duration_sec": room.timer_duration_sec,
            "players": _get_room_players_sync(room),
        }

    def next_turn(self, room: Room) -> dict:
        turn_order = room.turn_order or []
        next_turn_idx = room.current_turn_index + 1

        if next_turn_idx >= len(turn_order):
            next_turn_idx = 0
            room.current_round_num += 1
            if room.current_round_num > room.total_rounds:
                room.phase = Room.PHASE_GAME_END
                room.save(update_fields=['phase', 'current_round_num'])
                return {
                    "room_code": room.code, "phase": room.phase,
                    "players": _get_room_players_sync(room),
                }
            return self.end_round(room)

        room.current_turn_index = next_turn_idx
        room.save(update_fields=['current_turn_index'])
        
        return self.start_word_selection(room)
