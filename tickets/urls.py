from django.urls import path
from .views import create_ticket_view, ticket_list_view, ticket_delete_view

urlpatterns = [
    path('', ticket_list_view, name='ticket_list'),
    path('submit/', create_ticket_view, name='ticket_submit'),
    path('<int:pk>/delete/', ticket_delete_view, name='ticket_delete'),
]
