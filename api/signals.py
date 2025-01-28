import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from api.utils import publish_to_redis
from .models import Reminder
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Reminder)
def reminder_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Reminder model saves with enhanced logging.
    """
    print("\n=== REMINDER POST SAVE SIGNAL ===")
    print(f"➡️ Reminder ID: {instance.uid}")
    print(f"➡️ Is new reminder: {created}")
    print(f"➡️ Current sent status: {instance.sent}")
    
    if not instance.sent:
        action = 'created' if created else 'scheduled'
        print(f"➡️ Publishing with action: {action}")
        
        success = publish_to_redis(instance, action=action)
        
        if success:
            print("✅ Successfully handled post-save signal")
        else:
            print("❌ Failed to handle post-save signal")
    else:
        print("ℹ️ Reminder already sent, skipping Redis publish")
    
    print("==============================\n")