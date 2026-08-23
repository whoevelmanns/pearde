# Auto-imported by Python at startup (this directory is on PYTHONPATH in the
# compose override plane.sh writes). Hooks Django's Settings so that
# auto_login.AutoLoginMiddleware lands right after AuthenticationMiddleware —
# without replacing or wrapping Plane's settings module, which imports
# circularly and cannot be re-exported from another module.
import os

if os.environ.get("PLANE_AUTOLOGIN_EMAIL"):
    try:
        from django.conf import Settings

        _orig = Settings.__init__

        def _patched(self, settings_module):
            _orig(self, settings_module)
            mw = list(getattr(self, "MIDDLEWARE", []) or [])
            if mw and "auto_login.AutoLoginMiddleware" not in mw:
                after = next((i for i, m in enumerate(mw)
                              if "AuthenticationMiddleware" in m), len(mw) - 1)
                mw.insert(after + 1, "auto_login.AutoLoginMiddleware")
                self.MIDDLEWARE = mw

        Settings.__init__ = _patched
    except Exception:
        pass  # never break the interpreter over a convenience feature
