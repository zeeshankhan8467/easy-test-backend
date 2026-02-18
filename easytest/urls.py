"""
URL configuration for easytest project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from api.views import export_report_http

urlpatterns = [
    path('admin/', admin.site.urls),
    # Export report - plain Django view (HttpRequest/HttpResponse) to avoid DRF assertion
    path('api/report-export/<int:exam_id>/', export_report_http, name='report-export'),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
