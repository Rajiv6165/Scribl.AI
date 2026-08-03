import io
import os
import re
import json
import logging
import base64
import random
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class AIService:

    @staticmethod
    def render_strokes_to_image(stroke_events: list, width: int = 800, height: int = 600) -> bytes:
        """Renders stroke events onto a 2D canvas PNG image in memory using Pillow."""
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        for event in stroke_events:
            action_type = event.get('action_type', 'stroke')
            payload = event.get('payload', {})

            if action_type == 'clear':
                draw.rectangle([(0, 0), (width, height)], fill="white")
                continue

            if action_type == 'undo':
                # Simplified undo: full history replay is handled by caller passing clean history
                continue

            if action_type == 'stroke':
                points = payload.get('points', [])
                if not points:
                    continue

                color = payload.get('color', '#000000')
                brush_size = max(1, int(payload.get('brushSize', 6)))
                is_eraser = payload.get('isEraser', False)

                draw_color = "white" if is_eraser else color

                if len(points) == 1:
                    pt = points[0]
                    r = brush_size / 2.0
                    draw.ellipse([pt['x'] - r, pt['y'] - r, pt['x'] + r, pt['y'] + r], fill=draw_color)
                else:
                    coords = [(p['x'], p['y']) for p in points]
                    draw.line(coords, fill=draw_color, width=brush_size, joint='round')

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def predict_drawing_guess(stroke_events: list, word_hint: str, category: str = "general") -> list:
        """Queries Gemini Vision API with canvas snapshot to generate human-like guess candidates."""
        if not stroke_events:
            return []

        api_key = os.environ.get('GEMINI_API_KEY', '').strip()

        # Render stroke history to PNG image bytes
        image_bytes = AIService.render_strokes_to_image(stroke_events)

        if not api_key:
            logger.warning("GEMINI_API_KEY not configured. Falling back to heuristic guesser.")
            return AIService._fallback_heuristic_guesses(word_hint)

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = (
                f"You are a player in a fast-paced multiplayer drawing and guessing game. "
                f"Examine this canvas drawing. The secret word has this hint/length structure: '{word_hint}'. "
                f"Guess what item or concept is being drawn in this image. "
                f"Respond ONLY with your top 3 single-word guesses separated by commas. "
                f"Do not include numbers, explanation, or punctuation."
            )

            pil_image = Image.open(io.BytesIO(image_bytes))
            response = model.generate_content([prompt, pil_image])

            if response and response.text:
                raw_text = response.text.strip()
                candidates = [
                    re.sub(r'[^A-Z]', '', word.strip().upper())
                    for word in raw_text.split(',')
                    if word.strip()
                ]
                return [c for c in candidates if len(c) >= 2][:3]

        except Exception as err:
            logger.error(f"Gemini API call failed: {err}. Skipping AI guess attempt gracefully.")
            return AIService._fallback_heuristic_guesses(word_hint)

        return []

    @staticmethod
    def _fallback_heuristic_guesses(word_hint: str) -> list:
        """Resilient fallback when Gemini API key is unconfigured or rate limited."""
        hint_clean = word_hint.replace(' ', '')
        length = len(hint_clean) if hint_clean else 5

        sample_bank = {
            3: ["CAT", "DOG", "SUN", "BUS", "HAT", "BOX"],
            4: ["FISH", "BIRD", "TREE", "BOOK", "STAR", "CAKE", "FROG"],
            5: ["HOUSE", "APPLE", "RACKET", "PLANT", "CLOCK", "CHAIR"],
            6: ["BANANA", "GUITAR", "CAMERA", "TURTLE", "FLOWER", "RABBIT"],
            7: ["PENGUIN", "GIRAFFE", "DOLPHIN", "RAINBOW", "BALLOON", "BURGER"],
            8: ["ELEPHANT", "AIRPLANE", "UMBRELLA", "VOLCANO", "KEYBOARD"],
        }
        candidates = sample_bank.get(length, ["HOUSE", "BANANA", "ELEPHANT"])
        return random.sample(candidates, min(len(candidates), 2))

    @staticmethod
    def calculate_ai_guess_delay(room) -> int:
        """Adapts AI guess delay dynamically based on human player performance in current round."""
        from .models import Player

        human_players = Player.objects.filter(room=room, is_ai=False, is_connected=True)
        total_humans = human_players.count()
        guessed_humans = human_players.filter(has_guessed=True).count()

        if total_humans == 0:
            return 8

        # Ratio of human players who have guessed
        ratio = guessed_humans / float(total_humans)

        if ratio == 0:
            # Humans are struggling / haven't guessed yet -> AI delays 14-20 seconds
            return random.randint(14, 20)
        elif ratio < 0.5:
            # Moderate speed -> AI delays 10-14 seconds
            return random.randint(10, 14)
        else:
            # Humans are fast / dominating -> AI responds quicker 6-9 seconds
            return random.randint(6, 9)

    @staticmethod
    def generate_theme_word_pack(theme: str) -> list:
        """Generates ~30 themed drawing words using LLM with regex validation & fallback."""
        theme_clean = theme.strip()
        if not theme_clean:
            return []

        api_key = os.environ.get('GEMINI_API_KEY', '').strip()

        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')

                prompt = (
                    f"Generate a list of 30 fun, drawable words or short terms for a Pictionary drawing game "
                    f"under the theme: '{theme_clean}'. "
                    f"Respond ONLY with a JSON array of uppercase strings e.g. [\"WORD1\", \"WORD2\"]. "
                    f"Each word should be 3 to 16 characters long and easy to draw."
                )

                response = model.generate_content(prompt)
                if response and response.text:
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        raw_list = json.loads(match.group(0))
                        cleaned = []
                        for item in raw_list:
                            word = re.sub(r'[^A-Z]', '', str(item).upper().strip())
                            if 3 <= len(word) <= 18 and word not in cleaned:
                                cleaned.append(word)
                        if len(cleaned) >= 10:
                            return cleaned[:30]
            except Exception as err:
                logger.error(f"Failed to generate theme word pack via Gemini: {err}")

        # Fallback theme word pack generator
        theme_upper = theme_clean.upper()
        if "BOLLYWOOD" in theme_upper or "MOVIE" in theme_upper:
            return ["SHOLAY", "DANGAL", "DDLJ", "LAGAAN", "KABIR", "BAHUBALI", "AVATAR", "TITANIC", "JOKER", "INCEPTION", "GLADIATOR", "MATRIX"]
        elif "STARTUP" in theme_upper or "TECH" in theme_upper:
            return ["UNICORN", "PITCH", "VC", "FOUNDER", "PIVOT", "BLOCKCHAIN", "CLOUD", "ROBOT", "SERVER", "ALGORITHM", "PAYMENT", "DATABASE"]
        elif "SUPERHERO" in theme_upper or "MARVEL" in theme_upper:
            return ["BATMAN", "SPIDERMAN", "THOR", "IRONMAN", "HULK", "SUPERMAN", "SHIELD", "CAPE", "MASK", "HAMMER", "PORTAL", "MUTANT"]

        # Default themed fallback list
        return [f"{theme_clean.upper()}_{i}" for i in range(1, 15)]
