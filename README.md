# विशालवृत्तावलिः (Viśālavṛttāvaliḥ)

**Advanced Sanskrit Prosody & Poetic Composition Suite (छन्दोज्ञानम् &bull; काव्यसहायकः)**

*Created and maintained by **Balaji Baskaran**.*

---

## Overview

**विशालवृत्तावलिः** (*Viśālavṛttāvaliḥ*) is a complete standalone web application and prosodic computation engine for Sanskrit poetry, metric scansion, Upajāti hybrid identification, and meter-guided poetic composition.

---

## Key Features

- **200+ Sanskrit Meter Knowledge Base**:
  - Comprehensive definitions for Sama-vṛtta, Ardhasama-vṛtta, Viṣama-vṛtta, Upajāti, and Mātrā-vṛtta (such as *Āryā*, *Gīti*, *Upagīti*).
- **Poetic Composition Studio (काव्यसहायकः / Padapūrti)**:
  - Select target meters (e.g. *Mandākrāntā*, *Vasantatilakā*, *Indravajrā*, *Śārdūlavikrīḍita*).
  - Real-time syllable-by-syllable verification with color-coded slots (green for match, red for weight mismatch).
  - Next-syllable prompt indicator (prompts next required Laghu/Guru).
  - Caesura / Yati markers and classical sample templates.
- **Smart Upajāti (उपजाति) Hybrid Detection**:
  - Automatically identifies 16 traditional varieties of Triṣṭubh Upajāti (*Kīrti*, *Vāṇī*, *Mālā*, *Śālā*, *Haṃsī*, *Māyā*, *Kamalā*, etc.) and Jagatī Upajāti with pāda-by-pāda classification.
- **Detailed Scansion Breakdown**:
  - Akṣara (syllable) segmentation with conjunct consonant handling.
  - Laghu-Guru (ल/ग) binary prosodic weights.
  - 8-Gaṇa triad grouping (य, र, त, न, भ, ज, स, म).
  - Syllable count (letters) and Mātrā count (morae).
  - Traditional Jāti classification.
- **Smart Fuzzy Matching**:
  - Levenshtein distance on Laghu-Guru vectors with concrete edit operations (`i` for insert, `r` for replace, `d` for delete).
- **15+ Scripts & Transliteration Schemes**:
  - Devanagari, IAST, ITRANS, Harvard-Kyoto (HK), SLP1, WX, Bengali, Gujarati, Kannada, Malayalam, Oriya, Tamil, and Telugu.
- **Multi-Modal Input Modes**:
  - **Text Scansion**: 4-line verse aggregation or isolated line analysis.
  - **Poetic Composition Studio**: Interactive 4-pāda verse writing workbench.
  - **Image OCR**: Image upload / paste with editable OCR text extraction.
  - **Text File**: Batch processing of large text files.
  - **Examples Gallery**: Curated classical Sanskrit verses with one-click "Analyze" and "Copy".
  - **Help & Prosody Guide**: Complete guide to Laghu-Guru rules and Gaṇa mnemonics.
- **REST API**:
  - Programmatic endpoints at `/api/analyze` and `/api/compose-check`.

---

## Quick Start

### 1. Prerequisites & Virtual Environment

Ensure Python 3.8+ is installed:

```bash
git clone https://github.com/baskarn2/VashalaChadas.git
cd VashalaChadas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch the Application

```bash
python run.py
```
or
```bash
./run.sh
```

The application will open automatically in your browser at **`http://127.0.0.1:5000`**.

### CLI Options

```bash
python run.py --port 8080        # Custom port
python run.py --no-browser       # Do not auto-launch browser
python run.py --host 0.0.0.0     # Listen on all interfaces
```

---

## API Documentation

### 1. Scansion Analysis API (`POST /api/analyze`)

```bash
curl -X POST http://127.0.0.1:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "अस्त्युत्तरस्यां दिशि देवतात्मा\nहिमालयो नाम नगाधिराजः।\nपूर्वापरौ वारिनिधी विगाह्य\nस्थितः पृथिव्या इव मानदण्डः॥",
    "verse_mode": true,
    "fuzzy": true
  }'
```

### 2. Composition Validation API (`POST /api/compose-check`)

```bash
curl -X POST http://127.0.0.1:5000/api/compose-check \
  -H "Content-Type: application/json" \
  -d '{
    "meter": "इन्द्रवज्रा",
    "text": "लोकाभिरामं रणरङ्गधीरं"
  }'
```

---

## Author & License

Developed and maintained by **Balaji Baskaran** ([GitHub: baskarn2](https://github.com/baskarn2)).
