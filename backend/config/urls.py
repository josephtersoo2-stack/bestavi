from pathlib import Path
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.http import HttpResponse, FileResponse

frontend_dist = Path(settings.BASE_DIR).parent / 'frontend' / 'dist'

def serve_react_app(request):
    index_file = frontend_dist / 'index.html'
    if index_file.exists():
        return FileResponse(open(index_file, 'rb'), content_type='text/html')
    return HttpResponse(
        "<h3>Aviator Bot Backend Running</h3>"
        "<p>Frontend build not detected. If running locally, visit Vite dev server at http://localhost:5173.</p>",
        status=200
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('bot_engine.urls')),
    path('api/', include('bot_engine.urls')),
    re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': str(frontend_dist / 'assets')}),
    re_path(r'^favicon.svg$', serve, {'document_root': str(frontend_dist), 'path': 'favicon.svg'}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    re_path(r'^(?!api|admin|ws|static|assets).*$', serve_react_app),
]
