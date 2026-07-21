from django.contrib import admin
from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    # Columns shown in the admin list view
    list_display = ('issue_subject', 'full_name',
                    'email_address', 'urgency_level', 'submitted_on')

    # Filters on the right sidebar
    list_filter = ('urgency_level', 'submitted_on')

    # Search bar functionality
    search_fields = ('issue_subject', 'detailed_message',
                     'full_name', 'email_address')
