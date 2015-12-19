# -*- coding:utf-8 -*-
import logging
import csv
import json

# Django imports
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.gzip import gzip_page
from django.template import RequestContext
from django.core.cache import cache

from hashlib import sha224
from datetime import datetime

# Get an instance of a logger
logger = logging.getLogger('bluesoybean.custom')


def factory_render(request, template, context, verbose=False):
    output = context.get('output', 'html')
    if output == 'html':
        return render(request, template, context)
    if output == 'json':
        json_data = dict()
        if verbose:
            print context
        for key in context:
            value = context[key]
            if verbose:
                print "K: %s V: %s" % (key, value)
            try:
                json_data[key] = json.dumps(value)
            except TypeError:
                try:
                    if value.id:
                        nv = dict()
                        nv['class'] = value.__class__.__name__
                        nv['id'] = value.id
                except AttributeError:
                    try:
                        st = str(value)
                        json_data[key] = st
                    except Exception as ex:
                        template = "An exception of type {0} occured. Arguments:\n{1!r}"
                        message = template.format(type(ex).__name__, ex.args)
                        if verbose:
                            print message
            except Exception as ex:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                if verbose:
                    print message
        return JsonResponse(json_data)
    if output == "csv":
        fn = template.replace('.html', '')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % fn

        writer = csv.writer(response)
        for key in context:
            value = context[key]
            writer.writerow([key, value])

        return response


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

        now = datetime.utcnow()
        modified = now.strftime('%H:%M:%S-%a/%d/%b/%Y')
        resp['Last-Modified'] = modified

        if not settings.DEBUG:
            resp['Cache-Control'] = 'max-age'
            expires = now.replace(year=now.year+1)
            resp['Expires'] = expires.strftime('%H:%M:%S-%a/%d/%b/%Y')
            cache.set(key, resp, 600)
            logger.info("caching: %s" % template)
        else:
            resp['Cache-Control'] = 'no-cache'
    return resp


@gzip_page
def js_file(request, path):
    return render_asset('js/%s.js.html' % path, request,
                        content_type="text/javascript")


@gzip_page
def css_file(request, path):
    return render_asset('css/%s.css.html' % path, request,
                        content_type="text/css")
