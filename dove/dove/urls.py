from django.urls import path

from . import views

app_name = 'dove'

urlpatterns = [
    path('unsubscribe/<uuid:token>/', views.unsubscribe_confirm, name='unsubscribe'),
    path('unsubscribed/', views.unsubscribed, name='unsubscribed'),
]
