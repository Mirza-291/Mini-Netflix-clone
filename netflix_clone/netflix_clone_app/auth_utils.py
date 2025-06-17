# netflix_clone_app/auth_utils.py
from functools import wraps
from django.shortcuts import redirect

def session_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("is_admin"):
            return redirect("admin_login")
        return view_func(request, *args, **kwargs)
    return _wrapped
