from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Expense
from .forms import ExpenseForm


def landing_page(request):
    """
    Public landing page at the root URL (port 8000 /).
    If user is already signed in, redirects straight to their personal dashboard.
    """
    if request.user.is_authenticated:
        return redirect('expenses:dashboard')
    return render(request, 'expenses/landing.html')


def custom_404_view(request, exception=None):
    """
    Custom 404 page for nonexistent routes with a Go to Home Page button.
    """
    return render(request, '404.html', status=404)


@login_required(login_url='accounts:signin')
def dashboard(request):
    """
    Dashboard view providing summary totals, category breakdown,
    current month spending, and recent expenses for the logged-in user.
    """
    user_expenses = Expense.objects.filter(user=request.user)
    total_spending = user_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    expense_count = user_expenses.count()

    # Current month spending
    now = timezone.now()
    current_month_spending = user_expenses.filter(
        date__year=now.year,
        date__month=now.month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Spending grouped by category
    category_summary = (
        user_expenses.values('category')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    # 5 Most recent expenses
    recent_expenses = user_expenses.all()[:5]

    context = {
        'total_spending': total_spending,
        'expense_count': expense_count,
        'current_month_spending': current_month_spending,
        'current_month_name': now.strftime('%B %Y'),
        'category_summary': category_summary,
        'recent_expenses': recent_expenses,
    }
    return render(request, 'expenses/dashboard.html', context)


@login_required(login_url='accounts:signin')
def expense_list(request):
    """
    List view displaying all expenses for the logged-in user, sorted newest first.
    """
    expenses = Expense.objects.filter(user=request.user)
    total_spending = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    context = {
        'expenses': expenses,
        'total_spending': total_spending,
        'expense_count': expenses.count(),
    }
    return render(request, 'expenses/expense_list.html', context)


@login_required(login_url='accounts:signin')
def expense_create(request):
    """
    Create view to add a new expense for the logged-in user.
    """
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, f"Expense '{expense.title}' of ₹{expense.amount} was successfully added!")
            return redirect('expenses:expense_list')
    else:
        form = ExpenseForm(initial={'date': timezone.now().date()})

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'action_title': 'Add New Expense',
        'button_text': 'Add Expense',
    })


@login_required(login_url='accounts:signin')
def expense_update(request, pk):
    """
    Update view to edit an existing expense belonging to the logged-in user.
    """
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense '{expense.title}' was successfully updated!")
            return redirect('expenses:expense_list')
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'expense': expense,
        'action_title': f"Edit Expense: {expense.title}",
        'button_text': 'Save Changes',
    })


@login_required(login_url='accounts:signin')
def expense_delete(request, pk):
    """
    Delete view requiring POST confirmation before deleting an expense.
    """
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        title = expense.title
        amount = expense.amount
        expense.delete()
        messages.success(request, f"Expense '{title}' (₹{amount}) was deleted successfully.")
        return redirect('expenses:expense_list')

    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})
