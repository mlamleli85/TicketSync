from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    """
    A custom model tracking user contact and support requests
    """

    PRIORITY_CHOICES = [
        ('LOW', 'General Inquiry'),
        ('HIGH', 'Urgent Issue')
    ]

    # Link ticket directly to Django's Auth User model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets',
        null=True,
        blank=True
    )
    full_name = models.CharField(max_length=150)
    email_address = models.EmailField()
    issue_subject = models.CharField(max_length=200)
    detailed_message = models.TextField()
    urgency_level = models.CharField(
        max_length=4,
        choices=PRIORITY_CHOICES,
        default='LOW'
    )
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket from {self.full_name} - {self.issue_subject}"
