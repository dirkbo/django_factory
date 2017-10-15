from django.conf.urls import url

from django_factory import views

urlpatterns = [
     url(r'^(?P<path>.+)\.js', views.js_file, name='js_file'),
     url(r'^(?P<path>.+)\.css', views.css_file, name='css_file'),
     url(r'^pwa-serviceworker.js', views.pwa_serviceworker, name='pwa_serviceworker'),
]
