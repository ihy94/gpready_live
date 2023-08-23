from djoser.serializers import TokenSerializer,TokenCreateSerializer

from django.contrib import admin
from django.urls import path,include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path


admin.site.site_header = "Examination control panel"
admin.site.site_title = "Examination"
admin.site.index_title = "QcmLogy control panel"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('quizy.urls')),
    path('api/', include('startHere.urls')),
    path('api/', include('comments.urls')),
    path('subscription/', include('subscription.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),

    # path('api/', include('subscription.urls')),
    # path('__debug__/', include('debug_toolbar.urls')),

    
    path('api/', include('core.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    
    
    # path('', TemplateView.as_view(template_name="index.html")),
    

    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)