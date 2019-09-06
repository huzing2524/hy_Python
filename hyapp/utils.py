import uuid
import time
import random
import shortuuid
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from hyapp.models import HyLogs, HyCustomers
from hyapp.e import ecode, cache


def util_response(data='', code=ecode.SUCCESS, http_status=status.HTTP_200_OK):
    if http_status == status.HTTP_200_OK:
        if data == []:
            return Response({"code": code, "msg": ecode.ErrorCode[code], "data": data})
        elif data:
            return Response({"code": code, "msg": ecode.ErrorCode[code], "data": data})
        else:
            return Response({"code": code, "msg": ecode.ErrorCode[code]})
    else:
        return Response({"code": http_status, "msg": ecode.ErrorCode.get(http_status, 'error')}, status=http_status)


# 操作日志装饰器
def log_wrapper(module, operation):
    def decorator(func):
        def inner(*args, **kwargs):
            response = func(*args, **kwargs)
            account = args[1].redis_cache.get("account", 'admin')
            # ip
            request = args[1]
            if 'HTTP_X_FORWARDED_FOR' in request.META:
                ip = request.META['HTTP_X_FORWARDED_FOR']
            else:
                ip = request.META['REMOTE_ADDR']
            result = True if response.data['code'] == 200 else False
            operation_set = HyLogs.objects.create(operator=account, operation=operation, result=result, module=module,
                                                  ip=ip)
            operation_set.save()
            return response

        return inner

    return decorator


def generate_chart_id():
    return uuid.uuid4().hex


def generate_uuid():
    """生成18位短uuid，字符串"""
    # u22 = shortuuid.uuid()  # 22位uuid
    u18 = shortuuid.ShortUUID().random(length=18)  # 18位uuid
    return u18


def get_all_device_state():
    """
    获取所有设备的在线状态，1: 在线
    :return:
    """
    conn = get_redis_connection('default')
    keys = conn.keys(cache.get_all_device_online_key())
    states = dict()
    for key in keys:
        device_id = key.split('_')[-1]
        cache_time = conn.get(key)
        if cache_time and int(cache_time) > time.time():
            states[device_id] = {
                "online": "1"
            }
        else:
            states[device_id] = {
                "last_online": cache_time
            }
    return states


def get_device_online_state(device_id):
    conn = get_redis_connection('default')
    cache_time = conn.get(cache.get_device_online_key(device_id))
    if cache_time:
        if int(cache_time) > time.time():
            return '1', 0
        else:
            return '0', int(cache_time)
    else:
        return '0', 0


def generate_customer_id():
    while True:
        id_ = int(''.join(['1'] + [str(random.randrange(0, 9)) for i in range(9)]))
        print(id_)
        try:
            q = HyCustomers.objects.get(customer_id=int(id_))
        except Exception as e:
            break
    return id_
