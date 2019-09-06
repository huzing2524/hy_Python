from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password

import re
import jwt
import base64
import logging
import datetime
from hy import settings
from hyapp.e import ecode
from hyapp.utils import log_wrapper, util_response
from hyapp.constants import LOG_MODULE
from hyapp.models import HyUsers
from django_redis import get_redis_connection
from django.db import connection


class LogIn(APIView):

    @log_wrapper(LOG_MODULE['0'], '登录账号')
    def get(self, request):
        # print(make_password("1234", None, 'pbkdf2_sha1'))
        authorization = request.META.get("HTTP_AUTHORIZATION")
        if not authorization:
            return util_response(code=ecode.InvalidParams)
            # return Response({"code": 500, "msg": "你未认证无法登录！"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            authorization = authorization.split(" ")[-1]
            info = base64.b64decode(authorization).decode()
            # print(info)  # test:test
        except Exception:
            return util_response(code=ecode.InvalidParams)
            # return Response({"code": 500, "msg": "请求头token错误！"}, status=status.HTTP_200_OK)
        else:
            # todo 账号登录
            login_phone = info.split(":")[0]  # 'test'
            login_password = info.split(":")[-1]  # 'test'
            # print(login_phone, login_password)
            # logger.info(login_username, login_password)

            try:
                # 验证失败次数
                conn = get_redis_connection('default')
                fail_times = conn.hget(login_phone, 'fail_times')
                if fail_times:
                    fail_times = int(fail_times)
                    query_set = HyUsers.objects.filter(phone=login_phone)
                    if len(query_set) > 0:
                        customer_id = query_set[0].customer_id
                        allowed_fail_times = conn.hget(customer_id, 'fail_times') or \
                                             settings.DEFAULT_SYS_SETTINGS['fail_times']
                        if fail_times >= int(allowed_fail_times):
                            return util_response(code=ecode.TooManyFails)
                else:
                    fail_times = 0
                # 账号是否存在
                query_set = HyUsers.objects.filter(phone=login_phone)
                if len(query_set) == 0:
                    return util_response(code=ecode.InvalidAccount)
                    # return Response({"code": 500, "msg": "账号不存在！"}, status=status.HTTP_200_OK)

                password = query_set.values()[0]['password']
                user_name = query_set.values()[0]['name']
                verify_boolean = check_password(login_password, password)
                if verify_boolean:
                    payload = {"phone": login_phone, "exp": datetime.datetime.utcnow() + datetime.timedelta(
                        days=7)}
                    jwt_token = jwt.encode(payload, settings.JWT_SECRET_KEY)
                    # print("jwt_token=", jwt_token)
                    data = {"jwt": jwt_token, "name": user_name}
                    # 重置登录失败次数
                    conn.hset(login_phone, 'fail_times', '0')
                    return util_response(data)
                    # return Response({"code": 200, "msg": "ok", "data": data}, status=status.HTTP_200_OK)
                else:
                    fail_times += 1
                    conn.hset(login_phone, 'fail_times', str(fail_times))
                    now = datetime.datetime.now()
                    tomorrow = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
                    conn.expire(login_phone, (tomorrow-datetime.datetime.now()).seconds)
                    return util_response(code=ecode.InvalidPassword)
                    # return Response({"code": 200, "msg": "密码校验失败！"}, status=status.HTTP_200_OK)
            except Exception as e:
                logging.error(e)
                return util_response(code=ecode.ERROR)
                # return Response({"code": 500, "msg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendVerificationCode(APIView):
    # todo 异步

    def get(self, request):
        conn = get_redis_connection()
        phone = request.query_params.get('phone')
        try:
            match_result = re.match(r'^(13\d|14[5|7]|15\d|166|17[0|3|6|7]|18\d)\d{8}$', phone)
            if not match_result:
                return Response({'code': 200, "msg": "手机号不合法！"}, status=status.HTTP_200_OK)

            conn.set(phone+'_', '1234')
            conn.expire(phone+'_', 60)
            # return code
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class ChangePassword(APIView):

    @log_wrapper(LOG_MODULE['0'], '重置密码')
    def post(self, request):
        conn = get_redis_connection('default')
        phone = request.data.get('phone')
        code = request.data.get('code')
        new_password = request.data.get('pwd')

        try:
            r_code = conn.get(phone+'_')
            if not r_code:
                return util_response(code=ecode.InvalidCode)
                # return Response({"code": 500, 'msg': '验证码已失效，请重新验证！'})
            if r_code == code:
                new_password = make_password(new_password, None, 'pbkdf2_sha1')
            else:
                return util_response(code=ecode.WrongCode)
                # return Response({"code": 500, 'msg': '验证码验证失败！'})
            query_set = HyUsers.objects.filter(phone=phone)
            if len(query_set) == 0:
                return util_response(code=ecode.InvalidAccount)
                # return Response({"code": 500, "msg": "账号不存在！"})
            update = {'password': new_password}
            HyUsers.objects.filter(phone=phone).update(**update)
            # 重置登录失败次数
            conn.hset(phone, 'fail_times', '0')
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class MineAccount(APIView):

    def get(self, request):
        cursor = connection.cursor()
        conn = get_redis_connection('default')

        phone = request.redis_cache["phone"]
        account = request.redis_cache["account"]
        customer_id = request.redis_cache["customer_id"]

        sql = "select name from hy_users where phone = '{}';".format(phone)
        try:
            result = dict()
            cursor.execute(sql)
            result['name'] = cursor.fetchone()[0]
            result['account'] = account
            result['phone'] = phone
            result['logo'] = conn.hget(customer_id, 'icon')
            result['customer_name'] = conn.hget(customer_id, 'name')
            return util_response(result)
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)