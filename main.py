from flask import Flask, request, send_file, jsonify
from pathlib import Path
from tara_core import detect_keywords, requestResponse
from pydub import AudioSegment
from flask_cors import CORS
import traceback
import os

app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)  # ✅ allows access from webapp

# Directories
UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)
VOICES_DIR = Path('static/voices')
VOICES_DIR.mkdir(parents=True, exist_ok=True)

# Activation & termination voices
ACTIVATED_VOICE = VOICES_DIR / 'activated.wav'
TERMINATED_VOICE = VOICES_DIR / 'terminated.wav'

# Initialize Tara backend
api = requestResponse()
user_id = None
conversation_id = None
active = False  # Tara listens only after trigger word


def convert_to_wav(input_path: Path, output_path: Path):
    """Convert uploaded audio to mono 16kHz WAV"""
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format='wav')


@app.route('/')
def index():
    """Serve main web UI"""
    return app.send_static_file('index.html')


@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    """Handle Tara's speech input & AI responses."""
    global user_id, conversation_id, active
    try:
        # 1️⃣ Validate upload
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio uploaded'}), 400

        f = request.files['audio']
        orig_path = UPLOAD_DIR / f.filename
        f.save(orig_path)

        # 2️⃣ Convert to WAV
        wav_path = UPLOAD_DIR / 'recorded_audio.wav'
        convert_to_wav(orig_path, wav_path)

        # 3️⃣ Detect trigger/termination
        keyword = detect_keywords(str(wav_path))

        if not active:
            if keyword == 'TRIGGER':
                active = True
                print("✨ Tara activated")
                if ACTIVATED_VOICE.exists():
                    return send_file(str(ACTIVATED_VOICE), mimetype='audio/wav')
                else:
                    return jsonify({'status': 'activated'})
            else:
                return jsonify({'status': 'ignored'})

        # 🌙 Termination
        if keyword == 'TERMINATE':
            active = False
            print("🌙 Tara terminated")
            if TERMINATED_VOICE.exists():
                return send_file(str(TERMINATED_VOICE), mimetype='audio/wav')
            else:
                return jsonify({'status': 'terminated'})

        # 🧠 AI Response
        response = api.send_audio(str(wav_path), user_id, conversation_id)
        if response:
            user_id = response.get('userId')
            conversation_id = response.get('conversationId')
            resp_file = Path('response_audio.wav')
            if resp_file.exists():
                return send_file(str(resp_file), mimetype='audio/wav')
            else:
                return jsonify({'status': 'no_audio'}), 500
        else:
            return jsonify({'error': 'backend failed'}), 500

    except Exception as e:
        print("❌ Error:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask_without_audio():
    """Text fallback endpoint."""
    global user_id, conversation_id, active
    if not active:
        return jsonify({'error': 'Tara inactive'}), 400

    response = api.ask_question(user_id, conversation_id)
    if response:
        user_id = response.get('userId')
        conversation_id = response.get('conversationId')
        resp_file = Path('response_audio.wav')
        if resp_file.exists():
            return send_file(str(resp_file), mimetype='audio/wav')
        else:
            return jsonify({'status': 'no_audio'}), 500
    else:
        return jsonify({'error': 'backend failed'}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Tara backend running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
