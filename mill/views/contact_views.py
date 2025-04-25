from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from mill.forms import ContactTicketForm
from mill.models import ContactTicket, Factory

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
            messages.success(request, _("Your ticket has been submitted successfully. We'll get back to you soon."))
            return redirect('mill:contact_success')
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
@require_POST
def ticket_update(request, ticket_id):
    # Logic for updating ticket status (for admins/staff)
    if not request.user.is_staff:
        messages.error(request, _("You don't have permission to update ticket status."))
        return redirect('mill:my_tickets')
        
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
    
    return redirect('mill:my_tickets')