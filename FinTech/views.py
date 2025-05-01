from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.models import User, auth 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from datetime import datetime, timedelta
from .models import Expense, Income, IncomeCategory, ExpenseCategory, Account, Budget
from .forms import IncomeForm, ExpenseForm, IncomeCategoryForm, ExpenseCategoryForm
# Create your views here.

# Dashboard
def dashboard(request):
    if request.user.is_authenticated:
        my_account = Account.objects.get(user=request.user.id)
        balance = my_account.balance

        # Get today's date at midnight for consistent queries
        today = datetime.now().date()
        ten_days_ago = today - timedelta(days=9)  # For last 10 days including today
        
        # For Last 10 days Income Data (using optimized query)
        incomes_by_day = Income.objects.filter(
            user=request.user.id,
            date__gte=ten_days_ago,
            date__lte=today
        ).order_by('date')

        # Create a dictionary to store daily totals
        daily_income_totals = {(ten_days_ago + timedelta(days=i)): 0 for i in range(10)}
        
        # Calculate daily totals
        for income in incomes_by_day:
            daily_income_totals[income.date] = daily_income_totals.get(income.date, 0) + income.amount

        # Create the final list in chronological order
        Income_last_10days_amount = [daily_income_totals[ten_days_ago + timedelta(days=i)] for i in range(10)]

        # Last 10 days Expense Data (using the same optimized approach)
        expenses_by_day = Expense.objects.filter(
            user=request.user.id,
            date__gte=ten_days_ago,
            date__lte=today
        ).order_by('date')

        # Create a dictionary to store daily totals
        daily_expense_totals = {(ten_days_ago + timedelta(days=i)): 0 for i in range(10)}
        
        # Calculate daily totals
        for expense in expenses_by_day:
            daily_expense_totals[expense.date] = daily_expense_totals.get(expense.date, 0) + expense.amount

        # Create the final list in chronological order
        Expense_last_10days_amount = [daily_expense_totals[ten_days_ago + timedelta(days=i)] for i in range(10)]

        # Category distribution
        out_dict = {}
        my_catg = ExpenseCategory.objects.filter(user=request.user.id)
        for catg in my_catg:
            out_dict[catg.name] = 0

        expenses = Expense.objects.filter(user=request.user.id).order_by('id')
        for expense in expenses:
            catg = expense.category
            out_dict[catg.name] = out_dict[catg.name] + expense.amount

        # Create list from dict, only including categories with expenses
        catg_list = []
        catg_total_list = []
        for catg_name, total in out_dict.items():
            if total > 0:  # Only include categories with expenses
                catg_list.append(catg_name)
                catg_total_list.append(total)

        # Date formatting for x-axis labels
        temp_pre_10days_list = [ten_days_ago + timedelta(days=i) for i in range(10)]
        pre_10days_list = []            
        months = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
            5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        
        for i in temp_pre_10days_list:
            day = i.day
            month = months[i.month]
            pre_10days_list.append(f"{day}/{month}")
        # No need to reverse since we're already building in chronological order

        context = {
            "balance": balance,
            "category_list": catg_list,
            "catg_total_list": catg_total_list,
            "pre_10days_list": pre_10days_list,
            "Income_last_10days_amount": Income_last_10days_amount,
            "Expense_last_10days_amount": Expense_last_10days_amount
        }

        return render(request, "dashboard.html", context)
    else:
        return redirect("/")

