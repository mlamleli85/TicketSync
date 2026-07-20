from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SupportTicketForm
from .models import Ticket


def create_ticket_view(request):
    """
    Handles rendering the support ticket form and saving form submissions.
    Redirects to the ticket list upon successful submission.
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

            # Redirect to ticket list/dashboard
            return redirect('ticket_list')
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


@login_required
def ticket_list_view(request):
    """
    Dashboard view:
    - Standard users see only their tickets.
    - Staff/Superusers see all tickets across the system.
    """
    if request.user.is_staff:
        tickets = Ticket.objects.all().order_by('-created_at')
    else:
        tickets = Ticket.objects.filter(
            user=request.user).order_by('-created_at')

    return render(request, 'tickets/ticket_list.html', {'tickets': tickets})


@login_required
def ticket_delete_view(request, pk):
    """
    Front-end delete view to satisfy CRUD requirement without admin panel.
    """
    if request.user.is_staff:
        ticket = get_object_or_404(Ticket, pk=pk)
    else:
        ticket = get_object_or_404(Ticket, pk=pk, user=request.user)

    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Ticket deleted successfully.')
        return redirect('ticket_list')

    return render(request, 'tickets/ticket_confirm_delete.html',
                  {'ticket': ticket})
