from django.shortcuts import get_object_or_404, redirect, render

from postino.models import Subscription

from ..models import CampaignSend, Unsubscribe


def unsubscribe_confirm(request, token):
    send = get_object_or_404(CampaignSend, token=token)

    if request.method == 'POST':
        Unsubscribe.objects.get_or_create(email=send.email)
        Subscription.objects.filter(email=send.email).delete()
        return redirect('dove:unsubscribed')

    return render(request, 'dove/unsubscribe_confirm.html', {'email': send.email})


def unsubscribed(request):
    return render(request, 'dove/unsubscribed.html')
