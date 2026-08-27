#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Flask Web Routes.
"""

import unittest
from app import app


class TestWebAppRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Chandoj', response.data)

    def test_about_page(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About Sanskrit Prosody', response.data)

    def test_text_page_get(self):
        response = self.client.get('/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Identify from Text', response.data)

    def test_text_page_post(self):
        response = self.client.post('/text', data={
            'input_text': 'नमस्ते सदा वत्सले मातृभूमे',
            'text_mode': 'line',
            'output_scheme': 'devanagari'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xe0\xa4\xad\xe0\xa5\x81\xe0\xa4\x9c\xe0\xa4\x99\xe0\xa5\x8d\xe0\xa4\x97\xe0\xa4\xaa\xe0\xa5\x8d\xe0\xa4\xb0\xe0\xa4\xaf\xe0\xa4\xbe\xe0\xa4\xa4', response.data) # Devanagari भुजङ्गप्रयात

    def test_image_page_get(self):
        response = self.client.get('/image')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Identify from Image', response.data)

    def test_file_page_get(self):
        response = self.client.get('/file')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Identify from Text File', response.data)

    def test_examples_page(self):
        response = self.client.get('/examples')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Classical Sanskrit Meter Examples', response.data)

    def test_help_page(self):
        response = self.client.get('/help')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'What is a Chanda', response.data)

    def test_api_analyze(self):
        response = self.client.post('/api/analyze', json={
            'text': 'नमस्ते सदा वत्सले मातृभूमे',
            'verse_mode': False,
            'fuzzy': True
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['result']['line']), 1)
        line_res = data['result']['line'][0]['result']
        self.assertTrue(line_res['found'])


if __name__ == '__main__':
    unittest.main()
