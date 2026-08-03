import random
import string
from django.db import models
from django.utils import timezone


def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Room(models.Model):
    STATUS_LOBBY = 'LOBBY'
    STATUS_PLAYING = 'PLAYING'
    STATUS_FINISHED = 'FINISHED'

    STATUS_CHOICES = [
        (STATUS_LOBBY, 'Lobby'),
        (STATUS_PLAYING, 'Playing'),
        (STATUS_FINISHED, 'Finished'),
    ]

    code = models.CharField(max_length=8, unique=True, default=generate_room_code)
    host_name = models.CharField(max_length=50)
    max_players = models.IntegerField(default=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_LOBBY)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.code} ({self.status})"


class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    session_id = models.CharField(max_length=100)
    nickname = models.CharField(max_length=50)
    is_host = models.BooleanField(default=False)
    is_connected = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('room', 'nickname')

    def __str__(self):
        return f"{self.nickname} in {self.room.code}"


class Round(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='rounds')
    round_number = models.IntegerField(default=1)
    drawer = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='drawn_rounds')
    word = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Round {self.round_number} for Room {self.room.code}"


class StrokeEvent(models.Model):
    ACTION_STROKE = 'stroke'
    ACTION_CLEAR = 'clear'
    ACTION_UNDO = 'undo'

    ACTION_CHOICES = [
        (ACTION_STROKE, 'Stroke'),
        (ACTION_CLEAR, 'Clear'),
        (ACTION_UNDO, 'Undo'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='stroke_events')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, null=True, blank=True, related_name='stroke_events')
    sequence_number = models.BigIntegerField(default=0)
    player_nickname = models.CharField(max_length=50)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES, default=ACTION_STROKE)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sequence_number', 'created_at']

    def __str__(self):
        return f"Stroke #{self.sequence_number} ({self.action_type}) by {self.player_nickname} in {self.room.code}"
