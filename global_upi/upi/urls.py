from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
        path('register/', views.register_user, name='register'),
    path('user-login/', views.user_login, name='user_login'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),

path("approve-payment/<int:request_id>/", views.approve_payment, name="approve_payment"),

path("reject-payment/<int:request_id>/", views.reject_payment, name="reject_payment"),
    path('logout/', views.logout_user, name='logout'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),

path("add-balance/", views.add_balance, name="add_balance"),
path("find-receiver/", views.find_receiver, name="find_receiver"),
path("send-money/", views.send_money, name="send_money"),
path("approve-payment/<int:request_id>/", views.approve_payment, name="approve_payment"),
path("preview-transfer/", views.preview_transfer, name="preview_transfer"),
path("get_admin_wallet/", views.get_admin_wallet, name="get_admin_wallet"),
path('withdraw/', views.withdraw_balance, name='withdraw_balance'),
path('support/', views.support, name='support'),
    path('admin/support/', views.admin_support_tickets, name='admin_support'),
    path('change-password/', views.change_password, name='change_password'),
  path('admin-panel/block-user/<int:user_id>/', views.block_user, name='block_user'),
]