from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

from ..forms import SubscribeForm
from ..models import Subscription


def blog_subscribe(request):
    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        if form.is_valid():
            Subscription.objects.create(email=form.cleaned_data['email'])
            messages.success(request, getattr(
                settings, 'POSTINO_SUBSCRIBE_SUCCESS_MESSAGE',
                'Obrigado por assinar nosso Boletim Informativo!'))

    return redirect(getattr(settings, 'POSTINO_REDIRECT_URL', '/'))
