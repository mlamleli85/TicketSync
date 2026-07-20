from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.create_ticket_view, name='ticket_create'),
]
