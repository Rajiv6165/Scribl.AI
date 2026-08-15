import math
import logging
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)


class StrokeAnomalyDetector:
    """
    Server-side heuristic analyzer for detecting automated image pasting,
    bot drawing scripts, or synthetic stroke injection in Scribl.AI.
    """

    # Thresholds for anomaly detection
    HIGH_POINT_RATE_THRESHOLD = 120.0  # points per second
    EXTREME_POINT_RATE_THRESHOLD = 250.0  # points per second
    ZERO_DT_RATIO_THRESHOLD = 0.40  # ratio of zero time deltas
    UNIFORM_DT_STD_THRESHOLD = 2.0  # ms standard deviation in timing
    UNIFORM_DIST_STD_THRESHOLD = 0.5  # px standard deviation in distance

    @classmethod
    def analyze_stroke_events(cls, stroke_events: List[Dict[str, Any]]) -> Tuple[bool, float, List[str]]:
        """
        Analyzes a list of stroke events (or a sequence of stroke payloads) for a round or player.
        Returns:
            is_suspicious: bool (True if confidence score >= 0.70)
            score: float (0.0 to 1.0 confidence score)
            reasons: list of detected anomaly descriptions
        """
        if not stroke_events:
            return False, 0.0, []

        all_points = []
        stroke_count = 0

        for event in stroke_events:
            if isinstance(event, dict):
                action = event.get('action_type', 'stroke')
                payload = event.get('payload', {})
            else:
                action = getattr(event, 'action_type', 'stroke')
                payload = getattr(event, 'payload', {})

            if action == 'stroke' and isinstance(payload, dict):
                points = payload.get('points', [])
                if points:
                    all_points.extend(points)
                    stroke_count += 1

        if len(all_points) < 15:
            # Too few points to make a reliable determination
            return False, 0.0, []

        reasons = []
        score_components = []

        # 1. Analyze timing deltas (dt) and Point Rate (points per second)
        timestamps = [p.get('timestamp', 0) for p in all_points if isinstance(p, dict) and 'timestamp' in p]
        
        if len(timestamps) >= 10:
            dts = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
            non_negative_dts = [max(0, dt) for dt in dts]
            
            total_duration_ms = max(1, timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 1
            total_duration_sec = total_duration_ms / 1000.0
            points_per_second = len(all_points) / max(0.1, total_duration_sec)

            if points_per_second > cls.EXTREME_POINT_RATE_THRESHOLD:
                score_components.append(0.60)
                reasons.append(f"Implausibly high point rate ({points_per_second:.1f} pts/sec)")
            elif points_per_second > cls.HIGH_POINT_RATE_THRESHOLD:
                score_components.append(0.35)
                reasons.append(f"Elevated point rate ({points_per_second:.1f} pts/sec)")

            # Zero or near-zero time delta ratio
            zero_dts = sum(1 for dt in non_negative_dts if dt <= 1)
            zero_ratio = zero_dts / float(len(non_negative_dts)) if non_negative_dts else 0

            if zero_ratio > cls.ZERO_DT_RATIO_THRESHOLD:
                score_components.append(0.40)
                reasons.append(f"High ratio of instantaneous point coordinates ({zero_ratio * 100:.1f}%)")

            # Timing variance (std dev of dt)
            if len(non_negative_dts) > 5:
                mean_dt = sum(non_negative_dts) / len(non_negative_dts)
                variance_dt = sum((dt - mean_dt) ** 2 for dt in non_negative_dts) / len(non_negative_dts)
                std_dt = math.sqrt(variance_dt)

                if std_dt < cls.UNIFORM_DT_STD_THRESHOLD and mean_dt <= 5:
                    score_components.append(0.35)
                    reasons.append(f"Unnaturally uniform timing interval (std: {std_dt:.2f}ms)")

        # 2. Analyze spatial distances (dd)
        distances = []
        for i in range(1, len(all_points)):
            p1, p2 = all_points[i - 1], all_points[i]
            if isinstance(p1, dict) and isinstance(p2, dict):
                dx = p2.get('x', 0) - p1.get('x', 0)
                dy = p2.get('y', 0) - p1.get('y', 0)
                dist = math.sqrt(dx * dx + dy * dy)
                distances.append(dist)

        if len(distances) > 10:
            mean_dist = sum(distances) / len(distances)
            variance_dist = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
            std_dist = math.sqrt(variance_dist)

            # Check for perfectly uniform grid step increments
            if std_dist < cls.UNIFORM_DIST_STD_THRESHOLD and mean_dist > 1.0:
                score_components.append(0.40)
                reasons.append(f"Unnaturally uniform spatial step sizes (std: {std_dist:.2f}px)")

            # Check for extreme instantaneous distance leaps
            instant_leaps = sum(1 for d in distances if d > 250.0)
            if instant_leaps > 3:
                score_components.append(0.30)
                reasons.append(f"Multiple extreme instantaneous coordinate leaps ({instant_leaps} leaps > 250px)")

        # Compute overall confidence score capped at 1.0
        overall_score = min(1.0, round(sum(score_components), 2))
        is_suspicious = overall_score >= 0.70

        if is_suspicious:
            logger.warning(f"Anti-Cheat Flagged drawing: score={overall_score}, reasons={reasons}")

        return is_suspicious, overall_score, reasons
