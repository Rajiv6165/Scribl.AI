from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField, Subquery, OuterRef
from django.db.models.functions import TruncDate
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import Room, Player, Round, Guess, Word


class AnalyticsSummaryView(APIView):
    """
    Returns aggregated analytics for the game.
    Results are cached to avoid hammering the database.
    """
    
    @method_decorator(cache_page(60))
    def get(self, request, *args, **kwargs):
        # 1. Most-frequently-drawn words
        top_words = list(
            Round.objects.filter(status=Round.STATUS_COMPLETED)
            .exclude(word='')
            .values('word')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # 2. Average time-to-correct-guess per word difficulty tier
        # Subquery to find the difficulty of the word in the round
        difficulty_sq = Word.objects.filter(
            word=OuterRef('round__word')
        ).values('difficulty')[:1]
        
        avg_times_qs = (
            Guess.objects.filter(is_correct=True)
            .annotate(
                difficulty=Subquery(difficulty_sq),
                duration=ExpressionWrapper(F('created_at') - F('round__started_at'), output_field=DurationField())
            )
            .values('difficulty')
            .annotate(avg_duration=Avg('duration'))
        )
        
        avg_times_data = []
        for row in avg_times_qs:
            diff = row['difficulty'] or 'unknown'
            # Convert timedelta to seconds
            seconds = row['avg_duration'].total_seconds() if row['avg_duration'] else 0
            avg_times_data.append({'difficulty': diff, 'avg_seconds': round(seconds, 2)})

        # 3. Scribl-Bot guess accuracy vs human guess accuracy
        # Subquery to find if the player who made the guess is an AI
        is_ai_sq = Player.objects.filter(
            room=OuterRef('round__room'),
            nickname=OuterRef('player_nickname')
        ).values('is_ai')[:1]
        
        accuracy_qs = (
            Guess.objects
            .annotate(is_ai=Subquery(is_ai_sq))
            .values('is_ai')
            .annotate(
                total=Count('id'),
                correct=Count('id', filter=Q(is_correct=True))
            )
        )
        
        accuracy_data = []
        for row in accuracy_qs:
            total = row['total']
            correct = row['correct']
            rate = (correct / total) if total > 0 else 0
            accuracy_data.append({
                'is_ai': bool(row['is_ai']),
                'total_guesses': total,
                'correct_guesses': correct,
                'accuracy_rate': round(rate, 4)
            })

        # 4. Anti-cheat flag frequency over time (by date)
        # We'll combine player flags and round flags per date
        player_flags = list(
            Player.objects.filter(is_flagged=True)
            .annotate(date=TruncDate('joined_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        round_flags = list(
            Round.objects.filter(is_flagged=True)
            .annotate(date=TruncDate('started_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        # Merge frequencies
        flags_by_date = {}
        for row in player_flags:
            if row['date']:
                d = str(row['date'])
                flags_by_date[d] = flags_by_date.get(d, 0) + row['count']
        for row in round_flags:
            if row['date']:
                d = str(row['date'])
                flags_by_date[d] = flags_by_date.get(d, 0) + row['count']
            
        flags_timeline = [
            {'date': k, 'flags': v} for k, v in sorted(flags_by_date.items())
        ]

        # 5. Game mode popularity (rounds played per mode)
        mode_popularity = list(
            Round.objects.values(mode=F('room__game_mode'))
            .annotate(rounds_played=Count('id'))
            .order_by('-rounds_played')
        )

        return Response({
            'most_drawn_words': top_words,
            'avg_guess_times': avg_times_data,
            'accuracy': accuracy_data,
            'flags_timeline': flags_timeline,
            'mode_popularity': mode_popularity
        })
