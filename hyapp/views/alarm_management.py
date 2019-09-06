import random
import logging
import datetime
from django.db import connection
from rest_framework.response import Response
from rest_framework.views import APIView

from hyapp.models import HyAlarmEvent, HyConfirmAlarm, HyCustomers, HyNotifier, HyAlarmLevel
from hyapp.serializer import NotifierSerializer
from hyapp.constants import LOG_MODULE
from hyapp.utils import log_wrapper, util_response
from hyapp.permissions import AlarmPermission
from hyapp.e import ecode


# ----------------------------报警管理----------------------------


class RealTimeAlarm(APIView):
    permission_classes = [AlarmPermission]

    def get(self, request):
        cursor = connection.cursor()

        customer_id = request.query_params.get('customer_id')
        # device_id = request.query_params.get('device_id')
        site_id = request.query_params.get('site_id')
        device_name = request.query_params.get('device_name')
        status_ = request.query_params.get('status')
        alarm_id = request.query_params.get('id')
        page = request.query_params.get('page', '1')
        row = request.query_params.get('row', '10')

        limit = int(row)
        offset = int(row) * (int(page) - 1)

        if customer_id:
            c1 = "t3.customer_id = '{}' and ".format(customer_id)
        else:
            c1 = ''
        if device_name:
            c2 = "t2.name like '%{}%' and ".format(device_name)
        else:
            c2 = ''
        if status_:
            c3 = "t1.status = '{}' and ".format(status_)
        else:
            c3 = ''
        if site_id:
            c4 = "t2.site_id = '{}' and ".format(site_id)
        else:
            c4 = ''
        if alarm_id:
            c5 = "t1.id = '{}'".format(alarm_id)
        else:
            c5 = ''
        condition = (c1 + c2 + c3 + c4 + c5).rstrip('and ')
        if condition:
            condition = 'and ' + condition
        # todo 为什么字段变成了event_id_id?
        sql_1 = """
            select 
                * 
            from
                (
                select 
                    t1.id,
                    t2.name,
                    t1.name,
                    t1.content,
                    t1.value,
                    t1.status,
                    t4.site_name,
                    to_char(t1.time,'yyyy-mm-dd hh24:mi:ss'),
                    coalesce(t3.name_cn, ''),
                    row_number() over (order by t1.time desc) as rn
                from 
                    hy_alarm_event t1                
                left join 
                    hy_device t2 
                    on t2.id = t1.device_id_id
                left join 
                    hy_customers t3 
                    on t3.customer_id = t2.customer_id
                left join 
                    hy_sites t4 
                    on t4.id = t2.site_id
                where 
                    t1.alarm_type = 'AlarmEvent' 
                    and t1.time > now() - interval'24h' 
                    {}
                )t where rn > {} limit {};"""
        sql_2 = """
            select 
                count(1)
            from
                (
                select 
                    t1.id,
                    t2.name,
                    t1.name,
                    t1.content,
                    t1.value,
                    t1.status,
                    to_char(t1.time,'yyyy-mm-dd hh24:mi:ss'),
                    coalesce(t3.name_cn, ''),
                    row_number() over (order by t1.time desc) as rn
                from 
                    hy_alarm_event t1                
                left join 
                    hy_device t2 
                    on t2.id = t1.device_id_id
                left join 
                    hy_customers t3 
                    on t3.customer_id = t2.customer_id
                left join 
                    hy_sites t4 
                    on t4.id = t2.site_id
                where 
                    t1.alarm_type = 'AlarmEvent' 
                    and t1.time > now() - interval'24h' 
                    {}
                )t;"""
        target = ['id', 'device_name', 'name', 'content', 'value', 'status', 'site_name', 'time', 'customer_name']
        try:
            # print(sql_1.format(condition, offset, limit))
            cursor.execute(sql_1.format(condition, offset, limit))
            data = cursor.fetchall()
            cursor.execute(sql_2.format(condition))
            total = cursor.fetchone()[0]
            result = [dict(zip(target, i)) for i in data]
            data = {'list': result, 'total': total}
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)
            # return Response({'code': 500, 'msg': '服务器异常！'})

    @log_wrapper(LOG_MODULE['3'], '确认报警')
    def post(self, request, event_id):
        try:
            check_set = HyConfirmAlarm.objects.filter(event_id=event_id)
            if len(check_set) != 0:
                return Response({'code': 500, 'msg': '此报警信息已确认！'})
            event = HyAlarmEvent.objects.get(id=event_id)

            data = dict(request.data.items())
            data['event_id'] = event
            data['confirm_time'] = datetime.datetime.fromtimestamp(data['confirm_time'])
            post_set = HyConfirmAlarm.objects.create(**data)
            post_set.save()
            # 更新报警信息的状态
            HyAlarmEvent.objects.filter(id=event_id).update(status='1')
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class AlarmDetail(APIView):
    permission_classes = [AlarmPermission]

    def get(self, request, event_id):
        cursor = connection.cursor()
        sql_1 = """
            select 
                t2.name,
                t1.device_id_id,
                t1.name,
                t1.id,  
                coalesce(t3.level, '0'),
                to_char(t1.time,'yyyy-mm-dd hh24:mi:ss')
            from 
                hy_alarm_event t1 
            left join 
                hy_device t2
                on t1.device_id_id = t2.id
            left join
                hy_alarm_level t3 
                on t3.device_id_id = t1.device_id_id
                and t3.name = t1.name
            where 
                t1.id = '{}';""".format(event_id)
        sql_2 = """
            select 
                confirm_person,
                plan_description,
                problem,
                to_char(confirm_time,'yyyy-mm-dd hh24:mi:ss')
            from
                hy_confirm_alarm
            where 
                event_id_id = '{}';""".format(event_id)
        target_1 = ['device_name', 'device_id', 'name', 'alarm_id', 'level', 'time']
        target_2 = ['confirm_person', 'plan_description', 'problem', 'confirm_time']
        try:
            cursor.execute(sql_1)
            tmp = cursor.fetchone() or list()
            basic_info = dict(zip(target_1, tmp))
            cursor.execute(sql_2)
            tmp = cursor.fetchone() or list()
            alarm_solution = dict(zip(target_2, tmp))
            data = {'basic_info': basic_info, 'alarm_solution': alarm_solution}
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': data})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class AlarmHistory(APIView):
    permission_classes = [AlarmPermission]

    def get(self, request):
        cursor = connection.cursor()

        id_ = request.query_params.get('id')
        device_id = request.query_params.get('device_id')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        customer_id = request.query_params.get('customer_id')
        site_id = request.query_params.get('site_id')
        status_ = request.query_params.get('status')
        page = request.query_params.get('page', '1')
        row = request.query_params.get('row', '10')

        limit = int(row)
        offset = int(row) * (int(page) - 1)

        if id_:
            c1 = "t1.id = '{}' and ".format(id_)
        else:
            c1 = ''
        if device_id:
            c2 = "t2.id = '{}' and ".format(device_id)
        else:
            c2 = ''
        if start_time and end_time:
            c3 = "t1.time > TO_TIMESTAMP({}) and t1.time < TO_TIMESTAMP({}) and ".format(start_time, end_time)
        elif start_time:
            c3 = "t1.time > TO_TIMESTAMP({}) and ".format(start_time)
        elif end_time:
            c3 = "t1.time < TO_TIMESTAMP({}) and ".format(end_time)
        else:
            c3 = ''
        if customer_id:
            c4 = "t3.customer_id = '{}' and ".format(customer_id)
        else:
            c4 = ''
        if status_ == '0':
            c5 = "t1.status = '0' and t1.alarm_type = 'AlarmEvent' and "
        elif status_ == '1':
            c5 = "t1.status = '1' and "
        elif status_ == '2':
            c5 = "t1.alarm_type = 'AlarmRecover' and "
        else:
            c5 = ''
        if site_id:
            c6 = "t2.site_id = '{}'".format(site_id)
        else:
            c6 = ''
        condition = (c1 + c2 + c3 + c4 + c5 + c6).rstrip('and ')
        if condition:
            condition = 'where ' + condition

        sql_0 = """
                select 
                    t1.id,
                    t2.name,
                    t1.name,
                    t1.content,
                    t1.value,
                    case t1.alarm_type when 'AlarmRecover' then '2' else t1.status end as status_,
                    to_char(t1.time,'yyyy-mm-dd hh24:mi:ss') as time,
                    coalesce(t3.name_cn, ''),
                    t4.problem,
                    t4.plan_description,
                    t4.confirm_person,
                    t5.site_name, 
                    to_char(t4.confirm_time,'yyyy-mm-dd hh24:mi:ss') as confirm_time,
                    row_number() over (order by t1.time desc) as rn
                from 
                    hy_alarm_event t1                
                left join 
                    hy_device t2 
                    on t2.id = t1.device_id_id
                left join 
                    hy_customers t3 
                    on t3.customer_id = t2.customer_id
                left join 
                    hy_confirm_alarm t4
                    on t4.event_id_id = t1.id
                left join
                    hy_sites t5
                    on t5.id = t2.site_id
                {}
                """.format(condition)
        sql_1 = """select * from ({})t where rn > {} limit {};"""
        sql_2 = """
                select 
                    count(1)
                from
                    (
                    select 
                        t1.id,
                        t2.name,
                        t1.name,
                        t1.content,
                        t1.value,
                        t1.status,
                        t1.time,
                        coalesce(t3.name_cn, ''),
                        t4.problem,
                        t4.plan_description,
                        t4.confirm_person,
                        t4.confirm_time,
                        row_number() over (order by t1.time desc) as rn
                    from 
                        hy_alarm_event t1                
                    left join 
                        hy_device t2 
                        on t2.id = t1.device_id_id
                    left join 
                        hy_customers t3 
                        on t3.customer_id = t2.customer_id
                    left join 
                        hy_confirm_alarm t4
                        on t4.event_id_id = t1.id
                    left join
                        hy_sites t5
                        on t5.id = t2.site_id
                    {}
                        )t;"""
        target = ['id', 'device_name', 'name', 'content', 'value', 'status', 'time', 'customer_name', 'problem',
                  'plan_description', 'confirm_person', 'site_name', 'confirm_time']
        try:
            cursor.execute(sql_1.format(sql_0, offset, limit))
            data = cursor.fetchall()
            cursor.execute(sql_2.format(condition))
            total = cursor.fetchone()[0]
            result = [dict(zip(target, i)) for i in data]
            data = {'list': result, 'total': total}
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)
            # return Response({'code': 500, 'msg': '服务器异常！'})


