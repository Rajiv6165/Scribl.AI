import random
import string
from django.db import models
from django.utils import timezone


def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Room(models.Model):
    PHASE_LOBBY = 'LOBBY'
    PHASE_WORD_SELECT = 'WORD_SELECT'
    PHASE_DRAWING = 'DRAWING'
    PHASE_ROUND_END = 'ROUND_END'
    PHASE_GAME_END = 'GAME_END'

    PHASE_CHOICES = [
        (PHASE_LOBBY, 'Lobby'),
        (PHASE_WORD_SELECT, 'Selecting Word'),
        (PHASE_DRAWING, 'Drawing'),
        (PHASE_ROUND_END, 'Round Ended'),
        (PHASE_GAME_END, 'Game Ended'),
    ]

    code = models.CharField(max_length=8, unique=True, default=generate_room_code)
    host_name = models.CharField(max_length=50)
    max_players = models.IntegerField(default=10)
    total_rounds = models.IntegerField(default=3)
    current_round_num = models.IntegerField(default=0)
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default=PHASE_LOBBY)
    
    smart_ai_enabled = models.BooleanField(default=True)
    roast_mode_enabled = models.BooleanField(default=True)
    custom_theme = models.CharField(max_length=100, blank=True, default='')

    current_drawer_nickname = models.CharField(max_length=50, blank=True, default='')
    current_word = models.CharField(max_length=100, blank=True, default='')
    word_hint = models.CharField(max_length=100, blank=True, default='')
    
    timer_start_ms = models.BigIntegerField(default=0)
    timer_duration_sec = models.IntegerField(default=80)
    
    turn_order = models.JSONField(default=list)
    current_turn_index = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.code} ({self.phase} - AI:{self.smart_ai_enabled} Roast:{self.roast_mode_enabled})"


class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    session_id = models.CharField(max_length=100)
    nickname = models.CharField(max_length=50)
    is_host = models.BooleanField(default=False)
    is_connected = models.BooleanField(default=True)
    is_ai = models.BooleanField(default=False)
    
    score = models.IntegerField(default=0)
    has_guessed = models.BooleanField(default=False)
    guess_order = models.IntegerField(default=0)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('room', 'nickname')

    def __str__(self):
        return f"{self.nickname} ({'AI' if self.is_ai else 'User'} - {self.score} pts) in {self.room.code}"


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
    drawer_nickname = models.CharField(max_length=50, blank=True, default='')
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


class Word(models.Model):
    DIFFICULTY_EASY = 'easy'
    DIFFICULTY_MEDIUM = 'medium'
    DIFFICULTY_HARD = 'hard'

    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, 'Easy'),
        (DIFFICULTY_MEDIUM, 'Medium'),
        (DIFFICULTY_HARD, 'Hard'),
    ]

    word = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_EASY)
    category = models.CharField(max_length=50, default='general')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name='custom_words')

    def __str__(self):
        return f"{self.word} ({self.difficulty} - {self.category})"
