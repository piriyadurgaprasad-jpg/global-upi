from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from decimal import Decimal
from io import BytesIO
import qrcode

from django.core.files.base import ContentFile

from .models import UserProfile, Wallet, Transaction, MoneyRequest


# --------------------------------
# HOME
# --------------------------------

def home(request):
    return render(request, "home.html")


# --------------------------------
# REGISTER USER
# --------------------------------

def register_user(request):

    if request.method == "POST":

        name = request.POST.get("fullname")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        currency = request.POST.get("currency")
        password = request.POST.get("password")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already exists")
            return redirect("/")

        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )

        # Generate UPI ID
        upi_id = f"{user.username}@upi"

        # Create profile
        profile = UserProfile.objects.create(
            user=user,
            mobile=mobile,
            preferred_currency=currency,
            upi_id=upi_id
        )

        # Create wallet automatically
        Wallet.objects.create(
            user=user,
            currency=currency,
            balance=0
        )

        # Generate QR
        upi_link = f"upi://pay?pa={upi_id}&pn={name}&cu={currency}&am=0"

        qr = qrcode.make(upi_link)

        buffer = BytesIO()
        qr.save(buffer, format="PNG")

        file_name = f"user_{user.id}_qr.png"

        profile.qr_code.save(
            file_name,
            ContentFile(buffer.getvalue())
        )

        profile.save()

        messages.success(request, "Registration Successful")

    return redirect("/")


# --------------------------------
# USER LOGIN
# --------------------------------

def user_login(request):

    if request.method == "POST":

        identifier = request.POST.get("identifier")
        password = request.POST.get("password")

        try:
            profile = UserProfile.objects.get(mobile=identifier)
            username = profile.user.username
        except:
            username = identifier

        user = authenticate(request, username=username, password=password)

        if user and not user.is_superuser:
            login(request, user)
            return redirect("user_dashboard")

        messages.error(request, "Invalid Credentials")

    return redirect("/")


# --------------------------------
# ADMIN LOGIN
# --------------------------------

def admin_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.is_superuser:
            login(request, user)
            return redirect("admin_dashboard")

        messages.error(request, "Unauthorized Admin")

    return redirect("/")


# --------------------------------
# USER DASHBOARD
# --------------------------------

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .models import UserProfile, Wallet, Transaction, MoneyRequest

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialAccount
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def user_dashboard(request):
    user = request.user

    # =========================
    # PROFILE (Always ensure)
    # =========================
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "mobile": "",
            "preferred_currency": "",
            "upi_id": f"{user.username}@upi"
        }
    )

    # =========================
    # GOOGLE DATA FETCH
    # =========================
    social_account = SocialAccount.objects.filter(user=user).first()

    if social_account:
        extra_data = social_account.extra_data

        # ✅ Save Google data ONLY if not already saved
        if not user.first_name:
            user.first_name = extra_data.get("given_name", "")
            user.last_name = extra_data.get("family_name", "")
            user.email = extra_data.get("email", user.email)
            user.save()

    # =========================
    # NAME (Never Empty)
    # =========================
    name = user.get_full_name().strip()

    if not name:
        if social_account:
            name = (
                social_account.extra_data.get("name")
                or social_account.extra_data.get("given_name")
            )

    if not name:
        name = user.first_name

    if not name:
        name = user.username

    # =========================
    # EMAIL
    # =========================
    email = user.email

    if not email and social_account:
        email = social_account.extra_data.get("email", "")

    # =========================
    # REDIRECT IF PROFILE INCOMPLETE
    # =========================
    if not profile.mobile or not profile.preferred_currency:
        return redirect('complete_profile')

    # =========================
    # WALLET (Safe)
    # =========================
    wallet, _ = Wallet.objects.get_or_create(
        user=user,
        currency=profile.preferred_currency,
        defaults={"balance": 0}
    )

    # =========================
    # TRANSACTIONS
    # =========================
    recent_tx = Transaction.objects.filter(
        wallet__user=user
    ).order_by("-created_at")[:5]

    pending_requests = MoneyRequest.objects.filter(
        sender=user,
        status="Pending"
    ).order_by("-created_at")

    pending_count = pending_requests.count()

    # =========================
    # ALL TRANSACTIONS (Pagination)
    # =========================
    all_transactions_list = Transaction.objects.filter(
        wallet__user=user
    ).order_by("-created_at")

    paginator = Paginator(all_transactions_list, 7)
    page_number = request.GET.get('page', 1)

    try:
        all_transactions = paginator.page(page_number)
    except PageNotAnInteger:
        all_transactions = paginator.page(1)
    except EmptyPage:
        all_transactions = paginator.page(paginator.num_pages)

    # =========================
    # RENDER
    # =========================
    return render(request, "user_dashboard.html", {
        "profile": profile,
        "wallet": wallet,
        "name": name,
        "email": email,
        "recent_tx": recent_tx,
        "pending_requests": pending_requests,
        "pending_count": pending_count,
        "all_transactions": all_transactions,
        "paginator": paginator,
    })
