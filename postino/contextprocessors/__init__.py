from django.conf import settings


def postino(request):
    return {
        'base_template': getattr(settings, 'POSTINO_BASE_TEMPLATE', 'base.html'),
    }
