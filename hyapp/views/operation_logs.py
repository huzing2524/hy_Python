import logging
import datetime
from rest_framework.views import APIView

from hyapp.e import ecode
from hyapp.utils import util_response, log_wrapper
from hyapp.models import HyLogs
from hyapp.serializer import OperationLogsSerializer
from hyapp.constants import LOG_MODULE
# from hyapp.permissions import LogsPermission

# ----------------------------操作日志管理----------------------------


class OperationLogs(APIView):
    permission_classes = []

    def get(self, request):
        operator = request.query_params.get('operator')
        module = request.query_params.get('module')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        page = request.query_params.get('page', '1')
        row = request.query_params.get('row', '10')

        limit = int(row)
        offset = int(row) * (int(page) - 1)

        if start_time:
            start_time = datetime.datetime.fromtimestamp(int(start_time))
        if end_time:
            end_time = datetime.datetime.fromtimestamp(int(end_time))

        condition = dict()
        if operator:
            condition['operator__exact'] = operator
        if start_time:
            condition['time__gte'] = start_time
        if end_time:
            condition['time__lte'] = end_time
        if module:
            condition['module__exact'] = module
        try:
            query_set = HyLogs.objects.filter(**condition)
            total = len(query_set)
            data = OperationLogsSerializer(query_set, many=True).data
            data = data[offset:offset+limit]
            data = {'list': data, 'total': total}
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': {'list': data, 'total': total}})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class OperationLogsExcel(APIView):
    permission_classes = []

    @log_wrapper(LOG_MODULE['10'], '导出操作日志')
    def get(self, request):
        operator = request.query_params.get('operator')
        module = request.query_params.get('module')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')

        if start_time:
            start_time = datetime.datetime.fromtimestamp(int(start_time))
        if end_time:
            end_time = datetime.datetime.fromtimestamp(int(end_time))

        condition = dict()
        if operator:
            condition['operator__exact'] = operator
        if start_time:
            condition['time__gte'] = start_time
        if end_time:
            condition['time__lte'] = end_time
        if module:
            condition['module__exact'] = module
        try:
            query_set = HyLogs.objects.filter(**condition)
            result = list()
            # title = data[0].keys()
            title = ['序号', '操作人', '内容', '结果', '模块', '访问ip', '时间']
            result.append(title)
            # for i in query_set:
            #     result.append(OperationLogsSerializer(i).data)
            left = OperationLogsSerializer(query_set, many=True).data
            for i in left:
                result.append(i.values())
            return util_response(result)
            # return Response({'code': 200, 'msg': 'ok', 'data': result})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)