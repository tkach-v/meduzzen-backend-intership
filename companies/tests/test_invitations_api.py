"""
Tests for invitations API.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from companies.models import Company, CompanyInvitation, InvitationStatuses


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

        self.user1_token = self.client.post('/api/jwt/create/', self.user_1_payload).data['access']
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.user1_token)

    def test_list_company_invitations(self):
        url = f'/api/companies/{self.company.id}/invitations/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_company_invitation(self):
        url = f'/api/companies/{self.company.id}/invitations/'
        response = self.client.post(url, {'recipient': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        invitation = CompanyInvitation.objects.get(id=response.data['id'])
        self.assertEqual(getattr(invitation, 'status'), InvitationStatuses.PENDING)
        self.assertEqual(getattr(invitation, 'sender').id, self.user1.id)
        self.assertEqual(getattr(invitation, 'recipient').id, self.user2.id)
        self.assertEqual(getattr(invitation, 'company').id, self.company.id)

    def test_revoke_company_invitation(self):
        invitation = CompanyInvitation.objects.create(
            sender=self.user1,
            recipient=self.user2,
            company=self.company,
        )

        url = f'/api/companies/{self.company.id}/invitations/{invitation.id}/revoke/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatuses.REVOKED)

    def test_list_user_invitations(self):
        invitation = CompanyInvitation.objects.create(
            sender=self.user1,
            recipient=self.user2,
            company=self.company,
        )

        self.user2_token = self.client.post('/api/jwt/create/', self.user_2_payload).data['access']
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.user2_token)

        url = '/api/users/me/invitations/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(invitation.id, response.data['results'][0]['id'])

    def test_accept_invitation(self):
        invitation = CompanyInvitation.objects.create(
            sender=self.user1,
            recipient=self.user2,
            company=self.company,
        )

        self.user2_token = self.client.post('/api/jwt/create/', self.user_2_payload).data['access']
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.user2_token)

        url = f'/api/users/me/invitations/{invitation.id}/accept/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatuses.ACCEPTED)

    def test_decline_invitation(self):
        invitation = CompanyInvitation.objects.create(
            sender=self.user1,
            recipient=self.user2,
            company=self.company,
        )

        self.user2_token = self.client.post('/api/jwt/create/', self.user_2_payload).data['access']
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.user2_token)

        url = f'/api/users/me/invitations/{invitation.id}/decline/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatuses.DECLINED)
