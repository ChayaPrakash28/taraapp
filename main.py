from flask import Flask, request, send_file, jsonify
from pathlib import Path
from tara_core import detect_keywords, requestResponse
from pydub import AudioSegment

app = Flask(__name__, static_folder='static', static_url_path='/')

# Serve the index.html directly
@app.route('/')
def index():
    return app.send_static_file('index.html')

UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

VOICES_DIR = Path('static/voices')
ACTIVATED_VOICE = VOICES_DIR / 'activated.wav'
TERMINATED_VOICE = VOICES_DIR / 'terminated.wav'

api = requestResponse()
user_id = None
conversation_id = None
active = False  # Tara only responds after trigger word


def convert_to_wav(input_path: Path, output_path: Path):
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format='wav')


@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    global user_id, conversation_id, active

    # expect multipart form 'audio' file
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio uploaded'}), 400

    f = request.files['audio']
    orig_path = UPLOAD_DIR / f.filename
    f.save(orig_path)

    wav_path = UPLOAD_DIR / 'recorded_audio.wav'
    try:
        convert_to_wav(orig_path, wav_path)
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {e}'}), 500

    # detect trigger/termination using english-only recognizer
    keyword = detect_keywords(str(wav_path))

    if not active:
        if keyword == 'TRIGGER':
            active = True
            # return activation audio if available
            if ACTIVATED_VOICE.exists():
                return send_file(str(ACTIVATED_VOICE), mimetype='audio/wav')
            else:
                return jsonify({'status': 'activated'})
        else:
            return jsonify({'status': 'ignored'})

    # if active:
    if keyword == 'TERMINATE':
        active = False
        if TERMINATED_VOICE.exists():
            return send_file(str(TERMINATED_VOICE), mimetype='audio/wav')
        else:
            return jsonify({'status': 'terminated'})

    # normal conversation: forward to AI backend, which returns base64 audio
    response = api.send_audio(str(wav_path), user_id, conversation_id)
    if response:
        user_id = response.get('userId')
        conversation_id = response.get('conversationId')
        # api.save_base64_audio_file will have created response_audio.wav
        resp_file = Path('response_audio.wav')
        if resp_file.exists():
            return send_file(str(resp_file), mimetype='audio/wav')
        else:
            return jsonify({'status': 'no_audio', 'message': 'No audio returned'}), 500
    else:
        return jsonify({'error': 'backend failed'}), 500


@app.route('/ask', methods=['POST'])
def ask_without_audio():
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
    app.run(host='0.0.0.0', port=5000, debug=True)
