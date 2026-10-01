from django.urls import path
from .views import (
    TicketSyncLoginView,
    create_ticket_view,
    home_view,
    logout_view,
    signup_view,
    ticket_delete_view,
    ticket_detail_view,
    ticket_list_view,
    ticket_update_view,
)

urlpatterns = [
    # Public pages
    path('', home_view, name='home'),
    path('accounts/signup/', signup_view, name='signup'),
    path('accounts/login/', TicketSyncLoginView.as_view(), name='login'),
    path('accounts/logout/', logout_view, name='logout'),

    # Ticket pages (login required)
    path('tickets/', ticket_list_view, name='ticket_list'),
    path('tickets/new/', create_ticket_view, name='ticket_submit'),
    path('tickets/<int:pk>/', ticket_detail_view, name='ticket_detail'),
    path('tickets/<int:pk>/edit/', ticket_update_view,
         name='ticket_update'),
    path('tickets/<int:pk>/delete/', ticket_delete_view,
         name='ticket_delete'),
]
