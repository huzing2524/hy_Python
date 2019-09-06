from hyapp.e import cache
from hyapp.utils import util_response, log_wrapper
from hyapp.constants import LOG_MODULE
from rest_framework.views import APIView
from django_redis import get_redis_connection

import os
from hy import settings


class Manual(APIView):
    def get(self, request):
        print(request.META['HTTP_HOST'].split(':')[0])
        cache_key = cache.get_manual_key()
        conn = get_redis_connection('default')
        url = conn.get(cache_key) or ''
        return util_response(url)

    @log_wrapper(LOG_MODULE['9'], '更新使用手册')
    def post(self, request):
        pdf_content = request.FILES['content']
        path = os.path.join(os.path.dirname(settings.BASE_DIR), "static/pdf/manual.pdf")
        with open(path, 'wb') as file:
            file.write(bytes(pdf_content.read()))

        cache_key = cache.get_manual_key()
        conn = get_redis_connection('default')
        conn.set(cache_key, settings.STATIC_FILE_URL + "pdf/manual.pdf")

        return util_response()
