from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from mill.forms import FeedbackForm
from mill.models import Feedback

@login_required
def create_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            if form.cleaned_data['factories']:
                form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Feedback submitted successfully!')
            return redirect('feedback_list')
    else:
        form = FeedbackForm()
    
    return render(request, 'mill/feedback_form.html', {'form': form})

@login_required
def feedback_list(request):
    feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'mill/feedback_list.html', {'feedbacks': feedbacks})