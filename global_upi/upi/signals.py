from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from .models import UserProfile, Wallet

@receiver(user_signed_up)
def create_user_profile(request, user, **kwargs):
    profile = UserProfile.objects.create(
        user=user,
        mobile="",
        preferred_currency="INR",  # default
        upi_id=f"{user.username}@upi"
    )

    Wallet.objects.create(
        user=user,
        currency="INR",
        balance=0
    )