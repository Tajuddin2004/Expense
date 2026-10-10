from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Expense
from .forms import ExpenseForm


class ExpenseModelTests(TestCase):
    def test_create_expense_success(self):
        expense = Expense.objects.create(
            title="Groceries",
            amount=Decimal("450.50"),
            category="Food",
            date=timezone.now().date(),
            description="Weekly grocery shopping"
        )
        self.assertEqual(expense.title, "Groceries")
        self.assertEqual(expense.amount, Decimal("450.50"))
        self.assertEqual(str(expense), "Groceries - ₹450.50")
        self.assertIsInstance(str(expense), str)


class ExpenseFormTests(TestCase):
    def test_valid_form(self):
        form = ExpenseForm(data={
            'title': 'Metro Card Recharge',
            'amount': '200.00',
            'category': 'Travel',
            'date': '2026-10-10',
            'description': 'Commute'
        })
        self.assertTrue(form.is_valid())

    def test_invalid_zero_amount(self):
        form = ExpenseForm(data={
            'title': 'Free Snack',
            'amount': '0.00',
            'category': 'Food',
            'date': '2026-10-10',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_invalid_negative_amount(self):
        form = ExpenseForm(data={
            'title': 'Refund',
            'amount': '-50.00',
            'category': 'Other',
            'date': '2026-10-10',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_missing_required_title(self):
        form = ExpenseForm(data={
            'title': '',
            'amount': '100.00',
            'category': 'Bills',
            'date': '2026-10-10',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


class ExpenseViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        self.client.login(username="testuser", password="testpassword123")

        self.today = timezone.now().date()
        self.expense1 = Expense.objects.create(
            user=self.user,
            title="Lunch",
            amount=Decimal("150.00"),
            category="Food",
            date=self.today
        )
        self.expense2 = Expense.objects.create(
            user=self.user,
            title="Electricity Bill",
            amount=Decimal("850.00"),
            category="Bills",
            date=self.today
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('expenses:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Spending Overview")
        self.assertEqual(response.context['total_spending'], Decimal("1000.00"))
        self.assertEqual(response.context['expense_count'], 2)

    def test_expense_list_view(self):
        response = self.client.get(reverse('expenses:expense_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lunch")
        self.assertContains(response, "Electricity Bill")

    def test_expense_create_view_post(self):
        data = {
            'title': 'Movie Ticket',
            'amount': '320.00',
            'category': 'Shopping',
            'date': self.today,
            'description': 'Weekend movie'
        }
        response = self.client.post(reverse('expenses:expense_create'), data)
        self.assertRedirects(response, reverse('expenses:expense_list'))
        self.assertTrue(Expense.objects.filter(title="Movie Ticket", user=self.user).exists())

    def test_expense_update_view_post(self):
        data = {
            'title': 'Lunch (Executive)',
            'amount': '250.00',
            'category': 'Food',
            'date': self.today,
            'description': 'Updated price'
        }
        response = self.client.post(reverse('expenses:expense_update', args=[self.expense1.pk]), data)
        self.assertRedirects(response, reverse('expenses:expense_list'))
        self.expense1.refresh_from_db()
        self.assertEqual(self.expense1.title, "Lunch (Executive)")
        self.assertEqual(self.expense1.amount, Decimal("250.00"))

    def test_expense_delete_view_post(self):
        response = self.client.post(reverse('expenses:expense_delete', args=[self.expense1.pk]))
        self.assertRedirects(response, reverse('expenses:expense_list'))
        self.assertFalse(Expense.objects.filter(pk=self.expense1.pk).exists())

    def test_unknown_expense_returns_404(self):
        response = self.client.get(reverse('expenses:expense_update', args=[9999]))
        self.assertEqual(response.status_code, 404)

        delete_response = self.client.get(reverse('expenses:expense_delete', args=[9999]))
        self.assertEqual(delete_response.status_code, 404)
