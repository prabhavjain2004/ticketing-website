from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from django.http import HttpResponse

def favicon_view(request):
    """Handle favicon requests"""
    return HttpResponse(status=204)  # No content - suppresses 404 errors

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ticketing.urls')),
    # Logo test page for debugging
    path('logo-test/', TemplateView.as_view(template_name='logo_test.html'), name='logo_test'),
    # Handle favicon requests
    path('favicon.ico', favicon_view, name='favicon_ico'),
    path('favicon.png', favicon_view, name='favicon_png'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve static files in production (for Vercel)
if not settings.DEBUG:
    from django.views.static import serve
    urlpatterns += [
        path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
    ]