from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Room, Player, StrokeEvent, Word
from .services import RoomService


class RoomServicePhase2Test(TestCase):
    def setUp(self):
        RoomService.seed_word_bank()

    def test_create_and_join_room(self):
        result = RoomService.create_room(host_nickname="Alice")
        code = result["room_code"]
        self.assertEqual(result["host_nickname"], "Alice")

        join_res = RoomService.join_room(room_code=code, player_nickname="Bob", session_id="sess_bob")
        self.assertEqual(len(join_res["players"]), 2)

    def test_start_game_and_word_selection(self):
        create_res = RoomService.create_room(host_nickname="Alice")
        code = create_res["room_code"]
        RoomService.join_room(room_code=code, player_nickname="Bob", session_id="sess_bob")

        game_start = RoomService.start_game(room_code=code, host_nickname="Alice")
        self.assertEqual(game_start["phase"], Room.PHASE_WORD_SELECT)
        self.assertEqual(game_start["current_round_num"], 1)
        self.assertIn(game_start["current_drawer"], ["Alice", "Bob"])
        self.assertEqual(len(game_start["word_choices"]), 3)

    def test_select_word_and_submit_guess(self):
        create_res = RoomService.create_room(host_nickname="Alice")
        code = create_res["room_code"]
        RoomService.join_room(room_code=code, player_nickname="Bob", session_id="sess_bob")
        
        RoomService.start_game(room_code=code, host_nickname="Alice")
        room = Room.objects.get(code=code)
        drawer = room.current_drawer_nickname
        guesser = "Bob" if drawer == "Alice" else "Alice"

        # Select word
        select_res = RoomService.select_word(room_code=code, drawer_nickname=drawer, chosen_word="ELEPHANT")
        self.assertEqual(select_res["phase"], Room.PHASE_DRAWING)
        self.assertIn("_", select_res["word_hint"])

        # Incorrect guess
        wrong_res = RoomService.submit_guess(room_code=code, player_nickname=guesser, text="DOG")
        self.assertFalse(wrong_res["is_correct"])

        # Correct guess
        correct_res = RoomService.submit_guess(room_code=code, player_nickname=guesser, text="elephant")
        self.assertTrue(correct_res["is_correct"])
        self.assertGreater(correct_res["guesser_points"], 500)
        self.assertTrue(correct_res["all_guessed"])

    def test_end_round_and_next_turn(self):
        create_res = RoomService.create_room(host_nickname="Alice")
        code = create_res["room_code"]
        RoomService.join_room(room_code=code, player_nickname="Bob", session_id="sess_bob")

        RoomService.start_game(room_code=code, host_nickname="Alice")
        room = Room.objects.get(code=code)
        drawer = room.current_drawer_nickname
        RoomService.select_word(room_code=code, drawer_nickname=drawer, chosen_word="CAT")

        end_res = RoomService.end_round(room_code=code)
        self.assertEqual(end_res["phase"], Room.PHASE_ROUND_END)
        self.assertEqual(end_res["revealed_word"], "CAT")

        next_res = RoomService.next_turn(room_code=code)
        self.assertEqual(next_res["phase"], Room.PHASE_WORD_SELECT)
        self.assertNotEqual(next_res["current_drawer"], drawer)

    def test_stroke_replay_recording(self):
        create_res = RoomService.create_room(host_nickname="Artist")
        code = create_res["room_code"]

        payload = {
            "color": "#ff0000",
            "brushSize": 5,
            "points": [{"x": 10, "y": 20, "pressure": 0.5, "timestamp": 1000}]
        }
        stroke = RoomService.record_stroke_event(code, "Artist", "stroke", payload)
        self.assertEqual(stroke["sequence_number"], 1)

        replay = RoomService.get_replay_data(code)
        self.assertEqual(replay["total_strokes"], 1)


class RoomAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_room_api(self):
        response = self.client.post(reverse('room-create'), {'nickname': 'Charlie', 'max_players': 8})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('room_code', response.data)

    def test_join_room_api(self):
        create_res = self.client.post(reverse('room-create'), {'nickname': 'Charlie'})
        code = create_res.data['room_code']

        join_res = self.client.post(reverse('room-join'), {'room_code': code, 'nickname': 'Dave'})
        self.assertEqual(join_res.status_code, status.HTTP_200_OK)
        self.assertEqual(join_res.data['player_nickname'], 'Dave')
