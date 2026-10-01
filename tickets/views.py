from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .forms import (
    SignUpForm,
    StaffTicketForm,
    SupportTicketForm,
    TicketCommentForm,
)
from .models import SupportTicket


def tickets_visible_to(user):
    """
    Return the tickets a user is allowed to see:
    staff see every ticket, other users only their own.
    """
    tickets = SupportTicket.objects.select_related('user')
    if user.is_staff:
        return tickets
    return tickets.filter(user=user)


def get_ticket_or_404(user, pk):
    """Fetch a ticket the user may view, or raise a 404."""
    return get_object_or_404(tickets_visible_to(user), pk=pk)


def home_view(request):
    """
    Public landing page explaining what TicketSync does.
    Logged-in users also see a summary of their own tickets.
    """
    context = {}
    if request.user.is_authenticated:
        context['summary'] = tickets_visible_to(request.user).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(
                status__in=SupportTicket.EDITABLE_STATUSES)),
            resolved=Count('id', filter=Q(
                status=SupportTicket.STATUS_RESOLVED)),
        )
    return render(request, 'home.html', context)


def signup_view(request):
    """Register a new user account and log the user in."""
    if request.user.is_authenticated:
        return redirect('ticket_list')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f'Welcome to TicketSync, {user.username}! '
                'Your account has been created.'
            )
            return redirect('ticket_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


class TicketSyncLoginView(LoginView):
    """Site login page that confirms a successful login."""
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Log the user in and show a welcome message."""
        response = super().form_valid(form)
        messages.success(
            self.request, f'Welcome back, {self.request.user.username}!')
        return response

    def form_invalid(self, form):
        """Show an error message when the login details are wrong."""
        messages.error(self.request, 'Login failed. Please try again.')
        return super().form_invalid(form)


@require_POST
def logout_view(request):
    """Log the user out. Only accepts POST so links can't log users out."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def ticket_list_view(request):
    """
    Dashboard of tickets with search and status filtering.
    - Standard users see only their tickets.
    - Staff see all tickets across the system.
    """
    tickets = tickets_visible_to(request.user)

    # Status counts for the summary cards, before any filtering
    counts = tickets.aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status=SupportTicket.STATUS_OPEN)),
        in_progress=Count('id', filter=Q(
            status=SupportTicket.STATUS_IN_PROGRESS)),
        resolved=Count('id', filter=Q(status=SupportTicket.STATUS_RESOLVED)),
        closed=Count('id', filter=Q(status=SupportTicket.STATUS_CLOSED)),
    )

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    if search_query:
        tickets = tickets.filter(
            Q(issue_subject__icontains=search_query)
            | Q(detailed_message__icontains=search_query)
        )

    valid_statuses = [choice[0] for choice in SupportTicket.STATUS_CHOICES]
    if status_filter in valid_statuses:
        tickets = tickets.filter(status=status_filter)
    else:
        status_filter = ''

    context = {
        'tickets': tickets,
        'counts': counts,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': SupportTicket.STATUS_CHOICES,
    }
    return render(request, 'tickets/ticket_list.html', context)


@login_required
def create_ticket_view(request):
    """
    Show the support ticket form and save new tickets.
    The ticket is always linked to the logged-in user.
    """
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(
                request,
                'Your support ticket has been submitted successfully!')
            return redirect('ticket_detail', pk=ticket.pk)
        messages.error(request, 'Please correct the errors in the form below.')
    else:
        # Pre-fill the contact details from the user's account
        form = SupportTicketForm(user=request.user, initial={
            'full_name': request.user.get_full_name(),
            'email_address': request.user.email,
        })

    return render(request, 'tickets/ticket_form.html', {'form': form})


@login_required
def ticket_detail_view(request, pk):
    """
    Show a single ticket and its replies, and accept new replies.
    - Staff members can view any ticket.
    - Regular users can only view their own tickets.
    """
    ticket = get_ticket_or_404(request.user, pk)

    if request.method == 'POST':
        comment_form = TicketCommentForm(request.POST)
        if ticket.status == SupportTicket.STATUS_CLOSED:
            messages.error(request, 'This ticket is closed to new replies.')
            return redirect('ticket_detail', pk=ticket.pk)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            status_changed = ticket.apply_comment_rules(request.user)
            message = 'Your reply has been added.'
            if status_changed:
                message += (
                    f' Ticket status is now '
                    f'"{ticket.get_status_display()}".'
                )
            messages.success(request, message)
            return redirect('ticket_detail', pk=ticket.pk)
        messages.error(request, 'Your reply could not be added.')
    else:
        comment_form = TicketCommentForm()

    context = {
        'ticket': ticket,
        'comments': ticket.comments.select_related('author'),
        'comment_form': comment_form,
        'can_edit': ticket.can_be_edited_by(request.user),
        'can_delete': ticket.can_be_deleted_by(request.user),
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
def ticket_update_view(request, pk):
    """
    Edit an existing ticket, with the form pre-filled.
    Staff can also change the status. Owners can only edit tickets
    that are still open or in progress.
    """
    ticket = get_ticket_or_404(request.user, pk)

    if not ticket.can_be_edited_by(request.user):
        messages.error(
            request,
            'Resolved or closed tickets can no longer be edited. '
            'Add a reply instead.'
        )
        return redirect('ticket_detail', pk=ticket.pk)

    if request.user.is_staff:
        form_class = StaffTicketForm
    else:
        form_class = SupportTicketForm

    if request.method == 'POST':
        form = form_class(request.POST, instance=ticket, user=ticket.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket updated successfully!')
            return redirect('ticket_detail', pk=ticket.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = form_class(instance=ticket, user=ticket.user)

    context = {'form': form, 'ticket': ticket, 'is_edit': True}
    return render(request, 'tickets/ticket_form.html', context)


@login_required
def ticket_delete_view(request, pk):
    """Ask for confirmation, then delete the ticket on POST."""
    ticket = get_ticket_or_404(request.user, pk)

    if not ticket.can_be_deleted_by(request.user):
        messages.error(request, 'You cannot delete this ticket.')
        return redirect('ticket_detail', pk=ticket.pk)

    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Ticket deleted successfully.')
        return redirect('ticket_list')

    return render(request, 'tickets/ticket_confirm_delete.html',
                  {'ticket': ticket})
