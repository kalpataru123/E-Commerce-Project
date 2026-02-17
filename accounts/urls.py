"""
URL configuration for greatkart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .import views

urlpatterns = [
    path('login/', views.login_page, name="login"),
    path('register/', views.register, name="register"),
    path('logout/', views.logout_user, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('activate/<uidb64>/<token>/', views.activate, name="activate"),
    path('', views.dashboard, name="dashboard"),
    path('forgotPassword/', views.forgot_password, name="forgotPassword"),
    path('reset_password_confirm/<uidb64>/<token>/', views.reset_password_confirm, name="reset_password_confirm"),
    path('my_orders/',views.my_orders,name="my_orders"),
    path('edit_profile/',views.edit_profile,name="edit_profile"),
    path('change_password/',views.change_password,name="change_password"),
    path('order_detail/<int:order_id>/',views.order_detail,name="order_detail"),
]
