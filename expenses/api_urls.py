from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.expense_list_create_api, name='api_expense_list_create'),
    path('<int:pk>/', api_views.expense_detail_api, name='api_expense_detail'),
    path('dashboard/', api_views.dashboard_summary_api, name='api_dashboard_summary'),
]
