# -*- coding:utf-8 -*-
import logging

# Django imports
from django.http import HttpResponseBadRequest, HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.gzip import gzip_page
from django.template import RequestContext
from django.core.cache import cache

from hashlib import sha224

# Get an instance of a logger
logger = logging.getLogger('bluesoybean.custom')


def render_asset(template, request, content_type="text/plain",
                 force_shrink=False):
    key = "asset-%s" % template
    resp = cache.get(key, False)
    if resp is False:
        try:
            resp = render_to_string(template, {},
                                    context_instance=RequestContext(request))
        except Exception, e:
            if settings.DEBUG:
                raise e
            return HttpResponseBadRequest("bad Request: %s" % template)
        if not settings.DEBUG or force_shrink is True:
            if content_type.endswith("javascript"):
                from jsmin import jsmin
                resp = jsmin(resp)
            if content_type.endswith("css"):
                from cssmin import cssmin
                resp = cssmin(resp)
        etag = sha224(resp.encode('utf-8')).hexdigest()
        resp = HttpResponse(resp, content_type=content_type)
        resp['etag'] = etag
        #TODO: Far ahead expires header
        if not settings.DEBUG:
            cache.set(key, resp, 600)
            logger.info("caching: %s" % template)
    return resp


@gzip_page
def js_file(request, path):
    return render_asset('js/%s.js.html' % path, request,
                        content_type="text/javascript")


@gzip_page
def css_file(request, path):
    return render_asset('css/%s.css.html' % path, request,
                        content_type="text/css")
