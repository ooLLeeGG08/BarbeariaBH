from flask import Flask, request, jsonify, send_from_directory
import os
import traceback
from dotenv import load_dotenv
load_dotenv()

import requests

import config
from booking import get_available_slots, create_booking
from hairstyle import analyze_hairstyle
from image_validation import detect_image_mime
from ratelimit import RateLimiter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

ALLOWED_STATIC_FILES = {'style.css', 'app.js'}
ALLOWED_STATIC_DIRS = {'images'}

hairstyle_limiter = RateLimiter(max_requests=5, window_seconds=3600)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html', max_age=0)


@app.route('/<path:filename>')
def static_files(filename):
    if filename in ALLOWED_STATIC_FILES:
        return send_from_directory('.', filename, max_age=0)

    parts = filename.split('/')
    if len(parts) == 2 and parts[0] in ALLOWED_STATIC_DIRS:
        return send_from_directory(parts[0], parts[1], max_age=0)

    return jsonify({'error': 'Not found'}), 404


@app.route('/api/services', methods=['GET'])
def services():
    return jsonify({'services': config.SERVICES})


@app.route('/api/slots', methods=['GET'])
def slots():
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'date parameter required'}), 400
    try:
        available = get_available_slots(date)
        return jsonify({'slots': available})
    except Exception as e:
        print(f"Slots error: {e}")
        return jsonify({'error': 'Could not load available slots'}), 500


@app.route('/api/book', methods=['POST'])
def book():
    try:
        data = request.get_json()
        date = data.get('date')
        time = data.get('time')
        service = data.get('service')
        name = data.get('name', '')

        if not all([date, time, service]):
            return jsonify({'error': 'date, time and service are required'}), 400

        event_id = create_booking(date, time, service, name)
        return jsonify({'status': 'success', 'event_id': event_id})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Could not complete booking'}), 500


@app.route('/api/hairstyle', methods=['POST'])
def hairstyle():
    client_ip = request.remote_addr
    if not hairstyle_limiter.allow(client_ip):
        return jsonify({
            'error': 'rate_limited',
            'message': 'Demasiados pedidos. Tenta novamente dentro de uma hora.',
        }), 429

    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded'}), 400

    file = request.files['photo']
    image_bytes = file.read()

    mime_type = detect_image_mime(image_bytes)
    if mime_type is None:
        return jsonify({'error': 'File must be a JPEG, PNG, or WebP image'}), 400

    language = request.form.get('language', 'pt')
    preferences = {
        'maintenance': request.form.get('maintenance'),
        'beard': request.form.get('beard'),
        'length_goal': request.form.get('length_goal'),
    }

    try:
        result = analyze_hairstyle(image_bytes, mime_type, preferences=preferences, language=language)
        return jsonify({'status': 'success', 'analysis': result})
    except requests.exceptions.Timeout:
        return jsonify({'error': 'timeout', 'message': 'A análise demorou demasiado tempo.'}), 504
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            return jsonify({
                'error': 'upstream_rate_limited',
                'message': 'Serviço de análise sobrecarregado. Tenta novamente.',
            }), 503
        print(f"Hairstyle API error: {e}")
        return jsonify({'error': 'analysis_failed', 'message': 'Não foi possível analisar a foto.'}), 502
    except requests.exceptions.ConnectionError:
        return jsonify({
            'error': 'connection_failed',
            'message': 'Falha de ligação ao serviço de análise.',
        }), 502
    except requests.exceptions.RequestException as e:
        print(f"Hairstyle API error: {e}")
        return jsonify({'error': 'analysis_failed', 'message': 'Não foi possível analisar a foto.'}), 502


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Photo exceeds 8 MB limit'}), 413


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
