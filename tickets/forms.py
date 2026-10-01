from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import SupportTicket, TicketComment


# Characters allowed in a person's name besides letters
NAME_EXTRA_CHARACTERS = " -'."

SUBJECT_MIN_LENGTH = 5
MESSAGE_MIN_LENGTH = 20


class BootstrapFormMixin:
    """
    Add Bootstrap classes to every widget, and mark fields that have
    errors as invalid so Bootstrap shows them in red.
    """

    def apply_bootstrap(self):
        """Set the Bootstrap CSS class on each field's widget."""
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

    def full_clean(self):
        """After validation, highlight the fields that have errors."""
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                widget.attrs['class'] = (
                    widget.attrs.get('class', '') + ' is-invalid'
                ).strip()


class SupportTicketForm(BootstrapFormMixin, forms.ModelForm):
    """
    Form used by users to create and edit their support tickets.
    Pass the logged-in user as `user` so duplicate tickets can be
    detected.
    """

    class Meta:
        model = SupportTicket
        fields = [
            'full_name',
            'email_address',
            'issue_subject',
            'detailed_message',
            'urgency_level',
        ]
        labels = {
            'full_name': 'Full name',
            'email_address': 'Email address',
            'issue_subject': 'Subject',
            'detailed_message': 'Describe the issue',
            'urgency_level': 'Urgency',
        }
        help_texts = {
            'issue_subject': (
                f'A short summary, at least {SUBJECT_MIN_LENGTH} characters.'
            ),
            'detailed_message': (
                f'At least {MESSAGE_MIN_LENGTH} characters. Include what '
                'you expected to happen and what happened instead.'
            ),
        }
        widgets = {
            'detailed_message': forms.Textarea(attrs={
                'rows': 5,
                'data-min-length': MESSAGE_MIN_LENGTH,
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.apply_bootstrap()

    def clean_full_name(self):
        """Allow letters, spaces, hyphens, apostrophes and full stops."""
        name = self.cleaned_data['full_name'].strip()
        if not any(char.isalpha() for char in name):
            raise forms.ValidationError('Please enter your name.')
        for char in name:
            if not (char.isalpha() or char in NAME_EXTRA_CHARACTERS):
                raise forms.ValidationError(
                    'Names can only contain letters, spaces, hyphens, '
                    'apostrophes and full stops.'
                )
        return name

    def clean_issue_subject(self):
        """Require a meaningful subject line."""
        subject = self.cleaned_data['issue_subject'].strip()
        if len(subject) < SUBJECT_MIN_LENGTH:
            raise forms.ValidationError(
                f'The subject must be at least {SUBJECT_MIN_LENGTH} '
                'characters long.'
            )
        return subject

    def clean_detailed_message(self):
        """Require enough detail for the support team to act on."""
        message = self.cleaned_data['detailed_message'].strip()
        if len(message) < MESSAGE_MIN_LENGTH:
            raise forms.ValidationError(
                f'Please describe the issue in at least '
                f'{MESSAGE_MIN_LENGTH} characters.'
            )
        return message

    def clean(self):
        """
        Stop a user from opening a second active ticket with the same
        subject, which usually means a double submission.
        """
        cleaned_data = super().clean()
        subject = cleaned_data.get('issue_subject')
        if self.user is None or not subject:
            return cleaned_data

        duplicates = SupportTicket.objects.filter(
            user=self.user,
            issue_subject__iexact=subject,
            status__in=SupportTicket.EDITABLE_STATUSES,
        )
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            self.add_error(
                'issue_subject',
                'You already have an active ticket with this subject.'
            )
        return cleaned_data


class StaffTicketForm(SupportTicketForm):
    """Ticket form for staff, who can also change the ticket status."""

    class Meta(SupportTicketForm.Meta):
        fields = SupportTicketForm.Meta.fields + ['status']

    def clean(self):
        """Staff edits skip the duplicate check meant for ticket owners."""
        return forms.ModelForm.clean(self)


class TicketCommentForm(BootstrapFormMixin, forms.ModelForm):
    """Form for adding a reply to a ticket."""

    class Meta:
        model = TicketComment
        fields = ['body']
        labels = {'body': 'Add a reply'}
        widgets = {'body': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_body(self):
        """Reject empty or whitespace-only replies."""
        body = self.cleaned_data['body'].strip()
        if len(body) < 2:
            raise forms.ValidationError('The reply is too short.')
        return body


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    """Registration form that also asks for an email address."""

    email = forms.EmailField(
        required=True,
        help_text='Used to pre-fill your tickets.'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_email(self):
        """Each email address can only be registered once."""
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'An account with this email address already exists.'
            )
        return email
