from django.db import models
from django.contrib.auth.models import User


# -------------------------
# UserProfile (Main User Data)
# -------------------------
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    mobile = models.CharField(max_length=15, unique=True)
    preferred_currency = models.CharField(max_length=10, default="INR")
    first_name = models.CharField(max_length=100, blank=True)

    upi_id = models.CharField(max_length=50, unique=True, blank=True)

    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.upi_id})"

# -------------------------
# Additional Profile (Optional Features)
# -------------------------
class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    full_name = models.CharField(
        max_length=100,
        blank=True
    )

    two_factor_enabled = models.BooleanField(
        default=False
    )

    upi_id = models.CharField(
        max_length=50,
        blank=True
    )

    def __str__(self):
        return self.user.username


# -------------------------
# Wallet System
# -------------------------
class Wallet(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wallets"
    )

    currency = models.CharField(
        max_length=10
    )

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('user', 'currency')

    def __str__(self):
        return f"{self.user.username} - {self.currency} : {self.balance}"


# -------------------------
# Transactions
# -------------------------
class Transaction(models.Model):

    TRANSACTION_TYPE = (
        ('send', 'Send'),
        ('receive', 'Receive'),
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('convert', 'Convert'),
    )

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=10
    )

    description = models.CharField(
        max_length=200,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        default="Completed"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.wallet.user.username} | {self.transaction_type} | {self.amount} {self.currency}"



from django.db import models
from django.contrib.auth.models import User


# -------------------------
# Money Transfer Request
# -------------------------
class MoneyRequest(models.Model):

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_requests")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_requests")

    sender_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="sender_wallet")
    receiver_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="receiver_wallet")

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    converted_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    charge = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, default="Pending")

    created_at = models.DateTimeField(auto_now_add=True)


from django.db import models
from django.contrib.auth.models import User

class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_holder = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"
    
class UPI(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    upi_id = models.CharField(max_length=100)

    def __str__(self):
        return self.upi_id


# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_reply = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.user.email} ({self.status})"