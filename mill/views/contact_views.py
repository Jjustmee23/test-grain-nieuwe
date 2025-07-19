from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from mill.forms import ContactTicketForm, TicketResponseForm
from mill.models import ContactTicket, Factory, TicketResponse, Notification, NotificationCategory
from mill.services.notification_service import NotificationService
import json
from mill.services.simple_email_service import SimpleEmailService

def contact(request):
    # Get available factories for the dropdown
    factories = Factory.objects.filter(status=True).order_by('name')
    
    if request.method == 'POST':
        form = ContactTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            
            # If user is logged in, associate the ticket with them
            if request.user.is_authenticated:
                ticket.created_by = request.user
                
            ticket.save()
            
            # Send notifications to admins and super admins
            notification_service = NotificationService()
            email_service = SimpleEmailService()
            
            # Get all admin and super admin users
            admin_users = User.objects.filter(is_staff=True)
            
            for admin_user in admin_users:
                # Send notification
                notification_service.send_notification(
                    user=admin_user,
                    category_name='support_tickets',
                    title="New Support Ticket",
                    message=f"New ticket: {ticket.subject} from {ticket.name}",
                    priority='medium',
                    link=f"/admin/tickets/{ticket.id}/"
                )
                
                # Send email if user has email preferences
                if admin_user.email:
                    try:
                        html_content = f"""
                        <html>
                        <body>
                            <h2>New Support Ticket: {ticket.subject}</h2>
                            <p>A new support ticket has been submitted:</p>
                            <p><strong>From:</strong> {ticket.name} ({ticket.email})</p>
                            <p><strong>Subject:</strong> {ticket.subject}</p>
                            <p><strong>Type:</strong> {ticket.get_ticket_type_display()}</p>
                            <p><strong>Priority:</strong> {ticket.get_priority_display()}</p>
                            <p><strong>Message:</strong></p>
                            <p>{ticket.message}</p>
                            <p><a href="http://localhost:8000/admin/tickets/{ticket.id}/">View ticket</a></p>
                        </body>
                        </html>
                        """
                        email_service.send_email(
                            to_email=admin_user.email,
                            subject=f"New Support Ticket: {ticket.subject}",
                            html_content=html_content,
                            user=admin_user,
                            sent_by=None
                        )
                    except Exception as e:
                        print(f"Failed to send email to {admin_user.email}: {e}")
            
            messages.success(request, _("Your ticket has been submitted successfully. We'll get back to you soon."))
            return redirect('contact_success')
    else:
        # Pre-fill user info if logged in
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email
            }
        form = ContactTicketForm(initial=initial_data)
    
    context = {
        'form': form,
        'factories': factories
    }
    return render(request, 'mill/contact.html', context)

def contact_success(request):
    return render(request, 'mill/contact_success.html')

@login_required
def my_tickets(request):
    # Only show tickets created by the logged-in user
    tickets = ContactTicket.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'mill/my_tickets.html', {'tickets': tickets})

@login_required
def my_tickets(request):
    """User's tickets page"""
    # Get user's tickets
    tickets = ContactTicket.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'total_tickets': tickets.count(),
        'open_tickets': tickets.filter(status__in=['NEW', 'IN_PROGRESS', 'PENDING']).count(),
        'resolved_tickets': tickets.filter(status__in=['RESOLVED', 'CLOSED']).count(),
    }
    return render(request, 'mill/my_tickets.html', context)