from django.contrib import messages
from django.shortcuts import redirect, render

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from .models import UserProfile, Wallet

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import update_session_auth_hash

@login_required
def complete_profile(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        mobile = request.POST.get("mobile").strip()
        currency = request.POST.get("currency")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # 🚨 Duplicate mobile check
        if UserProfile.objects.filter(mobile=mobile).exclude(user=user).exists():
            messages.error(request, "Mobile number already registered!")
            return render(request, "complete_profile.html")

        # ✅ Save profile
        profile.mobile = mobile
        profile.preferred_currency = currency
        profile.save()

        # ✅ Set password (optional)
        if password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match!")
                return render(request, "complete_profile.html")

            user.set_password(password)
            user.save()

            # 🔥 IMPORTANT FIX
            update_session_auth_hash(request, user)

        # ✅ Ensure wallet (avoid duplicates)
        Wallet.objects.get_or_create(
            user=user,
            currency=currency,
            defaults={"balance": 0}
        )

        messages.success(request, "Profile completed successfully!")

        # ✅ FINAL REDIRECT
        return redirect("user_dashboard")

    return render(request, "complete_profile.html", {"profile": profile})
# ----------------------


# ----------
# ADMIN DASHBOARD
# --------------------------------
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import User, Wallet, Transaction, MoneyRequest  # adjust import path if needed
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q

from .models import (
    UserProfile, Wallet, Transaction, 
    MoneyRequest, SupportTicket
)
from django.db.models import Count, Sum
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect("user_dashboard")

    # ====================== Basic Stats ======================
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    # New users this month
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = User.objects.filter(date_joined__gte=start_of_month).count()

    # Wallet & Transaction Stats
    total_wallets = Wallet.objects.count()
    total_transactions = Transaction.objects.count()
    pending_requests_count = MoneyRequest.objects.filter(status="Pending").count()

    # Admin wallet (for balance display if needed)
    admin_wallet = Wallet.objects.filter(user__is_superuser=True).first()
    admin_balance = admin_wallet.balance if admin_wallet else 0.00

    # ====================== Request History Data ======================
    all_requests = MoneyRequest.objects.select_related(
        'sender', 'receiver', 'sender_wallet', 'receiver_wallet'
    ).order_by('-created_at')

    # ====================== Users Section Data ======================
    # Optimized queryset with related data
    all_users = User.objects.select_related('user_profile').prefetch_related('wallets').annotate(
        transaction_count=Count('wallets__transactions')
    ).order_by('-date_joined')

    # ====================== Support Section Data ======================
    support_tickets = SupportTicket.objects.select_related('user').order_by('-created_at')

    total_tickets = support_tickets.count()
    open_tickets = SupportTicket.objects.filter(status='Open').count()
    resolved_tickets = SupportTicket.objects.filter(status='Resolved').count()

    # ====================== Analytics Context (Basic) ======================
    # You can expand this later with more charts/stats
    total_revenue = Transaction.objects.filter(
        transaction_type='deposit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    context = {
        # Request History (for the table + stats)
        "requests": all_requests,
        "pending_requests_count": pending_requests_count,

        # Users Section
        "total_users": total_users,
        "active_users": active_users,
        "new_users_this_month": new_users_this_month,
        "all_users": all_users,

        # Support Section
        "support_tickets": support_tickets,
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,

        # General Stats
        "total_wallets": total_wallets,
        "total_transactions": total_transactions,
        "admin_balance": admin_balance,

        # Analytics (expandable)
        "total_revenue": total_revenue,
    }

    return render(request, "admin_dashboard.html", context)

# --------------------------------
# ADD BALANCE
# --------------------------------

@login_required
def add_balance(request):

    if request.method == "POST":

        amount = request.POST.get("amount")

        try:
            amount = Decimal(amount)
        except:
            messages.error(request, "Invalid amount")
            return redirect("user_dashboard")

        profile = UserProfile.objects.get(user=request.user)

        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            currency=profile.preferred_currency
        )

        wallet.balance += amount
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            transaction_type="deposit",
            amount=amount,
            currency=wallet.currency,
            description="Wallet Top-up"
        )

        messages.success(request, "Money added successfully")

    return redirect("user_dashboard")
