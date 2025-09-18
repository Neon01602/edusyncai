from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=SocialAccount)
def update_google_profile(sender, instance, created, **kwargs):
    if created and instance.provider == 'google':
        user = instance.user
        extra_data = instance.extra_data
        profile_picture_url = extra_data.get('picture')

        if profile_picture_url:
            user.profile_picture = profile_picture_url
            user.save()