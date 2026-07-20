from django.urls import path
from .views import (
    create_ticket_view,
    ticket_detail_view,
    ticket_list_view,
    ticket_delete_view,
    ticket_update_view,
)

urlpatterns = [
    path('', ticket_list_view, name='ticket_list'),
    path('submit/', create_ticket_view, name='ticket_submit'),
    path('<int:pk>/', ticket_detail_view, name='ticket_detail'),
    path('<int:pk>/edit/', ticket_update_view, name='ticket_update'),
    path('<int:pk>/delete/', ticket_delete_view, name='ticket_delete'),
]
