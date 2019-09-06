from rest_framework.views import APIView
from hyapp.models import Device
from hyapp.serializer import DeviceSerializer, DeviceList
from hyapp.utils import util_response, get_device_online_state, log_wrapper
from hyapp.permissions import DevicePermission
from hyapp.constants import LOG_MODULE
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.utils import IntegrityError
from rest_framework import status
from hyapp.e import ecode, cache

from django_redis import get_redis_connection

import logging
import json
import re


class DeviceAPI(APIView):
    permission_classes = [DevicePermission]

    def device_state(self, device, status):
        state, _ = get_device_online_state(device.id)
        return state == status

    def device_name(self, device, name):
        if re.match('.*' + name + '.*', device.name):
            return True
        else:
            return False

    def get(self, request):
        row = int(request.query_params.get('row', 10))
        page = int(request.query_params.get('page', 1))

        customer_id = request.query_params.get('customer_id')
        site_id = request.query_params.get('site_id')
        status = request.query_params.get('status')
        device_name = request.query_params.get('device_id')
        if customer_id and site_id:
            devices = Device.objects.filter(customer=customer_id, site=site_id)
        elif customer_id:
            devices = Device.objects.filter(customer=customer_id)
        elif site_id:
            devices = Device.objects.filter(site=site_id)
        else:
            devices = Device.objects.all()
        if status:
            devices = list(filter(lambda d: self.device_state(d, status), list(devices)))
        if device_name:
            devices = list(filter(lambda d: self.device_name(d, device_name), list(devices)))

        paginator = Paginator(devices, row)
        try:
            devices = paginator.page(page)
        except PageNotAnInteger:
            devices = paginator.page(1)
        except EmptyPage:
            devices = paginator.page(paginator.num_pages)

        devices = [DeviceSerializer(x).data for x in devices]

        return util_response(data={"list": devices, 'total': paginator.count})

    @log_wrapper(LOG_MODULE['2'], '新增设备')
    def post(self, request):
        device_id = request.data.get("id")
        pwd = request.data.get('pwd')
        name = request.data.get('name')
        if not device_id or not pwd or not name:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)
        obj = Device(id=device_id, pwd=pwd, name=name, customer_id=request.data.get('customer_id'),
                     site_id=request.data.get('site_id'))
        try:
            obj.save(force_insert=True)
        except IntegrityError as e:
            logging.error(e)
            return util_response(code=ecode.DeviceIDExist)

        return util_response()

    @log_wrapper(LOG_MODULE['2'], '修改设备')
    def put(self, request, id):
        Device.objects.filter(id=id).update(pwd=request.data.get('pwd'),
                                            name=request.data.get('name'), customer_id=request.data.get('customer_id'),
                                            site_id=request.data.get('site_id'))
        return util_response()


class DeviceItems(APIView):
    permission_classes = [DevicePermission]

    def get(self, request, device_id):
        """
        !! 将设备的tags 数据存储到redis
        获取设备返回数量的类型列表
        :param request:
        :param device_id:
        :return:
        """
        if not device_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)
        conn = get_redis_connection('default')
        cache_key = cache.get_device_monitor_data_key(device_id)
        res = conn.get(cache_key)
        data = []
        if res:
            res = json.loads(res)
            for item in res['Data']:
                data.append(item['name'])
        return util_response(data)


class SiteDeviceList(APIView):
    permission_classes = [DevicePermission]

    def get(self, request, site_id):
        """
        :param request:
        :param site_id:
        :return:
        """
        if not site_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)
        devices = Device.objects.filter(site=site_id)
        devices = [DeviceList(x).data for x in devices]
        return util_response(data=devices)
