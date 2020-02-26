from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework import status

from django.db import connections

from hy import settings
from hyapp.models import Device, AnalysisChart
from hyapp.utils import util_response, generate_chart_id, log_wrapper
from hyapp.constants import LOG_MODULE
from hyapp.e import cache
from hyapp.serializer import AnalisysChartSerializer
import json
from hyapp.permissions import DataAnalysisPermission


class RealTime(APIView):
    permission_classes = [DataAnalysisPermission]

    def get(self, request):
        site_id = request.query_params.get('site_id')
        if not site_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)

        cache_key = cache.get_realtime_device_items_key(site_id)
        conn = get_redis_connection('default')
        device_items = conn.get(cache_key)
        if not device_items:
            return util_response(data=[])

        device_items = json.loads(device_items)

        result = []

        for device in list(device_items.keys()):
            cache_key = cache.get_device_monitor_data_key(device)
            monitor_data = conn.get(cache_key)
            if not monitor_data:
                continue
            monitor_data = json.loads(monitor_data)
            for item in device_items.get(device, []):
                for mdata in monitor_data['Data']:
                    if item == mdata['name']:
                        mdata['device_id'] = device
                        result.append(mdata)
                        break
        return util_response(data=result)


class DeviceItems(APIView):
    permission_classes = [DataAnalysisPermission]

    def get(self, request):
        site_id = request.query_params.get('site_id')
        if not site_id:
            util_response(http_status=status.HTTP_400_BAD_REQUEST)
        cache_key = cache.get_realtime_device_items_key(site_id)
        conn = get_redis_connection('default')
        device_items = conn.get(cache_key)
        if not device_items:
            device_items = {}
        else:
            device_items = json.loads(device_items)

        items = []
        devices = Device.objects.filter(site_id=site_id)
        for device in devices:
            cache_key = cache.get_device_monitor_data_key(device.id)
            monitor_data = conn.get(cache_key)
            if not monitor_data:
                continue
            monitor_data = json.loads(monitor_data)

            for mdata in monitor_data['Data']:
                mdata['device_name'] = device.name
                mdata['device_id'] = device.id
                mdata['check'] = '1' if device_items.get(device.id, '') and mdata['name'] in device_items.get(
                    device.id) else '0'
                items.append(mdata)
        return util_response(data=items)

    def put(self, request):
        """
        将用户选择的数据以 {"设备id": ['设备数据1'，'设备数据2']} 存入缓存当中
        :param request:
        :return:
        """
        site_id = request.query_params.get('site_id')
        data = request.data.get('data', [])
        if not site_id:
            util_response(http_status=status.HTTP_400_BAD_REQUEST)
        save_cache = dict()
        for x in data:
            if save_cache.get(x['device_id']):
                save_cache.get(x['device_id']).append(x['name'])
            else:
                save_cache[x['device_id']] = [x['name']]

        cache_key = cache.get_realtime_device_items_key(site_id)
        conn = get_redis_connection('default')
        conn.set(cache_key, json.dumps(save_cache))
        return util_response()


class DeviceItemDetail(APIView):
    permission_classes = [DataAnalysisPermission]

    def get(self, request, item_id):
        device_id = request.query_params.get('device_id')
        start = request.query_params.get("start_time")
        end = request.query_params.get("end_time")
        if not start or not end or not device_id or not item_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)

        page = int(request.query_params.get("page", 1))
        row = int(request.query_params.get("row", 10))

        db_conn = connections['default']
        cursor = db_conn.cursor()

        order_state_sql = "select name, value, time from hy_monitor_data where device_id = %s and time > %s and" \
                          " time < %s and name = %s order by time desc offset %s limit %s;"

        count_sql = "select count(1) from hy_monitor_data where device_id = %s and time > %s and" \
                    " time < %s and name = %s ;"

        try:
            device = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            return util_response(http_status=status.HTTP_204_NO_CONTENT)

        cursor.execute(count_sql, (device_id, start, end, item_id))
        count_res = cursor.fetchone()
        cursor.execute(order_state_sql, (device_id, start, end, item_id, (page - 1) * row, row))
        res = cursor.fetchall()
        data_list = []
        for x in res:
            data_list.append({
                "name": x[0],
                "device_name": device.name,
                "value": x[1],
                "time": x[2].strftime("%Y-%m-%d %H:%M:%S")
            })
        data = {
            "list": data_list,
            "total": count_res[0]
        }
        return util_response(data)


