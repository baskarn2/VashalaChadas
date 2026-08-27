#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for विशालवृत्तावलिः Flask Web Routes.
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
        self.assertIn('विशालवृत्तावलिः'.encode('utf-8'), response.data)
        self.assertIn(b'GitHub: baskarn2/VashalaChadas', response.data)

    def test_about_page(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn('विशालवृत्तावलिः'.encode('utf-8'), response.data)
        self.assertIn('Akṣaragaṇa-vṛtta'.encode('utf-8'), response.data)
        self.assertIn('Mātrā-vṛtta'.encode('utf-8'), response.data)

    def test_compose_page_get(self):
        response = self.client.get('/compose')
        self.assertEqual(response.status_code, 200)
        self.assertIn('काव्यसहायकः'.encode('utf-8'), response.data)

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
        self.assertIn('भुजङ्गप्रयात'.encode('utf-8'), response.data)

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
        self.assertIn('उपजाति'.encode('utf-8'), response.data)

    def test_api_analyze(self):
        response = self.client.post('/api/analyze', json={
            'text': 'नमस्ते सदा वत्सले मातृभूमे',
            'verse_mode': False,
            'fuzzy': True
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_api_compose_check(self):
        response = self.client.post('/api/compose-check', json={
            'meter': 'इन्द्रवज्रा',
            'text': 'लोकाभिरामं रणरङ्गधीरं'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['complete'])

    def test_api_meters(self):
        response = self.client.get('/api/meters')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('मन्दाक्रान्ता', data['meters'])


if __name__ == '__main__':
    unittest.main()
