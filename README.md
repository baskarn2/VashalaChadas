# विशालवृत्तावलिः (Viśālavṛttāvaliḥ)

**Advanced Sanskrit Prosody & Poetic Composition Suite (छन्दोज्ञानम् &bull; काव्यसहायकः)**

*Hosted on GitHub: [github.com/baskarn2/VashalaChadas](https://github.com/baskarn2/VashalaChadas)*

---

## 🪟 Windows Desktop Quick Start (No Python Required)

For Windows users with low technical expertise, you can run **विशालवृत्तावलिः** directly as a standalone desktop application:

### Step-by-Step Instructions:

1. **Download the Windows ZIP**:
   - Go to the **[Actions Tab](https://github.com/baskarn2/VashalaChadas/actions)** (or **[Releases Tab](https://github.com/baskarn2/VashalaChadas/releases)**) on GitHub.
   - Click the latest build and download **`Vishalavrttavalih-Windows-x64.zip`**.
2. **Extract the ZIP file**:
   - Right-click the downloaded `.zip` file and select **Extract All...** to extract it into a folder.
3. **Launch the App**:
   - Open the extracted folder and double-click **`Vishalavrttavalih.exe`**.
   - The application will automatically launch in its own desktop window!

### Uninstallation & Cleaning Old Versions:
- Double-click **`cleanup_uninstall.bat`** in the application folder.
- It will stop any running instances, clean caches/temporary files, and completely remove the folder.

---


## 💻 Running from Source (Windows / macOS / Linux)

If you prefer running from source with Python (3.8+):

### On Windows:
1. Double-click `setup.bat` (first time only) to install dependencies automatically.
2. Double-click `run.bat` to launch the application.

### On macOS / Linux:
```bash
git clone https://github.com/baskarn2/VashalaChadas.git
cd VashalaChadas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

---

## 🌟 Key Features

- **200+ Sanskrit Meter Knowledge Base**:
  - Comprehensive definitions for Sama-vṛtta, Ardhasama-vṛtta, Viṣama-vṛtta, Upajāti, and Mātrā-vṛtta (such as *Āryā*, *Gīti*, *Upagīti*).
- **Poetic Composition Studio (काव्यसहायकः / Padapūrti)**:
  - Select target meters (e.g. *Mandākrāntā*, *Vasantatilakā*, *Indravajrā*, *Śārdūlavikrīḍita*).
  - Real-time syllable-by-syllable verification with color-coded slots (green for match, red for weight mismatch).
  - Next-syllable prompt indicator (prompts next required Laghu/Guru).
  - Caesura / Yati markers and classical sample templates.
- **Smart Upajāti (उपजाति) Hybrid Detection**:
  - Automatically identifies 16 traditional varieties of Triṣṭubh Upajāti (*Kīrti*, *Vāṇī*, *Mālā*, *Śālā*, *Haṃsī*, *Māyā*, *Kamalā*, etc.) and Jagatī Upajāti with pāda-by-pāda classification.
- **Pādānta-Guru Metrical Rule (*पादस्यान्ते द्विरूपत्वम्*)**:
  - Automatically detects when the last syllable of a quarter or verse ends in a natural short vowel (Laghu) and evaluates it as Guru in meter matching, highlighted with purple badge styling (`ल* (गुरु)`).
- **Detailed Scansion Breakdown**:
  - Akṣara (syllable) segmentation with conjunct consonant handling.
  - Laghu-Guru (ल/ग) binary prosodic weights.
  - 8-Gaṇa triad grouping (य, र, त, न, भ, ज, स, म) aligned above each 3-syllable group.
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

## 🛠️ CLI Options

```bash
python run.py --port 8080        # Custom port
python run.py --no-browser       # Do not auto-launch browser
python run.py --host 0.0.0.0     # Listen on all network interfaces
```

---

## 📜 GitHub Repository

Hosted at **[github.com/baskarn2/VashalaChadas](https://github.com/baskarn2/VashalaChadas)**.
