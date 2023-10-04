"""
Tests for health_check app.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_server_status(self):
        res = self.client.get('/api/health_check/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_server_response(self):
        res = self.client.get('/api/health_check/')
        self.assertEqual(res.data, {
            "status_code": 200,
            "detail": "ok",
            "result": "working"
        })
