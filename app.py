from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import logging

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://karrotts69.github.io"}})
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

@app.route('/api/process', methods=['POST'])
def process_audio():
    try:
        logger.info("Processing started")
        file = request.files['file']
        drum_style = request.form['drumStyle']
        bass_style = request.form['bassStyle']
        drum_intensity = float(request.form['drumIntensity']) / 100
        bass_intensity = float(request.form['bassIntensity']) / 100

        if not file.filename.endswith(('.mp3', '.wav')):
            logger.error("Invalid file type")
            return jsonify({"error": "Only MP3 and WAV files supported"}), 400

        input_path = f"temp_{file.filename}"
        logger.info(f"Saving file to {input_path}")
        file.save(input_path)

        logger.info("Loading audio with librosa")
        y, sr = librosa.load(input_path, sr=None)

        t = np.linspace(0, len(y) / sr, len(y))
        bass_freq = 60 if bass_style == "fingered" else 40
        bass = bass_intensity * np.sin(2 * np.pi * bass_freq * t)
        drums = drum_intensity * np.random.normal(0, 0.1, len(y)) if drum_style == "rock" else \
                drum_intensity * np.random.normal(0, 0.05, len(y))
        processed_y = y + bass + drums

        output_path = f"processed_{file.filename}"
        temp_wav_path = output_path if file.filename.endswith('.wav') else output_path.replace('.mp3', '.wav')
        logger.info(f"Writing WAV to {temp_wav_path}")
        sf.write(temp_wav_path, processed_y, sr)

        if file.filename.endswith('.mp3'):
            logger.info("Converting to MP3")
            wav_audio = AudioSegment.from_wav(temp_wav_path)
            output_path_mp3 = output_path
            wav_audio.export(output_path_mp3, format='mp3')
            output_path = output_path_mp3
            mime_type = 'audio/mpeg'
            os.remove(temp_wav_path)
        else:
            output_path = temp_wav_path
            mime_type = 'audio/wav'

        os.remove(input_path)
        logger.info(f"Sending file: {output_path}")
        response = send_file(output_path, mimetype=mime_type)
        os.remove(output_path)
        return response

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)