#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
विशालवृत्तावलिः (Viśālavṛttāvaliḥ) - Sanskrit Prosody & Poetic Composition Suite.

Author: Balaji Baskaran (GitHub: baskarn2)
"""

import os
import base64
import datetime
import pathlib
import json

from flask import (
    Flask, request, render_template, flash,
    send_from_directory, jsonify, redirect, url_for
)
from werkzeug.utils import secure_filename

from indic_transliteration import sanscript
from core.chanda import Chanda, STANDARD_METER_TEMPLATES

import sys

# Base directory (supports both script mode and PyInstaller bundle mode)
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = pathlib.Path(sys._MEIPASS)
    USER_WORK_DIR = pathlib.Path(os.path.dirname(sys.executable))
elif os.environ.get('VISHALA_BASE_DIR'):
    BASE_DIR = pathlib.Path(os.environ['VISHALA_BASE_DIR'])
    USER_WORK_DIR = BASE_DIR
else:
    BASE_DIR = pathlib.Path(__file__).resolve().parent
    USER_WORK_DIR = BASE_DIR

DATA_DIR = BASE_DIR / "data"
TMP_DIR = USER_WORK_DIR / "tmp"
PHOTOS_DIR = TMP_DIR / "photos"
TEXTS_DIR = TMP_DIR / "texts"
RESULTS_DIR = TMP_DIR / "results"

# Ensure directories exist
TMP_DIR.mkdir(parents=True, exist_ok=True)
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
TEXTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# Initialize Core Engine
CHANDA = Chanda(data_path=str(DATA_DIR))

# Create Flask Web Application
app = Flask(
    "विशालवृत्तावलिः",
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)
app.secret_key = os.environ.get("SECRET_KEY", "vishalavrttavalih_secret_key_2026")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit


@app.context_processor
def inject_global_constants():
    """Global variables injected into Jinja templates."""
    return {
        'now': datetime.datetime.now(),
        'available_schemes': [
            ("", "Match Input"),
            ("devanagari", "Devanagari (संस्कृतम्)"),
            ("iast", "IAST (Roman International)"),
            ("itrans", "ITRANS"),
            ("hk", "Harvard-Kyoto"),
            ("wx", "WX"),
            ("slp1", "SLP1"),
            ("bengali", "Bangla (বাংলা)"),
            ("gujarati", "Gujarati (ગુજરાતી)"),
            ("kannada", "Kannada (ಕನ್ನಡ)"),
            ("malayalam", "Malayalam (മലയാളം)"),
            ("oriya", "Oriya (ଓଡ଼ିଆ)"),
            ("tamil", "Tamil (தமிழ்)"),
            ("telugu", "Telugu (తెలుగు)"),
            ("assamese", "Assamese (অসমীয়া)")
        ],
        'text_modes': [
            ("verse", "Verse Mode (4-Pada Grouping)"),
            ("line", "Line Mode (Single Lines)")
        ]
    }


@app.template_filter('transliterate')
def transliterate_filter(text, scheme):
    """Jinja filter to transliterate text to target scheme."""
    if not text:
        return ""
    if scheme and scheme != sanscript.DEVANAGARI and scheme != "":
        try:
            return sanscript.transliterate(str(text), sanscript.DEVANAGARI, scheme)
        except Exception:
            return str(text)
    return str(text)


###############################################################################
# Web Routes
###############################################################################

@app.route('/', strict_slashes=False)
def home():
    """Home / About page."""
    data = {'title': 'About विशालवृत्तावलिः'}
    return render_template('about.html', data=data)


@app.route('/about', strict_slashes=False)
def show_about():
    data = {'title': 'About विशालवृत्तावलिः'}
    return render_template('about.html', data=data)


@app.route('/text', methods=['GET', 'POST'], strict_slashes=False)
def identify_from_text():
    """Text-based meter identification."""
    data = {
        'title': 'Identify from Text',
        'text_mode': 'verse',
        'output_scheme': ''
    }

    if request.method == 'POST':
        input_text = request.form.get('input_text', '').strip()
        data['text'] = input_text
        data['output_scheme'] = request.form.get('output_scheme', '')
        data['text_mode'] = request.form.get('text_mode', 'verse')
        verse_mode = (data['text_mode'] == 'verse')

        if input_text:
            try:
                answer = CHANDA.identify_from_text(
                    input_text,
                    verse=verse_mode,
                    fuzzy=True,
                    save_path=str(RESULTS_DIR),
                    scheme=data['output_scheme']
                )
                data['result'] = answer['result']
                data['result_path'] = answer['path']
                data['summary'] = CHANDA.summarize_results(data['result'])
                data['summary_pretty'] = CHANDA.format_summary(data['summary'])
            except Exception as e:
                flash(f"Error during scansion analysis: {e}", "danger")
        else:
            flash("Please enter some Sanskrit text to analyze.", "warning")

    return render_template('text.html', data=data)


@app.route('/compose', methods=['GET', 'POST'], strict_slashes=False)
def show_compose():
    """Poetic Composition Assistant (काव्यसहायकः)."""
    data = {
        'title': 'काव्यसहायकः &bull; Poetic Composition Studio',
        'meter_catalog': STANDARD_METER_TEMPLATES,
        'output_scheme': ''
    }
    return render_template('compose.html', data=data)


@app.route('/image', methods=['GET', 'POST'], strict_slashes=False)
def identify_from_image():
    """Image-based OCR meter identification."""
    data = {
        'title': 'Identify from Image (OCR)',
        'engines': {
            'tesseract': 'Tesseract OCR',
            'fallback': 'Manual / Preview Mode'
        },
        'engine': 'tesseract',
        'text_mode': 'verse',
        'output_scheme': ''
    }

    if request.method == 'POST':
        data['text'] = request.form.get('input_text', '').strip()
        data['output_scheme'] = request.form.get('output_scheme', '')
        data['text_mode'] = request.form.get('text_mode', 'verse')
        ocr_engine = request.form.get('ocr-engine', 'tesseract')
        data['engine'] = ocr_engine
        verse_mode = (data['text_mode'] == 'verse')

        image_data = request.form.get('image_data')
        if image_data:
            data['image'] = image_data

        image_file = request.files.get('image_file')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            filepath = PHOTOS_DIR / filename
            image_file.save(str(filepath))

            with open(str(filepath), 'rb') as img_f:
                image_base64 = base64.b64encode(img_f.read()).decode('utf-8')
            data['image'] = image_base64

            if ocr_engine == 'tesseract':
                try:
                    import pytesseract
                    from PIL import Image
                    img = Image.open(str(filepath))
                    try:
                        extracted = pytesseract.image_to_string(img, lang='san+mar+hin+ben+tel+guj+tam+mal+kan')
                    except Exception:
                        extracted = pytesseract.image_to_string(img)
                    data['text'] = extracted.strip()
                    if not data['text']:
                        flash("OCR completed but did not detect recognizable text. You can edit the text directly.", "info")
                    else:
                        flash("OCR successfully extracted text from image.", "success")
                except Exception as e:
                    flash(f"Tesseract OCR system unavailable ({e}). You can type or paste the text manually below.", "warning")

        if data.get('text'):
            try:
                answer = CHANDA.identify_from_text(
                    data['text'],
                    verse=verse_mode,
                    fuzzy=True,
                    save_path=str(RESULTS_DIR),
                    scheme=data['output_scheme']
                )
                data['result'] = answer['result']
                data['result_path'] = answer['path']
                data['summary'] = CHANDA.summarize_results(data['result'])
                data['summary_pretty'] = CHANDA.format_summary(data['summary'])
            except Exception as e:
                flash(f"Error analyzing text: {e}", "danger")

    return render_template('image_file.html', data=data)


@app.route('/file', methods=['GET', 'POST'], strict_slashes=False)
def identify_from_file():
    """File upload meter identification."""
    data = {
        'title': 'Identify from Text File',
        'text_mode': 'verse',
        'output_scheme': ''
    }

    if request.method == 'POST':
        data['output_scheme'] = request.form.get('output_scheme', '')
        data['text_mode'] = request.form.get('text_mode', 'verse')
        verse_mode = (data['text_mode'] == 'verse')

        text_file = request.files.get('text_file')
        if text_file and text_file.filename:
            filename = secure_filename(text_file.filename)
            filepath = TEXTS_DIR / filename
            text_file.save(str(filepath))

            try:
                with open(str(filepath), 'r', encoding='utf-8') as f:
                    data['text'] = f.read()
            except UnicodeDecodeError:
                with open(str(filepath), 'r', encoding='latin-1') as f:
                    data['text'] = f.read()

            if data.get('text'):
                try:
                    answer = CHANDA.identify_from_text(
                        data['text'],
                        verse=verse_mode,
                        fuzzy=True,
                        save_path=str(RESULTS_DIR),
                        scheme=data['output_scheme']
                    )
                    data['result'] = answer['result']
                    data['result_path'] = answer['path']
                    data['summary'] = CHANDA.summarize_results(data['result'])
                    data['summary_pretty'] = CHANDA.format_summary(data['summary'])
                    flash(f"Successfully processed file '{filename}'.", "success")
                except Exception as e:
                    flash(f"Error during file analysis: {e}", "danger")
        else:
            flash("Please choose a valid text file to upload.", "warning")

    return render_template('text_file.html', data=data)


@app.route('/examples', strict_slashes=False)
def show_examples():
    """Interactive examples gallery."""
    data = {
        'title': 'Classical Sanskrit Meter Examples',
        'examples': CHANDA.read_examples()
    }
    return render_template('examples.html', data=data)


@app.route('/help', strict_slashes=False)
def show_help():
    """Help & Documentation."""
    data = {'title': 'Help & Prosody Guide'}
    return render_template('help.html', data=data)


@app.route('/feedback', methods=['POST'], strict_slashes=False)
def feedback():
    """Log user feedback locally."""
    name = request.form.get('feedback-name', 'Anonymous')
    email = request.form.get('feedback-email', '')
    msg = request.form.get('feedback-msg', '')
    url = request.form.get('feedback-url', '')

    log_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'name': name,
        'email': email,
        'message': msg,
        'url': url
    }
    fb_file = TMP_DIR / "feedback.jsonl"
    with open(str(fb_file), 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    return jsonify({
        'success': True,
        'message': 'Thank you! Your feedback has been recorded.'
    })


@app.route('/download/<string:filename>')
def download_result(filename):
    """Download analysis results (JSON or TXT)."""
    return send_from_directory(str(RESULTS_DIR), filename, as_attachment=True)


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """REST API endpoint for programmatic analysis."""
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get('text', '')
    verse_mode = payload.get('verse_mode', True)
    fuzzy = payload.get('fuzzy', True)
    output_scheme = payload.get('output_scheme', None)

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        answer = CHANDA.identify_from_text(
            text,
            verse=verse_mode,
            fuzzy=fuzzy,
            scheme=output_scheme
        )
        summary = CHANDA.summarize_results(answer['result'])
        return jsonify({
            'success': True,
            'result': answer['result'],
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compose-check', methods=['POST'])
def api_compose_check():
    """REST API endpoint for live syllable verification during composition."""
    payload = request.get_json(force=True, silent=True) or {}
    meter_name = payload.get('meter', 'इन्द्रवज्रा')
    text = payload.get('text', '')

    eval_result = CHANDA.evaluate_composition(meter_name, text)
    if 'error' in eval_result:
        return jsonify({'success': False, 'error': eval_result['error']}), 400

    return jsonify({
        'success': True,
        'data': eval_result
    })


@app.route('/api/meters', methods=['GET'])
def api_meters():
    """Return dictionary of standard meter templates."""
    return jsonify({
        'success': True,
        'meters': STANDARD_METER_TEMPLATES
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    print(f"Starting विशालवृत्तावलिः (Viśālavṛttāvaliḥ) on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
