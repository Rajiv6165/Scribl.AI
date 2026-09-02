from rest_framework import serializers
from .models import Room, Player, StrokeEvent


class RoomCreateSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=50)
    max_players = serializers.IntegerField(default=10, min_value=2, max_value=20)
    game_mode = serializers.CharField(max_length=20, default='classic')


class RoomJoinSerializer(serializers.Serializer):
    room_code = serializers.CharField(max_length=8)
    nickname = serializers.CharField(max_length=50)


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['nickname', 'is_host', 'is_connected', 'joined_at']


class RoomDetailSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = ['code', 'host_name', 'max_players', 'status', 'created_at', 'players']


class StrokeEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrokeEvent
        fields = ['sequence_number', 'player_nickname', 'action_type', 'payload', 'created_at']
