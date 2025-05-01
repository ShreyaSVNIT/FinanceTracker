from django import forms
from .models import Income, Expense, IncomeCategory, ExpenseCategory, Account
from django.core.exceptions import ValidationError
from django.utils import timezone

# ------------------------
# Shared date validation for both forms
# ------------------------
class BaseTransactionForm(forms.ModelForm):
    """Base class for transaction forms with common validation logic"""
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError("Date cannot be in the future")
        return date

# ------------------------
# Category Forms
# ------------------------
class IncomeCategoryForm(forms.ModelForm):
    class Meta:
        model = IncomeCategory
        fields = ['name']
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 2:
            raise ValidationError('Category name must be at least 2 characters long')
        return name

class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name']
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 2:
            raise ValidationError('Category name must be at least 2 characters long')
        return name

# ------------------------
# Income Form (now mirrors ExpenseForm)
# ------------------------
class IncomeForm(BaseTransactionForm):
    class Meta:
        model = Income
        fields = ['name', 'category', 'amount', 'date', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_category(self):
        category = self.cleaned_data.get('category')
        print(f"[DEBUG] IncomeForm clean_category - value: {category}")
        if not category:
            print(f"[DEBUG] IncomeForm clean_category - invalid category")
            raise ValidationError("Please select a valid category")
        return category

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        print(f"[DEBUG] IncomeForm clean_amount - value: {amount}")
        if not amount or amount <= 0:
            print(f"[DEBUG] IncomeForm clean_amount - invalid amount")
            raise ValidationError("Amount must be greater than zero")
        if amount != round(amount, 2):
            raise ValidationError("Amount cannot have more than 2 decimal places")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        print(f"[DEBUG] IncomeForm clean method - cleaned_data: {cleaned_data}")
        # Add custom income-related validation here if needed
        return cleaned_data

# ------------------------
# Expense Form (unchanged)
# ------------------------
class ExpenseForm(BaseTransactionForm):
    class Meta:
        model = Expense
        fields = ['name', 'category', 'amount', 'date', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_category(self):
        category = self.cleaned_data.get('category')
        print(f"[DEBUG] ExpenseForm clean_category - value: {category}")
        if not category:
            print(f"[DEBUG] ExpenseForm clean_category - invalid category")
            raise ValidationError("Please select a valid category")
        return category

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        print(f"[DEBUG] ExpenseForm clean_amount - value: {amount}")
        if not amount or amount <= 0:
            print(f"[DEBUG] ExpenseForm clean_amount - invalid amount")
            raise ValidationError("Amount must be greater than zero")
        if amount != round(amount, 2):
            raise ValidationError("Amount cannot have more than 2 decimal places")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        print(f"[DEBUG] ExpenseForm clean method - cleaned_data: {cleaned_data}")
        
        if 'user' in self.initial:
            user = self.initial['user']
            try:
                account = Account.objects.get(user=user)
                if 'amount' in cleaned_data and account.balance < cleaned_data['amount']:
                    print(f"[DEBUG] ExpenseForm clean - insufficient balance. Required: {cleaned_data['amount']}, Available: {account.balance}")
                    raise ValidationError({
                        'amount': f'Insufficient balance. Available: {account.balance:.2f}'
                    })
            except Account.DoesNotExist:
                print(f"[DEBUG] ExpenseForm clean - account does not exist for user: {user.id}")
                raise ValidationError("Account not found. Please contact support.")
        return cleaned_data
