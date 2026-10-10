from decimal import Decimal
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Expense
from .serializers import ExpenseSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def expense_list_create_api(request):
    """
    List user expenses or create a new expense for authenticated user.
    """
    if request.method == 'GET':
        expenses = Expense.objects.filter(user=request.user)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def expense_detail_api(request, pk):
    """
    Retrieve, update or delete a specific expense owned by authenticated user.
    """
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'GET':
        serializer = ExpenseSerializer(expense)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = ExpenseSerializer(expense, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        title = expense.title
        expense.delete()
        return Response({"success": True, "message": f"Expense '{title}' was deleted successfully."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary_api(request):
    """
    Returns dashboard statistics (total, monthly, categories, recent) for the authenticated user.
    """
    user_expenses = Expense.objects.filter(user=request.user)
    total_spending = user_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    expense_count = user_expenses.count()

    now = timezone.now()
    current_month_spending = user_expenses.filter(
        date__year=now.year,
        date__month=now.month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    category_summary = (
        user_expenses.values('category')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    recent_expenses = user_expenses.all()[:5]

    return Response({
        "total_spending": float(total_spending),
        "expense_count": expense_count,
        "current_month_spending": float(current_month_spending),
        "current_month_name": now.strftime('%B %Y'),
        "category_summary": [
            {
                "category": item['category'],
                "total": float(item['total']),
                "count": item['count']
            }
            for item in category_summary
        ],
        "recent_expenses": ExpenseSerializer(recent_expenses, many=True).data
    }, status=status.HTTP_200_OK)
