# -*- coding:utf-8 -*-
import logging
import csv
import json

# Django imports
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from django.views.decorators.gzip import gzip_page
from django.core.cache import cache
from django.template.loader import get_template, render_to_string

from hashlib import sha224
from datetime import datetime, timedelta

# Get an instance of a logger
logger = logging.getLogger(__name__)


def factory_render(request, template, context, verbose=False):
    output = context.get('output', 'html')
    if output == 'html':
        return render(request, template, context)
    if output == 'json':
        json_data = dict()
        logger.info(context)
        for key in context:
            value = context[key]
            logger.debug("K: %s V: %s" % (key, value))
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
                        logger.info(message)
            except Exception as ex:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                logger.warn(message)
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
                 force_shrink=True):
    language = getattr(request, 'LANGUAGE_CODE', "")
    key = "asset-%s-%s" % (template, language)
    resp = cache.get(key, False)
    debug = settings.DEBUG

    if resp is False:
        try:
            resp = render_to_string(template_name=template, request=request)
        except Exception as e:
            if debug:
                raise e
            else:
                logger.warning(e)
            return HttpResponseBadRequest("bad Request: %s" % template)

        if not debug or force_shrink is True:
            try:
                if content_type.endswith("javascript"):
                    logger.info("js minified")
                    from jsmin import jsmin
                    resp = jsmin(resp)
                else:
                    logger.info("content Type: %s", content_type)
            except Exception as e:
                logger.warning("error shrinking js: %s", e)

            try:
                if content_type.endswith("css"):
                    from cssmin import cssmin
                    resp = cssmin(resp)
            except Exception as e:
                logger.warning("error shrinking css: %s", e)

        resp = HttpResponse(resp)
        etag = sha224(resp.content).hexdigest()
        resp['Content-Type'] = content_type
        resp['etag'] = etag

        now = timezone.now()
        modified = now.astimezone(timezone.utc).strftime('%H:%M:%S-%a/%d/%b/%Y')
        resp['Last-Modified'] = modified

        if not debug:
            resp['Cache-Control'] = 'public, max-age=6000'
            expires = now.astimezone(timezone.utc) + timedelta(days=365)
            resp['Expires'] = expires.strftime('%H:%M:%S-%a/%d/%b/%Y')
            cache.set(key, resp, 600)
            logger.info("caching: %s" % template)
        else:
            resp['Cache-Control'] = 'public, max-age=60'
            expires = now.astimezone(timezone.utc) + timedelta(minutes=3)
            resp['Expires'] = expires.strftime('%H:%M:%S-%a/%d/%b/%Y')
            cache.set(key, resp, 60)
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


@gzip_page
def pwa_serviceworker(request):
    template = get_template('js/service_worker.js.html')
    html = template.render()
    return HttpResponse(html, content_type="application/x-javascript")
