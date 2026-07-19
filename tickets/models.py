from django.db import models


class SupportTicket(models.Model):
    """
    A custom model tracking user contact and suport requests
    """

    PRIORITY_CHOICES = [
        ('LOW', 'General Inquiry'),
        ('HIGH', 'Urgent Issue')
    ]

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