class AlarmHistoryExcel(APIView):
    permission_classes = []

    @log_wrapper(LOG_MODULE['3'], '导出历史报警')
    def get(self, request):
        cursor = connection.cursor()

        id_ = request.query_params.get('id')
        device_id = request.query_params.get('device_id')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')

        if id_:
            c1 = "t1.id = '{}' and ".format(id_)
        else:
            c1 = ''
        if device_id:
            c2 = "t2.id = '{}' and ".format(device_id)
        else:
            c2 = ''
        if start_time and end_time:
            c3 = "t1.time > TO_TIMESTAMP({}) and t1.time < TO_TIMESTAMP({}) ".format(start_time, end_time)
        elif start_time:
            c3 = "t1.time > TO_TIMESTAMP({}) ".format(start_time)
        elif end_time:
            c3 = "t1.time < TO_TIMESTAMP({}) ".format(end_time)
        else:
            c3 = ''

        condition = (c1 + c2 + c3).rstrip('and ')
        if condition:
            condition = 'where ' + condition

        sql_0 = """
                select 
                    t1.id,
                    t1.name,
                    t1.content,
                    t1.status,
                    t1.value,
                    t2.name,
                    coalesce(t3.name_cn, '') as customer_name,
                    to_char(t1.time,'yyyy-mm-dd hh24:mi:ss') as time,
                    t4.confirm_person,
                    to_char(t4.confirm_time,'yyyy-mm-dd hh24:mi:ss') as time,
                    t4.problem,
                    t4.plan_description
                from 
                    hy_alarm_event t1                
                left join 
                    hy_device t2 
                    on t2.id = t1.device_id_id
                left join 
                    hy_customers t3 
                    on t3.customer_id = t2.customer_id
                left join 
                    hy_confirm_alarm t4
                    on t4.event_id_id = t1.id
                {}
                """.format(condition)
        # target = ['id', 'name'， 'content', 'status', 'value', 'device_name', 'customer_name', 'time',
        # 'confirm_person', 'confirm_time', 'problem',  'plan_description']
        target = ['编码', '名称', '信息', '状态', '值', '报警设备', '所属客户', '发生时间', '确认人', '确认时间', '问题描述',
                  '解决方案']
        try:
            cursor.execute(sql_0)
            excel_data = cursor.fetchall()
            excel_data.insert(0, target)
            return util_response(excel_data)
            # return Response({'code': 200, 'msg': 'ok', 'data': excel_data})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)
            # return Response({'code': 500, 'msg': '服务器异常！'})


