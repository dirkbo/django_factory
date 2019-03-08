from django.conf import settings

import logging
logger = logging.getLogger(__name__)


def google_ids(request):
    track_users = getattr(settings, 'GOOGLE_TRACK_USERS', True)
    track_staff = getattr(settings, 'GOOGLE_TRACK_STAFF', False)

    no_tracking = {'GANALYTICS_UA': False,
                   'GADSENSE_UA': False,
                   'GOOGLE_ADS_AW': False
                   }

    if request.user.is_staff and track_staff is False:
        return no_tracking

    if request.user.is_authenticated and track_users is False:
        return no_tracking

    return {'GANALYTICS_UA': getattr(settings, 'GOOGLE_ANALYTICS_UA', False),
            'GADSENSE_UA': getattr(settings, 'GOOGLE_ADSENSE_CLIENT', False),
            'GOOGLE_ADS_AW': getattr(settings, 'GOOGLE_ADS_AW', False)
            }

