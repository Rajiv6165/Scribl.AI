from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rooms.analytics_views import AnalyticsSummaryView

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/rooms/', include('rooms.urls')),
    path('api/analytics/summary/', AnalyticsSummaryView.as_view(), name='analytics-summary'),
    path('api/health/', health_check),
]
