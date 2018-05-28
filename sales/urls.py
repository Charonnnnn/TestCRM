"""TestCRM URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path,include,re_path
from sales import views

urlpatterns = [
    path('', views.sales_index, name='sales_index'),
    path('customer/', views.customer_list),

    re_path('customer/(\d+)/enrollment/', views.enrollment),
    re_path('customer/registration/(\d+)/(\w+)/', views.stu_registration),
    re_path('contract_review/(\d+)/', views.contract_review),
    re_path('payment/(\d+)/', views.payment,name='payment'),
    re_path('enrollment_rejection/(\d+)/', views.enrollment_rejection, name='enrollment_rejection'),

]
