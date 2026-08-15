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
    def generate_drawing_roast(stroke_events: list, revealed_word: str) -> str:
        """Generates a short, PG-rated, good-natured AI roast/critique of the drawing."""
        api_key = os.environ.get('GEMINI_API_KEY', '').strip()
        
        fallback_roasts = [
            f"A bold, avant-garde rendition of '{revealed_word}'! It definitely has strong abstract energy.",
            f"Minimalist, expressive, and truly unforgettable! Is that a '{revealed_word}' or modern art?",
            f"The artist clearly has a unique vision for '{revealed_word}'. Monet would be intrigued!",
            f"Captures the essence of '{revealed_word}' with pure artistic bravery!"
        ]

        if not api_key or not stroke_events:
            return random.choice(fallback_roasts)

        try:
            image_bytes = AIService.render_strokes_to_image(stroke_events)
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = (
                f"You are a hilarious, friendly AI game master in a drawing game. "
                f"Examine this canvas drawing which was supposed to be '{revealed_word}'. "
                f"Provide a short, funny, PG-rated, good-natured 2-sentence roast/critique of the drawing. "
                f"Keep it light, kind-spirited, and appropriate for all ages — no mean or harmful put-downs."
            )

            pil_image = Image.open(io.BytesIO(image_bytes))
            response = model.generate_content([prompt, pil_image])

            if response and response.text:
                return response.text.strip()

        except Exception as err:
            logger.error(f"Failed to generate AI drawing roast via Gemini: {err}")

        return random.choice(fallback_roasts)

    @staticmethod
    def generate_match_highlight_recap(revealed_word: str, drawer_nickname: str) -> str:
        """Generates a short, fun AI match highlight card for the final game over results screen."""
        api_key = os.environ.get('GEMINI_API_KEY', '').strip()

        fallback_recaps = [
            f"🎨 Match Highlight: Picasso of the match award goes to {drawer_nickname} for their iconic '{revealed_word}'!",
            f"✨ Match Highlight: Most creative interpretation goes to {drawer_nickname}'s drawing of '{revealed_word}'!",
            f"🏆 Match Highlight: {drawer_nickname} stole the spotlight with their unforgettable '{revealed_word}' drawing!"
        ]

        if not api_key:
            return random.choice(fallback_recaps)

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = (
                f"Write a short 2-sentence fun AI Match Highlight recap for a drawing game. "
                f"Award {drawer_nickname} a funny, lighthearted trophy title for their drawing of '{revealed_word}'. "
                f"Keep it positive, PG-rated, and humorous."
            )

            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()

        except Exception as err:
            logger.error(f"Failed to generate match highlight recap via Gemini: {err}")

        return random.choice(fallback_recaps)

    @staticmethod
    def generate_spectator_commentary(event_type: str, event_data: dict) -> str:
        """
        Generates short live play-by-play commentary for spectators based ONLY on public event data.
        NEVER receives or uses the secret word to prevent spoilers.
        """
        time_left = event_data.get('time_left', 0)
        drawer_name = event_data.get('drawer', 'The drawer')
        guesser_name = event_data.get('guesser', 'A player')
        stroke_count = event_data.get('stroke_count', 0)
        round_num = event_data.get('round_num', 1)

        fallbacks = {
            'ROUND_START': [
                f"🎙️ Round {round_num} is off! {drawer_name} takes the canvas!",
                f"🎙️ Here we go! {drawer_name} is stepping up to draw in Round {round_num}!",
                f"🎙️ Round {round_num} begins! Let's see what {drawer_name} has in store for us!"
            ],
            'TIME_MILESTONE': [
                f"⏰ Just {time_left} seconds remaining! The pressure is rising on the canvas!",
                f"⚡ {time_left}s left on the clock! Will anyone figure it out in time?",
                f"⏳ Clock is ticking down: {time_left} seconds left for the remaining guessers!"
            ],
            'CANVAS_PROGRESS': [
                f"🎨 The drawing is really taking shape now! ({stroke_count} strokes placed)",
                f"🖌️ Bold strokes coming down from {drawer_name}! The crowd is watching closely!",
                f"✨ Fast pace on the canvas! {drawer_name} is moving quickly!"
            ],
            'CORRECT_GUESS': [
                f"🎉 BOOM! {guesser_name} cracked the drawing with {time_left} seconds left!",
                f"🔥 What a read! {guesser_name} jumps onto the scoreboard!",
                f"⚡ Lightning quick guess from {guesser_name}! Score update incoming!"
            ],
            'ROUND_END': [
                f"🏁 Round {round_num} comes to a close! What a performance by {drawer_name}!",
                f"👏 Time's up! That wraps up Round {round_num}!",
                f"🏆 End of Round {round_num}! Let's check the updated standings!"
            ]
        }

        fallback_list = fallbacks.get(event_type, fallbacks['CANVAS_PROGRESS'])
        default_commentary = random.choice(fallback_list)

        api_key = os.environ.get('GEMINI_API_KEY', '').strip()
        if not api_key:
            return default_commentary

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = (
                f"You are a hype esports commentator shoutcasting a drawing game live for spectators. "
                f"Generate a single short 1-sentence (under 15 words) energetic play-by-play commentary line for this event: "
                f"Event Type: {event_type}, Time Left: {time_left}s, Drawer: '{drawer_name}', Guesser: '{guesser_name}', Strokes: {stroke_count}. "
                f"CRITICAL: Do NOT guess or mention any secret drawing words. Keep it strictly focused on the game action, timer, and excitement."
            )

            response = model.generate_content(prompt)
            if response and response.text:
                res_text = response.text.strip().replace('\n', ' ')
                if res_text:
                    return f"🎙️ {res_text}"
        except Exception as err:
            logger.error(f"Failed to generate spectator commentary via Gemini: {err}")

        return default_commentary

    @staticmethod
    def _fallback_heuristic_guesses(word_hint: str) -> list:
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
        from .models import Player

        human_players = Player.objects.filter(room=room, is_ai=False, is_connected=True)
        total_humans = human_players.count()
        guessed_humans = human_players.filter(has_guessed=True).count()

        if total_humans == 0:
            return 8

        ratio = guessed_humans / float(total_humans)

        if ratio == 0:
            return random.randint(14, 20)
        elif ratio < 0.5:
            return random.randint(10, 14)
        else:
            return random.randint(6, 9)

    @staticmethod
    def generate_theme_word_pack(theme: str) -> list:
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

        theme_upper = theme_clean.upper()
        if "BOLLYWOOD" in theme_upper or "MOVIE" in theme_upper:
            return ["SHOLAY", "DANGAL", "DDLJ", "LAGAAN", "KABIR", "BAHUBALI", "AVATAR", "TITANIC", "JOKER", "INCEPTION", "GLADIATOR", "MATRIX"]
        elif "STARTUP" in theme_upper or "TECH" in theme_upper:
            return ["UNICORN", "PITCH", "VC", "FOUNDER", "PIVOT", "BLOCKCHAIN", "CLOUD", "ROBOT", "SERVER", "ALGORITHM", "PAYMENT", "DATABASE"]
        elif "SUPERHERO" in theme_upper or "MARVEL" in theme_upper:
            return ["BATMAN", "SPIDERMAN", "THOR", "IRONMAN", "HULK", "SUPERMAN", "SHIELD", "CAPE", "MASK", "HAMMER", "PORTAL", "MUTANT"]

        return [f"{theme_clean.upper()}_{i}" for i in range(1, 15)]