@login_required
def ticket_detail(request, ticket_id):
    """View ticket details and responses"""
    ticket = get_object_or_404(ContactTicket, id=ticket_id, created_by=request.user)
    
    if request.method == 'POST':
        form = TicketResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.ticket = ticket
            response.created_by = request.user
            response.save()
            
            # Send notification to admins
            notification_service = NotificationService()
            admin_users = User.objects.filter(is_staff=True)
            
            for admin_user in admin_users:
                notification_service.send_notification(
                    user=admin_user,
                    category_name='support_tickets',
                    title=f"New Response to Ticket: {ticket.subject}",
                    message=f"User {request.user.get_full_name()} responded to ticket",
                    priority='medium',
                    link=f"/admin/tickets/{ticket.id}/"
                )
            
            messages.success(request, _("Your response has been added to the ticket."))
            return redirect('ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketResponseForm()
    
    # Mark responses as read
    ticket.mark_responses_as_read(request.user)
    
    context = {
        'ticket': ticket,
        'responses': ticket.get_responses(),
        'form': form,
    }
    return render(request, 'mill/ticket_detail.html', context)

@login_required
@require_POST
def ticket_update(request, ticket_id):
    """Update ticket status (for admins/staff)"""
    if not request.user.is_staff:
        messages.error(request, _("You don't have permission to update ticket status."))
        return redirect('my_tickets')
        
    try:
        ticket = ContactTicket.objects.get(id=ticket_id)
        new_status = request.POST.get('status')
        if new_status and new_status in dict(ContactTicket.STATUS_CHOICES):
            ticket.status = new_status
            ticket.save()
            messages.success(request, _("Ticket status updated to {status}").format(
                status=ticket.get_status_display()
            ))
        else:
            messages.error(request, _("Invalid status value"))
    except ContactTicket.DoesNotExist:
        messages.error(request, _("Ticket not found"))
    
    return redirect('my_tickets')

@login_required
def admin_tickets(request):
    """Admin view for managing all tickets"""
    if not request.user.is_superuser or not request.user.userprofile.support_tickets_enabled:
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('manage_profile')
    
    # Get all tickets with filtering
    tickets = ContactTicket.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    # Filter by priority
    priority_filter = request.GET.get('priority')
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        tickets = tickets.filter(
            Q(subject__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'total_tickets': tickets.count(),
        'new_tickets': tickets.filter(status='NEW').count(),
        'in_progress_tickets': tickets.filter(status='IN_PROGRESS').count(),
        'pending_tickets': tickets.filter(status='PENDING').count(),
        'resolved_tickets': tickets.filter(status='RESOLVED').count(),
        'closed_tickets': tickets.filter(status='CLOSED').count(),
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
    }
    return render(request, 'mill/admin_tickets.html', context)

@login_required
def admin_ticket_detail(request, ticket_id):
    """Admin view for ticket details and responses"""
    if not request.user.is_superuser or not request.user.userprofile.support_tickets_enabled:
        messages.error(request, _("You don't have permission to access this page."))
        return redirect('manage_profile')
    
    ticket = get_object_or_404(ContactTicket, id=ticket_id)
    
    if request.method == 'POST':
        form = TicketResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.ticket = ticket
            response.created_by = request.user
            response.is_internal = request.POST.get('is_internal') == 'on'
            response.save()
            
            # Send notification to ticket creator
            if ticket.created_by and ticket.created_by.email:
                notification_service = NotificationService()
                email_service = SimpleEmailService()
                
                # Send notification
                notification_service.send_notification(
                    user=ticket.created_by,
                    category_name='support_tickets',
                    title=f"Response to your ticket: {ticket.subject}",
                    message=f"An admin has responded to your ticket",
                    priority='medium',
                    link=f"/tickets/{ticket.id}/"
                )
                
                # Send email
                try:
                    html_content = f"""
                    <html>
                    <body>
                        <h2>Response to your ticket: {ticket.subject}</h2>
                        <p>An admin has responded to your support ticket:</p>
                        <p><strong>Ticket:</strong> {ticket.subject}</p>
                        <p><strong>Response:</strong> {response.message}</p>
                        <p><a href="http://localhost:8000/tickets/{ticket.id}/">View full conversation</a></p>
                    </body>
                    </html>
                    """
                    email_service.send_email(
                        to_email=ticket.created_by.email,
                        subject=f"Response to your ticket: {ticket.subject}",
                        html_content=html_content,
                        user=ticket.created_by,
                        sent_by=request.user
                    )
                except Exception as e:
                    print(f"Failed to send email to {ticket.created_by.email}: {e}")
            
            messages.success(request, _("Response added successfully."))
            return redirect('admin_ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketResponseForm()
    
    context = {
        'ticket': ticket,
        'responses': ticket.get_responses(),
        'form': form,
    }
    return render(request, 'mill/admin_ticket_detail.html', context)

@login_required
@require_POST
def admin_ticket_status_update(request, ticket_id):
    """Update ticket status from admin panel"""
    if not request.user.is_superuser or not request.user.userprofile.support_tickets_enabled:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        ticket = ContactTicket.objects.get(id=ticket_id)
        new_status = request.POST.get('status')
        new_priority = request.POST.get('priority')
        assigned_to_id = request.POST.get('assigned_to')
        
        if new_status and new_status in dict(ContactTicket.STATUS_CHOICES):
            ticket.status = new_status
        
        if new_priority and new_priority in dict(ContactTicket.PRIORITY_LEVELS):
            ticket.priority = new_priority
        
        if assigned_to_id:
            try:
                assigned_user = User.objects.get(id=assigned_to_id, is_staff=True)
                ticket.assigned_to = assigned_user
            except User.DoesNotExist:
                pass
        
        ticket.save()
        
        return JsonResponse({
            'success': True,
            'status': ticket.get_status_display(),
            'priority': ticket.get_priority_display(),
            'assigned_to': ticket.assigned_to.get_full_name() if ticket.assigned_to else None
        })
    except ContactTicket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)

@login_required
def admin_search_users(request):
    """Search users for admin ticket creation"""
    if not request.user.is_superuser or not request.user.userprofile.support_tickets_enabled:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    query = request.GET.get('q', '').strip()
    print(f"DEBUG: Search query: '{query}'")
    
    if len(query) < 2:
        print("DEBUG: Query too short, returning empty results")
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(username__icontains=query)
    ).order_by('first_name', 'last_name')[:10]
    
    print(f"DEBUG: Found {users.count()} users")
    for user in users:
        print(f"DEBUG: User - ID: {user.id}, Username: {user.username}, Email: {user.email}, First: {user.first_name}, Last: {user.last_name}")
    
    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'email': user.email,
            'username': user.username
        })
    
    print(f"DEBUG: Returning {len(user_list)} users")
    return JsonResponse({'users': user_list})

