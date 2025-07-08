from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Session
from django.core.management import call_command

@receiver(pre_save, sender=Session)
def handle_session_change(sender, instance, **kwargs):
    if instance.pk is None:  # New Session, no ID in database yet
        return  # Skip querying
    try:
        old_session = Session.objects.get(id=instance.id)
        # Add your logic here, e.g., compare old_session.is_current with instance.is_current
    except Session.DoesNotExist:
        pass