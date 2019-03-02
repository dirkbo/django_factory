from django.conf import settings

import logging
logger = logging.getLogger(__name__)


def google_ids(request):
    if request.user.is_staff:
        return {'GANALYTICS_UA': False,
                'GADSENSE_UA': False,
                'GOOGLE_ADS_AW': False
                }

    return {'GANALYTICS_UA': getattr(settings, 'GOOGLE_ANALYTICS_UA', False),
            'GADSENSE_UA': getattr(settings, 'GOOGLE_ADSENSE_CLIENT', False),
            'GOOGLE_ADS_AW': getattr(settings, 'GOOGLE_ADS_AW', False)
            }

