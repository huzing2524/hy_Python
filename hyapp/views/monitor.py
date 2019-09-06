import json
import os

from rest_framework.views import APIView

from hy import settings
from hyapp.serializer import ChartSerializer
from hyapp.utils import util_response, generate_chart_id, log_wrapper, get_device_online_state
from hyapp.constants import LOG_MODULE
from hyapp.permissions import MonitorPermission
from datetime import datetime
from rest_framework import status
from hyapp.models import Chart, Device
from hyapp.e import cache
from django_redis import get_redis_connection
from django.db import connections

import time


class MainMap(APIView):
    permission_classes = [MonitorPermission]

    # todo 从盒子上传数据中获取相关数据
    def get(self, request):
        customer_id = request.query_params.get("customer_id")
        site_id = request.query_params.get("site_id")
        state = request.query_params.get("state")

        db_conn = connections['default']
        cursor = db_conn.cursor()
        total = 0
        total_running = 0
        devices = []
        sql = ''
        if not customer_id:
            sql = '''    
            select
                t1.devices,
                t2.site_name,
                t2.province || t2.city || t2.district || t2.address as address,
                t3.name_cn as customer_name,
                t2.lng,
                t2.lat
            from
                (
                select
                    array_agg(id) as devices,
                    ( array_agg(customer_id))[1] as customer_id,
                    site_id
                from
                    hy_device
                group by
                    site_id ) t1
            left join hy_sites t2 on
                t1.site_id = t2.id
            left join hy_customers t3 on
                t1.customer_id = t3.customer_id;
            '''
        elif not site_id:
            sql = '''    
                select
                    t1.devices,
                    t2.site_name,
                    t2.province || t2.city || t2.district || t2.address as address,
                    t3.name_cn as customer_name,
                    t2.lng,
                    t2.lat
                from
                    (
                    select
                        array_agg(id) as devices,
                        ( array_agg(customer_id))[1] as customer_id,
                        site_id
                    from
                        hy_device
                    where customer_id = '{}'
                    group by
                        site_id ) t1
                left join hy_sites t2 on
                    t1.site_id = t2.id
                left join hy_customers t3 on
                    t1.customer_id = t3.customer_id;
                '''.format(customer_id)
        else:
            sql = '''    
                select
                    t1.devices,
                    t2.site_name,
                    t2.province || t2.city || t2.district || t2.address as address,
                    t3.name_cn as customer_name,
                    t2.lng,
                    t2.lat
                from
                    (
                    select
                        array_agg(id) as devices,
                        ( array_agg(customer_id))[1] as customer_id,
                        site_id
                    from
                        hy_device
                    where site_id = '{}'
                    group by
                        site_id ) t1
                left join hy_sites t2 on
                    t1.site_id = t2.id
                left join hy_customers t3 on
                    t1.customer_id = t3.customer_id;
                '''.format(site_id)

        cursor.execute(sql)
        res = cursor.fetchall()

        for x in res:
            running = 0
            d = 0
            for device_id in x[0]:
                online, _ = get_device_online_state(device_id)
                if online == "1":
                    running += 1
                if state and state == online:
                    d += 1
                elif not state:
                    d += 1
            if d > 0:
                total_running += running
                total += len(x[0])
                devices.append({
                    'customer_name': x[3],
                    'site_name': x[1],
                    'address': x[2],
                    'devices': str(d),
                    'running': str(running),
                    'wanning': 0,
                    'warn_msgs': 0,
                    'lng': x[4],
                    'lat': x[5],
                })
        data = {
            'total': total,
            'running': total_running,
            'warning': 0,
            'warn_msgs': 0,
            'devices': devices
        }
        return util_response(data=data)


class MainChat(APIView):
    permission_classes = [MonitorPermission]

    def get(self, request):
        site_id = request.query_params.get("site_id")
        if not site_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)

        charts = Chart.objects.filter(site=site_id)
        data = [ChartSerializer(x).data for x in charts]
        return util_response(data={"charts": data, "img": settings.STATIC_FILE_URL + "img/chart_gy"})


