from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/blog/', permanent=False)),
    path('blog/', include('postino.urls')),
    path('newsletter/', include('dove.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
