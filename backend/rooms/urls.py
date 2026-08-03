from django.urls import path
from .views import CreateRoomView, JoinRoomView, RoomDetailView, RoomReplayView, GenerateWordPackView

urlpatterns = [
    path('create/', CreateRoomView.as_view(), name='room-create'),
    path('join/', JoinRoomView.as_view(), name='room-join'),
    path('generate-word-pack/', GenerateWordPackView.as_view(), name='generate-word-pack'),
    path('<str:code>/', RoomDetailView.as_view(), name='room-detail'),
    path('<str:code>/replay/', RoomReplayView.as_view(), name='room-replay'),
]
