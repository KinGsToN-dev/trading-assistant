from django.urls import path
from . import views

urlpatterns = [
    path('watchlist/', views.watchlist, name='market-watchlist'),
    path('refresh/', views.manual_refresh, name='market-refresh'),
    path('<str:symbol>/', views.price_detail, name='market-price-detail'),
    path('<str:symbol>/candles/', views.candles, name='market-candles'),
    path('debug/', views.debug_coingecko, name='market-debug'),
]