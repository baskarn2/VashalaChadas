#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Sanskrit Meter Identification and Scansion Engine for विशालवृत्तावलिः (Viśālavṛttāvaliḥ).

Author: Balaji Baskaran
Handles Akṣara-gaṇa-vṛtta, Mātrā-vṛtta, Ardhasama-vṛtta, Viṣama-vṛtta,
Upajāti hybrid detection, Pādānta-Guru metrical rule, and Poetic Composition.
"""

import os
import re
import csv
import json
import hashlib
import functools
import itertools
from collections import defaultdict, Counter
from typing import Tuple, List, Dict, Optional, Any, Union

import Levenshtein as Lev
from indic_transliteration import sanscript
from indic_transliteration.detect import detect
from indic_transliteration.sanscript import transliterate

import sanskrit_text as skt

# LRU Cache Size
MAX_CACHE = 1024


# 16 Classical Named Sub-types of Triṣṭubh Upajāti
UPAJATI_TRISTUBH_NAMES = {
    (False, False, False, False): ("इन्द्रवज्रा (शुद्ध)", "All 4 pādas Indravajrā"),
    (True, True, True, True): ("उपेन्द्रवज्रा (शुद्ध)", "All 4 pādas Upendravajrā"),
    (True, False, False, False): ("उपजाति (कीर्ति)", "Pāda 1 Upendra, Pādas 2-4 Indra"),
    (False, True, False, False): ("उपजाति (वाणी)", "Pāda 2 Upendra, Pādas 1,3,4 Indra"),
    (False, False, True, False): ("उपजाति (माला)", "Pāda 3 Upendra, Pādas 1,2,4 Indra"),
    (False, False, False, True): ("उपजाति (शाला)", "Pāda 4 Upendra, Pādas 1-3 Indra"),
    (True, True, False, False): ("उपजाति (हंसी)", "Pādas 1,2 Upendra, Pādas 3,4 Indra"),
    (False, True, True, False): ("उपजाति (माया)", "Pādas 2,3 Upendra, Pādas 1,4 Indra"),
    (False, False, True, True): ("उपजाति (चेती)", "Pādas 3,4 Upendra, Pādas 1,2 Indra"),
    (True, False, False, True): ("उपजाति (भद्रा)", "Pādas 1,4 Upendra, Pādas 2,3 Indra"),
    (True, False, True, False): ("उपजाति (प्रेमा)", "Pādas 1,3 Upendra, Pādas 2,4 Indra"),
    (False, True, False, True): ("उपजाति (कमला)", "Pādas 2,4 Upendra, Pādas 1,3 Indra"),
    (True, True, True, False): ("उपजाति (ऋद्धि)", "Pādas 1-3 Upendra, Pāda 4 Indra"),
    (False, True, True, True): ("उपजाति (सिद्धि)", "Pādas 2-4 Upendra, Pāda 1 Indra"),
    (True, False, True, True): ("उपजाति (बुद्धि)", "Pādas 1,3,4 Upendra, Pāda 2 Indra"),
    (True, True, False, True): ("उपजाति (शुद्धि)", "Pādas 1,2,4 Upendra, Pāda 3 Indra"),
}


# Known Standard Meter Templates for Poetic Composition Assistant
STANDARD_METER_TEMPLATES = {
    "अनुष्टुभ्": {
        "name": "अनुष्टुभ् (Anuṣṭubh / Śloka)",
        "syllables": 8,
        "matras": 12,
        "pattern": "LLLLLLLL",
        "pattern_display": "— — — — ल ग ल/ग —",
        "gana": "श्लोक (५ ल, ६ ग, ७ ल/ग)",
        "yati": "8 (Pādānta)",
        "description": "Most ubiquitous Sanskrit epic meter (Mahābhārata, Rāmāyaṇa, Gītā). 8 syllables per pada."
    },
    "इन्द्रवज्रा": {
        "name": "इन्द्रवज्रा (Indravajrā)",
        "syllables": 11,
        "matras": 18,
        "pattern": "GGLGGLLGLGG",
        "pattern_display": "ग ग ल | ग ग ल | ल ग ल | ग ग",
        "gana": "त त ज ग ग",
        "yati": "5, 6 (11)",
        "description": "Classic 11-syllable Triṣṭubh meter starting with Guru."
    },
    "उपेन्द्रवज्रा": {
        "name": "उपेन्द्रवज्रा (Upendravajrā)",
        "syllables": 11,
        "matras": 17,
        "pattern": "LGLGGLLGLGG",
        "pattern_display": "ल ग ल | ग ग ल | ल ग ल | ग ग",
        "gana": "ज त ज ग ग",
        "yati": "5, 6 (11)",
        "description": "Sister meter to Indravajrā, beginning with Laghu."
    },
    "उपजाति": {
        "name": "उपजाति (Upajāti)",
        "syllables": 11,
        "matras": 17,
        "pattern": "-GLGGLLGLGG",
        "pattern_display": "[ल/ग] ग ल | ग ग ल | ल ग ल | ग ग",
        "gana": "[ज/त] त ज ग ग",
        "yati": "5, 6 (11)",
        "description": "Flexible hybrid verse combining Indravajrā and Upendravajrā across the 4 quarters."
    },
    "शालिनी": {
        "name": "शालिनी (Śālinī)",
        "syllables": 11,
        "matras": 19,
        "pattern": "GGGGGLGGLGG",
        "pattern_display": "ग ग ग | ग ग ल | ग ग ल | ग ग",
        "gana": "म त त ग ग",
        "yati": "4, 7 (11)",
        "description": "Solemn Triṣṭubh meter with yati after 4th and 7th syllables."
    },
    "रथोद्धता": {
        "name": "रथोद्धता (Rathoddhatā)",
        "syllables": 11,
        "matras": 17,
        "pattern": "GLGLGLLGLGL",
        "pattern_display": "ग ल ग | ल ल ल | ग ल ग | ल ग",
        "gana": "र न र ल ग",
        "yati": "11",
        "description": "Chariot-movement 11-syllable meter with lively cadence."
    },
    "द्रुतविलम्बित": {
        "name": "द्रुतविलम्बित (Drutavilambita)",
        "syllables": 12,
        "matras": 17,
        "pattern": "LLLGLLGLLGLG",
        "pattern_display": "ल ल ल | ग ल ल | ग ल ल | ग ल ग",
        "gana": "न भ भ र",
        "yati": "12",
        "description": "Fast-slow alternating cadence meter of 12 syllables."
    },
    "वंशस्थ": {
        "name": "वंशस्थ (Vaṃśastha)",
        "syllables": 12,
        "matras": 18,
        "pattern": "LGLGGLGGLGLG",
        "pattern_display": "ल ग ल | ग ग ल | ल ग ल | ग ल ग",
        "gana": "ज त ज र",
        "yati": "5, 7 (12)",
        "description": "Standard 12-syllable Jagatī meter used extensively by Kālidāsa and Bhāravi."
    },
    "भुजङ्गप्रयात": {
        "name": "भुजङ्गप्रयात (Bhujaṅgaprayāta)",
        "syllables": 12,
        "matras": 20,
        "pattern": "LGGLGGLGGLGG",
        "pattern_display": "ल ग ग | ल ग ग | ल ग ग | ल ग ग",
        "gana": "य य य य",
        "yati": "6, 6 (12)",
        "description": "Serpent-gliding meter composed purely of 4 Ya-gaṇas. Famous in Śaṅkarācārya stotras."
    },
    "तोटक": {
        "name": "तोटक (Toṭaka)",
        "syllables": 12,
        "matras": 16,
        "pattern": "LLGLLGLLGLLG",
        "pattern_display": "ल ल ग | ल ल ग | ल ल ग | ल ल ग",
        "gana": "स स स स",
        "yati": "12",
        "description": "Rhythmic dancing meter of 4 Sa-gaṇas. (e.g. Toṭakāṣṭakam)."
    },
    "वसन्ततिलका": {
        "name": "वसन्ततिलका (Vasantatilakā)",
        "syllables": 14,
        "matras": 21,
        "pattern": "GGLGLLLGLGLGG",
        "pattern_display": "ग ग ल | ग ल ल | ल ग ल | ल ग ल | ग ग",
        "gana": "त भ ज ज ग ग",
        "yati": "8, 6 (14)",
        "description": "Ornament of Springtime, highly graceful 14-syllable meter with yati at 8 and 6."
    },
    "मालिनी": {
        "name": "मालिनी (Mālinī)",
        "syllables": 15,
        "matras": 22,
        "pattern": "LLLLLLGGGLGGLGG",
        "pattern_display": "ल ल ल | ल ल ल | ग ग ग | ल ग ग | ल ग ग",
        "gana": "न न म य य",
        "yati": "8, 7 (15)",
        "description": "Garland meter starting with 6 swift light syllables, followed by resonant heavy syllables."
    },
    "शिखरिणी": {
        "name": "शिखरिणी (Śikhariṇī)",
        "syllables": 17,
        "matras": 25,
        "pattern": "LGGGGLLLLLLGGLGGL",
        "pattern_display": "ल ग ग | ग ग ग | ल ल ल | ल ल ग | ग ल ग | ल",
        "gana": "य म न स भ ल ग",
        "yati": "6, 11 (17)",
        "description": "Peak / Crest meter with pause after 6th and 17th syllables (e.g. Saundaryalaharī)."
    },
    "मन्दाक्रान्ता": {
        "name": "मन्दाक्रान्ता (Mandākrāntā)",
        "syllables": 17,
        "matras": 26,
        "pattern": "GGGGLLLLLLGGLGGLG",
        "pattern_display": "ग ग ग | ग ल ल | ल ल ल | ग ग ल | ग ग ल | ग",
        "gana": "म भ न त त ग ग",
        "yati": "4, 6, 7 (17)",
        "description": "Slow-advancing, majestic meter of Meghadūta with pauses at 4, 10, and 17 syllables."
    },
    "शार्दूलविक्रीडित": {
        "name": "शार्दूलविक्रीडित (Śārdūlavikrīḍita)",
        "syllables": 19,
        "matras": 29,
        "pattern": "GGGLLGLGLLLGGLGGLGG",
        "pattern_display": "ग ग ग | ल ल ग | ल ग ल | ल ल ग | ग ल ग | ग ल ग",
        "gana": "म स ज स त त ग",
        "yati": "12, 7 (19)",
        "description": "Tiger's play - grand, powerful 19-syllable meter with pause at 12th and 19th syllables."
    },
    "स्रग्धरा": {
        "name": "स्रग्धरा (Sragdharā)",
        "syllables": 21,
        "matras": 32,
        "pattern": "GGGGGLGLLLLLLGGGLGGLGG",
        "pattern_display": "ग ग ग | ग ल ग | ल ल ल | ल ल ल | ग ग ग | ल ग ग | ल ग ग",
        "gana": "म र भ न य य य",
        "yati": "7, 7, 7 (21)",
        "description": "Garland-bearer - magnificent 21-syllable meter with tri-equal 7-syllable pauses."
    },
    "आर्या": {
        "name": "आर्या (Āryā)",
        "syllables": 0,
        "matras": 57,
        "pattern": "12-18-12-15",
        "pattern_display": "पाद १: १२ मात्राः | पाद २: १८ मात्राः | पाद ३: १२ मात्राः | पाद ४: १५ मात्राः",
        "gana": "मात्रागण (गण = ४ मात्राः, ६ठे में ज-गण/ल)",
        "yati": "Pādānta",
        "description": "Supreme Mātrā-vṛtta meter of Sanskrit philosophical & lyrical poetry."
    }
}


class Chanda:
    """Chanda (Sanskrit Meter) Identifier and Scansion Engine for विशालवृत्तावलिः"""
    Y = 'Y'
    R = 'R'
    T = 'T'
    N = 'N'
    B = 'B'
    J = 'J'
    S = 'S'
    M = 'M'
    L = 'L'
    G = 'G'
    SYMBOLS = f'{Y}{R}{T}{N}{B}{J}{S}{M}{L}{G}'
    GANA = {
        Y: f'{L}{G}{G}',
        R: f'{G}{L}{G}',
        T: f'{G}{G}{L}',
        N: f'{L}{L}{L}',
        B: f'{G}{L}{L}',
        J: f'{L}{G}{L}',
        S: f'{L}{L}{G}',
        M: f'{G}{G}{G}'
    }

    def __init__(self, data_path: Optional[str] = None, symbols: str = 'यरतनभजसमलग'):
        if data_path is None:
            data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            if not os.path.exists(data_path):
                data_path = os.path.join(os.path.dirname(__file__), 'data')

        self.data_path = data_path
        self.input_map = dict(zip(symbols, self.SYMBOLS))
        self.output_map = dict(zip(self.SYMBOLS, symbols))
        self.ttable_in = str.maketrans(self.input_map)
        self.ttable_out = str.maketrans(self.output_map)
        self.gana = self.GANA.copy()
        self.gana_inv = {v: k for k, v in self.gana.items()}

        # Databases
        self.CHANDA = defaultdict(list)
        self.SINGLE_CHANDA = defaultdict(list)
        self.MULTI_CHANDA = defaultdict(list)
        self.JAATI = defaultdict(list)
        self.SPLITS = defaultdict(list)
        self.MATRA_CHANDA = defaultdict(list)
        self.MATRA_PATTERNS = {}

        # Read Data
        self.read_data()

    ###########################################################################
    # Prosody & Syllable Marking with Pādānta-Guru Rule
    ###########################################################################

    def mark_lg(self, text: str) -> Tuple[List[List[List[str]]], List[str], List[bool]]:
        """
        Mark Laghu-Guru for Devanagari text.
        Tracks natural weights and flags Pādānta-Guru rule (last letter counted as Guru even if naturally Laghu).
        """
        skip_syllables = [skt.AVAGRAHA]
        lg_marks = []
        padanta_flags = []
        syllables = skt.get_syllables(text)
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        if not flat_syllables:
            return flat_syllables, lg_marks, padanta_flags

        # Find the index of the last non-halanta vocalic syllable
        last_vocalic_idx = -1
        for idx in range(len(flat_syllables) - 1, -1, -1):
            s = flat_syllables[idx]
            if s[-1] != skt.HALANTA and s not in skip_syllables:
                last_vocalic_idx = idx
                break

        for idx, syllable in enumerate(flat_syllables):
            if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
                lg_marks.append('')
                padanta_flags.append(False)
                continue

            if idx == len(flat_syllables) - 1 or idx == last_vocalic_idx:
                is_natural_laghu = skt.is_laghu(syllable)
                lg_marks.append(self.L if is_natural_laghu else self.G)
                # If naturally Laghu and at the very end of line/pada, eligible for Padanta-Guru
                padanta_flags.append(is_natural_laghu)
            else:
                next_syllable = flat_syllables[idx + 1]
                laghu = (
                    skt.is_laghu(syllable) and
                    (skt.HALANTA not in next_syllable)
                )
                lg_marks.append(self.L if laghu else self.G)
                padanta_flags.append(False)

        return syllables, lg_marks, padanta_flags

    def _scan_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Scan line, return syllables, marks, padanta flags, and clean LG string."""
        clean_line = skt.clean(line).strip()
        if not clean_line:
            return None

        syllables, lg_marks, padanta_flags = self.mark_lg(clean_line)
        lg_str = ''.join(self.input_map.get(m, m) for m in lg_marks if m)
        if not lg_str:
            return None

        # Build Padanta-elevated alternative string (where last L is treated as G)
        alt_lg_str = lg_str
        if lg_str and lg_str[-1] == self.L:
            alt_lg_str = lg_str[:-1] + self.G

        return {
            'line': clean_line,
            'syllables': syllables,
            'lg_marks': lg_marks,
            'padanta_flags': padanta_flags,
            'lg_str': lg_str,
            'alt_lg_str': alt_lg_str
        }

    def lg_to_gana(self, lg_str: str) -> str:
        gana = []
        for i in range(0, len(lg_str), 3):
            group = lg_str[i:i + 3]
            gana.append(self.gana_inv.get(group, group))
        return ''.join(gana)

    def gana_to_lg(self, gana_str: str) -> str:
        return gana_str.translate(str.maketrans(self.gana))

    def count_matra(self, gana_str: str) -> int:
        lg_str = self.gana_to_lg(gana_str)
        return lg_str.count(self.L) + lg_str.count(self.G) * 2

    ###########################################################################
    # Data Loading
    ###########################################################################

    def read_jaati(self, file_path: str) -> Dict[int, Tuple[str, ...]]:
        jaati = defaultdict(list)
        if not os.path.exists(file_path):
            return jaati
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                if not row or not row[0].strip():
                    continue
                letter_count = int(row[0].strip())
                names = [c.strip() for c in row[1].split(',') if c.strip()]
                jaati[letter_count] = tuple(names)

        self.JAATI.update(jaati)
        return jaati

    def read_chanda_definitions(self, chanda_file: str) -> Dict[str, List]:
        chanda = defaultdict(list)
        multi_chanda = defaultdict(list)
        splits = defaultdict(list)
        chanda_pada = defaultdict(dict)

        if not os.path.exists(chanda_file):
            return chanda

        with open(chanda_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                if not row or not row[0].strip():
                    continue

                names = tuple(c.strip() for c in row[0].split(',') if c.strip())
                pada = row[1].strip() if len(row) > 1 else ''
                lakshana = ''.join(row[2].split()) if len(row) > 2 else ''
                lakshana = lakshana.translate(self.ttable_in)
                lakshana = self.gana_to_lg(lakshana)
                lakshana = lakshana.replace('-', f"[{self.L}{self.G}]")

                if pada:
                    chanda_pada[names][pada] = lakshana
                else:
                    chanda_pada[names]['1'] = lakshana
                    chanda_pada[names]['2'] = lakshana

                if lakshana:
                    meters = tuple((c, (pada,)) for c in names)
                    chanda[lakshana].extend(meters)

        for _chanda_names, _pada_lakshana in chanda_pada.items():
            multi_pada = []
            multi_lakshana = []
            for _pada, _lakshana in _pada_lakshana.items():
                multi_pada.append(_pada)
                multi_lakshana.append(_lakshana)

                if len(multi_pada) == 2:
                    names = tuple((_name, tuple(multi_pada)) for _name in _chanda_names)
                    combined_key = ''.join(multi_lakshana)
                    multi_chanda[combined_key].extend(names)
                    splits[combined_key].append(multi_lakshana)
                    multi_pada = []
                    multi_lakshana = []

        for k, v in chanda.items():
            self.SINGLE_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)
        for k, v in multi_chanda.items():
            self.MULTI_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)

        self.SPLITS.update(splits)
        return chanda

    def read_matra_definitions(self, matra_file: str):
        if not os.path.exists(matra_file):
            return
        with open(matra_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                if not row or not row[0].strip() or len(row) < 2:
                    continue
                names = [c.strip() for c in row[0].split(',') if c.strip()]
                raw_pattern = row[1].replace(',', '-').split('-')
                try:
                    pattern = tuple(int(x.strip()) for x in raw_pattern if x.strip())
                    self.MATRA_CHANDA[pattern].extend([(name, ()) for name in names])
                    for name in names:
                        self.MATRA_PATTERNS[name] = pattern
                except Exception:
                    continue

    def read_data(self):
        self.read_jaati(os.path.join(self.data_path, 'chanda_jaati.csv'))
        for fname in ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv', 'chanda_upajaati.csv']:
            fpath = os.path.join(self.data_path, fname)
            if os.path.exists(fpath):
                self.read_chanda_definitions(fpath)
        self.read_matra_definitions(os.path.join(self.data_path, 'chanda_matra.csv'))

    def read_examples(self) -> Dict[str, List[str]]:
        ex_path = os.path.join(self.data_path, 'examples.json')
        if os.path.exists(ex_path):
            with open(ex_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    ###########################################################################
    # Text Processing & Scheme Detection
    ###########################################################################

    def process_text(self, text: str) -> Tuple[List[str], str]:
        scheme = detect(text)
        if scheme != sanscript.DEVANAGARI:
            devanagari_text = transliterate(text, scheme, sanscript.DEVANAGARI)
        else:
            devanagari_text = text

        lines = []
        for line in skt.split_lines(devanagari_text):
            clean_line = skt.clean(line).strip()
            if clean_line:
                lines.append(clean_line)
        return lines, scheme

    ###########################################################################
    # Direct & Regex Matching
    ###########################################################################

    def _lookup_lg(self, lg_str: str, dictionary: Dict[str, Any], alt_lg_str: Optional[str] = None) -> Tuple[str, List, bool, bool]:
        """
        Lookup in meter dictionary. Checks natural lg_str and Padanta-promoted alt_lg_str.
        Returns: (matched_lg, chanda_list, found, used_padanta)
        """
        if lg_str in dictionary:
            return lg_str, dictionary[lg_str], True, False
        if alt_lg_str and alt_lg_str in dictionary:
            return alt_lg_str, dictionary[alt_lg_str], True, True
        if lg_str:
            last = lg_str[-1]
            alt_last = self.G if last == self.L else self.L
            flipped_lg = lg_str[:-1] + alt_last
            if flipped_lg in dictionary:
                return flipped_lg, dictionary[flipped_lg], True, True
        return lg_str, [], False, False

    def find_direct_match(self, line: str, multi: bool = False) -> Optional[Dict[str, Any]]:
        scan = self._scan_line(line)
        if scan is None:
            return None

        dictionary = self.MULTI_CHANDA if multi else self.SINGLE_CHANDA
        match_lg, chanda_list, found, used_padanta = self._lookup_lg(
            scan['lg_str'], dictionary, alt_lg_str=scan.get('alt_lg_str')
        )

        chanda = []
        jaati = []
        gana = []
        length = []
        matra = []

        if found:
            chanda += chanda_list

        if not multi:
            jaati = self.JAATI.get(len(match_lg), self.JAATI.get(-1, ('अज्ञात',)))
            gana = [self.lg_to_gana(scan['lg_str'])]
            length = [str(len(match_lg))]
            matra = [str(self.count_matra(match_lg))]
        elif found:
            splits = self.SPLITS.get(match_lg, [])
            jaati = [
                "(" + ', '.join(
                    ' / '.join(self.JAATI.get(len(split), self.JAATI.get(-1, ('अज्ञात',))))
                    for split in split_group
                ) + ")"
                for split_group in splits
            ]
            # Always return continuous clean ganas aligned with the line
            gana = [self.lg_to_gana(scan['lg_str'])]
            length = [
                f"({' + '.join(str(len(split)) for split in split_group)})"
                for split_group in splits
            ]
            matra = [
                f"({' + '.join(str(self.count_matra(split)) for split in split_group)})"
                for split_group in splits
            ]

        return {
            'found': found,
            'used_padanta': used_padanta,
            'syllables': scan['syllables'],
            'lg': scan['lg_marks'],
            'padanta_flags': scan['padanta_flags'],
            'gana': gana,
            'chanda': chanda,
            'jaati': list(jaati),
            'length': length,
            'matra': matra
        }

    ###########################################################################
    # Fuzzy Matching
    ###########################################################################

    def _editops(self, s1: str, s2: str, replace_cost: int = 1, delete_cost: int = 1, insert_cost: int = 1, max_diff: int = 3):
        distance = Lev.distance(s1, s2)
        if distance > max_diff:
            return distance, None
        ops = Lev.editops(s1, s2)
        cost = 0
        for op in ops:
            if op[0] == 'replace':
                cost += replace_cost
            elif op[0] == 'delete':
                cost += delete_cost
            elif op[0] == 'insert':
                cost += insert_cost
        return cost, ops

    def transform(self, line: str, signature: str, replace_cost: int = 1, delete_cost: int = 1, insert_cost: int = 1, max_diff: int = 3):
        scan = self._scan_line(line)
        if scan is None:
            return 0, None
        syllables = scan['syllables']
        lg_marks = scan['lg_marks']
        lg_str = scan['lg_str']

        lg_signature = self.gana_to_lg(signature)
        cost, ops = self._editops(
            lg_str, lg_signature,
            replace_cost=replace_cost,
            delete_cost=delete_cost,
            insert_cost=insert_cost,
            max_diff=max_diff
        )
        if ops is None:
            return cost, None
        if not ops:
            return 0, []

        distance = len(ops)
        idx = 0
        lg_idx = 0
        op_idx = 0
        output = []
        op, spos, dpos = ops[op_idx]

        for lid, line_item in enumerate(syllables):
            output_line = []
            for wid, word in enumerate(line_item):
                output_word = []
                for cid, syllable in enumerate(word):
                    output_syllable = syllable
                    if lg_marks[idx]:
                        if lg_idx == spos:
                            if op[0] == 'i':
                                output_syllable = f'i({lg_signature[dpos]})'
                                output_word.append(output_syllable)
                                op_idx += 1
                            if op_idx < distance:
                                op, spos, dpos = ops[op_idx]
                                if op[0] != 'i':
                                    output_syllable = f'{op[0]}({syllable})'
                                    if op[0] == 'r':
                                        substitute = lg_signature[dpos]
                                        output_syllable += f'[{substitute}]'
                                        laghu = skt.is_laghu(syllable)
                                        if not (laghu == (substitute == self.L)):
                                            tm = skt.toggle_matra(syllable)
                                            if tm:
                                                output_syllable += f'{{{tm}}}'
                                op_idx += 1
                                if op_idx < distance:
                                    op, spos, dpos = ops[op_idx]
                        lg_idx += 1
                    idx += 1
                    output_word.append(output_syllable)
                output_line.append(output_word)
            output.append(output_line)
        return cost, output

    ###########################################################################
    # Single Line Scansion
    ###########################################################################

    def identify_line(self, line: str, fuzzy: bool = True, k: int = 10, scheme: Optional[str] = None) -> Dict[str, Any]:
        lines, detected_scheme = self.process_text(line)
        output_scheme = scheme or (detected_scheme if detected_scheme != sanscript.DEVANAGARI else None)

        if not lines:
            return {}
        line = lines[0]

        answer = {}
        direct_match = self.find_direct_match(line)
        multi_match = self.find_direct_match(line, multi=True)

        if direct_match is None:
            return answer

        found = bool(direct_match['found'] or (multi_match and multi_match['found']))

        scan = self._scan_line(line)
        lg_str = scan['lg_str'] if scan else ''
        alt_lg_str = scan.get('alt_lg_str', lg_str) if scan else ''

        regex_matches = [rk for rk in self.CHANDA if re.match(f'^{rk}$', lg_str) or re.match(f'^{rk}$', alt_lg_str)]
        if regex_matches:
            found = True
        is_regex_match = bool(regex_matches)

        chanda = []
        jaati = []
        gana = []
        length = []
        matra = []

        if found:
            if direct_match['found']:
                chanda += direct_match['chanda']
                jaati += direct_match['jaati']
                gana += direct_match['gana']
                length += direct_match['length']
                matra += direct_match['matra']
            if multi_match and multi_match['found']:
                chanda += multi_match['chanda']
                jaati += multi_match['jaati']
                gana += multi_match['gana']
                length += multi_match['length']
                matra += multi_match['matra']
            if is_regex_match:
                chanda += [
                    c for m in regex_matches for c in self.CHANDA.get(m, [])
                    if c not in chanda
                ]

        # Natural LG list
        full_lg = [self.output_map.get(c, c) for c in direct_match['lg']]
        padanta_flags = direct_match.get('padanta_flags', [])

        # Display LG marks with Padanta annotation
        display_lg = []
        display_lg_classes = []
        for idx, m in enumerate(direct_match['lg']):
            if not m:
                display_lg.append('')
                display_lg_classes.append('')
                continue
            is_padanta = (idx < len(padanta_flags) and padanta_flags[idx])
            dev_char = self.output_map.get(m, m)
            if is_padanta:
                display_lg.append(f"{dev_char}*")
                display_lg_classes.append('cell-padanta')
            else:
                display_lg.append(dev_char)
                display_lg_classes.append('cell-laghu' if m == self.L else 'cell-guru')

        full_length = len(lg_str)
        full_matra = self.count_matra(lg_str)
        
        # Always compute pure continuous Gaṇas aligned with the line
        full_gana = self.lg_to_gana(lg_str).translate(self.ttable_out)
        full_jaati = self.JAATI.get(len(lg_str), self.JAATI.get(-1, ('अज्ञात',)))

        display_line = line
        display_syllables = [s for ln in direct_match['syllables'] for w in ln for s in w]
        display_gana = full_gana
        display_length = ' / '.join(length) if length else full_length
        display_matra = ' / '.join(matra) if matra else full_matra
        display_chanda = ' / '.join(self.format_chanda_pada(c, p) for c, p in chanda)
        display_jaati = ' / '.join(jaati if jaati else full_jaati)

        answer['found'] = found
        answer['syllables'] = display_syllables
        answer['lg'] = full_lg
        answer['raw_lg'] = [self.output_map.get(m, m) for m in direct_match['lg'] if m]
        answer['padanta_flags'] = padanta_flags
        answer['gana'] = full_gana
        answer['length'] = full_length
        answer['matra'] = full_matra
        answer['chanda'] = chanda
        answer['jaati'] = jaati

        answer['display_scheme'] = output_scheme
        answer['display_line'] = display_line
        answer['display_syllables'] = display_syllables
        answer['display_lg'] = display_lg
        answer['display_lg_classes'] = display_lg_classes
        answer['display_gana'] = display_gana
        answer['display_length'] = display_length
        answer['display_matra'] = display_matra
        answer['display_chanda'] = display_chanda
        answer['display_jaati'] = display_jaati

        answer['fuzzy'] = []
        if not found and fuzzy:
            for chanda_lg, chanda_names in self.CHANDA.items():
                chanda_gana = self.lg_to_gana(chanda_lg)
                cost, suggestion = self.transform(line, chanda_lg)
                if suggestion is not None:
                    similarity = max(0.0, 1.0 - cost / max(len(chanda_lg), 1))
                    output_sug = ', '.join([s for ln in suggestion for w in ln for s in w])
                    _display_chanda = ' / '.join(self.format_chanda_pada(c, p) for c, p in chanda_names)
                    answer['fuzzy'].append({
                        "chanda": chanda_names,
                        "gana": chanda_gana.translate(self.ttable_out),
                        "suggestion": output_sug,
                        "cost": cost,
                        "similarity": similarity,
                        "display_chanda": _display_chanda
                    })
            answer['fuzzy'] = sorted(answer['fuzzy'], key=lambda x: x["similarity"], reverse=True)[:k]

        return answer

    ###########################################################################
    # Upajāti Hybrid Verse Detection
    ###########################################################################

    def _check_upajati_hybrid(self, line_results: List[Dict[str, Any]], verse_lines: List[int]) -> Optional[Tuple[List[str], float, str]]:
        if len(verse_lines) < 2:
            return None

        tristubh_padas = []
        is_all_tristubh = True

        jagati_padas = []
        is_all_jagati = True

        for l_idx in verse_lines:
            res = line_results[l_idx]['result']
            m_names = [c[0] for c in res.get('chanda', [])]
            
            is_indra = ('इन्द्रवज्रा' in m_names)
            is_upendra = ('उपेन्द्रवज्रा' in m_names)
            
            if is_indra or is_upendra:
                tristubh_padas.append(is_upendra)
            else:
                lg_marks = [m for m in res.get('lg', []) if m]
                if len(lg_marks) == 11:
                    first_is_laghu = (lg_marks[0] in ['ल', 'L', 'ल*'])
                    tristubh_padas.append(first_is_laghu)
                else:
                    is_all_tristubh = False

            is_vamsastha = ('वंशस्थ' in m_names)
            is_indravamsa = ('इन्द्रवंशा' in m_names)
            if is_vamsastha or is_indravamsa:
                jagati_padas.append(is_vamsastha)
            else:
                is_all_jagati = False

        if is_all_tristubh and len(tristubh_padas) == 4:
            has_indra = False in tristubh_padas
            has_upendra = True in tristubh_padas
            if has_indra and has_upendra:
                tuple_key = tuple(tristubh_padas)
                sub_name, desc = UPAJATI_TRISTUBH_NAMES.get(tuple_key, ("उपजाति", "Mixed Indravajrā & Upendravajrā"))
                pada_desc = []
                for p_idx, is_u in enumerate(tristubh_padas, 1):
                    pada_desc.append(f"पाद {p_idx}: {'उपेन्द्रवज्रा' if is_u else 'इन्द्रवज्रा'}")
                detail = f" ({', '.join(pada_desc)})"
                return ([sub_name, "उपजाति (इन्द्रवज्रा + उपेन्द्रवज्रा)"], 4.0, detail)

        if is_all_jagati and len(jagati_padas) == 4:
            has_vam = True in jagati_padas
            has_ind = False in jagati_padas
            if has_vam and has_ind:
                pada_desc = []
                for p_idx, is_v in enumerate(jagati_padas, 1):
                    pada_desc.append(f"पाद {p_idx}: {'वंशस्थ' if is_v else 'इन्द्रवंशा'}")
                detail = f" ({', '.join(pada_desc)})"
                return (["उपजाति (वंशस्थ + इन्द्रवंशा)", "जगती-उपजाति"], 4.0, detail)

        return None

    ###########################################################################
    # Full Text & Verse Analysis
    ###########################################################################

    def identify_from_text(
        self,
        text: str,
        verse: bool = False,
        fuzzy: bool = True,
        save_path: Optional[str] = None,
        scheme: Optional[str] = None
    ) -> Dict[str, Any]:
        line_results = []
        verse_results = []

        lines, detected_scheme = self.process_text(text)
        output_scheme = scheme or (detected_scheme if detected_scheme != sanscript.DEVANAGARI else None)

        for line in lines:
            if not line:
                continue
            line_ans = self.identify_line(line, fuzzy=fuzzy, scheme=output_scheme)
            line_results.append({
                'line': line,
                'result': line_ans
            })

        if verse:
            verse_result = {
                'chanda': None,
                'scheme': output_scheme,
                'scores': [],
                'lines': []
            }
            ongoing_score = Counter()
            line_count = 0

            for line_idx, line_item in enumerate(line_results):
                line_res = line_item['result']
                if line_res.get('found'):
                    for _c, _p in line_res.get('chanda', []):
                        ongoing_score[_c] += 1
                else:
                    for fuzzy_match in line_res.get('fuzzy', []):
                        for _c, _p in fuzzy_match.get('chanda', []):
                            ongoing_score[_c] += fuzzy_match.get('similarity', 0.0)

                verse_result['lines'].append(line_idx)
                line_count += 1

                if line_count % 4 == 0 or line_idx == len(line_results) - 1:
                    upajati_match = self._check_upajati_hybrid(line_results, verse_result['lines'])
                    if upajati_match:
                        best_matches = (upajati_match[0], upajati_match[1])
                        verse_scores = [(name, upajati_match[1]) for name in upajati_match[0]]
                    else:
                        verse_scores = ongoing_score.most_common()
                        if verse_scores:
                            best_score = verse_scores[0][1]
                            best_matches = ([
                                _c for _c, _score in verse_scores if _score == best_score
                            ], best_score)
                        else:
                            best_matches = (['अज्ञात'], 0)

                    verse_result['scores'] = verse_scores
                    verse_result['chanda'] = best_matches

                    for _line_idx in verse_result['lines']:
                        lr = line_results[_line_idx]['result']
                        if not lr.get('found') and lr.get('fuzzy'):
                            priority_fuzzy = []
                            other_fuzzy = []
                            for fm in lr['fuzzy']:
                                match_names = [c[0] for c in fm.get('chanda', [])]
                                if any(mn in best_matches[0] for mn in match_names):
                                    priority_fuzzy.append(fm)
                                else:
                                    other_fuzzy.append(fm)
                            lr['fuzzy'] = priority_fuzzy + other_fuzzy

                    verse_results.append(verse_result)
                    verse_result = {
                        'chanda': None,
                        'scheme': output_scheme,
                        'scores': [],
                        'lines': []
                    }
                    ongoing_score = Counter()

        results = {
            'line': line_results,
            'verse': verse_results
        }

        simple_result = []
        if verse:
            for v_idx, verse_res in enumerate(verse_results, 1):
                best_names = " / ".join(verse_res['chanda'][0])
                best_score = verse_res['chanda'][1]
                simple_result.append(f"Verse {v_idx}: {best_names} (Score: {best_score})")
                simple_result.append("-" * 40)
                for line_idx in verse_res['lines']:
                    l_res = line_results[line_idx]['result']
                    simple_result.append(self.format_line_result(l_res))
                simple_result.append("")
        else:
            for l_item in line_results:
                simple_result.append(self.format_line_result(l_item['result']))
                simple_result.append("")

        json_filename = None
        txt_filename = None

        if save_path is not None:
            os.makedirs(save_path, exist_ok=True)
            md5sum = hashlib.md5(text.encode('utf-8')).hexdigest()
            result_id = f"result_{md5sum}_{int(verse)}_{int(fuzzy)}"

            json_filename = f"{result_id}.json"
            json_path = os.path.join(save_path, json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            txt_filename = f"{result_id}.txt"
            txt_path = os.path.join(save_path, txt_filename)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(simple_result))

        return {
            'result': results,
            'path': {
                'json': json_filename,
                'txt': txt_filename
            }
        }

    ###########################################################################
    # Poetic Composition Assistant (काव्यसहायकः)
    ###########################################################################

    def get_meter_template(self, meter_name: str) -> Optional[Dict[str, Any]]:
        return STANDARD_METER_TEMPLATES.get(meter_name)

    def evaluate_composition(self, meter_name: str, line_text: str) -> Dict[str, Any]:
        tpl = self.get_meter_template(meter_name)
        if not tpl:
            return {'error': f"Meter '{meter_name}' not found in composition catalog"}

        target_pattern = tpl['pattern']
        target_lg = target_pattern.replace('L', 'ल').replace('G', 'ग')
        target_len = len(target_pattern)

        scan = self._scan_line(line_text)
        if not scan:
            return {
                'meter': tpl,
                'syllables': [],
                'current_lg': [],
                'matches': [],
                'mismatches': [],
                'next_expected': target_lg[0] if target_lg else 'ल',
                'remaining': target_len,
                'complete': False,
                'is_valid': False
            }

        syllables = [s for ln in scan['syllables'] for w in ln for s in w]
        current_lg = [self.output_map.get(m, m) for m in scan['lg_marks'] if m]

        matches = []
        mismatches = []
        is_valid = True

        for i, curr in enumerate(current_lg):
            if i < target_len:
                exp = target_lg[i]
                if exp == '-' or exp == curr:
                    matches.append(i)
                elif i == target_len - 1 and curr == 'ल' and exp == 'ग':
                    # Padanta-Guru promotion allowed on final syllable
                    matches.append(i)
                else:
                    mismatches.append(i)
                    is_valid = False
            else:
                mismatches.append(i)
                is_valid = False

        complete = (len(current_lg) == target_len and is_valid)
        next_expected = target_lg[len(current_lg)] if len(current_lg) < target_len else None
        remaining = max(0, target_len - len(current_lg))

        return {
            'meter': tpl,
            'syllables': syllables,
            'current_lg': current_lg,
            'matches': matches,
            'mismatches': mismatches,
            'next_expected': next_expected,
            'remaining': remaining,
            'complete': complete,
            'is_valid': is_valid
        }

    ###########################################################################
    # Summary & Formatters
    ###########################################################################

    def summarize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        line_results = results.get('line', [])
        verse_results = results.get('verse', [])

        match_line_statistics = defaultdict(Counter)
        fuzzy_line_statistics = defaultdict(Counter)
        verse_statistics = defaultdict(Counter)
        counts = defaultdict(int)

        for line_answer in line_results:
            counts['line'] += 1
            line_result = line_answer.get('result', line_answer)
            if line_result.get('found'):
                counts['match_line'] += 1
                chanda_list = [c.strip() for c in line_result.get('display_chanda', '').split('/') if c.strip()]
                gana_list = [g.strip() for g in line_result.get('display_gana', '').split('/') if g.strip()]
                match_line_statistics['chanda'].update(chanda_list)
                match_line_statistics['gana'].update(gana_list)
            else:
                counts['fuzzy_line'] += 1
                for idx, fuzzy_match in enumerate(line_result.get('fuzzy', [])):
                    if idx == 0:
                        counts['mismatch_syllable'] += fuzzy_match.get('cost', 0)
                    chanda_list = [c.strip() for c in fuzzy_match.get('display_chanda', '').split('/') if c.strip()]
                    fuzzy_line_statistics['chanda'].update(chanda_list)
                    break

        for verse_result in verse_results:
            counts['verse'] += 1
            chanda_list, chanda_score = verse_result.get('chanda', ([], 0))
            if chanda_score == len(verse_result.get('lines', [])):
                counts['match_verse'] += 1
            else:
                counts['fuzzy_verse'] += 1
            verse_statistics['chanda'].update(chanda_list)

        return {
            'verse': verse_statistics,
            'line': {
                'fuzzy': fuzzy_line_statistics,
                'match': match_line_statistics,
            },
            'count': counts
        }

    @staticmethod
    def format_chanda_pada(chanda: str, pada: tuple) -> str:
        if not pada:
            return chanda
        if len(pada) == 1:
            return f"{chanda} (पाद {pada[0]})" if pada[0] else chanda
        if len(pada) == 2:
            return f"{chanda} (पाद {pada[0]}-{pada[1]})"
        if len(pada) == 4:
            return f"{chanda} (पाद {pada[0]}-{pada[3]})"
        return chanda

    @classmethod
    def format_line_result(cls, line_result: Dict[str, Any]) -> str:
        output_lines = [
            line_result.get('display_line', ''),
            f"\tSyllables: {' | '.join(line_result.get('display_syllables', []))}",
            f"\tLG: {' '.join(line_result.get('display_lg', []))}",
            f"\tGa\u1e47a: {line_result.get('display_gana', '')}",
            f"\tCounts: {line_result.get('display_length', 0)} syllables, {line_result.get('display_matra', 0)} morae",
            f"\tChanda: {line_result.get('display_chanda', 'Not found')}",
            f"\tJ\u0101ti: {line_result.get('display_jaati', 'Unknown')}"
        ]
        if line_result.get('fuzzy'):
            best_match = line_result['fuzzy'][0]
            sim = best_match.get('similarity', 0.0)
            output_lines.extend([
                f"\tFuzzy: {best_match.get('display_chanda', '')} ({sim:.1%})",
                f"\t\tSuggestion: {best_match.get('suggestion', '')}"
            ])
        return "\n".join(output_lines)

    @staticmethod
    def format_summary(result_summary: Dict[str, Any]) -> str:
        output = []
        if result_summary.get("verse") and result_summary["verse"].get("chanda"):
            output.extend([
                "Verse Statistics",
                "----------------"
            ])
            for idx, (chanda_name, chanda_count) in enumerate(
                result_summary["verse"]["chanda"].most_common(),
                start=1
            ):
                output.append(f"{idx:>4}. {chanda_name}: {chanda_count}")
            output.append("")

        output.extend([
            "Line Statistics",
            "---------------"
        ])

        if result_summary.get("line", {}).get("match", {}).get("chanda"):
            output.append("-- Exact Match")
            for idx, (chanda_name, chanda_count) in enumerate(
                result_summary["line"]["match"]["chanda"].most_common(),
                start=1
            ):
                output.append(f"{idx:>4}. {chanda_name}: {chanda_count}")
            output.append("")

        if result_summary.get("line", {}).get("fuzzy", {}).get("chanda"):
            output.append("-- Fuzzy Match")
            for idx, (chanda_name, chanda_count) in enumerate(
                result_summary["line"]["fuzzy"]["chanda"].most_common(),
                start=1
            ):
                output.append(f"{idx:>4}. {chanda_name}: {chanda_count}")
            output.append("")

        counts = result_summary.get("count", {})
        output.extend([
            "Counts",
            "------",
            f"* Total Lines: {counts.get('line', 0)}",
            f"  - Exact Match: {counts.get('match_line', 0)}",
            f"  - Fuzzy Match: {counts.get('fuzzy_line', 0)}",
            f"* Total Verses: {counts.get('verse', 0)}",
            f"  - Exact Match: {counts.get('match_verse', 0)}",
            f"  - Fuzzy Match: {counts.get('fuzzy_verse', 0)}",
            f"* Total Syllables Mismatched: {counts.get('mismatch_syllable', 0)}",
        ])

        return "\n".join(output)