# Income
# Income
@login_required(login_url='/')
def incomes(request):  # Changed from 'income' to 'incomes' to match URL pattern
    try:
        print(f"[DEBUG] ================== INCOME VIEW CALLED ==================")
        print(f"[DEBUG] Request method: {request.method}")
        print(f"[DEBUG] User ID: {request.user.id}")
        
        # Get categories for this user
        categories = IncomeCategory.objects.filter(user=request.user)
        print(f"[DEBUG] Found {categories.count()} categories for user {request.user.id}")
        
        # Get incomes for this user
        incomes = Income.objects.filter(user=request.user).order_by('-date')
        print(f"[DEBUG] Found {incomes.count()} incomes")
        
        if incomes.exists():
            for income in incomes:
                try:
                    category_name = income.category.name if income.category else "None"
                    print(f"[DEBUG] Income: {income.id}, {income.name}, {income.amount}, Category: {category_name}")
                except Exception as e:
                    print(f"[DEBUG] Error accessing income data: {str(e)}")
                    
        # Initialize form variable
        form = IncomeForm()
                    
        if request.method == "POST":
            print(f"[DEBUG] POST request received")
            print(f"[DEBUG] Raw POST data: {request.POST}")
            
            # Validate all required fields are present
            required_fields = ['name', 'category', 'amount', 'date']
            missing_fields = []
            
            for field in required_fields:
                if field not in request.POST or not request.POST[field]:
                    missing_fields.append(field)
                    print(f"[DEBUG] Missing required field: {field}")
                    
            if missing_fields:
                for field in missing_fields:
                    messages.error(request, f"Missing required field: {field}")
                print(f"[DEBUG] Form submission halted due to missing fields: {missing_fields}")
                return redirect('/incomes')
            
            # Create and validate form
            form = IncomeForm(request.POST)
            print(f"[DEBUG] Form created, is_bound: {form.is_bound}")
            
            if form.is_valid():
                print(f"[DEBUG] Form is valid")
                try:
                    with transaction.atomic():
                        # Verify category belongs to user
                        category_id = form.cleaned_data['category'].id
                        if not IncomeCategory.objects.filter(id=category_id, user=request.user).exists():
                            error_msg = "Invalid category selected - category doesn't belong to current user"
                            print(f"[DEBUG] {error_msg}")
                            messages.error(request, error_msg)
                            return redirect('/incomes')
                        
                        # Create income record
                        income = form.save(commit=False)
                        income.user = request.user
                        
                        # Get the account and verify it exists
                        try:
                            my_account = get_object_or_404(Account, user=request.user)
                            print(f"[DEBUG] Account found. ID: {my_account.id}, Current balance: {my_account.balance}")
                        except Exception as acc_error:
                            print(f"[DEBUG] Account retrieval error: {str(acc_error)}")
                            messages.error(request, f"Account error: {str(acc_error)}")
                            return redirect('/incomes')
                        
                        # Get amount for logging
                        amount = form.cleaned_data['amount']
                        print(f"[DEBUG] Income amount: {amount}")
                        
                        # Save the income record
                        print(f"[DEBUG] About to save income to database")
                        income.save()
                        print(f"[DEBUG] Income saved successfully with ID: {income.id}")
                        
                        # Update account balance
                        original_balance = my_account.balance
                        my_account.balance += float(amount)
                        my_account.save()
                        print(f"[DEBUG] Account balance updated: {original_balance} -> {my_account.balance}")
                        
                        # Success message and redirect
                        messages.success(request, f"Income '{income.name}' for {income.amount} added successfully!")
                        return redirect('/incomes')
                except Exception as e:
                    print(f"[DEBUG] Unexpected exception: {str(e)}")
                    messages.error(request, f"Error adding income: {str(e)}")
                    return redirect('/incomes')
            else:
                print(f"[DEBUG] Form validation failed: {form.errors}")
                
                # Add error messages for display
                for field, errors in form.errors.items():
                    for error in errors:
                        error_msg = f"{field}: {error}"
                        print(f"[DEBUG] Form error: {error_msg}")
                        messages.error(request, error_msg)
        
        # Render the template with context
        return render(request, "income.html", {
            "categories": categories,
            "incomes": incomes,
            "form": form
        })
        
    except Exception as e:
        print(f"[DEBUG] Error in income view: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('/dashboard')

# Expenses
@login_required(login_url='/')
def expenses(request):
    try:
        # Get user's expense categories
        categories = ExpenseCategory.objects.filter(user=request.user)
        
        # If user has no categories, create a default one
        if not categories.exists():
            print(f"No expense categories found for user {request.user.id}, creating default category")
            ExpenseCategory.objects.create(
                name="General Expense",
                user=request.user
            )
            categories = ExpenseCategory.objects.filter(user=request.user)
        
        # Get user's expenses
        expenses = Expense.objects.filter(user=request.user).order_by('-date')
        
        # Initialize form - this needs to be outside the if/else for request method
        form = ExpenseForm()
        
        # For debugging
        print(f"Found {categories.count()} categories for user {request.user.id}")
        print(f"Found {expenses.count()} expense entries")
        
        if request.method == "POST":
            print(f"[DEBUG] POST request received")
            print(f"[DEBUG] Raw POST data: {request.POST}")
            
            # Validate all required fields are present
            required_fields = ['name', 'category', 'amount', 'date']
            missing_fields = []
            
            for field in required_fields:
                if field not in request.POST or not request.POST[field]:
                    missing_fields.append(field)
                    print(f"[DEBUG] Missing required field: {field}")
                    
            if missing_fields:
                for field in missing_fields:
                    messages.error(request, f"Missing required field: {field}")
                print(f"[DEBUG] Form submission halted due to missing fields: {missing_fields}")
                return redirect('/expenses')
            
            # Create and validate form
            form = ExpenseForm(request.POST)
            print(f"[DEBUG] Form created, is_bound: {form.is_bound}")
            
            if form.is_valid():
                print(f"[DEBUG] Form is valid")
                try:
                    with transaction.atomic():
                        # Get the account
                        my_account = get_object_or_404(Account, user=request.user)
                        print(f"[DEBUG] Account found. ID: {my_account.id}, Balance: {my_account.balance}")
                        
                        # Check sufficient balance
                        amount = form.cleaned_data['amount']
                        print(f"[DEBUG] Expense amount: {amount}")
                        
                        if my_account.balance < amount:
                            print(f"[DEBUG] Insufficient balance. Required: {amount}, Available: {my_account.balance}")
                            messages.error(request, f"Insufficient balance. Required: {amount}, Available: {my_account.balance}")
                            return redirect('/expenses')
                        
                        # Create and save expense record
                        expense = form.save(commit=False)
                        expense.user = request.user
                        expense.save()
                        print(f"[DEBUG] Expense saved with ID: {expense.id}")
                        
                        # Update account balance
                        original_balance = my_account.balance
                        my_account.balance -= amount
                        my_account.save()
                        print(f"[DEBUG] Account balance updated: {original_balance} -> {my_account.balance}")
                        
                        messages.success(request, f"Expense '{expense.name}' for {expense.amount} added successfully!")
                        return redirect('/expenses')
                except Exception as e:
                    print(f"[DEBUG] Unexpected exception: {str(e)}")
                    messages.error(request, f"Error adding expense: {str(e)}")
                    return redirect('/expenses')
            else:
                print(f"[DEBUG] Form validation failed: {form.errors}")
                
                # Add error messages for display
                for field, errors in form.errors.items():
                    for error in errors:
                        error_msg = f"{field}: {error}"
                        print(f"[DEBUG] Form error: {error_msg}")
                        messages.error(request, error_msg)
        
        # Render the template with context
        return render(request, "expense.html", {
            "categories": categories,
            "expenses": expenses,
            "form": form
        })
        
    except Exception as e:
        print(f"Error in expense view: {str(e)}")
        messages.error(request, "An error occurred while loading the expense page. Please try again.")
        return redirect('/dashboard')


# EDIT Income
def edit_income(request,id):
    if request.user.is_authenticated:
        income=Income.objects.get(id=id)
        if request.method=="POST":
            name=request.POST['name']
            category_id=request.POST.get('category')
            amount=request.POST['amount']
            date=request.POST['date']
            note=request.POST.get('note')
            category = get_object_or_404(IncomeCategory, id=int(category_id), user=request.user)

            # Update Account Balance
            my_account= Account.objects.get(user=User.objects.get(id = request.user.id))
            if float(amount)<income.amount:
                my_account.balance-=float((income.amount-float(amount)))
            else:
                my_account.balance+=float((float(amount)-income.amount))
            
            my_account.save()
            print("Account balance updated")

            # Update income 
            income.name=name
            income.amount=float(amount)
            if date:
                income.date=date
            income.note=note
            income.category=category
            income.save()
            print("Income Details Updated")
            return redirect("/incomes")

        categories = IncomeCategory.objects.filter(user=request.user)
        return render(request,"income_edit.html",{"income":income,"categories":categories})
    else:
        return redirect("/")

# EDIT Expense
def edit_expense(request,id):
    if request.user.is_authenticated:
        expense=Expense.objects.get(id=id)
        if request.method=="POST":
            name=request.POST['name']
            category_id=request.POST.get('category')
            amount=request.POST['amount']
            date=request.POST['date']
            note=request.POST.get('note')
            category = ExpenseCategory.objects.get(user=request.user.id,id=int(category_id))

            # Update Account Balance
            my_account= Account.objects.get(user=User.objects.get(id = request.user.id))
            if float(amount)<expense.amount:
                my_account.balance+=float((expense.amount-float(amount)))
            else:
                my_account.balance-=float((float(amount)-expense.amount))
            
            my_account.save()
            print("Account balance updated")

            # Update expense 
            expense.name=name
            expense.amount=float(amount)
            if date:
                expense.date=date
            expense.note=note
            expense.category=category
            expense.save()
            print("expense Details Updated")
            return redirect("/expenses")

        categories= ExpenseCategory.objects.filter(user=request.user.id)
        return render(request,"expense_edit.html",{"expense":expense,"categories":categories})
    else:
        return redirect("/")


# Delete Expense
def delete_expense(request,id):
    if request.user.is_authenticated:
        expense=Expense.objects.get(id=id)
        my_account= Account.objects.get(user=User.objects.get(id = request.user.id))
        my_account.balance+=float(expense.amount)
        my_account.save()
        print("Account balance updated")

        Expense.objects.get(id=id).delete()
        print("Expense deleted")
        return redirect("/expenses")
    else:
        return redirect("/")
    
# Delete Incmoe
def delete_income(request,id):
    if request.user.is_authenticated:
        income=Income.objects.get(id=id)
        my_account= Account.objects.get(user=User.objects.get(id = request.user.id))
        my_account.balance-=float(income.amount)
        my_account.save()
        print("Account balance updated")

        Income.objects.get(id=id).delete()
        print("Income Deleted")
        return redirect("/incomes")
    else:
        return redirect("/")


# For Report generation
import csv
def expense_report(request, duration):
    if not request.user.is_authenticated:
        return redirect("/")

    today = datetime.now().date()
    
    if duration == "daily":
        # Get today's expenses (from start to end of day)
        start_date = today
        end_date = today + timedelta(days=1)
        expenses = Expense.objects.filter(
            user=request.user.id,
            date__gte=start_date,
            date__lt=end_date
        ).order_by("date")
    elif duration == "weekly":
        # Get last 7 days expenses
        start_date = today - timedelta(days=6)  # Include today
        expenses = Expense.objects.filter(
            user=request.user.id,
            date__gte=start_date,
            date__lte=today
        ).order_by("date")
    elif duration == "monthly":
        # Get last 30 days expenses
        start_date = today - timedelta(days=29)  # Include today
        expenses = Expense.objects.filter(
            user=request.user.id,
            date__gte=start_date,
            date__lte=today
        ).order_by("date")
    else:
        # Get all expenses
        expenses = Expense.objects.filter(
            user=request.user.id
        ).order_by("date")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Expenses_{duration}_report.csv"'
    writer = csv.writer(response)
    writer.writerow(["Sr.No.", "Name", "Category", "Amount", "Date", "Note"])
    
    total_amount = 0
    for counter, expense in enumerate(expenses, 1):
        writer.writerow([
            counter,
            expense.name,
            expense.category,
            expense.amount,
            expense.date,
            expense.note
        ])
        total_amount += expense.amount
    
    # Add total row
    writer.writerow([])  # Empty row for spacing
    writer.writerow(["Total", "", "", total_amount, "", ""])
    
    return response

# For Report generation
import csv
def income_report(request, duration):
    if not request.user.is_authenticated:
        return redirect("/")

    today = datetime.now().date()
    
    if duration == "daily":
        # Get today's incomes (from start to end of day)
        start_date = today
        end_date = today + timedelta(days=1)
        incomes = Income.objects.filter(
            user=request.user.id,
            date__gte=start_date,
            date__lt=end_date
        ).order_by("date")
    elif duration == "weekly":
        # Get last 7 days incomes
        start_date = today - timedelta(days=6)  # Include today
        incomes = Income.objects.filter(
            user=request.user.id,
            date__gte=start_date,
            date__lte=today
        ).order_by("date")
    elif duration == "monthly":
        # Get last 30 days incomes
        start_date = today - timedelta(days=29)  # Include today
        incomes = Income.objects.filter(
            user=request.user.id,
            date__gte=start_date,
            date__lte=today
        ).order_by("date")
    else:
        # Get all incomes
        incomes = Income.objects.filter(
            user=request.user.id
        ).order_by("date")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Incomes_{duration}_report.csv"'
    writer = csv.writer(response)
    writer.writerow(["Sr.No.", "Name", "Category", "Amount", "Date", "Note"])
    
    total_amount = 0
    for counter, income in enumerate(incomes, 1):
        writer.writerow([
            counter,
            income.name,
            income.category,
            income.amount,
            income.date,
            income.note
        ])
        total_amount += income.amount
    
    # Add total row
    writer.writerow([])  # Empty row for spacing
    writer.writerow(["Total", "", "", total_amount, "", ""])
    
    return response

# Settings
def settings(request):
    if request.user.is_authenticated:
        profile= User.objects.get(id=request.user.id)
        expense_categories=ExpenseCategory.objects.filter(user=request.user)
        income_categories=IncomeCategory.objects.filter(user=request.user)
        if request.method== "POST":
            first_name= request.POST['first_name']
            last_name= request.POST['last_name']
            email= request.POST['email']

            profile.first_name=first_name
            profile.last_name=last_name
            profile.email=email
            profile.save()

            print("Profile Updated")
            return redirect("/profile")
        else:
            return render(request,"settings.html",{"profile":profile,"expense_categories":expense_categories,"income_categories":income_categories})
    else:
        return render(request, "/",{})



# Add Income category
@login_required(login_url='/')
def add_income_category(request):
    if request.method == "POST":
        form = IncomeCategoryForm(request.POST)
        if form.is_valid():
            try:
                # Save without committing, then add user
                category = form.save(commit=False)
                category.user = request.user
                category.save()
                messages.success(request, "Income category created successfully!")
            except Exception as e:
                messages.error(request, f"Error creating category: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("/settings")

# Add Expense category
@login_required(login_url='/')
def add_expense_category(request):
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            try:
                # Save without committing, then add user
                category = form.save(commit=False)
                category.user = request.user
                category.save()
                messages.success(request, "Expense category created successfully!")
            except Exception as e:
                messages.error(request, f"Error creating category: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("/settings")

# Remove expense category
def remove_expense_category(request,id):
    if request.user.is_authenticated:
        ExpenseCategory.objects.get(user=request.user.id,id=id).delete()
        print("Category Deleted")
        return redirect("/settings")
    else:
        return redirect("/")
    
# Remove Income category
def remove_income_category(request,id):
    if request.user.is_authenticated:
        IncomeCategory.objects.get(id=id).delete()
        print("Category Deleted")
        return redirect("/settings")
    else:
        return redirect("/")


# Index page
def index(request):
    if request.user.is_authenticated:
        return redirect("/dashboard")
    else:
        return render(request, "index.html",{})

# Signup 
def signup(request):
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=email).exists():
            print("Username is already used")
            messages.error(request, "Email address already in use. Please login or use a different email.")
            return redirect('/')
        
        # Create user only if the email doesn't exist
        user = User.objects.create_user(
            username=email,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.save()
        print("User Account created successfully")
        
        # Create Account for users
        Account.objects.create(
            user=user,
            balance=0,
            details="Primary account for User="+str(user.id),
            name=f'Account for {user.id}-{first_name}'
        )
        print("Users Account Created!!")
        
        # Create default expense categories
        ExpenseCategory.objects.create(name="General Expense", user=user)
        ExpenseCategory.objects.create(name="Food", user=user)
        ExpenseCategory.objects.create(name="Transportation", user=user)
        print("Default expense categories created")
        
        # Create default income categories
        IncomeCategory.objects.create(name="Salary", user=user)
        IncomeCategory.objects.create(name="Other Income", user=user)
        print("Default income categories created")
        
        messages.success(request, "Account created successfully! Please login.")
        return redirect('/')
        
    return render(request, "index.html", {})
    
# Profile
def profile(request):
    if request.user.is_authenticated:
        profile= User.objects.get(id=request.user.id)
        account= Account.objects.get(user=request.user.id)
        if request.method== "POST":
            first_name= request.POST['first_name']
            last_name= request.POST['last_name']
            email= request.POST['email']

            profile.first_name=first_name
            profile.last_name=last_name
            profile.email=email
            profile.save()

            print("Profile Updated")
            return redirect("/profile")
        else:
            return render(request,"profile.html",{"profile":profile,"balance":account.balance})
    else:
        return render(request, "/",{})
    

# Login
def login(request):
    if request.method== "POST":
        username = request.POST['email']
        password = request.POST['password']

        user= auth.authenticate(username=username,password=password)

        if user is not None:
            auth.login(request,user)
            print(f"User {username} is logged in")
            return redirect("/dashboard")
        else:
            print("Invalid Login details")
            # Redirect to the index page for authentication failure
            return redirect("/")
    else:
        # For GET requests, redirect to the index page instead of trying to render "/"
        return redirect("/")


def logout(request):
    if request.user.is_authenticated:
        auth.logout(request)
    return redirect("/")