class MainTable(APIView):
    permission_classes = [MonitorPermission]

    def get(self, request):
        request.query_params("customer_id")
        request.query_params("site_id")
        data = [{
            "name": "i1",
            "value": "2"
        }]
        return util_response(data=data)


class ChartAPI(APIView):
    permission_classes = [MonitorPermission]

    @log_wrapper(LOG_MODULE['1'], '新增数据看板')
    def post(self, request):
        site_id = request.query_params.get("site_id")
        customer_id = request.query_params.get("customer_id")
        if not site_id or not customer_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)
        name = request.data.get('name', '')
        chart_type = request.data.get('type', '1')
        time_type = request.data.get('time_type', '')
        items = request.data.get('items', {})
        chart_id = generate_chart_id()
        obj = Chart(id=chart_id, name=name, chart_type=chart_type, time_type=time_type,
                    customer_id=customer_id,
                    site_id=site_id, items=items)
        obj.save()

        cache_key = cache.get_chart_items_key(chart_id)
        conn = get_redis_connection('default')
        conn.set(cache_key, json.dumps({"items": items, "chart_type": chart_type, "time_type": time_type}))

        return util_response()

    @log_wrapper(LOG_MODULE['1'], '编辑数据看板')
    def put(self, request, chart_id):
        name = request.data.get('name', '')
        chart_type = request.data.get('type', '1')
        time_type = request.data.get('time_type', '')
        items = request.data.get('items', {})
        if not chart_id or not name or not chart_type or not time_type or not items:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)

        chart = Chart.objects.get(id=chart_id)
        chart.name = name
        chart.chart_type = chart_type
        chart.time_type = time_type
        chart.items = items
        chart.save()

        cache_key = cache.get_chart_items_key(chart_id)
        conn = get_redis_connection('default')
        conn.set(cache_key, json.dumps({"items": items, "chart_type": chart_type, "time_type": time_type}))

        return util_response()

    @log_wrapper(LOG_MODULE['1'], '删除数据看板')
    def delete(self, request, chart_id):

        Chart.objects.get(id=chart_id).delete()
        cache_key = cache.get_chart_items_key(chart_id)
        conn = get_redis_connection('default')
        conn.delete(cache_key)
        return util_response()


class DeviceItems(APIView):
    permission_classes = [MonitorPermission]

    def get(self, request):
        site_id = request.query_params.get("site_id")
        devices = Device.objects.filter(site_id=site_id)

        conn = get_redis_connection('default')
        data = []
        for device in devices:
            cache_key = cache.get_device_monitor_data_key(device.id)
            monitor_data = conn.get(cache_key)
            if not monitor_data:
                continue
            monitor_data = json.loads(monitor_data)
            for item in monitor_data['Data']:
                item['device_name'] = device.name
                item['device_id'] = device.id
                data.append(item)
        return util_response(data=data)