@login_required
def send_money(request):
    if request.method == "POST":
        upi_id = request.POST.get("upi_id")
        try:
            amount = Decimal(request.POST.get("amount"))
            if amount <= 0:
                messages.error(request, "Amount must be greater than zero")
                return redirect("user_dashboard")
        except:
            messages.error(request, "Invalid amount")
            return redirect("user_dashboard")

        # Get sender wallet
        try:
            sender_wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            messages.error(request, "Wallet not found")
            return redirect("user_dashboard")

        # Find receiver
        try:
            receiver_profile = UserProfile.objects.get(upi_id=upi_id)
        except UserProfile.DoesNotExist:
            messages.error(request, "Receiver not found. Please check UPI ID.")
            return redirect("user_dashboard")

        receiver_user = receiver_profile.user
        receiver_wallet = Wallet.objects.get(user=receiver_user)

        # ==================== ADD SELF-TRANSFER CHECK ====================
        if receiver_user == request.user:
            messages.error(request, "You cannot send money to yourself.")
            return redirect("user_dashboard")
        # ================================================================

        sender_currency = sender_wallet.currency
        receiver_currency = receiver_wallet.currency


        total_deduct = amount 

        if sender_wallet.balance < total_deduct:
            messages.error(request, "Insufficient balance")
            return redirect("user_dashboard")

        # Currency conversion
        rate = EXCHANGE_RATES.get(sender_currency, {}).get(receiver_currency, 1)
        converted_amount = amount * Decimal(rate)

        # Deduct from sender immediately
        sender_wallet.balance -= total_deduct
        sender_wallet.save()

        # Create pending request
        MoneyRequest.objects.create(
            sender=request.user,
            receiver=receiver_user,
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=amount,
            converted_amount=converted_amount,
          
            status="Pending"
        )

        messages.success(request, "Transfer request sent to admin for approval")
        return redirect("user_dashboard")

    return redirect("user_dashboard")

# --------------------------------
# FIND RECEIVER
# --------------------------------

@login_required
def find_receiver(request):
    identifier = request.GET.get("identifier", "").strip()

    if not identifier:
        return JsonResponse({"success": False, "message": "Identifier required"})

    try:
        receiver_profile = None

        # Try UPI ID
        try:
            receiver_profile = UserProfile.objects.get(upi_id=identifier)
        except UserProfile.DoesNotExist:
            pass

        # Try Mobile
        if not receiver_profile:
            try:
                receiver_profile = UserProfile.objects.get(mobile=identifier)
            except UserProfile.DoesNotExist:
                pass

        # Try Email
        if not receiver_profile:
            try:
                receiver_profile = UserProfile.objects.get(user__email=identifier)
            except UserProfile.DoesNotExist:
                pass

        if receiver_profile:
            # Prevent showing yourself as receiver
            if receiver_profile.user == request.user:
                return JsonResponse({
                    "success": False,
                    "message": "You cannot send money to yourself"
                })

            return JsonResponse({
                "success": True,
                "receiver": {
                    "name": receiver_profile.user.first_name or "User",
                    "upi_id": receiver_profile.upi_id,
                    "mobile": receiver_profile.mobile,
                    "currency": receiver_profile.preferred_currency
                }
            })

        return JsonResponse({"success": False, "message": "Receiver not found"})

    except Exception:
        return JsonResponse({"success": False, "message": "Error finding receiver"})

