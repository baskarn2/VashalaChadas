#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Sanskrit Meter Scansion Engine.
"""

import unittest
from core.chanda import Chanda


class TestChandaEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chanda = Chanda()

    def test_anustubh_scansion(self):
        text = "को न्वस्मिन् साम्प्रतं लोके गुणवान् कश्च वीर्यवान्"
        res = self.chanda.identify_line(text)
        self.assertTrue(res['found'])
        meter_names = [c[0] for c in res['chanda']]
        self.assertIn('अनुष्टुभ्', meter_names)
        self.assertEqual(res['length'], 16) # 16 vocalic syllables (8+8 padas)

    def test_bhujangaprayata_scansion(self):
        text = "नमस्ते सदा वत्सले मातृभूमे"
        res = self.chanda.identify_line(text)
        self.assertTrue(res['found'])
        meter_names = [c[0] for c in res['chanda']]
        self.assertIn('भुजङ्गप्रयात', meter_names)
        # Gana pattern for Bhujangaprayata is Y Y Y Y
        self.assertIn('य', res['gana'])

    def test_shardulavikridita_scansion(self):
        text = "विद्या नाम नरस्य रूपमधिकं प्रच्छन्नगुप्तं धनम्"
        res = self.chanda.identify_line(text)
        self.assertTrue(res['found'])
        meter_names = [c[0] for c in res['chanda']]
        self.assertIn('शार्दूलविक्रीडित', meter_names)

    def test_mandakranta_scansion(self):
        text = "कश्चित्कान्ताविरहगुरुणा स्वाधिकारात्प्रमत्तः"
        res = self.chanda.identify_line(text)
        self.assertTrue(res['found'])
        meter_names = [c[0] for c in res['chanda']]
        self.assertIn('मन्दाक्रान्ता', meter_names)

    def test_iast_input(self):
        text = "namaste sadā vatsale mātṛbhūme"
        res = self.chanda.identify_line(text, scheme='iast')
        self.assertTrue(res['found'])
        meter_names = [c[0] for c in res['chanda']]
        self.assertIn('भुजङ्गप्रयात', meter_names)

    def test_fuzzy_matching(self):
        # Altered syllable weight: 'सद' (Laghu) instead of 'सदा' (Guru)
        text = "नमस्ते सद वत्सले मातृभूमे"
        res = self.chanda.identify_line(text, fuzzy=True)
        self.assertFalse(res['found'])
        self.assertTrue(len(res['fuzzy']) > 0)
        best_fuzzy = res['fuzzy'][0]
        self.assertIn('भुजङ्गप्रयात', best_fuzzy['display_chanda'])
        self.assertGreater(best_fuzzy['similarity'], 0.8)
        self.assertEqual(best_fuzzy['cost'], 1)
        self.assertIn('r(द)[G]', best_fuzzy['suggestion'])

    def test_verse_mode_analysis(self):
        verse = """को न्वस्मिन् साम्प्रतं लोके गुणवान् कश्च वीर्यवान्।
धर्मज्ञश्च कृतज्ञश्च सत्यवाक्यो दृढव्रतः॥
चारित्रेण च को युक्तः सर्वभूतेषु को हितः।
विद्वान् कः कः समर्थश्च कश्चैकप्रियदर्शनः॥"""
        ans = self.chanda.identify_from_text(verse, verse=True, fuzzy=True)
        results = ans['result']
        self.assertEqual(len(results['line']), 4)
        self.assertEqual(len(results['verse']), 1)
        verse_winner = results['verse'][0]['chanda']
        self.assertIn('अनुष्टुभ्', verse_winner[0])


if __name__ == '__main__':
    unittest.main()