class DeviceItemDetailExcel(APIView):
    permission_classes = [DataAnalysisPermission]

    def get(self, request, item_id):
        device_id = request.query_params.get('device_id')
        start = request.query_params.get("start_time")
        end = request.query_params.get("end_time")
        site_name = request.query_params.get("site_name", '')
        if not start or not end or not device_id or not item_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)

        db_conn = connections['default']
        cursor = db_conn.cursor()

        order_state_sql = "select name, value, time from hy_monitor_data where device_id = %s and" \
                          " name = %s  and time > %s and time < %s  order by time desc"

        device = Device.objects.get(pk=device_id)

        cursor.execute(order_state_sql, (device_id, item_id, start, end))
        res = cursor.fetchall()
        data_list = []
        title = ['时间', '数据名称', '数据值', '所属设备', '站点名称']
        for x in res:
            data_list.append([x[2].strftime("%Y-%m-%d %H:%M:%S"), x[0], x[1], device.name, site_name])
        data = {
            "title": title,
            "list": data_list,
        }
        return util_response(data)


class ChartAPI(APIView):
    permission_classes = [DataAnalysisPermission]

    @log_wrapper(LOG_MODULE['5'], '新增数据看板')
    def get(self, request):
        site_id = request.query_params.get("site_id")
        if not site_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)

        charts = AnalysisChart.objects.filter(site=site_id)
        data = [AnalisysChartSerializer(x).data for x in charts]
        return util_response(data=data)

    def post(self, request):
        site_id = request.query_params.get("site_id")
        customer_id = request.query_params.get("customer_id")
        forecast = request.query_params.get("type") == '1'
        if not site_id or not customer_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)
        name = request.data.get('name', '')
        chart_type = request.data.get('type', '1')
        time_type = request.data.get('time_type', '')
        items = request.data.get('items', {})
        chart_id = generate_chart_id()
        obj = AnalysisChart(id=chart_id, name=name, chart_type=chart_type, time_type=time_type,
                            customer_id=customer_id,
                            site_id=site_id, items=items, forecast=forecast)
        obj.save()

        cache_key = cache.get_analysis_chart_items_key(chart_id)
        conn = get_redis_connection('default')
        conn.set(cache_key,
                 json.dumps({"items": items, "chart_type": chart_type, "time_type": time_type,
                             "forecast": '1' if forecast else '0'}))

        return util_response()

    @log_wrapper(LOG_MODULE['5'], '编辑数据看板')
    def put(self, request, chart_id):
        name = request.data.get('name', '')
        chart_type = request.data.get('type', '1')
        time_type = request.data.get('time_type', '')
        items = request.data.get('items', {})
        if not chart_id or not name or not chart_type or not time_type or not items:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)

        chart = AnalysisChart.objects.get(id=chart_id)
        chart.name = name
        chart.chart_type = chart_type
        chart.time_type = time_type
        chart.items = items
        chart.save()

        cache_key = cache.get_analysis_chart_items_key(chart_id)
        conn = get_redis_connection('default')
        conn.set(cache_key, json.dumps(
            {"items": items, "chart_type": chart_type, "time_type": time_type,
             "forecast": '1' if chart.forecast else '0'}))

        return util_response()


class ChartDeviceItems(APIView):
    permission_classes = [DataAnalysisPermission]

    def get(self, request):
        site_id = request.query_params.get("site_id")
        devices = Device.objects.filter(site=site_id)

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


class ChartData(APIView):
    permission_classes = [DataAnalysisPermission]

    def time_type(self, time_type):
        t = {
            "0": "minute",
            "1": "hour",
            "2": "day"
        }
        return t[time_type]

    def histogram_chart(self, items, time_type, forecast):

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

    def pie_chart(self, items, time_type):
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

    def line_chart(self, items, time_type, forecast):
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

        cache_key = cache.get_analysis_chart_items_key(chart_id)
        conn = get_redis_connection('default')
        cache_res = conn.get(cache_key)
        if not cache_res:
            return util_response(http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # {"items": items, "chart_type": chart_type, "time_type": time_type, "forecast": forecast}
        cache_res = json.loads(cache_res)
        data = dict()
        if cache_res['chart_type'] == '0':
            data = self.histogram_chart(cache_res['items'], cache_res['time_type'], cache_res['forecast'])
        elif cache_res['chart_type'] == '1':
            data = self.line_chart(cache_res['items'], cache_res['time_type'], cache_res['forecast'])
        elif cache_res['chart_type'] == '2':
            data = self.bar_chart(cache_res['items'], cache_res['time_type'])
        elif cache_res['chart_type'] == '3':
            data = self.pie_chart(cache_res['items'], cache_res['time_type'])
        return util_response(data=data)
