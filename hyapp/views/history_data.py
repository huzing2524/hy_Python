from rest_framework.views import APIView
from hyapp.utils import util_response, log_wrapper
from hyapp.constants import LOG_MODULE
from rest_framework import status

from django.db import connections


class History(APIView):
    def get(self, request):
        """
        :param request:
        :return:
        """
        device_id = request.query_params.get("device_id")
        item_id = request.query_params.get("device_item_id")
        start = request.query_params.get("start_time")
        end = request.query_params.get("end_time")
        if not start or not end or not device_id or not item_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)
        page = int(request.query_params.get("page", 1))
        row = int(request.query_params.get("row", 10))

        db_conn = connections['default']
        cursor = db_conn.cursor()

        # start = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S").date()
        # end = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S").date()

        order_state_sql = "select name, value, time from hy_monitor_data where device_id = %s and time > %s and" \
                          " time < %s and name = %s order by time desc offset %s limit %s;"

        count_sql = "select count(1) from hy_monitor_data where device_id = %s and time > %s and" \
                    " time < %s and name = %s ;"

        cursor.execute(count_sql, (device_id, start, end, item_id))
        count_res = cursor.fetchone()
        cursor.execute(order_state_sql, (device_id, start, end, item_id, (page - 1) * row, row))
        res = cursor.fetchall()
        data_list = []
        for x in res:
            data_list.append({
                "device_item": x[0],
                "value": x[1],
                "time": x[2].strftime("%Y-%m-%d %H:%M:%S")
            })
        data = {
            "list": data_list,
            "total": count_res[0]
        }
        return util_response(data)


class HistoryExcel(APIView):
    @log_wrapper(LOG_MODULE['6'], '导出历史数据')
    def get(self, request):
        """
        :param request:
        :return:
        """
        device_id = request.query_params.get("device_id")
        item_id = request.query_params.get("device_item_id")
        start = request.query_params.get("start_time")
        end = request.query_params.get("end_time")
        if not start or not end or not device_id or not item_id:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST)

        db_conn = connections['default']
        cursor = db_conn.cursor()

        order_state_sql = "select name, value, time from hy_monitor_data where device_id = %s and" \
                          " name = %s and time > %s and time < %s order by time desc"

        cursor.execute(order_state_sql, (device_id, item_id, start, end))
        res = cursor.fetchall()
        data_list = []
        title = ['时间', '数据名称', '数据值']
        for x in res:
            data_list.append([x[2].strftime("%Y-%m-%d %H:%M:%S"), x[0], x[1]])
        data = {
            "title": title,
            "list": data_list,
        }
        return util_response(data)
