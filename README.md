# Chandojñānam Local Web Application

**Sanskrit Meter Identification and Utilization System (छन्दोज्ञानम्)**

A standalone local web application that reproduces and enhances the operations, user interface, and scansion features of [Chandojñānam](https://github.com/hrishikeshrt/chanda) (formerly at `sanskrit.iitk.ac.in/jnanasangraha/chanda/`).

---

## Features

- **200+ Sanskrit Meter Database**: Comprehensive definitions for Sama-vṛtta, Ardhasama-vṛtta, Viṣama-vṛtta, Upajāti, and Mātrā-vṛtta (such as Āryā, Gīti, Upagīti).
- **Detailed Scansion Breakdown**:
  - Akṣara (syllable) segmentation with conjunct consonant handling.
  - Laghu-Guru (ल/ग) binary prosodic weight marking.
  - 8-Gaṇa triad grouping (य, र, त, न, भ, ज, स, म) with remaining syllable annotations.
  - Syllable count (letters) and Mātrā count (morae).
  - Traditional Jāti classification.
- **Smart Fuzzy Matching**:
  - Identifies nearest meters using Levenshtein edit distance on Laghu-Guru patterns.
  - Generates concrete syllable-level transformation suggestions (`i` for insertion, `r` for replacement, `d` for deletion).
- **Multi-Script & Transliteration Support**:
  - Over 15 scripts/schemes: Devanagari, IAST, ITRANS, Harvard-Kyoto (HK), SLP1, WX, Bangla (Bengali), Gujarati, Kannada, Malayalam, Oriya, Tamil, Telugu, and Assamese.
- **Multiple Input Modes**:
  - **Text Mode**: Direct text entry with Verse (4-line grouping) and Line modes.
  - **Image Mode**: Image upload / clipboard paste with OCR extraction and scansion.
  - **File Mode**: Batch text file processing with instant scansion analysis.
  - **Examples Gallery**: Curated classical Sanskrit verses with one-click "Analyze" and "Copy".
  - **Help & Prosody Guide**: Educational reference for Laghu-Guru rules and Gaṇa mnemonic tables.
- **Offline & Self-Contained**:
  - Runs completely locally with embedded databases and bundled static assets (Bootstrap, FontAwesome, jQuery).
- **Export & REST API**:
  - Download scansion results as JSON or TXT.
  - Includes a JSON REST API endpoint `/api/analyze` for programmatic integrations.

---

## Quick Start

### 1. Prerequisites & Virtual Environment

Ensure Python 3.8+ is installed. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch the Application

Run the server with the included launcher script:

```bash
python run.py
```
or
```bash
./run.sh
```

By default, the server runs on `http://127.0.0.1:5000` and automatically opens in your default web browser.

### Command Line Options

```bash
python run.py --port 8080        # Run on custom port 8080
python run.py --no-browser       # Do not auto-launch browser
python run.py --host 0.0.0.0     # Listen on all network interfaces
```

---

## Project Structure

```
├── app.py                       # Main Flask web server & routes
├── run.py                       # Local application launcher
├── run.sh                       # Quick bash startup script
├── requirements.txt             # Python dependencies
├── core/
│   ├── __init__.py
│   ├── chanda.py                # Core meter identification and scansion engine
│   ├── analyzer.py              # Prosody syllable weight calculation
│   ├── processor.py             # Script detection and transliteration
│   ├── constants.py             # Prosody and script constants
│   ├── formatter.py             # Output display formatters
│   ├── types.py                 # Dataclasses & types
│   └── utils.py                 # Utilities
├── data/
│   ├── chanda_sama.csv          # Sama-vrtta definitions (200+ meters)
│   ├── chanda_ardhasama.csv     # Ardhasama-vrtta definitions
│   ├── chanda_vishama.csv       # Vishama-vrtta definitions
│   ├── chanda_upajaati.csv      # Upajati hybrid definitions
│   ├── chanda_matra.csv         # Matra-vrtta definitions
│   ├── chanda_jaati.csv         # Jati letter mappings
│   └── examples.json            # Curated Sanskrit verse examples
├── templates/
│   ├── header.html              # Navigation header and branding
│   ├── footer.html              # Footer & JS bundle
│   ├── about.html               # About Sanskrit prosody and system
│   ├── text.html                # Text input scansion view
│   ├── image_file.html          # Image OCR scansion view
│   ├── text_file.html           # File upload scansion view
│   ├── examples.html            # Interactive examples gallery
│   ├── help.html                # Sanskrit prosody and usage guide
│   ├── result.html              # Scansion result container
│   ├── line_result.html         # Individual line scansion table
│   └── result_summary.html      # Analysis summary modal
└── static/
    ├── bootstrap/               # Bootstrap CSS & JS
    ├── fontawesome/             # FontAwesome icons & webfonts
    └── custom/                  # Custom application CSS & JS
```

---

## API Usage

You can also interact with the local scansion engine via REST API:

```bash
curl -X POST http://127.0.0.1:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "को न्वस्मिन् साम्प्रतं लोके गुणवान् कश्च वीर्यवान्।\nधर्मज्ञश्च कृतज्ञश्च सत्यवाक्यो दृढव्रतः॥",
    "verse_mode": true,
    "fuzzy": true,
    "output_scheme": "devanagari"
  }'
```

---

## Reference & Citation

If you use Chandojñānam in academic work, please cite:

```bibtex
@inproceedings{terdalkar2023chandojnanam,
    title = "Chandojnanam: A {S}anskrit Meter Identification and Utilization System",
    author = "Terdalkar, Hrishikesh and Bhattacharya, Arnab",
    booktitle = "Proceedings of the Computational Sanskrit & Digital Humanities: 18th World Sanskrit Conference",
    month = jan,
    year = "2023",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.wsc-csdh.8",
    pages = "113--127"
}
```