class AlarmNotice(APIView):
    permission_classes = [AlarmPermission]

    def get(self, request):
        cursor = connection.cursor()
        customer_id = request.query_params.get('customer_id')
        page = request.query_params.get('page', '1')
        row = request.query_params.get('row', '10')

        limit = int(row)
        offset = int(row) * (int(page) - 1)

        if customer_id:
            condition = "t1.customer_id = '{}' ".format(customer_id)
        else:
            condition = ''
        if condition:
            condition = 'where ' + condition

        sql_1 = """
            select
                *
            from(
                select
                    t1.customer_id,
                    t1.name_cn,
                    array_agg(t2.name) as notifier,
                    array_agg(t2.status) as status,
                    row_number() over (order by t1.time desc) as rn 
                from 
                    hy_customers t1
                left join
                    hy_notifier t2
                    on t1.customer_id = t2.customer_id_id
                %s 
                group by t1.customer_id)t
            where rn > %d limit %d;""" % (condition, offset, limit)
        sql_2 = """
            select
                count(1)
            from(
                select
                    t1.customer_id, 
                    t1.name_cn,
                    array_agg(t2.name) as notifier,
                    case array_agg(t2.status) when '{1}' then '1' else '0' end as status
                from 
                    hy_customers t1
                left join
                    hy_notifier t2
                    on t1.customer_id = t2.customer_id_id
                %s
                group by t1.customer_id
                )t;""" % condition
        target = ['customer_id', 'customer_name', 'notifier', 'status']
        try:
            cursor.execute(sql_1)
            data = cursor.fetchall()
            cursor.execute(sql_2)
            total = cursor.fetchone()[0]
            result = [dict(zip(target, i)) for i in data]
            for i in result:
                if '1' in i['status']:
                    i['status'] = '1'
                else:
                    i['status'] = '0'
            data = {'list': result, 'total': total}
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['3'], '关闭报警通知/启用报警通知')
    def post(self, request, customer_id):
        try:
            data = dict(request.data.items())
            customer = HyCustomers.objects.get(customer_id=customer_id)
            customer.customer_notifier.all().update(**data)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class AlarmNotifiers(APIView):
    permission_classes = [AlarmPermission]

    def get(self, request, id_):
        try:
            customer = HyCustomers.objects.get(customer_id=id_)
        except Exception as e:
            return util_response(code=ecode.InvalidParams)
            # return Response({'code': 400, 'msg': '请求参数有误！'})
        try:
            notifiers = customer.customer_notifier.all()
            data = NotifierSerializer(notifiers, many=True).data
            total = len(data)
            data = {'list': data, 'total': total}
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['3'], '报警通知新增通知人')
    def post(self, request, id_):
        try:
            data = dict(request.data.items())
            data['customer_id_id'] = id_

            # 判断手机号是否重复
            query_set = HyNotifier.objects.filter(phone=data['phone'], customer_id_id=id_)
            if len(query_set) > 0:
                return util_response(code=ecode.ExistedPhone)

            post_set = HyNotifier.objects.create(**data)
            post_set.save()
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['3'], '修改报警通知人')
    def put(self, request, id_):
        try:
            data = dict(request.data.items())
            # 判断手机号是否重复
            query_set = HyNotifier.objects.filter(id=id_)
            if query_set:
                customer_id = query_set[0].customer_id
            query_set = HyNotifier.objects.filter(customer_id=customer_id, phone=data['phone']).exclude(id=id_)
            if len(query_set) > 0:
                return util_response(code=ecode.ExistedPhone)
            HyNotifier.objects.filter(id=id_).update(**data)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['3'], '删除报警通知人')
    def delete(self, request, id_):
        try:
            HyNotifier.objects.filter(id=id_).delete()
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)
            # return Response({'code': 500, 'msg': '服务器异常！'})