@login_required
@require_POST
def admin_create_ticket(request):
    """Create a new ticket from admin panel"""
    if not request.user.is_superuser or not request.user.userprofile.support_tickets_enabled:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get form data
        user_id = request.POST.get('user_id')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        priority = request.POST.get('priority')
        ticket_type = request.POST.get('ticket_type')
        
        # Validate required fields
        if not all([user_id, subject, message, priority, ticket_type]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=400)
        
        # Create ticket
        ticket = ContactTicket.objects.create(
            name=f"{user.first_name} {user.last_name}".strip() or user.username,
            email=user.email,
            subject=subject,
            message=message,
            priority=priority,
            ticket_type=ticket_type,
            created_by=user,
            status='NEW'
        )
        
        # Send notification to user
        notification_service = NotificationService()
        notification_service.send_notification(
            user=user,
            category_name='support_tickets',
            title=f"New Support Ticket: {subject}",
            message=f"A support ticket has been created for you",
            priority='medium',
            link=f"/tickets/{ticket.id}/"
        )
        
        # Send email notification
        try:
            email_service = SimpleEmailService()
            html_content = f"""
            <html>
            <body>
                <h2>New Support Ticket: {subject}</h2>
                <p>A support ticket has been created for you:</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Priority:</strong> {ticket.get_priority_display()}</p>
                <p><strong>Type:</strong> {ticket.get_ticket_type_display()}</p>
                <p><strong>Message:</strong> {message}</p>
                <p><a href="http://localhost:8000/tickets/{ticket.id}/">View your ticket</a></p>
            </body>
            </html>
            """
            email_service.send_email(
                to_email=user.email,
                subject=f"New Support Ticket: {subject}",
                html_content=html_content,
                user=user,
                sent_by=request.user
            )
        except Exception as e:
            print(f"Failed to send email to {user.email}: {e}")
        
        return JsonResponse({
            'success': True,
            'ticket_id': ticket.id,
            'message': 'Ticket created successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def admin_quick_reply(request, ticket_id):
    """Quick reply to a ticket from admin panel"""
    if not request.user.is_superuser or not request.user.userprofile.support_tickets_enabled:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        ticket = ContactTicket.objects.get(id=ticket_id)
        message = request.POST.get('message', '').strip()
        is_internal = request.POST.get('is_internal') == 'on'
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Create response
        response = TicketResponse.objects.create(
            ticket=ticket,
            message=message,
            created_by=request.user,
            is_internal=is_internal
        )
        
        # Update ticket status if not internal
        if not is_internal:
            if ticket.status == 'NEW':
                ticket.status = 'IN_PROGRESS'
                ticket.save()
        
        # Send notification to user if not internal
        if not is_internal and ticket.created_by and ticket.created_by.email:
            notification_service = NotificationService()
            email_service = SimpleEmailService()
            
            # Send notification
            notification_service.send_notification(
                user=ticket.created_by,
                category_name='support_tickets',
                title=f"Response to your ticket: {ticket.subject}",
                message=f"An admin has responded to your ticket",
                priority='medium',
                link=f"/tickets/{ticket.id}/"
            )
            
            # Send email
            try:
                html_content = f"""
                <html>
                <body>
                    <h2>Response to your ticket: {ticket.subject}</h2>
                    <p>An admin has responded to your support ticket:</p>
                    <p><strong>Ticket:</strong> {ticket.subject}</p>
                    <p><strong>Response:</strong> {message}</p>
                    <p><a href="http://localhost:8000/tickets/{ticket.id}/">View full conversation</a></p>
                </body>
                </html>
                """
                email_service.send_email(
                    to_email=ticket.created_by.email,
                    subject=f"Response to your ticket: {ticket.subject}",
                    html_content=html_content,
                    user=ticket.created_by,
                    sent_by=request.user
                )
            except Exception as e:
                print(f"Failed to send email to {ticket.created_by.email}: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Response sent successfully'
        })
        
    except ContactTicket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def admin_assign_ticket(request, ticket_id):
    """Assign ticket to a user"""
    if not request.user.is_superuser or not request.user.userprofile.support_tickets_enabled:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        ticket = ContactTicket.objects.get(id=ticket_id)
        assigned_to_id = request.POST.get('assigned_to')
        
        if not assigned_to_id:
            return JsonResponse({'error': 'User ID is required'}, status=400)
        
        try:
            assigned_user = User.objects.get(id=assigned_to_id, is_staff=True)
            ticket.assigned_to = assigned_user
            ticket.save()
            
            # Send notification to assigned user
            notification_service = NotificationService()
            notification_service.send_notification(
                user=assigned_user,
                category_name='support_tickets',
                title=f"Ticket assigned: {ticket.subject}",
                message=f"A ticket has been assigned to you",
                priority='medium',
                link=f"/admin/tickets/{ticket.id}/"
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Ticket assigned to {assigned_user.get_full_name()}'
            })
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=400)
        
    except ContactTicket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def admin_transfer_ticket(request, ticket_id):
    """Transfer ticket to different department"""
    if not request.user.is_superuser or not request.user.userprofile.support_tickets_enabled:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        ticket = ContactTicket.objects.get(id=ticket_id)
        department = request.POST.get('department')
        reason = request.POST.get('reason', '').strip()
        
        if not department:
            return JsonResponse({'error': 'Department is required'}, status=400)
        
        # Update ticket type (department)
        ticket.ticket_type = department
        ticket.save()
        
        # Create internal note about transfer
        if reason:
            TicketResponse.objects.create(
                ticket=ticket,
                message=f"Ticket transferred to {department} department. Reason: {reason}",
                created_by=request.user,
                is_internal=True
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Ticket transferred to {department} department'
        })
        
    except ContactTicket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def admin_delete_ticket(request, ticket_id):
    """Delete a ticket"""
    if not request.user.is_superuser or not request.user.userprofile.support_tickets_enabled:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        ticket = ContactTicket.objects.get(id=ticket_id)
        ticket.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Ticket deleted successfully'
        })
        
    except ContactTicket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)