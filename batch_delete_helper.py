#!/usr/bin/env python3
"""
Batch Delete Helper Script
This script helps delete batches with proper error handling and force delete options.
"""

import os
import sys
import django

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mill.models import Batch
from django.contrib.auth.models import User
from mill.utils.permmissions_handler_utils import is_super_admin

def delete_batch(batch_id, force_delete=False, username='danny'):
    """Delete a batch with proper error handling"""
    try:
        # Get user
        user = User.objects.get(username=username)
        if not is_super_admin(user):
            print(f"❌ User '{username}' is not a super admin")
            return False
            
        # Get batch
        batch = Batch.objects.get(id=batch_id)
        print(f"📦 Found batch: {batch.batch_number} (ID: {batch.id})")
        print(f"   Status: {batch.status}")
        print(f"   Factory: {batch.factory.name if batch.factory else 'No Factory'}")
        
        # Check if can delete
        if batch.status in ['in_process', 'completed'] and not force_delete:
            print(f"❌ Cannot delete batch in '{batch.status}' status")
            print(f"   Use force_delete=True to force delete")
            return False
            
        # Delete the batch
        batch_number = batch.batch_number
        batch.delete()
        
        print(f"✅ Successfully deleted batch '{batch_number}'")
        return True
        
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found")
        return False
    except Batch.DoesNotExist:
        print(f"❌ Batch with ID {batch_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error deleting batch: {str(e)}")
        return False

def main():
    """Main function to handle batch deletion"""
    print("🔧 BATCH DELETE HELPER")
    print("=" * 30)
    
    # Show available batches
    print("\n📋 AVAILABLE BATCHES:")
    batches = Batch.objects.all().order_by('id')
    for batch in batches:
        can_delete = batch.status not in ['in_process', 'completed']
        print(f"   ID {batch.id}: {batch.batch_number} ({batch.status}) → Can delete: {can_delete}")
    
    # Delete specific batches
    batch_ids = [14, 15, 17]  # The ones that were causing 400 errors
    
    print(f"\n🗑️ DELETING BATCHES: {batch_ids}")
    for batch_id in batch_ids:
        print(f"\n--- Deleting Batch {batch_id} ---")
        success = delete_batch(batch_id, force_delete=False)
        if not success:
            print(f"   Trying force delete...")
            success = delete_batch(batch_id, force_delete=True)
        
        if success:
            print(f"   ✅ Batch {batch_id} deleted successfully")
        else:
            print(f"   ❌ Failed to delete batch {batch_id}")
    
    # Show remaining batches
    print(f"\n📋 REMAINING BATCHES:")
    remaining = Batch.objects.all().order_by('id')
    for batch in remaining:
        print(f"   ID {batch.id}: {batch.batch_number} ({batch.status})")

if __name__ == "__main__":
    main() 