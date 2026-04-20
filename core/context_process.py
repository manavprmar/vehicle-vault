def user_role(request):
    """
    Add user role to template context for easy access in templates.
    """
    role = None
    if request.user.is_authenticated:
        role = request.user.role
    return {"user_role": role}
    
