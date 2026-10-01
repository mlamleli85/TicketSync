from django.contrib import admin
from .models import SupportTicket, TicketComment


class TicketCommentInline(admin.TabularInline):
    """Show a ticket's comments on its admin page."""
    model = TicketComment
    extra = 0
    readonly_fields = ('created_on',)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """Admin configuration for support tickets."""
    # Columns shown in the admin list view
    list_display = ('issue_subject', 'full_name', 'email_address',
                    'urgency_level', 'status', 'submitted_on')
    list_editable = ('status',)

    # Filters on the right sidebar
    list_filter = ('status', 'urgency_level', 'submitted_on')

    # Search bar functionality
    search_fields = ('issue_subject', 'detailed_message',
                     'full_name', 'email_address')
    inlines = [TicketCommentInline]


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    """Admin configuration for ticket comments."""
    list_display = ('ticket', 'author', 'created_on')
    search_fields = ('body',)
