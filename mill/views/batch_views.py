from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from mill.models import BatchForFactory, Factory
from django.http import HttpResponse
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

def manage_batches(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"Action: {action}")

        try:
            if action == "add_batch":
                with transaction.atomic():
                    factory_id = request.POST.get('factory')
                    batch_number = request.POST.get('batch_number')
                    amount_wheat = request.POST.get('amount_wheat')
                    waist_factor = request.POST.get('waist_factor')
                    datetime_field = request.POST.get('datetime_field')

                    # Validate batch_number
                    if not batch_number:
                        raise ValueError("Batch number cannot be empty")

                    factory = Factory.objects.get(id=factory_id)
                    print(f"Creating batch for factory: {factory.name}")
                    
                    batch = BatchForFactory.objects.create(
                        batchInteger=batch_number,
                        factory=factory,
                        amountofwheat=amount_wheat,
                        waistfactor=waist_factor
                    )
                    print(f"Batch {batch_number} created successfully")
                    messages.success(request, 'Batch created successfully')

            elif action == "update_batch":
                with transaction.atomic():
                    batch_id = request.POST.get('batch_id')
                    batch = get_object_or_404(BatchForFactory, id=batch_id)
                    print(f"Updating batch: {batch.batchInteger}")

                    batch_number = request.POST.get('batch_number')
                    # Validate batch_number
                    if not batch_number:
                        raise ValueError("Batch number cannot be empty")

                    batch.batchInteger = batch_number
                    batch.amountofwheat = request.POST.get('amount_wheat')
                    batch.waistfactor = request.POST.get('waist_factor')
                    batch.save()
                    
                    print(f"Batch {batch.batchInteger} updated successfully")
                    messages.success(request, 'Batch updated successfully')

            elif action == "delete_batch":
                batch_id = request.POST.get('batch_id')
                batch = get_object_or_404(BatchForFactory, id=batch_id)
                print(f"Deleting batch: {batch.batchInteger}")
                
                batch.delete()
                print("Batch deleted successfully")
                messages.success(request, 'Batch deleted successfully')

        except ObjectDoesNotExist as e:
            messages.error(request, f"Error: {str(e)}")
            print(f"Error occurred: {str(e)}")
        except ValueError as e:
            messages.error(request, f"Validation error: {str(e)}")
            print(f"Validation error: {str(e)}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            print(f"Unexpected error: {str(e)}")

        return redirect('manage_batches')

    print("Rendering batch management template")
    factories = Factory.objects.all()
    batches = BatchForFactory.objects.all().order_by('-DateTimeField')
    return render(request, 'mill/manage_batch.html', {
        'factories': factories,
        'batches': batches
    })

def batch_list(request):
    batches = BatchForFactory.objects.all().order_by('-DateTimeField')
    return render(request, 'mill/manage_batch.html', {'batches': batches})