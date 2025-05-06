from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Session
from django.core.management import call_command

@receiver(pre_save, sender=Session)
def handle_session_change(sender, instance, **kwargs):
    if instance.id:  # Existing session
        old_session = Session.objects.get(id=instance.id)
        if old_session.is_current and not instance.is_current:
            # Session is being marked as non-current
            call_command('mark_compulsory_carryovers')