from django.utils.deprecation import MiddlewareMixin

class DisableCSRFForAPI(MiddlewareMixin):
    """Disable CSRF for API endpoints when coming through proxy"""
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Disable CSRF for all /api/ endpoints
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        # Also disable for paths that contain /proxy/
        elif '/proxy/' in request.path:
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None