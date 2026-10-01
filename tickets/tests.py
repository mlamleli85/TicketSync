"""
Automated tests for the TicketSync tickets app.

Run with:  python manage.py test
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import SignUpForm, StaffTicketForm, SupportTicketForm
from .models import SupportTicket, TicketComment

PASSWORD = 'Str0ng-pass-123'


def make_ticket(user, **overrides):
    """Create a ticket for the given user with sensible defaults."""
    data = {
        'user': user,
        'full_name': 'Test User',
        'email_address': 'test@example.com',
        'issue_subject': 'Cannot log in to my account',
        'detailed_message': 'The login page shows an error every time.',
        'urgency_level': 'LOW',
    }
    data.update(overrides)
    return SupportTicket.objects.create(**data)


def valid_form_data(**overrides):
    """Return valid POST data for the ticket form."""
    data = {
        'full_name': 'Jane Doe',
        'email_address': 'jane@example.com',
        'issue_subject': 'Printer not working',
        'detailed_message': 'The office printer shows a paper jam error.',
        'urgency_level': 'HIGH',
    }
    data.update(overrides)
    return data


class BaseTestCase(TestCase):
    """Creates an owner, another user and a staff member for each test."""

    def setUp(self):
        self.owner = User.objects.create_user(
            'owner', 'owner@example.com', PASSWORD)
        self.other = User.objects.create_user(
            'other', 'other@example.com', PASSWORD)
        self.staff = User.objects.create_user(
            'staff', 'staff@example.com', PASSWORD, is_staff=True)
        self.ticket = make_ticket(self.owner)


class SupportTicketModelTests(BaseTestCase):
    """Tests for the SupportTicket model and its business rules."""

    def test_string_representation(self):
        self.assertEqual(
            str(self.ticket),
            'Ticket from Test User - Cannot log in to my account')

    def test_new_ticket_is_open(self):
        self.assertEqual(self.ticket.status, SupportTicket.STATUS_OPEN)
        self.assertTrue(self.ticket.is_active)

    def test_absolute_url_points_to_detail_page(self):
        self.assertEqual(
            self.ticket.get_absolute_url(),
            reverse('ticket_detail', args=[self.ticket.pk]))

    def test_view_permissions(self):
        self.assertTrue(self.ticket.can_be_viewed_by(self.owner))
        self.assertTrue(self.ticket.can_be_viewed_by(self.staff))
        self.assertFalse(self.ticket.can_be_viewed_by(self.other))

    def test_owner_cannot_edit_resolved_ticket(self):
        self.ticket.status = SupportTicket.STATUS_RESOLVED
        self.assertFalse(self.ticket.can_be_edited_by(self.owner))
        self.assertTrue(self.ticket.can_be_edited_by(self.staff))

    def test_staff_reply_moves_open_ticket_to_in_progress(self):
        changed = self.ticket.apply_comment_rules(self.staff)
        self.ticket.refresh_from_db()
        self.assertTrue(changed)
        self.assertEqual(
            self.ticket.status, SupportTicket.STATUS_IN_PROGRESS)

    def test_owner_reply_reopens_resolved_ticket(self):
        self.ticket.status = SupportTicket.STATUS_RESOLVED
        self.ticket.save()
        changed = self.ticket.apply_comment_rules(self.owner)
        self.ticket.refresh_from_db()
        self.assertTrue(changed)
        self.assertEqual(self.ticket.status, SupportTicket.STATUS_OPEN)

    def test_owner_reply_on_open_ticket_keeps_status(self):
        changed = self.ticket.apply_comment_rules(self.owner)
        self.assertFalse(changed)
        self.assertEqual(self.ticket.status, SupportTicket.STATUS_OPEN)

    def test_old_urgent_open_ticket_needs_attention(self):
        urgent = make_ticket(self.owner, urgency_level='HIGH',
                             issue_subject='Server is down')
        self.assertFalse(urgent.needs_attention)
        SupportTicket.objects.filter(pk=urgent.pk).update(
            submitted_on=timezone.now() - timedelta(days=2))
        urgent.refresh_from_db()
        self.assertTrue(urgent.needs_attention)

    def test_deleting_ticket_deletes_comments(self):
        TicketComment.objects.create(
            ticket=self.ticket, author=self.owner, body='Any update?')
        self.ticket.delete()
        self.assertEqual(TicketComment.objects.count(), 0)


class SupportTicketFormTests(BaseTestCase):
    """Tests for ticket form validation."""

    def test_valid_data(self):
        form = SupportTicketForm(data=valid_form_data(), user=self.owner)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        form = SupportTicketForm(data={}, user=self.owner)
        self.assertFalse(form.is_valid())
        for field in ['full_name', 'email_address', 'issue_subject',
                      'detailed_message']:
            self.assertIn(field, form.errors)

    def test_subject_too_short(self):
        form = SupportTicketForm(
            data=valid_form_data(issue_subject='Hi'), user=self.owner)
        self.assertFalse(form.is_valid())
        self.assertIn('issue_subject', form.errors)

    def test_message_too_short(self):
        form = SupportTicketForm(
            data=valid_form_data(detailed_message='Broken'),
            user=self.owner)
        self.assertFalse(form.is_valid())
        self.assertIn('detailed_message', form.errors)

    def test_name_with_numbers_rejected(self):
        form = SupportTicketForm(
            data=valid_form_data(full_name='J4ne D0e'), user=self.owner)
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)

    def test_invalid_email_rejected(self):
        form = SupportTicketForm(
            data=valid_form_data(email_address='not-an-email'),
            user=self.owner)
        self.assertFalse(form.is_valid())
        self.assertIn('email_address', form.errors)

    def test_duplicate_active_subject_rejected(self):
        form = SupportTicketForm(
            data=valid_form_data(
                issue_subject='cannot log in to my account'),
            user=self.owner)
        self.assertFalse(form.is_valid())
        self.assertIn('issue_subject', form.errors)

    def test_same_subject_allowed_after_ticket_closed(self):
        self.ticket.status = SupportTicket.STATUS_CLOSED
        self.ticket.save()
        form = SupportTicketForm(
            data=valid_form_data(issue_subject=self.ticket.issue_subject),
            user=self.owner)
        self.assertTrue(form.is_valid())

    def test_editing_ticket_is_not_a_duplicate_of_itself(self):
        form = SupportTicketForm(
            data=valid_form_data(issue_subject=self.ticket.issue_subject),
            instance=self.ticket, user=self.owner)
        self.assertTrue(form.is_valid())

    def test_only_staff_form_has_status_field(self):
        self.assertNotIn('status', SupportTicketForm().fields)
        self.assertIn('status', StaffTicketForm().fields)

    def test_signup_rejects_existing_email(self):
        form = SignUpForm(data={
            'username': 'newuser',
            'email': 'OWNER@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class AuthenticationViewTests(BaseTestCase):
    """Tests for registration, login, logout and login status."""

    def test_home_page_is_public(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Not logged in')
        self.assertContains(response, reverse('signup'))

    def test_home_page_shows_login_status(self):
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Logged in as')
        self.assertContains(response, 'owner')

    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
        }, follow=True)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertRedirects(response, reverse('ticket_list'))

    def test_login_with_valid_details(self):
        response = self.client.post(reverse('login'), {
            'username': 'owner', 'password': PASSWORD}, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertContains(response, 'Welcome back, owner!')

    def test_login_with_wrong_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'owner', 'password': 'wrong'})
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Login failed')

    def test_logout_requires_post(self):
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)

    def test_logout(self):
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.post(reverse('logout'), follow=True)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'You have been logged out.')

    def test_ticket_pages_require_login(self):
        urls = [
            reverse('ticket_list'),
            reverse('ticket_submit'),
            reverse('ticket_detail', args=[self.ticket.pk]),
            reverse('ticket_update', args=[self.ticket.pk]),
            reverse('ticket_delete', args=[self.ticket.pk]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertRedirects(
                response, f"{reverse('login')}?next={url}")


class TicketCrudViewTests(BaseTestCase):
    """Tests for creating, reading, updating and deleting tickets."""

    def login(self, username='owner'):
        self.client.login(username=username, password=PASSWORD)

    # Create
    def test_create_form_is_prefilled_with_account_email(self):
        self.login()
        response = self.client.get(reverse('ticket_submit'))
        self.assertContains(response, 'owner@example.com')

    def test_create_ticket(self):
        self.login()
        response = self.client.post(
            reverse('ticket_submit'), valid_form_data(), follow=True)
        ticket = SupportTicket.objects.get(
            issue_subject='Printer not working')
        self.assertEqual(ticket.user, self.owner)
        self.assertRedirects(
            response, reverse('ticket_detail', args=[ticket.pk]))
        self.assertContains(response, 'submitted successfully')

    def test_create_invalid_ticket_shows_errors(self):
        self.login()
        response = self.client.post(
            reverse('ticket_submit'), valid_form_data(issue_subject=''))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors')
        self.assertEqual(SupportTicket.objects.count(), 1)

    # Read
    def test_user_sees_only_own_tickets(self):
        make_ticket(self.other, issue_subject='Other user ticket')
        self.login()
        response = self.client.get(reverse('ticket_list'))
        self.assertContains(response, self.ticket.issue_subject)
        self.assertNotContains(response, 'Other user ticket')

    def test_staff_sees_all_tickets(self):
        make_ticket(self.other, issue_subject='Other user ticket')
        self.login('staff')
        response = self.client.get(reverse('ticket_list'))
        self.assertContains(response, self.ticket.issue_subject)
        self.assertContains(response, 'Other user ticket')

    def test_search_and_status_filter(self):
        make_ticket(self.owner, issue_subject='Billing question here',
                    status=SupportTicket.STATUS_RESOLVED)
        self.login()
        response = self.client.get(reverse('ticket_list'), {'q': 'billing'})
        self.assertContains(response, 'Billing question here')
        self.assertNotContains(response, self.ticket.issue_subject)
        response = self.client.get(
            reverse('ticket_list'), {'status': 'OPEN'})
        self.assertContains(response, self.ticket.issue_subject)
        self.assertNotContains(response, 'Billing question here')

    def test_other_user_cannot_view_ticket(self):
        self.login('other')
        response = self.client.get(
            reverse('ticket_detail', args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 404)

    # Update
    def test_update_form_is_prefilled(self):
        self.login()
        response = self.client.get(
            reverse('ticket_update', args=[self.ticket.pk]))
        self.assertContains(response, self.ticket.issue_subject)
        self.assertContains(response, self.ticket.detailed_message)

    def test_update_ticket(self):
        self.login()
        response = self.client.post(
            reverse('ticket_update', args=[self.ticket.pk]),
            valid_form_data(issue_subject='Updated subject line'),
            follow=True)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.issue_subject, 'Updated subject line')
        self.assertContains(response, 'Ticket updated successfully!')

    def test_other_user_cannot_update_ticket(self):
        self.login('other')
        response = self.client.post(
            reverse('ticket_update', args=[self.ticket.pk]),
            valid_form_data(issue_subject='Hacked subject'))
        self.assertEqual(response.status_code, 404)
        self.ticket.refresh_from_db()
        self.assertNotEqual(self.ticket.issue_subject, 'Hacked subject')

    def test_owner_cannot_update_resolved_ticket(self):
        self.ticket.status = SupportTicket.STATUS_RESOLVED
        self.ticket.save()
        self.login()
        response = self.client.get(
            reverse('ticket_update', args=[self.ticket.pk]))
        self.assertRedirects(
            response, reverse('ticket_detail', args=[self.ticket.pk]))

    def test_staff_can_change_status(self):
        self.login('staff')
        data = valid_form_data(status=SupportTicket.STATUS_RESOLVED)
        self.client.post(
            reverse('ticket_update', args=[self.ticket.pk]), data)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, SupportTicket.STATUS_RESOLVED)

    # Delete
    def test_delete_asks_for_confirmation(self):
        self.login()
        response = self.client.get(
            reverse('ticket_delete', args=[self.ticket.pk]))
        self.assertContains(response, 'Delete this ticket?')
        self.assertTrue(
            SupportTicket.objects.filter(pk=self.ticket.pk).exists())

    def test_delete_ticket(self):
        self.login()
        response = self.client.post(
            reverse('ticket_delete', args=[self.ticket.pk]), follow=True)
        self.assertFalse(
            SupportTicket.objects.filter(pk=self.ticket.pk).exists())
        self.assertContains(response, 'Ticket deleted successfully.')

    def test_other_user_cannot_delete_ticket(self):
        self.login('other')
        response = self.client.post(
            reverse('ticket_delete', args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            SupportTicket.objects.filter(pk=self.ticket.pk).exists())


class TicketCommentViewTests(BaseTestCase):
    """Tests for replying to tickets."""

    def test_owner_can_reply(self):
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.post(
            reverse('ticket_detail', args=[self.ticket.pk]),
            {'body': 'Any update on this?'}, follow=True)
        self.assertEqual(self.ticket.comments.count(), 1)
        self.assertContains(response, 'Your reply has been added.')

    def test_staff_reply_updates_status(self):
        self.client.login(username='staff', password=PASSWORD)
        self.client.post(
            reverse('ticket_detail', args=[self.ticket.pk]),
            {'body': 'We are looking into it.'})
        self.ticket.refresh_from_db()
        self.assertEqual(
            self.ticket.status, SupportTicket.STATUS_IN_PROGRESS)

    def test_cannot_reply_to_closed_ticket(self):
        self.ticket.status = SupportTicket.STATUS_CLOSED
        self.ticket.save()
        self.client.login(username='owner', password=PASSWORD)
        self.client.post(
            reverse('ticket_detail', args=[self.ticket.pk]),
            {'body': 'Hello?'})
        self.assertEqual(self.ticket.comments.count(), 0)

    def test_empty_reply_rejected(self):
        self.client.login(username='owner', password=PASSWORD)
        self.client.post(
            reverse('ticket_detail', args=[self.ticket.pk]), {'body': ' '})
        self.assertEqual(self.ticket.comments.count(), 0)
