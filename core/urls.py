from django.urls import path
from . import views

app_name = "core"


urlpatterns = [
    path('login/', views.UserLoginView, name='login'),
    path("signup/", views.UserSignupView, name="signup"),
    path("verify-otp/", views.VerifyOTPView, name="verify_otp"),
    path("logout/", views.LogoutViewCustom, name="logout"),
    path("contact/", views.contact, name="contact"),
    path("faq/", views.faq, name="faq"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("about/", views.about, name="about"),

    # Services
    path("car-loan/", views.car_loan, name="car_loan"),
    path("car-insurance/", views.car_insurance, name="car_insurance"),
    path("car-valuation/", views.car_valuation, name="car_valuation"),
    path("sell-your-car/", views.sell_car, name="sell_car"),
    path("help-center/", views.help_center, name="help_center"),
    path("sitemap/", views.sitemap, name="sitemap"),
    path("loan-application/", views.loan_application, name="loan_application"),
    path("insurance-quote/", views.insurance_quote, name="insurance_quote"),
    path("valuation-check/", views.valuation_check, name="valuation_check"),
    
    # Dashboards
    path("dashboard/", views.DashboardRedirectView, name="dashboard_redirect"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/seller/", views.seller_dashboard, name="seller_dashboard"),
    path("dashboard/buyer/", views.buyer_dashboard, name="buyer_dashboard"),
    
    # Profile
    path("profile/", views.ProfileUpdateView, name="profile"),

    # Password Recovery
    path("password-reset/", views.PasswordResetRequestView, name="password_reset"),
    path("password-reset/verify/", views.PasswordResetVerifyView, name="password_reset_verify"),

    # User Management
    path("manage-users/", views.UserManageListView, name="manage_users"),
    path("manage-users/delete/<str:user_id>/", views.UserDeleteView, name="forced_delete_user"),
]