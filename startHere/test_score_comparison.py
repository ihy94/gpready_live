from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from startHere.models import Category, Record
from startHere.views import ScoreComparisonView
from subscription.models import Package, Subscription


class ScoreComparisonViewTests(TestCase):
    def setUp(self):
        self.package = Package.objects.create(title='AKT', description='Test package')
        self.category = Category.objects.create(title='Clinical medicine')
        self.category.package.add(self.package)
        self.user = get_user_model().objects.create_user(
            email='owner@example.test', username='owner', password='test-password'
        )
        Subscription.objects.create(
            user=self.user,
            package=self.package,
            active=True,
            expiry_date=timezone.now() + timedelta(days=30),
        )
        self.factory = APIRequestFactory()

    def get_response(self, user=None):
        request = self.factory.get('/api/score_comparison/', {'package': self.package.id})
        force_authenticate(request, user=user or self.user)
        return ScoreComparisonView.as_view()(request)

    def add_record(self, user, correct, wrong):
        return Record.objects.create(
            user=user,
            category=self.category,
            correct_answers=correct,
            wrong_answers=wrong,
        )

    def test_returns_aggregate_distribution_only_after_minimum_cohort(self):
        self.add_record(self.user, correct=16, wrong=4)
        User = get_user_model()
        for index in range(30):
            peer = User.objects.create_user(
                email=f'peer{index}@example.test', username=f'peer{index}', password='test-password'
            )
            self.add_record(peer, correct=10, wrong=10)

        response = self.get_response()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['available'])
        self.assertEqual(response.data['accuracy'], 80)
        self.assertEqual(response.data['cohort_size'], 30)
        self.assertEqual(response.data['cohort_average'], 50)
        self.assertEqual(response.data['percentile'], 100)
        self.assertEqual(sum(response.data['histogram']), 30)
        self.assertNotIn('user_id', response.data)

    def test_hides_comparison_for_small_cohort(self):
        self.add_record(self.user, correct=16, wrong=4)
        User = get_user_model()
        for index in range(29):
            peer = User.objects.create_user(
                email=f'peer{index}@example.test', username=f'peer{index}', password='test-password'
            )
            self.add_record(peer, correct=10, wrong=10)

        response = self.get_response()

        self.assertFalse(response.data['available'])
        self.assertEqual(response.data['reason'], 'small_cohort')
        self.assertNotIn('cohort_size', response.data)
        self.assertNotIn('histogram', response.data)

    def test_requires_twenty_personal_attempts(self):
        self.add_record(self.user, correct=9, wrong=10)

        response = self.get_response()

        self.assertFalse(response.data['available'])
        self.assertEqual(response.data['reason'], 'minimum_attempts')
        self.assertEqual(response.data['attempts'], 19)
        self.assertNotIn('histogram', response.data)
