from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SupportTicketForm


def create_ticket_view(request):
    """
    Handles rendering the support ticket form and saving form submissions.
    Redirects to a success alert message upon successful submission.
    """
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            # Save the ticket to the database
            ticket = form.save(commit=False)

            # If the user is logged in, attach them as the creator
            if request.user.is_authenticated:
                ticket.user = request.user

            ticket.save()

            # Show a success feedback message to the user
            messages.success(
                request,
                'Your support ticket has been submitted successfully!')

            # Redirect back to the form (or ticket list once created)
            return redirect('ticket_create')
        else:
            messages.error(
                request, 'Please correct the errors in the form below.')
    else:
        # GET request: Display an empty form
        form = SupportTicketForm()

    context = {
        'form': form
    }
    return render(request, 'tickets/ticket_form.html', context)
