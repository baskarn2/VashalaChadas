#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for विशालवृत्तावलिः (Viśālavṛttāvaliḥ) Prosody Engine.
"""

import unittest
from core.chanda import Chanda, STANDARD_METER_TEMPLATES


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
        self.assertEqual(res['length'], 16)

    def test_bhujangaprayata_scansion(self):
        text = "नमस्ते सदा वत्सले मातृभूमे"
        res = self.chanda.identify_line(text)
        self.assertTrue(res['found'])
        meter_names = [c[0] for c in res['chanda']]
        self.assertIn('भुजङ्गप्रयात', meter_names)
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
        text = "नमस्ते सद वत्सले मातृभूमे"
        res = self.chanda.identify_line(text, fuzzy=True)
        self.assertFalse(res['found'])
        self.assertTrue(len(res['fuzzy']) > 0)
        best_fuzzy = res['fuzzy'][0]
        self.assertIn('भुजङ्गप्रयात', best_fuzzy['display_chanda'])
        self.assertGreater(best_fuzzy['similarity'], 0.8)
        self.assertEqual(best_fuzzy['cost'], 1)
        self.assertIn('r(द)[G]', best_fuzzy['suggestion'])

    def test_upajati_detection(self):
        kumarasambhava = """अस्त्युत्तरस्यां दिशि देवतात्मा
हिमालयो नाम नगाधिराजः।
पूर्वापरौ वारिनिधी विगाह्य
स्थितः पृथिव्या इव मानदण्डः॥"""
        ans = self.chanda.identify_from_text(kumarasambhava, verse=True, fuzzy=True)
        results = ans['result']
        self.assertEqual(len(results['verse']), 1)
        verse_winner = results['verse'][0]['chanda']
        self.assertTrue(any('उपजाति' in name for name in verse_winner[0]))
        self.assertEqual(verse_winner[1], 4.0)

    def test_composition_evaluator(self):
        line = "लोकाभिरामं रणरङ्गधीरं"
        res = self.chanda.evaluate_composition("इन्द्रवज्रा", line)
        self.assertTrue(res['complete'])
        self.assertEqual(res['remaining'], 0)
        self.assertEqual(len(res['matches']), 11)
        self.assertEqual(len(res['mismatches']), 0)

        partial_line = "कश्चित्कान्ताविरह"
        part_res = self.chanda.evaluate_composition("मन्दाक्रान्ता", partial_line)
        self.assertFalse(part_res['complete'])
        self.assertEqual(part_res['next_expected'], 'ल')
        self.assertGreater(part_res['remaining'], 0)


if __name__ == '__main__':
    unittest.main()
