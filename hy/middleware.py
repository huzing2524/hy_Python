# -*- coding: utf-8 -*-
import jwt
from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django_redis import get_redis_connection
from rest_framework import status

from hyapp.models import HyUsers
from hyapp.constants import REDIS_CACHE


#
#
# def _redis_pool_number():
#     """输出redis连接池数量"""
#     r = get_redis_connection("default")  # Use the name you have defined for Redis in settings.CACHES
#     connection_pool = r.connection_pool
#     print("Created connections so far: %d" % connection_pool._created_connections)


class JwtTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 跳过jwt token校验
        if request.path in ["/test/", '/api/v1/login/', '/api/v1/reset/', '/api/v1/send/code/']:
            request.redis_cache = REDIS_CACHE
            return
        token = request.META.get("HTTP_AUTHORIZATION")

        if token:
            try:
                token = token.split(" ")[-1]
                # print(token)
                payload = jwt.decode(token, key=settings.JWT_SECRET_KEY, verify=True)
                if "phone" in payload and "exp" in payload:
                    REDIS_CACHE["phone"] = payload["phone"]
                    request.redis_cache = REDIS_CACHE
                else:
                    raise jwt.InvalidTokenError
            except jwt.ExpiredSignatureError:
                return HttpResponse("jwt token expired", status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return HttpResponse("Invalid jwt token", status=status.HTTP_401_UNAUTHORIZED)
        else:
            return HttpResponse("lack of jwt token", status=status.HTTP_401_UNAUTHORIZED)

    def process_response(self, request, response):
        return response


class RedisMiddleware(MiddlewareMixin):
    """Redis读取缓存, hash类型
    key: "13212345678"
    field: value
    {"account": "admin"}
    """

    def process_request(self, request):
        phone = request.redis_cache["phone"]
        conn = get_redis_connection("default")
        # print(phone), print(conn.hvals(phone))
        if phone.isdigit():
            account = conn.hget(phone, "account")
            right = conn.hget(phone, 'right')
            customer_id = conn.hget(phone, 'customer_id')
            if not account or not right or not customer_id:
                query_set = HyUsers.objects.filter(phone=phone)
                print(query_set.values())
                if len(query_set) > 0:
                    account = query_set[0].account
                    right = ','.join(query_set[0].right)
                    customer_id = query_set[0].customer_id
                    conn.hset(phone, 'account', account)
                    conn.hset(phone, 'right', right)
                    print(type(customer_id), customer_id)
                    conn.hset(phone, 'customer_id', customer_id)
            request.redis_cache["account"] = account
            request.redis_cache["rights"] = right
            request.redis_cache["customer_id"] = customer_id
            # print('redis_cache', request.redis_cache)
        else:
            return None

    def process_response(self, request, response):
        return response
