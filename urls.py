from django.urls import re_path
from django_factory import views

urlpatterns = [
     re_path(r'^(?P<path>.+)\.js', views.js_file, name='js_file'),
     re_path(r'^(?P<path>.+)\.css', views.css_file, name='css_file'),
]