class AlarmLevel(APIView):
    permission_classes = [AlarmPermission]

    def get(self, request):
        cursor = connection.cursor()

        customer_id = request.query_params.get('customer_id')
        name = request.query_params.get('name')
        page = request.query_params.get('page', '1')
        row = request.query_params.get('row', '10')

        limit = int(row)
        offset = int(row) * (int(page) - 1)

        if customer_id:
            c1 = "t2.customer_id = {} and ".format(customer_id)
        else:
            c1 = ''
        if name:
            c2 = "t1.name like '%{}%'".format(name)
        else:
            c2 = ''
        condition = (c1 + c2).rstrip('and ')
        if condition:
            condition = 'where ' + condition

        sql_1 = """
            select
                *
            from(
                select 
                    t1.id,
                    t1.name,
                    t1.info,
                    t2.name,
                    t1.level,
                    t1.remark,
                    t3.name_cn,
                    row_number() over (order by t1.time desc) as rn
                from 
                    hy_alarm_level t1
                left join 
                    hy_device t2 
                    on t2.id = t1.device_id_id
                left join 
                    hy_customers t3 
                    on t2.customer_id = t3.customer_id
                {})t
            where rn > {} limit {};"""
        sql_2 = """
               select
                   count(1)
               from(
                   select 
                       t1.id,
                       t1.name,
                       t1.info,
                       t2.name,
                       t1.level,
                       t1.remark,
                       t3.name_cn
                   from 
                       hy_alarm_level t1
                   left join 
                       hy_device t2 
                       on t2.id = t1.device_id_id
                   left join 
                       hy_customers t3 
                       on t2.customer_id = t3.customer_id
                   {})t;"""
        target = ['id', 'name', 'info', 'device_name', 'level', 'remark', 'customer_name']
        try:
            cursor.execute(sql_1.format(condition, offset, limit))
            data = cursor.fetchall()
            cursor.execute(sql_2.format(condition))
            total = cursor.fetchone()[0]
            result = [dict(zip(target, i)) for i in data]
            data = {'list': result, 'total': total}
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': {'list': result, 'total': total}})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['3'], '修改报警优先级')
    def post(self, request, id_):
        try:
            data = dict(request.data.items())
            HyAlarmLevel.objects.filter(id=id_).update(**data)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class AlarmPredict(APIView):
    permission_classes = [AlarmPermission]

    def get(self, request):
        cursor = connection.cursor()

        num = request.query_params.get('num', '6')

        sql = """
            select 
                t1.id, 
                t1.name, 
                t1.content, 
                t1.value,  
                t2.name,
                t3.name_cn,
                to_char(t1.time + interval '24 hour','yyyy-mm-dd hh24:mi:ss') as time
            from 
                hy_alarm_event t1 
            left join 
                hy_device t2
                on t1.device_id_id = t2.id
            left join 
                hy_customers t3 
                on t2.customer_id = t3.customer_id
            limit {};"""
        target = ['id', 'name', 'content', 'value', 'device_name', 'customer_name', 'time']
        try:
            cursor.execute(sql.format(num))
            data = cursor.fetchall()
            result = [dict(zip(target, i)) for i in data]
            for i in result:
                i['probability'] = '%.2f' % (random.random()*(95-82)+82)
            data = {'list': result, 'total': num}
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': {'list': result, 'total': num}})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)
