"""
Tests for requests API.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from companies.models import Company
from users.models import RequestStatuses, UserRequest


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class InvitationsTests(APITestCase):
    def setUp(self):
        self.user_1_payload = {
            'email': 'user1@example.com',
            'password': 'testpass123'
        }

        self.user_2_payload = {
            'email': 'user2@example.com',
            'password': 'testpass123'
        }

        self.user1 = create_user(**self.user_1_payload)
        self.user2 = create_user(**self.user_2_payload)
        self.company = Company.objects.create(name='Company1', owner=self.user1)
        self.company.members.add(self.user1)

        self.user2_token = self.client.post('/api/jwt/create/', self.user_2_payload).data['access']
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.user2_token)

    def test_list_user_requests(self):
        url = '/api/users/me/requests/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_user_request(self):
        url = '/api/users/me/requests/'
        response = self.client.post(url, {'company': self.company.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        request = UserRequest.objects.get(id=response.data['id'])
        self.assertEqual(getattr(request, 'status'), RequestStatuses.PENDING)
        self.assertEqual(getattr(request, 'sender').id, self.user2.id)
        self.assertEqual(getattr(request, 'company').id, self.company.id)

    def test_cancel_user_request(self):
        request = UserRequest.objects.create(
            sender=self.user2,
            company=self.company,
        )

        url = f'/api/users/me/requests/{request.id}/cancel/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request.refresh_from_db()
        self.assertEqual(request.status, RequestStatuses.CANCELLED)

    def test_list_company_requests(self):
        request = UserRequest.objects.create(
            sender=self.user2,
            company=self.company,
        )

        self.user1_token = self.client.post('/api/jwt/create/', self.user_1_payload).data['access']
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.user1_token)

        url = f'/api/companies/{self.company.id}/requests/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(request.id, response.data['results'][0]['id'])

    def test_approve_request(self):
        request = UserRequest.objects.create(
            sender=self.user2,
            company=self.company,
        )

        self.user1_token = self.client.post('/api/jwt/create/', self.user_1_payload).data['access']
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.user1_token)

        url = f'/api/companies/{self.company.id}/requests/{request.id}/approve/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request.refresh_from_db()
        self.assertEqual(request.status, RequestStatuses.APPROVED)

    def test_reject_request(self):
        request = UserRequest.objects.create(
            sender=self.user2,
            company=self.company,
        )

        self.user1_token = self.client.post('/api/jwt/create/', self.user_1_payload).data['access']
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.user1_token)

        url = f'/api/companies/{self.company.id}/requests/{request.id}/reject/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request.refresh_from_db()
        self.assertEqual(request.status, RequestStatuses.REJECTED)
