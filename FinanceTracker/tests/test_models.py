from django.test import TestCase
from django.contrib.auth.models import User
from FinTech.models import IncomeCategory, ExpenseCategory, Income, Expense, Account
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

class CategoryModelTest(TestCase):
    
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_income_category_creation(self):
        # Create an IncomeCategory instance
        income_category = IncomeCategory.objects.create(name='Salary', user=self.user)
        
        # Check if the category was created successfully
        self.assertEqual(income_category.name, 'Salary')
        self.assertEqual(income_category.user, self.user)
        self.assertIsInstance(income_category, IncomeCategory)

    def test_expense_category_creation(self):
        # Create an ExpenseCategory instance
        expense_category = ExpenseCategory.objects.create(name='Food', user=self.user)
        
        # Check if the category was created successfully
        self.assertEqual(expense_category.name, 'Food')
        self.assertEqual(expense_category.user, self.user)
        self.assertIsInstance(expense_category, ExpenseCategory)

    def test_income_category_str_method(self):
        # Create an IncomeCategory instance
        income_category = IncomeCategory.objects.create(name='Salary', user=self.user)
        
        # Check if the string representation is correct
        self.assertEqual(str(income_category), 'Salary')

    def test_expense_category_str_method(self):
        # Create an ExpenseCategory instance
        expense_category = ExpenseCategory.objects.create(name='Food', user=self.user)
        
        # Check if the string representation is correct
        self.assertEqual(str(expense_category), 'Food')

    def test_income_category_user_relationship(self):
        # Create an IncomeCategory instance
        income_category = IncomeCategory.objects.create(name='Bonus', user=self.user)
        
        # Check if the user relationship is correct
        self.assertEqual(income_category.user.username, 'testuser')
        self.assertEqual(self.user.user_inc_catg.count(), 1)  # Check that the user has 1 income category

    def test_expense_category_user_relationship(self):
        # Create an ExpenseCategory instance
        expense_category = ExpenseCategory.objects.create(name='Transport', user=self.user)
        
        # Check if the user relationship is correct
        self.assertEqual(expense_category.user.username, 'testuser')
        self.assertEqual(self.user.user_exp_catg.count(), 1)  # Check that the user has 1 expense category


class TransactionModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        
        # Create test categories
        self.income_category = IncomeCategory.objects.create(
            name='Salary',
            user=self.user
        )
        self.expense_category = ExpenseCategory.objects.create(
            name='Food',
            user=self.user
        )
        
        # Create test account
        self.account = Account.objects.create(
            user=self.user,
            name='Test Account',
            balance=1000.00,
            details='Test account for transactions'
        )

    def test_income_creation(self):
        income = Income.objects.create(
            user=self.user,
            name='Monthly Salary',
            amount=5000.00,
            category=self.income_category,
            note='Regular monthly salary'
        )
        
        self.assertEqual(income.name, 'Monthly Salary')
        self.assertEqual(income.amount, 5000.00)
        self.assertEqual(income.note, 'Regular monthly salary')
        self.assertEqual(str(income), f"Rs.{income.amount} received for {income.name}")
        self.assertEqual(income.user.Inc_user_name.first(), income)

    def test_expense_creation(self):
        expense = Expense.objects.create(
            user=self.user,
            name='Grocery Shopping',
            amount=100.00,
            category=self.expense_category,
            note='Monthly groceries'
        )
        
        self.assertEqual(expense.name, 'Grocery Shopping')
        self.assertEqual(expense.amount, 100.00)
        self.assertEqual(expense.note, 'Monthly groceries')
        self.assertEqual(str(expense), f"Rs.{expense.amount} spent for {expense.name}")
        self.assertEqual(expense.user.Exp_user_name.first(), expense)

    def test_income_mandatory_note_field(self):
        # Test that note field is mandatory for Income
        with self.assertRaises(IntegrityError):
            Income.objects.create(
                user=self.user,
                name='Test Income',
                amount=1000.00,
                category=self.income_category,
                note=None
            )

    def test_expense_mandatory_note_field(self):
        # Test that note field is mandatory for Expense
        with self.assertRaises(IntegrityError):
            Expense.objects.create(
                user=self.user,
                name='Test Expense',
                amount=100.00,
                category=self.expense_category,
                note=None
            )

    def test_default_date(self):
        # Test that date defaults to current date for Income
        income = Income.objects.create(
            user=self.user,
            name='Test Income',
            amount=1000.00,
            category=self.income_category,
            note='Test note'
        )
        self.assertEqual(income.date.date(), timezone.now().date())
        
        # Test that date defaults to current date for Expense
        expense = Expense.objects.create(
            user=self.user,
            name='Test Expense',
            amount=100.00,
            category=self.expense_category,
            note='Test note'
        )
        self.assertEqual(expense.date.date(), timezone.now().date())

    def test_category_relationship(self):
        # Test Income category relationship
        income = Income.objects.create(
            user=self.user,
            name='Test Income',
            amount=1000.00,
            category=self.income_category,
            note='Test note'
        )
        self.assertEqual(income.category.income_catg.first(), income)
        
        # Test Expense category relationship
        expense = Expense.objects.create(
            user=self.user,
            name='Test Expense',
            amount=100.00,
            category=self.expense_category,
            note='Test note'
        )
        self.assertEqual(expense.category.expense_catg.first(), expense)

    def test_user_relationship(self):
        # Create multiple transactions
        income1 = Income.objects.create(
            user=self.user,
            name='Income 1',
            amount=1000.00,
            category=self.income_category,
            note='Test note 1'
        )
        income2 = Income.objects.create(
            user=self.user,
            name='Income 2',
            amount=2000.00,
            category=self.income_category,
            note='Test note 2'
        )
        expense1 = Expense.objects.create(
            user=self.user,
            name='Expense 1',
            amount=500.00,
            category=self.expense_category,
            note='Test note 3'
        )
        expense2 = Expense.objects.create(
            user=self.user,
            name='Expense 2',
            amount=300.00,
            category=self.expense_category,
            note='Test note 4'
        )
        
        # Test user-transaction relationships
        self.assertEqual(self.user.Inc_user_name.count(), 2)
        self.assertEqual(self.user.Exp_user_name.count(), 2)
        self.assertIn(income1, self.user.Inc_user_name.all())
        self.assertIn(income2, self.user.Inc_user_name.all())
        self.assertIn(expense1, self.user.Exp_user_name.all())
        self.assertIn(expense2, self.user.Exp_user_name.all())
