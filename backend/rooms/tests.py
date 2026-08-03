from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Room, Player, StrokeEvent
from .services import RoomService


class RoomServiceTest(TestCase):
    def test_create_room(self):
        result = RoomService.create_room(host_nickname="Alice")
        self.assertIn("room_code", result)
        self.assertEqual(result["host_nickname"], "Alice")
        
        room = Room.objects.get(code=result["room_code"])
        self.assertEqual(room.host_name, "Alice")
        
        player = Player.objects.get(room=room, nickname="Alice")
        self.assertTrue(player.is_host)
        self.assertTrue(player.is_connected)

    def test_join_room(self):
        create_res = RoomService.create_room(host_nickname="Alice")
        code = create_res["room_code"]

        join_res = RoomService.join_room(room_code=code, player_nickname="Bob", session_id="sess_bob")
        self.assertEqual(join_res["player_nickname"], "Bob")
        self.assertFalse(join_res["is_host"])
        self.assertEqual(len(join_res["players"]), 2)

    def test_record_and_replay_strokes(self):
        create_res = RoomService.create_room(host_nickname="Artist")
        code = create_res["room_code"]

        payload1 = {
            "color": "#ff0000",
            "brushSize": 5,
            "points": [{"x": 10, "y": 20, "pressure": 0.5, "timestamp": 1000}]
        }
        stroke1 = RoomService.record_stroke_event(code, "Artist", "stroke", payload1)
        self.assertEqual(stroke1["sequence_number"], 1)

        payload2 = {
            "color": "#00ff00",
            "brushSize": 10,
            "points": [{"x": 30, "y": 40, "pressure": 0.8, "timestamp": 1050}]
        }
        stroke2 = RoomService.record_stroke_event(code, "Artist", "stroke", payload2)
        self.assertEqual(stroke2["sequence_number"], 2)

        replay = RoomService.get_replay_data(code)
        self.assertEqual(replay["total_strokes"], 2)
        self.assertEqual(replay["events"][0]["payload"], payload1)
        self.assertEqual(replay["events"][1]["payload"], payload2)


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

    def test_replay_api(self):
        create_res = self.client.post(reverse('room-create'), {'nickname': 'Artist'})
        code = create_res.data['room_code']

        RoomService.record_stroke_event(code, "Artist", "stroke", {"points": [{"x": 1, "y": 2}]})

        replay_res = self.client.get(reverse('room-replay', kwargs={'code': code}))
        self.assertEqual(replay_res.status_code, status.HTTP_200_OK)
        self.assertEqual(replay_res.data['total_strokes'], 1)
