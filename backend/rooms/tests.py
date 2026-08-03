import os
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Room, Player, StrokeEvent, Word
from .services import RoomService
from .ai_service import AIService


class RoomServicePhase4Test(TestCase):
    def setUp(self):
        RoomService.seed_word_bank()

    def test_toggle_roast_mode(self):
        create_res = RoomService.create_room(host_nickname="Alice", roast_mode_enabled=True)
        code = create_res["room_code"]

        off_res = RoomService.toggle_roast_mode(code, False)
        self.assertFalse(off_res["roast_mode_enabled"])

        on_res = RoomService.toggle_roast_mode(code, True)
        self.assertTrue(on_res["roast_mode_enabled"])

    def test_drawing_roast_generation_and_fallback(self):
        create_res = RoomService.create_room(host_nickname="Alice")
        code = create_res["room_code"]
        RoomService.record_stroke_event(code, "Alice", "stroke", {"points": [{"x": 10, "y": 20}]})

        # Test fallback when API key is unconfigured
        roast = AIService.generate_drawing_roast([], "ELEPHANT")
        self.assertIsInstance(roast, str)
        self.assertGreater(len(roast), 10)

        # Test service wrapper non-blocking roast call
        round_roast = RoomService.generate_round_roast(code)
        self.assertEqual(round_roast["room_code"], code)
        self.assertIn("roast", round_roast)

    def test_match_recap_generation(self):
        create_res = RoomService.create_room(host_nickname="Alice")
        code = create_res["room_code"]

        recap = AIService.generate_match_highlight_recap("ELEPHANT", "Alice")
        self.assertIsInstance(recap, str)
        self.assertIn("Alice", recap)

        match_recap = RoomService.generate_match_recap(code)
        self.assertEqual(match_recap["room_code"], code)
        self.assertIn("recap", match_recap)

    def test_end_round_non_blocking(self):
        create_res = RoomService.create_room(host_nickname="Alice")
        code = create_res["room_code"]
        RoomService.join_room(code, "Bob", "sess_bob")
        RoomService.start_game(code, "Alice")
        room = Room.objects.get(code=code)

        # Verify end_round returns immediately
        end_res = RoomService.end_round(code)
        self.assertEqual(end_res["phase"], Room.PHASE_ROUND_END)
        self.assertTrue(end_res["roast_mode_enabled"])


class RoomServicePhase3AITest(TestCase):
    def setUp(self):
        RoomService.seed_word_bank()

    def test_create_room_with_ai_player(self):
        result = RoomService.create_room(host_nickname="Alice", smart_ai_enabled=True)
        code = result["room_code"]
        room = Room.objects.get(code=code)
        
        self.assertTrue(room.smart_ai_enabled)
        bot = Player.objects.filter(room=room, is_ai=True).first()
        self.assertIsNotNone(bot)
        self.assertEqual(bot.nickname, "Scribl-Bot")

    def test_toggle_smart_ai(self):
        result = RoomService.create_room(host_nickname="Alice", smart_ai_enabled=True)
        code = result["room_code"]

        off_res = RoomService.toggle_smart_ai(code, False)
        self.assertFalse(off_res["smart_ai_enabled"])
        bot_count = Player.objects.filter(room__code=code, is_ai=True).count()
        self.assertEqual(bot_count, 0)

        on_res = RoomService.toggle_smart_ai(code, True)
        self.assertTrue(on_res["smart_ai_enabled"])
        bot = Player.objects.filter(room__code=code, is_ai=True).first()
        self.assertIsNotNone(bot)

    def test_pil_canvas_image_rendering(self):
        stroke_events = [
            {
                "action_type": "stroke",
                "payload": {
                    "color": "#ff0000",
                    "brushSize": 8,
                    "points": [{"x": 10, "y": 10}, {"x": 50, "y": 50}]
                }
            }
        ]
        image_bytes = AIService.render_strokes_to_image(stroke_events)
        self.assertTrue(image_bytes.startswith(b'\x89PNG'))
        self.assertGreater(len(image_bytes), 100)

    def test_ai_guess_submission_through_normal_validation_path(self):
        create_res = RoomService.create_room(host_nickname="Alice", smart_ai_enabled=True)
        code = create_res["room_code"]
        RoomService.join_room(room_code=code, player_nickname="Bob", session_id="sess_bob")

        RoomService.start_game(room_code=code, host_nickname="Alice")
        room = Room.objects.get(code=code)

        if room.current_drawer_nickname == "Scribl-Bot":
            RoomService.next_turn(code)
            room = Room.objects.get(code=code)

        drawer = room.current_drawer_nickname
        RoomService.select_word(room_code=code, drawer_nickname=drawer, chosen_word="CAT")

        RoomService.record_stroke_event(code, drawer, "stroke", {"points": [{"x": 10, "y": 20}]})

        guess_res = RoomService.submit_guess(room_code=code, player_nickname="Scribl-Bot", text="CAT")
        self.assertTrue(guess_res["is_correct"])
        self.assertEqual(guess_res["player_nickname"], "Scribl-Bot")
        
        bot = Player.objects.get(room=room, nickname="Scribl-Bot")
        self.assertTrue(bot.has_guessed)
        self.assertGreater(bot.score, 500)

    def test_ai_word_pack_generation_and_filtering(self):
        theme_words = AIService.generate_theme_word_pack("Bollywood Movies")
        self.assertGreaterEqual(len(theme_words), 5)

        create_res = RoomService.create_room(host_nickname="Alice", smart_ai_enabled=True)
        code = create_res["room_code"]

        res = RoomService.generate_and_apply_custom_word_pack(code, "Superhero Gadgets")
        self.assertEqual(res["custom_theme"], "Superhero Gadgets")
        self.assertGreaterEqual(res["word_count"], 5)

    def test_gemini_api_failure_resilience(self):
        with patch("google.generativeai.GenerativeModel") as mock_model:
            mock_model.side_effect = Exception("API Quota Exceeded 500 Error")

            guesses = AIService.predict_drawing_guess([{"action_type": "stroke", "payload": {}}], "_ _ _")
            self.assertIsInstance(guesses, list)

        create_res = RoomService.create_room(host_nickname="Alice", smart_ai_enabled=True)
        code = create_res["room_code"]
        RoomService.start_game(room_code=code, host_nickname="Alice")
        room = Room.objects.get(code=code)
        drawer = room.current_drawer_nickname

        RoomService.select_word(code, drawer, "CAT")
        RoomService.record_stroke_event(code, drawer, "stroke", {"points": [{"x": 1, "y": 2}]})

        attempt_res = RoomService.execute_ai_guess_attempt(code)
        self.assertIn("executed", attempt_res)


class RoomAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_room_api(self):
        response = self.client.post(reverse('room-create'), {'nickname': 'Charlie', 'max_players': 8})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('room_code', response.data)

    def test_generate_word_pack_api(self):
        create_res = self.client.post(reverse('room-create'), {'nickname': 'Charlie'})
        code = create_res.data['room_code']

        pack_res = self.client.post(reverse('generate-word-pack'), {'room_code': code, 'theme': 'Startup Buzzwords'})
        self.assertEqual(pack_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pack_res.data['custom_theme'], 'Startup Buzzwords')
