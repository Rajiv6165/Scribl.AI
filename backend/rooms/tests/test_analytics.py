from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rooms.models import Room, Player, Round, Guess, Word


class AnalyticsViewTests(TestCase):
    def setUp(self):
        # 1. Create a Word dictionary
        Word.objects.create(word="apple", difficulty=Word.DIFFICULTY_EASY)
        Word.objects.create(word="quantum", difficulty=Word.DIFFICULTY_HARD)

        # 2. Create Rooms
        self.room1 = Room.objects.create(code="RM111", game_mode=Room.MODE_CLASSIC)
        self.room2 = Room.objects.create(code="RM222", game_mode=Room.MODE_SPEED)
        self.room3 = Room.objects.create(code="RM333", game_mode=Room.MODE_CLASSIC)
        
        # 3. Create Players (Humans and AI)
        self.human = Player.objects.create(room=self.room1, nickname="Alice", is_ai=False, is_flagged=True)
        self.human.joined_at = timezone.now() - timedelta(days=1)
        self.human.save()
        
        self.ai = Player.objects.create(room=self.room1, nickname="Scribl-Bot", is_ai=True)
        self.human2 = Player.objects.create(room=self.room2, nickname="Alice", is_ai=False)

        # 4. Create Rounds
        # Round 1: word 'apple', completed
        now = timezone.now()
        self.round1 = Round.objects.create(
            room=self.room1, round_number=1, word="apple", status=Round.STATUS_COMPLETED,
            is_flagged=True
        )
        self.round1.started_at = now - timedelta(seconds=10)
        self.round1.save()

        # Round 2: word 'apple', completed
        self.round2 = Round.objects.create(
            room=self.room1, round_number=2, word="apple", status=Round.STATUS_COMPLETED
        )
        
        # Round 3: word 'quantum', completed, in Speed mode
        self.round3 = Round.objects.create(
            room=self.room2, round_number=1, word="quantum", status=Round.STATUS_COMPLETED
        )
        self.round3.started_at = now - timedelta(seconds=30)
        self.round3.save()

        # 5. Create Guesses
        # Human guesses "apple" correctly in 5 seconds
        g1 = Guess.objects.create(
            round=self.round1, player_nickname="Alice", text="apple", is_correct=True
        )
        g1.created_at = self.round1.started_at + timedelta(seconds=5)
        g1.save()
        
        # Human guesses wrong
        Guess.objects.create(
            round=self.round1, player_nickname="Alice", text="app", is_correct=False
        )

        # AI guesses "apple" correctly in 2 seconds
        g3 = Guess.objects.create(
            round=self.round1, player_nickname="Scribl-Bot", text="apple", is_correct=True
        )
        g3.created_at = self.round1.started_at + timedelta(seconds=2)
        g3.save()

        # Human guesses "quantum" correctly in 20 seconds
        g4 = Guess.objects.create(
            round=self.round3, player_nickname="Alice", text="quantum", is_correct=True
        )
        g4.created_at = self.round3.started_at + timedelta(seconds=20)
        g4.save()
        
    def test_analytics_summary_data(self):
        url = reverse('analytics-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # 1. Most-drawn words
        words = data['most_drawn_words']
        # 'apple' was used twice, 'quantum' once
        self.assertTrue(len(words) >= 2)
        self.assertEqual(words[0]['word'], 'apple')
        self.assertEqual(words[0]['count'], 2)
        self.assertEqual(words[1]['word'], 'quantum')
        self.assertEqual(words[1]['count'], 1)

        # 2. Average guess times per difficulty
        # Easy ('apple'): 5s human + 2s ai = 7s / 2 = 3.5s
        # Hard ('quantum'): 20s human = 20s / 1 = 20s
        avg_times = {item['difficulty']: item['avg_seconds'] for item in data['avg_guess_times']}
        self.assertEqual(avg_times['easy'], 3.5)
        self.assertEqual(avg_times['hard'], 20.0)

        # 3. Accuracy AI vs Human
        # Human: 3 guesses total (2 correct, 1 wrong) -> 66.67%
        # AI: 1 guess total (1 correct) -> 100%
        accuracies = {str(item['is_ai']).lower(): item for item in data['accuracy']}
        self.assertEqual(accuracies['false']['total_guesses'], 3)
        self.assertEqual(accuracies['false']['correct_guesses'], 2)
        self.assertAlmostEqual(accuracies['false']['accuracy_rate'], 0.6667, places=4)
        
        self.assertEqual(accuracies['true']['total_guesses'], 1)
        self.assertEqual(accuracies['true']['correct_guesses'], 1)
        self.assertAlmostEqual(accuracies['true']['accuracy_rate'], 1.0, places=4)

        # 4. Anti-cheat flags
        # Human flagged (1), Round1 flagged (1). Might be on different dates or same date.
        flags_timeline = data['flags_timeline']
        total_flags = sum(item['flags'] for item in flags_timeline)
        self.assertEqual(total_flags, 2)

        # 5. Game mode popularity
        # 2 classic rounds (round1, round2 in room1)
        # 1 speed round (round3 in room2)
        modes = {item['mode']: item['rounds_played'] for item in data['mode_popularity']}
        self.assertEqual(modes['classic'], 2)
        self.assertEqual(modes['speed'], 1)
