import speech_recognition as sr
import pybase64
import requests
from pathlib import Path

# 🔊 Trigger and termination keywords (English only)
TRIGGERS = [
    "hello tara", "hey tara", "hi tara", "tara let's play",
    "tara story time", "wake up tara", "ok tara", "tara start",
    "listen tara", "tara are you there"
]

TERMINATORS = [
    "goodbye tara", "sleep now tara", "that's all tara",
    "stop tara", "the end tara", "tara bye", "tara stop listening",
    "tara exit", "tara shutdown"
]


def detect_keywords(audio_path):
    """Detect trigger or termination keywords in recorded audio."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language="en-US").lower()
        print(f"🗣️ Recognized Speech: {text}")

        for t in TRIGGERS:
            if t in text:
                print("✅ Trigger detected.")
                return "TRIGGER"

        for t in TERMINATORS:
            if t in text:
                print("🛑 Termination detected.")
                return "TERMINATE"

    except sr.UnknownValueError:
        print("❌ Could not understand audio.")
    except sr.RequestError as e:
        print(f"⚠️ Speech recognition API error: {e}")

    return None


class requestResponse:
    """Handles communication with Tara AI backend."""

    def __init__(self):
        self.api_url = "https://voice-bot-backend-147374697476.asia-south1.run.app/api/ai"

    def create_base64_audio_file(self, audio_path):
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
        return pybase64.b64encode(audio_data).decode('utf-8')

    def save_base64_audio_file(self, base64_audio_data, output_path):
        """Decode and save AI-generated audio."""
        audio_bytes = pybase64.b64decode(base64_audio_data)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'wb') as audio_file:
            audio_file.write(audio_bytes)
        print(f"🎧 Response audio saved at: {output_path}")

    def send_audio(self, audio_path, user_id, conversation_id):
        """Send audio to AI backend for processing."""
        data = {
            'audioData': self.create_base64_audio_file(audio_path),
            'userId': user_id,
            'conversationId': conversation_id,
            'api_key': 'be3a0d00-c7ff-4537-8cbb-bed8090f8b5b'
        }
        try:
            response = requests.post(f"{self.api_url}/answer-query", json=data)
            if response.status_code == 201:
                data = response.json()
                audioData = data['audioFile']
                self.save_base64_audio_file(audioData, "response_audio.wav")
                print("✅ AI backend responded successfully.")
                return data
            else:
                print(f"⚠️ Backend failed with {response.status_code}")
        except Exception as e:
            print(f"❌ Request error: {e}")
        return None

    def ask_question(self, user_id, conversation_id):
        """Ask follow-up question without new audio."""
        data = {
            'audioData': None,
            'userId': user_id,
            'conversationId': conversation_id,
            'api_key': 'be3a0d00-c7ff-4537-8cbb-bed8090f8b5b'
        }
        try:
            response = requests.post(f"{self.api_url}/answer-query", json=data)
            if response.status_code == 201:
                data = response.json()
                audioData = data['audioFile']
                self.save_base64_audio_file(audioData, "response_audio.wav")
                return data
            else:
                print("⚠️ Backend failed to answer.")
        except Exception as e:
            print(f"❌ Error asking question: {e}")
        return None
