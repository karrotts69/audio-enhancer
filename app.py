from flask import Flask, request, send_file
from flask_cors import CORS
import os
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://karrotts69.github.io"}})

@app.route('/api/process', methods=['POST'])
def process_audio():
    # Get file and form data
    file = request.files['file']
    drum_style = request.form['drumStyle']
    bass_style = request.form['bassStyle']
    drum_intensity = float(request.form['drumIntensity']) / 100  # Scale 0-1
    bass_intensity = float(request.form['bassIntensity']) / 100  # Scale 0-1

    # Validate file
    if not file.filename.endswith(('.mp3', '.wav')):
        return {"error": "Only MP3 and WAV files are supported"}, 400

    # Save uploaded file temporarily
    input_path = f"temp_{file.filename}"
    file.save(input_path)

    # Load audio
    y, sr = librosa.load(input_path, sr=None)

    # Placeholder processing (replace with your AI logic)
    t = np.linspace(0, len(y) / sr, len(y))
    bass_freq = 60 if bass_style == "fingered" else 40  # Vary by style
    bass = bass_intensity * np.sin(2 * np.pi * bass_freq * t)
    drums = drum_intensity * np.random.normal(0, 0.1, len(y)) if drum_style == "rock" else \
            drum_intensity * np.random.normal(0, 0.05, len(y))  # Vary by style
    processed_y = y + bass + drums

    # Save processed audio as WAV first
    output_path = f"processed_{file.filename}"
    temp_wav_path = output_path if file.filename.endswith('.wav') else output_path.replace('.mp3', '.wav')
    sf.write(temp_wav_path, processed_y, sr)

    # Convert to MP3 if input was MP3
    if file.filename.endswith('.mp3'):
        wav_audio = AudioSegment.from_wav(temp_wav_path)
        output_path_mp3 = output_path  # Keep original .mp3 extension
        wav_audio.export(output_path_mp3, format='mp3')
        output_path = output_path_mp3
        mime_type = 'audio/mpeg'
        os.remove(temp_wav_path)  # Clean up temp WAV
    else:
        output_path = temp_wav_path
        mime_type = 'audio/wav'

    # Clean up input file
    os.remove(input_path)

    # Send file back
    response = send_file(output_path, mimetype=mime_type)

    # Clean up output file after sending
    @app.after_request
    def cleanup(response):
        if os.path.exists(output_path):
            os.remove(output_path)
        return response

    return response

@app.route('/api/health', methods=['GET'])
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)