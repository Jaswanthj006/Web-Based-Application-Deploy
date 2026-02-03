from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.LoginView.as_view()),
    path('auth/register/', views.RegisterView.as_view()),
    path('upload/', views.UploadCSVView.as_view()),
    path('history/', views.HistoryListView.as_view()),
    path('summary/<int:pk>/', views.SummaryView.as_view()),
    path('data/<int:pk>/', views.DataTableView.as_view()),
    path('report/<int:pk>/pdf/', views.ReportPDFView.as_view()),
]
