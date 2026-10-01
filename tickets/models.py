from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class SupportTicket(models.Model):
    """
    A support request raised by a registered user.

    Tickets move through a simple lifecycle (Open -> In Progress ->
    Resolved -> Closed). The status rules live on the model so that every
    view applies them in the same way.
    """

    PRIORITY_CHOICES = [
        ('LOW', 'General Inquiry'),
        ('HIGH', 'Urgent Issue'),
    ]

    STATUS_OPEN = 'OPEN'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    # Statuses in which the ticket owner may still edit their ticket
    EDITABLE_STATUSES = (STATUS_OPEN, STATUS_IN_PROGRESS)

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
    status = models.CharField(
        max_length=11,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN
    )
    submitted_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_on']

    def __str__(self):
        return f"Ticket from {self.full_name} - {self.issue_subject}"

    def get_absolute_url(self):
        """Return the URL of this ticket's detail page."""
        return reverse('ticket_detail', kwargs={'pk': self.pk})

    @property
    def is_active(self):
        """True while the ticket still needs work from the support team."""
        return self.status in self.EDITABLE_STATUSES

    @property
    def age_in_days(self):
        """Number of whole days since the ticket was submitted."""
        return (timezone.now() - self.submitted_on).days

    @property
    def needs_attention(self):
        """
        Flag urgent tickets that are still open after more than a day,
        so staff can spot them on the dashboard.
        """
        return (
            self.urgency_level == 'HIGH'
            and self.status == self.STATUS_OPEN
            and self.age_in_days >= 1
        )

    def is_owned_by(self, user):
        """True if the given user created this ticket."""
        return user.is_authenticated and self.user_id == user.pk

    def can_be_viewed_by(self, user):
        """Staff can view every ticket; users can view their own."""
        return user.is_staff or self.is_owned_by(user)

    def can_be_edited_by(self, user):
        """
        Staff can always edit. Owners can edit only while the ticket is
        still active, so resolved or closed tickets keep their history.
        """
        if user.is_staff:
            return True
        return self.is_owned_by(user) and self.is_active

    def can_be_deleted_by(self, user):
        """Staff can delete any ticket; owners can delete their own."""
        return user.is_staff or self.is_owned_by(user)

    def apply_comment_rules(self, author):
        """
        Update the ticket status after a new comment:
        - a staff reply on an open ticket moves it to In Progress;
        - an owner reply on a resolved ticket reopens it.
        Returns True if the status changed.
        """
        new_status = self.status
        if author.is_staff and self.status == self.STATUS_OPEN:
            new_status = self.STATUS_IN_PROGRESS
        elif (self.is_owned_by(author)
              and self.status == self.STATUS_RESOLVED):
            new_status = self.STATUS_OPEN

        if new_status != self.status:
            self.status = new_status
            self.save(update_fields=['status', 'updated_on'])
            return True
        return False


class TicketComment(models.Model):
    """
    A reply on a support ticket, written by the ticket owner or by staff.
    Together the comments form the conversation about the issue.
    """

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_comments'
    )
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return f"Comment by {self.author} on ticket #{self.ticket_id}"

    @property
    def is_from_staff(self):
        """True if the comment was written by a member of staff."""
        return self.author.is_staff