class ChartDataAPI(APIView):
    permission_classes = [MonitorPermission]

    def time_type(self, time_type):
        t = {
            "0": "minute",
            "1": "hour",
            "2": "day"
        }
        return t[time_type]

    def histogram_and_pie_chart(self, items, time_type):
        device_id, device_item_id = items[0]['device_id'], items[0]['name']
        sql = ''' SELECT date_trunc(%s, "time") AS time , avg(value :: float) as avg FROM   
        hy_monitor_data where name = %s and device_id = %s GROUP  BY 1  order by 1 desc offset 0 limit 5;'''
        db_conn = connections['default']
        cursor = db_conn.cursor()
        cursor.execute(sql, (self.time_type(time_type), device_item_id, device_id))
        res = cursor.fetchall()[::-1]
        data_x = []
        data_y = []
        for x in res:
            data_x.append(x[0].strftime("%Y-%m-%d %H:%M:%S"))
            data_y.append(x[1])
        return {'data_x': data_x, 'data_y': data_y}

    def bar_chart(self, items, time_type):
        sql = ''' SELECT date_trunc(%s, "time") AS time , avg(value :: float) as avg FROM   
                hy_monitor_data where name = %s and device_id = %s GROUP  BY 1  order by 1 desc offset 0 limit 1;'''
        db_conn = connections['default']
        cursor = db_conn.cursor()
        data_x = []
        data_y = []
        for item in items:
            cursor.execute(sql, (self.time_type(time_type), item['name'], item['device_id']))
            res = cursor.fetchone()
            device = Device.objects.get(id=item['device_id'])
            data_x.append(res[1])
            data_y.append(device.name + item['name'])
        return {'data_x': data_x, 'data_y': data_y}

    def line_chart(self, items, time_type):
        sql = ''' SELECT date_trunc(%s, "time") AS time , avg(value :: float) as avg FROM   
            hy_monitor_data where name = %s and device_id = %s GROUP  BY 1  order by 1 desc offset 0 limit 5;'''
        db_conn = connections['default']
        cursor = db_conn.cursor()
        data_x = []
        data_y = []
        for item in items:
            datax = []
            datay = []
            cursor.execute(sql, (self.time_type(time_type), item['name'], item['device_id']))
            res = cursor.fetchall()
            for x in res:
                datax.append(x[0].strftime("%Y-%m-%d %H:%M:%S"))
                datay.append(x[1])
            data_x = datax
            data_y.append(datay)

        return {'data_x': data_x, 'data_y': data_y, 'items': items}

    def get(self, request, chart_id):
        """
        chart_type 0: 柱状图，1：折线图 2：条形图 3：饼图
        time_type 0: 分 1: 时 2: 天
        :param request:
        :param chart_id:
        :return:
        """

        cache_key = cache.get_chart_items_key(chart_id)
        conn = get_redis_connection('default')
        cache_res = conn.get(cache_key)
        if not cache_res:
            return util_response(http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # {"items": items, "chart_type":chart_type, "time_type":time_type}
        cache_res = json.loads(cache_res)
        data = dict()
        if cache_res['chart_type'] == '0':
            data = self.histogram_and_pie_chart(cache_res['items'], cache_res['time_type'])
        elif cache_res['chart_type'] == '1':
            data = self.line_chart(cache_res['items'], cache_res['time_type'])
        elif cache_res['chart_type'] == '2':
            data = self.bar_chart(cache_res['items'], cache_res['time_type'])
        elif cache_res['chart_type'] == '3':
            data = self.histogram_and_pie_chart(cache_res['items'], cache_res['time_type'])
        return util_response(data)


class ChartImg(APIView):
    permission_classes = [MonitorPermission]

    @log_wrapper(LOG_MODULE['1'], '上传工艺流程图')
    def post(self, request):
        img = request.FILES['img']
        if not img:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)
        path = os.path.join(os.path.dirname(settings.BASE_DIR), "static/img/chart_gy")
        with open(path, 'wb') as file:
            file.write(bytes(img.read()))
        return util_response()


#  获取当前分钟的 前四分钟, 和当前分钟组成5个
#  hour date同理
def minute_range():
    time_range = []
    ts = int(time.time())
    for x in range(5):
        time_range.append(datetime.fromtimestamp(ts - x * 60).strftime('%H:%M'))
    return time_range[::-1]


def hour_range():
    time_range = []
    ts = int(time.time())
    for x in range(5):
        time_range.append(datetime.fromtimestamp(ts - x * 60 * 60).strftime('%H:00'))
    return time_range[::-1]


def date_range():
    time_range = []
    ts = int(time.time())
    for x in range(5):
        time_range.append(datetime.fromtimestamp(ts - x * 60 * 60 * 24).strftime('%m.%d'))
    return time_range[::-1]