# --------------------------------
# EXCHANGE RATES
# --------------------------------

EXCHANGE_RATES = {

    "INR": {"USD": 0.012, "GBP": 0.0095, "INR": 1},

    "USD": {"INR": 83, "GBP": 0.79, "USD": 1},

    "GBP": {"INR": 105, "USD": 1.26, "GBP": 1}

}
from decimal import Decimal

CURRENCY_TO_INR = {
    "INR": Decimal("1"),
    "USD": Decimal("83"),
    "GBP": Decimal("105"),
    "KWD": Decimal("270")
}

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal
from .models import Wallet, MoneyRequest, Transaction


from django.shortcuts import get_object_or_404, redirect
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
from decimal import Decimal
from .models import Wallet, MoneyRequest, Transaction

@login_required
def approve_payment(request, request_id):

    if not request.user.is_superuser:
        return redirect("user_dashboard")

    payment = get_object_or_404(MoneyRequest, id=request_id)

    sender_wallet = payment.sender_wallet
    receiver_wallet = payment.receiver_wallet

    amount = payment.amount
    converted_amount = payment.converted_amount

    receiver_wallet.balance += converted_amount
    receiver_wallet.save()

  

    Transaction.objects.create(
        wallet=sender_wallet,
        transaction_type="send",
        amount=amount,
        currency=sender_wallet.currency,
        description=f"Sent to {payment.receiver.username}"
    )

    Transaction.objects.create(
        wallet=receiver_wallet,
        transaction_type="receive",
        amount=converted_amount,
        currency=receiver_wallet.currency,
        description=f"Received from {payment.sender.username}"
    )

   

    payment.status = "Approved"
    payment.save()

    return redirect("admin_dashboard")
# --------------------------------
# REJECT PAYMENT
# --------------------------------

@login_required
def reject_payment(request, request_id):

    if not request.user.is_superuser:
        return redirect("user_dashboard")

    payment = get_object_or_404(MoneyRequest, id=request_id)

    payment.status = "Rejected"
    payment.save()

    return redirect("admin_dashboard")


# --------------------------------
# LOGOUT
# --------------------------------

def logout_user(request):
    logout(request)
    return redirect("/")



@login_required
def preview_transfer(request):

    upi_id = request.GET.get("upi_id")
    amount = request.GET.get("amount")

    try:
        amount = Decimal(amount)
    except:
        return JsonResponse({"success": False})

    try:
        receiver_profile = UserProfile.objects.get(upi_id=upi_id)
    except:
        return JsonResponse({"success": False})

    sender_wallet = Wallet.objects.filter(user=request.user).first()
    receiver_wallet = Wallet.objects.filter(user=receiver_profile.user).first()

    sender_currency = sender_wallet.currency
    receiver_currency = receiver_wallet.currency

    rate = EXCHANGE_RATES.get(sender_currency, {}).get(receiver_currency, 1)

    converted = amount * Decimal(rate)


    total = amount 

    return JsonResponse({
        "success": True,
        "amount": float(amount),
        "converted_amount": float(converted),
       
        "total": float(total),
        "sender_currency": sender_currency,
        "receiver_currency": receiver_currency
    })


from django.contrib.auth.models import User
from .models import Wallet

from django.contrib.auth.models import User
from .models import Wallet

def get_admin_wallet():

    admin_user = User.objects.filter(is_superuser=True).first()

    admin_wallet, created = Wallet.objects.get_or_create(
        user=admin_user,
        currency="INR",
        defaults={"balance": 0}
    )

    return admin_wallet


from decimal import Decimal

