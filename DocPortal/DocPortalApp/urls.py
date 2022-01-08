from os import stat
from django.conf import settings
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('converted/<str:doc>', views.converted, name='converted'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/deleteFile/<str:doc>', views.delete, name='deleteDoc'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)