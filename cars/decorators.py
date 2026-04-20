<<<<<<< HEAD
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login')
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse("You do not have permission to access this page.")
        return wrapper

    return decorator

def seller_or_admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.SELLER, User.Role.ADMIN]: # type: ignore
            messages.error(request, "Seller or Admin access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def buyer_or_admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.BUYER, User.Role.ADMIN]: # type: ignore
            messages.error(request, "Buyer or Admin access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def dealer_or_admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.DEALER, User.Role.ADMIN]: # type: ignore
            messages.error(request, "Dealer or Admin access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def seller_or_dealer_or_admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.SELLER, User.Role.DEALER, User.Role.ADMIN]: # type: ignore
            messages.error(request, "Seller or Dealer or Admin access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def buyer_or_seller_or_dealer_or_admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.BUYER, User.Role.SELLER, User.Role.DEALER, User.Role.ADMIN]: # type: ignore
            messages.error(request, "Buyer or Seller or Dealer or Admin access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def buyer_or_seller_or_dealer_or_admin_or_staff_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.BUYER, User.Role.SELLER, User.Role.DEALER, User.Role.ADMIN, User.Role.STAFF]: # type: ignore
            messages.error(request, "Buyer or Seller or Dealer or Admin or Staff access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def buyer_or_seller_or_dealer_or_admin_or_staff_or_finance_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.BUYER, User.Role.SELLER, User.Role.DEALER, User.Role.ADMIN, User.Role.STAFF, User.Role.FINANCE]: # type: ignore
            messages.error(request, "Buyer or Seller or Dealer or Admin or Staff or Finance access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def buyer_or_seller_or_dealer_or_admin_or_staff_or_finance_or_insurance_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.BUYER, User.Role.SELLER, User.Role.DEALER, User.Role.ADMIN, User.Role.STAFF, User.Role.FINANCE, User.Role.INSURANCE]: # type: ignore
            messages.error(request, "Buyer or Seller or Dealer or Admin or Staff or Finance or Insurance access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def buyer_or_seller_or_dealer_or_admin_or_staff_or_finance_or_insurance_or_mechanic_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.BUYER, User.Role.SELLER, User.Role.DEALER, User.Role.ADMIN, User.Role.STAFF, User.Role.FINANCE, User.Role.INSURANCE, User.Role.MECHANIC]: # type: ignore
            messages.error(request, "Buyer or Seller or Dealer or Admin or Staff or Finance or Insurance or Mechanic access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def buyer_or_seller_or_dealer_or_admin_or_staff_or_finance_or_insurance_or_mechanic_or_mechanic_admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.BUYER, User.Role.SELLER, User.Role.DEALER, User.Role.ADMIN, User.Role.STAFF, User.Role.FINANCE, User.Role.INSURANCE, User.Role.MECHANIC, User.Role.MECHANIC_ADMIN]: # type: ignore
            messages.error(request, "Buyer or Seller or Dealer or Admin or Staff or Finance or Insurance or Mechanic or Mechanic Admin access only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper
=======
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login')
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse("You do not have permission to access this page.")
        return wrapper
    return decorator
>>>>>>> 5a1a3e867c88f623617f14ff6f950e7e72a946c0
