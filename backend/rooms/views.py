from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RoomCreateSerializer, RoomJoinSerializer, RoomDetailSerializer
from .services import RoomService
from .models import Room


class CreateRoomView(APIView):
    def post(self, request):
        serializer = RoomCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        nickname = serializer.validated_data['nickname']
        max_players = serializer.validated_data.get('max_players', 10)
        smart_ai_enabled = request.data.get('smart_ai_enabled', True)

        try:
            result = RoomService.create_room(
                host_nickname=nickname,
                max_players=max_players,
                smart_ai_enabled=smart_ai_enabled
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)


class JoinRoomView(APIView):
    def post(self, request):
        serializer = RoomJoinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        room_code = serializer.validated_data['room_code']
        nickname = serializer.validated_data['nickname']
        session_id = request.data.get('session_id', 'rest_client')

        try:
            result = RoomService.join_room(room_code=room_code, player_nickname=nickname, session_id=session_id)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as err:
            return Response({'error': str(err)}, status=status.HTTP_404_NOT_FOUND)


class GenerateWordPackView(APIView):
    def post(self, request):
        room_code = request.data.get('room_code', '')
        theme = request.data.get('theme', '')

        if not room_code or not theme:
            return Response({'error': 'room_code and theme are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = RoomService.generate_and_apply_custom_word_pack(room_code=room_code, theme=theme)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)


class RoomDetailView(APIView):
    def get(self, request, code):
        try:
            room = Room.objects.get(code=code.upper())
            serializer = RoomDetailSerializer(room)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            return Response({'error': f'Room {code} not found'}, status=status.HTTP_404_NOT_FOUND)


class RoomReplayView(APIView):
    def get(self, request, code):
        try:
            replay_data = RoomService.get_replay_data(room_code=code)
            return Response(replay_data, status=status.HTTP_200_OK)
        except ValueError as err:
            return Response({'error': str(err)}, status=status.HTTP_404_NOT_FOUND)
