import speech_recognition as sr
import pybase64
import requests
from pathlib import Path

TRIGGERS = [
    "hello tara", "hey tara", "hi tara", "tara let's play", "tara story time",
    "wake up tara", "ok tara", "tara start", "listen tara", "tara are you there",
    "tara talk to me", "tara activate", "tara can you hear me"
]

TERMINATORS = [
    "goodbye tara", "sleep now tara", "that's all tara", "stop tara", "the end tara",
    "tara bye", "tara stop listening", "tara exit", "tara shutdown", "tara go to sleep",
    "tara stop", "tara finish", "tara end conversation"
]

def detect_keywords(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    try:
        # Force English-only recognition
        text = recognizer.recognize_google(audio, language="en-IN").lower()

        print(f"Detected (EN): {text}")
        for t in TRIGGERS:
            if t in text:
                print("✅ Trigger")
                return "TRIGGER"
        for t in TERMINATORS:
            if t in text:
                print("🛑 Terminate")
                return "TERMINATE"
    except sr.UnknownValueError:
        print("Could not understand.")
    except sr.RequestError as e:
        print(f"Recognition request error: {e}")
    return None


class requestResponse:
    def __init__(self):
        self.api_url = "https://voice-bot-backend-147374697476.asia-south1.run.app/api/ai"

    def create_base64_audio_file(self, audio_path):
        with open(audio_path, "rb") as f:
            return pybase64.b64encode(f.read()).decode('utf-8')

    def save_base64_audio_file(self, b64_data, output_path):
        audio_bytes = pybase64.b64decode(b64_data)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, 'wb') as f:
            f.write(audio_bytes)
        print(f"Saved audio to {output_path}")

    def send_audio(self, audio_path, user_id, conversation_id):
        data = {
            'audioData': self.create_base64_audio_file(audio_path),
            'userId': user_id,
            'conversationId': conversation_id,
            'language': 'en',
            'api_key': 'be3a0d00-c7ff-4537-8cbb-bed8090f8b5b'
        }

        try:
            res = requests.post(f"{self.api_url}/answer-query", json=data)
            if res.status_code == 201:
                print("Sent audio to AI.")
                d = res.json()
                audioData = d.get('audioFile')
                if audioData:
                    self.save_base64_audio_file(audioData, "response_audio.wav")
                return d
            else:
                print("AI backend failed:", res.status_code, res.text)
                return None
        except Exception as e:
            print("Error sending to AI:", e)
            return None

    def ask_question(self, user_id, conversation_id):
        data = {
            'audioData': None,
            'userId': user_id,
            'conversationId': conversation_id,
            'language': 'en',
            'api_key': 'be3a0d00-c7ff-4537-8cbb-bed8090f8b5b'
        }
        try:
            res = requests.post(f"{self.api_url}/answer-query", json=data)
            if res.status_code == 201:
                d = res.json()
                audioData = d.get('audioFile')
                if audioData:
                    self.save_base64_audio_file(audioData, "response_audio.wav")
                return d
            else:
                print("AI ask failed:", res.status_code, res.text)
                return None
        except Exception as e:
            print("Error during ask:", e)
            return None
