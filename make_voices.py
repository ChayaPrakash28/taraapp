from gtts import gTTS
from pathlib import Path

# Make sure the folder exists
voices_dir = Path('static/voices')
voices_dir.mkdir(parents=True, exist_ok=True)

# Generate activation voice
gTTS("Hi there! I'm awake!").save(voices_dir / "activated.wav")

# Generate termination voice
gTTS("Okay! Going to sleep now. Bye!").save(voices_dir / "terminated.wav")

print("✅ Activation and termination voice files created in static/voices/")
