import os
import logging
from rest_framework.views import APIView

from hy.settings import BASE_DIR, DEFAULT_SYS_SETTINGS
from hyapp.e import ecode
from hyapp.utils import log_wrapper, util_response
from hyapp.constants import LOG_MODULE
from hyapp.permissions import SysSettingsPermission
from hy.settings import IMAGE_PATH
from django_redis import get_redis_connection


# ----------------------------系统设置管理----------------------------


class SystemInfo(APIView):
    permission_classes = [SysSettingsPermission]

    def get(self, request):
        try:
            conn = get_redis_connection('default')
            customer_id = request.redis_cache['customer_id']

            # todo 固定测试环境
            data = dict()
            data['icon'] = conn.hget(customer_id, 'icon') or DEFAULT_SYS_SETTINGS['icon']
            data['bg_img'] = conn.hget(customer_id, 'bg') or DEFAULT_SYS_SETTINGS['bg']
            data['name'] = conn.hget(customer_id, 'name') or DEFAULT_SYS_SETTINGS['name']
            data['language'] = conn.hget(customer_id, 'language') or DEFAULT_SYS_SETTINGS['language']
            data['login_failure_times'] = conn.hget(customer_id, 'fail_times') or DEFAULT_SYS_SETTINGS['fail_times']
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': data})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class SystemInfoLogo(APIView):
    permission_classes = [SysSettingsPermission]

    @log_wrapper(LOG_MODULE['8'], '修改logo')
    def put(self, request):
        try:
            conn = get_redis_connection('default')
            customer_id = request.redis_cache['customer_id']

            new_icon = request.FILES['icon']
            extension = os.path.splitext(new_icon.name)[1]
            new_icon_name = '{}_icon{}'.format(customer_id, extension)
            # print('new_icon_name', new_icon_name)
            old_icon = conn.hget(customer_id, 'icon') or new_icon_name
            old_icon_name = old_icon.split('/')[-1]
            # print('old_icon_name', old_icon_name)
            if old_icon_name == new_icon_name:
                delete = False
            else:
                delete = True
            new_icon_path = os.path.join(os.path.dirname(BASE_DIR), "static/img/{}".format(new_icon_name))
            with open(new_icon_path, 'wb') as file:
                file.write(bytes(new_icon.read()))
                conn.hset(customer_id, 'icon', IMAGE_PATH + "img/{}".format(new_icon_name))
            # 当新图片正常保存后再删除旧图片
            if delete:
                old_icon_path = os.path.join(os.path.dirname(BASE_DIR), 'static/img/{}'.format(old_icon_name))
                os.remove(old_icon_path)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class BackgroundImg(APIView):
    permission_classes = [SysSettingsPermission]

    @log_wrapper(LOG_MODULE['8'], '修改background pic')
    def put(self, request):
        try:
            conn = get_redis_connection('default')
            customer_id = request.redis_cache['customer_id']

            new_bg = request.FILES['img']
            extension = os.path.splitext(new_bg.name)[1]
            new_bg_name = '{}_bg{}'.format(customer_id, extension)
            # print('new_bg_name', new_bg_name)
            old_bg = conn.hget(customer_id, 'bg') or new_bg_name
            old_bg_name = old_bg.split('/')[-1]
            # print('old_bg_name', old_bg_name)
            if old_bg_name == new_bg_name:
                delete = False
            else:
                delete = True
            new_bg_path = os.path.join(os.path.dirname(BASE_DIR), "static/img/{}".format(new_bg_name))
            with open(new_bg_path, 'wb') as file:
                file.write(bytes(new_bg.read()))
                conn.hset(customer_id, 'bg', IMAGE_PATH + "img/{}".format(new_bg_name))
            # 当新图片正常保存后再删除旧图片
            if delete:
                old_bg_path = os.path.join(os.path.dirname(BASE_DIR), 'static/img/{}'.format(old_bg_name))
                os.remove(old_bg_path)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class SystemInfoName(APIView):
    permission_classes = [SysSettingsPermission]

    @log_wrapper(LOG_MODULE['8'], '修改名称')
    def put(self, request):
        try:
            customer_id = request.redis_cache['customer_id']
            conn = get_redis_connection('default')
            name = request.data.get('name')
            conn.hset(customer_id, 'name', name)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class SystemInfoFailTimes(APIView):
    permission_classes = [SysSettingsPermission]

    @log_wrapper(LOG_MODULE['8'], '修改允许验证失败次数')
    def put(self, request):
        try:
            customer_id = request.redis_cache['customer_id']
            conn = get_redis_connection('default')
            times = int(request.data.get('times'))
            conn.hset(customer_id, 'fail_times', str(times))
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

