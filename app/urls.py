from django.urls import path

from . import views

urlpatterns = [
    path('signup', views.user_creation, name='user_creation'),
    path('signin/', views.user_authentication, name="authentication"),
    path('data-extraction/', views.document_extraction, name="data_extraction"),
]