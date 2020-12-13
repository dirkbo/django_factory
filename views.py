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
from django.views.generic import TemplateView

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
            context = dict()
            context['hide_log'] = not getattr(settings, 'DEBUG', False)
            logger.info("Hide js log: %s", context['hide_log'])
            resp = render_to_string(template_name=template, request=request, context=context)
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

        cache_time_seconds = 60 * 60
        if debug:
            cache_time_seconds = 60
        resp['Cache-Control'] = 'public, max-age={}'.format(cache_time_seconds)
        expires = now.astimezone(timezone.utc) + timedelta(seconds=cache_time_seconds)
        resp['Expires'] = expires.strftime('%H:%M:%S-%a/%d/%b/%Y')
        cache.set(key, resp, cache_time_seconds)
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
def manifest(request):
    # manifest.json 
    # include path in urls:
    # 
    # path('manifest.json', manifest, name='html5_manifest'),
    #    
    # Make sure path is on highest level, directly under / 
    import json
    language = getattr(request, 'LANGUAGE_CODE', "en").lower()

    context = dict()
    context["manifest_version"] = 2
    pwa_settings = getattr(settings, 'PWA_SETTINGS', {})

    pwa_settings_texts = pwa_settings.get('texts', {})
    pwa_settings_text = pwa_settings_texts.get(language, {})
    context["name"] = pwa_settings_text.get("long_name", "A Blog")
    context["short_name"] = pwa_settings_text.get("short_name", "Blog")
    context["description"] = pwa_settings_text.get("description", "Description")
    # Get language specific texts

    context["start_url"] = pwa_settings.get('start_url', '/')
    context["display"] = pwa_settings.get('display', '')
    context["orientation"] = pwa_settings.get('orientation', '')

    context["background_color"] = pwa_settings.get("background_color", "#512498")
    context["theme_color"] = pwa_settings.get("theme_color", "#512498")
    context["icons"] = pwa_settings.get("icons", [])
    context["permissions"] = pwa_settings.get("permissions", [])

    return HttpResponse(json.dumps(context), content_type="text/json")


@gzip_page
def pwa_serviceworker(request):
    # Service worker view 
    # include url 
    #     path('pwa-serviceworker.js', pwa_serviceworker, name='pwa_serviceworker'),
    # Make sure url is directly under /, can only access same level or deeper. 
    template = get_template('js/service_worker.js.html')
    html = template.render()
    return HttpResponse(html, content_type="application/x-javascript")
