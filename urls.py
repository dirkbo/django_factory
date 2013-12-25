from django.conf.urls import patterns, url

from django_factory import views

urlpatterns = patterns('',
     url(r'^(?P<path>.+)\.js', views.js_file, name='js_file'),
     url(r'^(?P<path>.+)\.css', views.css_file, name='css_file'),
)
