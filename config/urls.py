"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from store import views as store_views
from store import cart_views, account_views

urlpatterns = [
    path('account/', account_views.account, name='account'),
    path('account/login/', account_views.login, name='account_login'),
    path('login/', account_views.account, name='login'),
    path('cart/', cart_views.detail, name='cart'),
    path('cart/add/', cart_views.add, name='cart_add'),
    path('cart/change/', cart_views.change, name='cart_change'),
    path('cart/checkout/', cart_views.checkout, name='checkout'),
    path("health/", lambda request: JsonResponse({"status": "ok"}), name="health"),
    path('admin/', admin.site.urls),
    path('', store_views.home, name='home'),
    path('collections/', store_views.collections, name='collections'),
    path('collections/<slug:slug>/', store_views.category, name='category'),
    path('new-arrivals/', store_views.new_arrivals, name='new_arrivals'),
    path('product/<slug:slug>/', store_views.product_detail, name='product'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
