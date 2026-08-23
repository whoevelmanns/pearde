"""Auto-login for the local single-user Plane: every anonymous request is
signed in as the service account, so no screen in the app ever asks for a
password. Sign-out signs you straight back in.

Active only when PLANE_AUTOLOGIN_EMAIL is set — plane.sh sets it via the
compose override it writes, and only while the proxy is pinned to 127.0.0.1.
"""
import os


class AutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.email = os.environ.get("PLANE_AUTOLOGIN_EMAIL")

    def __call__(self, request):
        if self.email and not request.user.is_authenticated:
            from django.contrib.auth import login
            from plane.db.models import User

            user = User.objects.filter(email=self.email, is_active=True).first()
            if user is not None:
                login(request, user,
                      backend="django.contrib.auth.backends.ModelBackend")
        return self.get_response(request)
