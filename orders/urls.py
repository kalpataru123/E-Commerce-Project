from django.urls import path
from .import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payment, name='payments'),
    path('payment_done/', views.payment_done, name='payment_done'),
    path('invoice/<str:order_number>/<str:payment_id>/', views.download_invoice, name='download_invoice'),


]