@login_required
def withdraw_balance(request):

    if request.method == "POST":

        amount = Decimal(request.POST.get("amount"))
        withdraw_type = request.POST.get("withdraw_type")

        profile = UserProfile.objects.get(user=request.user)

        wallet = Wallet.objects.get(
            user=request.user,
            currency=profile.preferred_currency
        )

        if wallet.balance < amount:
            messages.error(request, "Insufficient balance")
            return redirect("user_dashboard")

        # Deduct balancesend
        wallet.balance -= amount
        wallet.save()

        # Save transaction
        Transaction.objects.create(
            wallet=wallet,
            transaction_type="withdraw",
            amount=amount,
            currency=wallet.currency,
            description=f"Money Withdrawn"
        )

        messages.success(request, f"Withdrawn Successful")

    return redirect("user_dashboard")



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SupportTicket

# =====================================
# SUPPORT VIEW - FIXED
# =====================================
@login_required
def support(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    
    wallet = None
    if profile:
        wallet = Wallet.objects.filter(
            user=request.user,
            currency=profile.preferred_currency
        ).first()

    if request.method == "POST":
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        if not subject:
            messages.error(request, "Please enter a subject.")
            return redirect("support")

        if not message or len(message) < 15:
            messages.error(request, "Please describe your issue in more detail (minimum 15 characters).")
            return redirect("support")

        # Create support ticket - CORRECT FIELD NAMES
        SupportTicket.objects.create(
            user=request.user,
            subject=subject,      # ← Correct
            message=message,      # ← Correct
            status="Open"
        )

        messages.success(request, "Your support ticket has been submitted successfully. Our team will respond within 2 hours.")
        return redirect("support")

    # GET request
    user_tickets = SupportTicket.objects.filter(user=request.user).order_by("-created_at")

    recent_tx = Transaction.objects.filter(wallet__user=request.user).order_by("-created_at")[:5]
    pending_requests = MoneyRequest.objects.filter(sender=request.user, status="Pending").order_by("-created_at")
    pending_count = pending_requests.count()
    all_transactions = Transaction.objects.filter(wallet__user=request.user).order_by("-created_at")

    return render(request, "user_dashboard.html", {
        "profile": profile,
        "wallet": wallet,
        "recent_tx": recent_tx,
        "pending_requests": pending_requests,
        "pending_count": pending_count,
        "all_transactions": all_transactions,
        "user_tickets": user_tickets,
    })
# Optional: Admin view to see all tickets (you can add later)
@login_required
def admin_support_tickets(request):
    if not request.user.is_superuser:
        return redirect("user_dashboard")

    tickets = SupportTicket.objects.all().order_by("-created_at")
    return render(request, "admin_support.html", {"tickets": tickets})




from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

# =====================================
# CHANGE PASSWORD VIEW
# =====================================
@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            # Keep user logged in after password change
            update_session_auth_hash(request, user)
            
            messages.success(request, "Your password has been changed successfully!")
            return redirect("user_dashboard")   # or "profile" if you have separate profile page
        else:
            # Pass errors to template
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    
    # For GET request - we still need to render full dashboard context
    profile = UserProfile.objects.filter(user=request.user).first()
    wallet = Wallet.objects.filter(
        user=request.user,
        currency=profile.preferred_currency if profile else None
    ).first()

    recent_tx = Transaction.objects.filter(wallet__user=request.user).order_by("-created_at")[:5]
    pending_requests = MoneyRequest.objects.filter(sender=request.user, status="Pending").order_by("-created_at")
    pending_count = pending_requests.count()
    all_transactions = Transaction.objects.filter(wallet__user=request.user).order_by("-created_at")
    user_tickets = SupportTicket.objects.filter(user=request.user).order_by("-created_at") if 'SupportTicket' in globals() else []

    return render(request, "user_dashboard.html", {
        "profile": profile,
        "wallet": wallet,
        "recent_tx": recent_tx,
        "pending_requests": pending_requests,
        "pending_count": pending_count,
        "all_transactions": all_transactions,
        "user_tickets": user_tickets,
        "password_form": PasswordChangeForm(request.user),  # optional
    })


@login_required
def block_user(request, user_id):
    if not request.user.is_superuser:
        return redirect("admin_dashboard")
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f"User has been {'unblocked' if user.is_active else 'blocked'} successfully.")
    return redirect("admin_dashboard")


