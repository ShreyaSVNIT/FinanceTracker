from django.contrib import admin #django's built in admin to manage models
from .models import IncomeCategory,ExpenseCategory,Income,Expense,Account

# Register your models here.
admin.site.register(IncomeCategory)
admin.site.register(ExpenseCategory)

# to modify income page for admin
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['user','name','date','amount','category','note']
    search_fields = ('user','name', 'category')
    list_filter = ('user','category','date')
admin.site.register(Income, IncomeAdmin)

# modifies expense page for admin.
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['user','name','date','amount','category','note'] #display options
    search_fields = ('user','name', 'category') 
    list_filter = ('user','category','date') #filter options
admin.site.register(Expense, ExpenseAdmin)

# TO Modify Account page for admin
class AccountAdmin(admin.ModelAdmin):
    list_display = ['user','name','balance']
admin.site.register(Account, AccountAdmin)

