from django.urls import path
from . import views

urlpatterns = [
    path('settings/', views.settings_view, name='notification-settings'),
    path('telegram/link/', views.link_telegram, name='notification-telegram-link'),
    path('telegram/unlink/', views.unlink_telegram, name='notification-telegram-unlink'),
    path('test/', views.test_notification, name='notification-test'),
    path('history/', views.history, name='notification-history'),
]