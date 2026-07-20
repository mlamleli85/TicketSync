from django import forms
from .models import SupportTicket


class SupportTicketForm(forms.ModelForm):
    """
    A form for users to submit support tickets.
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
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email_address': forms.EmailInput(attrs={'class': 'form-control'}),
            'issue_subject': forms.TextInput(attrs={'class': 'form-control'}),
            'detailed_message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'urgency_level': forms.Select(attrs={'class': 'form-select'}),
        }
