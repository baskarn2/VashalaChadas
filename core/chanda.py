#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Sanskrit Meter Identification and Scansion Engine.

Handles Akṣara-gaṇa-vṛtta, Mātrā-vṛtta, Ardhasama-vṛtta, Viṣama-vṛtta,
and Upajāti meters with exact matching, Levenshtein fuzzy matching,
verse-level aggregations, and multi-script transliteration.
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


class Chanda:
    """Chanda (Sanskrit Meter) Identifier and Scansion Engine"""
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
    # Prosody & Syllable Marking
    ###########################################################################

    @functools.lru_cache(maxsize=MAX_CACHE)
    def mark_lg(self, text: str) -> Tuple[List[List[List[str]]], List[str]]:
        """
        Mark Laghu-Guru for Devanagari text.

        Returns
        -------
        syllables : list
            Nested syllable structure from skt tokenizer.
        lg_marks : list[str]
            Laghu ('L') / Guru ('G') / empty ('') marks for each syllable.
        """
        skip_syllables = [skt.AVAGRAHA]
        lg_marks = []
        syllables = skt.get_syllables(text)
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        if not flat_syllables:
            return flat_syllables, lg_marks

        for idx, syllable in enumerate(flat_syllables[:-1]):
            if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
                lg_marks.append('')
                continue
            laghu = (
                skt.is_laghu(syllable) and
                (skt.HALANTA not in flat_syllables[idx + 1])
            )
            lg_marks.append(self.L if laghu else self.G)

        # Handle the last syllable
        syllable = flat_syllables[-1]
        if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
            lg_marks.append('')
        else:
            lg_marks.append(self.L if skt.is_laghu(syllable) else self.G)

        return syllables, lg_marks

    def _scan_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Scan line, return syllables, marks and clean LG string."""
        clean_line = skt.clean(line).strip()
        if not clean_line:
            return None

        syllables, lg_marks = self.mark_lg(clean_line)
        lg_str = ''.join(self.input_map.get(m, m) for m in lg_marks if m)
        if not lg_str:
            return None

        return {
            'line': clean_line,
            'syllables': syllables,
            'lg_marks': lg_marks,
            'lg_str': lg_str
        }

    # ----------------------------------------------------------------------- #

    def lg_to_gana(self, lg_str: str) -> str:
        """Transform Laghu-Guru string into Gana string (e.g. LGL -> J)"""
        gana = []
        for i in range(0, len(lg_str), 3):
            group = lg_str[i:i + 3]
            gana.append(self.gana_inv.get(group, group))
        return ''.join(gana)

    def gana_to_lg(self, gana_str: str) -> str:
        """Transform Gana string into Laghu-Guru string"""
        return gana_str.translate(str.maketrans(self.gana))

    def count_matra(self, gana_str: str) -> int:
        """Count matra from a Gana or Laghu-Guru string"""
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
        """Read all definitions from data path."""
        self.read_jaati(os.path.join(self.data_path, 'chanda_jaati.csv'))
        for fname in ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv', 'chanda_upajaati.csv']:
            fpath = os.path.join(self.data_path, fname)
            if os.path.exists(fpath):
                self.read_chanda_definitions(fpath)
        self.read_matra_definitions(os.path.join(self.data_path, 'chanda_matra.csv'))

    def read_examples(self) -> Dict[str, List[str]]:
        """Load curated examples from examples.json."""
        ex_path = os.path.join(self.data_path, 'examples.json')
        if os.path.exists(ex_path):
            with open(ex_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    ###########################################################################
    # Text Processing & Scheme Detection
    ###########################################################################

    def process_text(self, text: str) -> Tuple[List[str], str]:
        """Detect transliteration scheme and return cleaned Devanagari lines."""
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

    def _lookup_lg(self, lg_str: str, dictionary: Dict[str, Any]) -> Tuple[str, List, bool]:
        """Lookup LG pattern with optional terminal syllable fallback."""
        if lg_str in dictionary:
            return lg_str, dictionary[lg_str], True

        # Sanskrit metric convention: last syllable can be treated as Guru
        if lg_str:
            last = lg_str[-1]
            alt_last = self.G if last == self.L else self.L
            alt_lg = lg_str[:-1] + alt_last
            if alt_lg in dictionary:
                return alt_lg, dictionary[alt_lg], True

        return lg_str, [], False

    def find_direct_match(self, line: str, multi: bool = False) -> Optional[Dict[str, Any]]:
        scan = self._scan_line(line)
        if scan is None:
            return None

        dictionary = self.MULTI_CHANDA if multi else self.SINGLE_CHANDA
        match_lg, chanda_list, found = self._lookup_lg(scan['lg_str'], dictionary)

        chanda = []
        jaati = []
        gana = []
        length = []
        matra = []

        if found:
            chanda += chanda_list

        if not multi:
            jaati = self.JAATI.get(len(match_lg), self.JAATI.get(-1, ('अज्ञात',)))
            gana = [self.lg_to_gana(match_lg)]
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
            gana = [
                f"({', '.join(self.lg_to_gana(s) for s in split_group)})"
                for split_group in splits
            ]
            length = [
                f"({' + '.join(str(len(s)) for s in split_group)})"
                for split_group in splits
            ]
            matra = [
                f"({' + '.join(str(self.count_matra(s)) for s in split_group)})"
                for split_group in splits
            ]

        return {
            'found': found,
            'syllables': scan['syllables'],
            'lg': scan['lg_marks'],
            'gana': gana,
            'chanda': chanda,
            'jaati': list(jaati),
            'length': length,
            'matra': matra
        }

    def find_matra_match(self, matra_counts: Tuple[int, ...]) -> Dict[str, Any]:
        """Check for Mātrā-vṛtta matches (e.g. Āryā: 12-18-12-15)."""
        found = matra_counts in self.MATRA_CHANDA
        chanda = []
        if found:
            chanda = self.MATRA_CHANDA.get(matra_counts, [])
        elif len(matra_counts) == 2:
            # 2-line verse collapsing 4 padas (p1+p2, p3+p4)
            collapsed = []
            for pattern, meters in self.MATRA_CHANDA.items():
                if len(pattern) == 4 and (pattern[0] + pattern[1], pattern[2] + pattern[3]) == matra_counts:
                    collapsed.extend(meters)
            if collapsed:
                found = True
                chanda = collapsed

        matra_str = '-'.join(str(m) for m in matra_counts)
        return {
            'found': found,
            'chanda': chanda,
            'matra_pattern': matra_counts,
            'matra_display': matra_str,
            'is_matra_vrtta': True
        }

    ###########################################################################
    # Fuzzy Matching
    ###########################################################################

    def _editops(self, s1: str, s2: str, replace_cost: int = 1, delete_cost: int = 1, insert_cost: int = 1, max_diff: int = 3):
        """Compute Levenshtein edit operations with early termination."""
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
        """Annotate syllable sequence with edit operations."""
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
        """
        Analyze a single line of Sanskrit text.

        Returns full dictionary formatted for both web views and JSON APIs.
        """
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

        regex_matches = [rk for rk in self.CHANDA if re.match(f'^{rk}$', lg_str)]
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

        full_lg = [self.output_map.get(c, c) for c in direct_match['lg']]
        full_length = len(lg_str)
        full_matra = self.count_matra(lg_str)
        full_gana = self.lg_to_gana(lg_str).translate(self.ttable_out)
        full_jaati = self.JAATI.get(len(lg_str), self.JAATI.get(-1, ('अज्ञात',)))

        # Display properties
        display_line = line
        display_syllables = [s for ln in direct_match['syllables'] for w in ln for s in w]
        display_lg = full_lg
        display_gana = ' / '.join(gana).translate(self.ttable_out) if gana else full_gana
        display_length = ' / '.join(length) if length else full_length
        display_matra = ' / '.join(matra) if matra else full_matra
        display_chanda = ' / '.join(self.format_chanda_pada(c, p) for c, p in chanda)
        display_jaati = ' / '.join(jaati if jaati else full_jaati)

        answer['found'] = found
        answer['syllables'] = display_syllables
        answer['lg'] = full_lg
        answer['gana'] = full_gana
        answer['length'] = full_length
        answer['matra'] = full_matra
        answer['chanda'] = chanda
        answer['jaati'] = jaati

        answer['display_scheme'] = output_scheme
        answer['display_line'] = display_line
        answer['display_syllables'] = display_syllables
        answer['display_lg'] = display_lg
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
        """
        Analyze multi-line text or verse with statistics & export files.
        """
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

                    # Reorder fuzzy matches in the verse lines to prioritize winning meter
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

        # Format simple text scansion for export
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
    # Summary & Statistics
    ###########################################################################

    def summarize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate line and verse counts & statistics."""
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

    ###########################################################################
    # String Formatters
    ###########################################################################

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
