import logging
from rest_framework.views import APIView
from django.contrib.auth.hashers import make_password
from django_redis import get_redis_connection
from hyapp.e import ecode
from hyapp.models import HyUsers
from hyapp.serializer import UserSerializer
from hyapp.permissions import RightsPermission
from hyapp.utils import util_response, log_wrapper
from hyapp.constants import LOG_MODULE

# ----------------------------权限管理----------------------------


class UserRight(APIView):
    permission_classes = [RightsPermission]

    def get(self, request):
        account = request.query_params.get('account')
        name = request.query_params.get('name')
        phone = request.query_params.get('phone')
        page = request.query_params.get('page', '1')
        row = request.query_params.get('row', '10')

        offset = (int(page) - 1) * int(row)
        limit = int(row)

        condition = dict()
        if account:
            condition['account__icontains'] = account
        if name:
            condition['name__icontains'] = name
        if phone:
            condition['phone__icontains'] = phone
        try:
            query_set = HyUsers.objects.filter(**condition)
            total = len(query_set)
            data = UserSerializer(query_set, many=True).data
            data = data[offset: offset+limit]
            data = {'list': data, 'total': total}
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': {'list': data, 'total': total}})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)
            # return Response({'code': 500, 'msg': '服务器异常！'})

    @log_wrapper(LOG_MODULE['7'], '新增管理员')
    def post(self, request):
        data = dict(request.data.items())
        try:
            HyUsers.objects.get(phone=data['phone'])
            return util_response(code=ecode.ExistedPhone)
        except Exception as e:
            pass
        try:
            HyUsers.objects.get(account=data['account'])
            return util_response(code=ecode.ExistedPhone)
        except Exception as e:
            pass
        try:
            password = make_password(data['password'], None, 'pbkdf2_sha1')
            data['password'] = password
            data['creator'] = request.redis_cache['account']
            post_set = HyUsers.objects.create(**data)
            post_set.save()
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)
            # return Response({'code': 500, 'msg': '服务器异常！'})

    @log_wrapper(LOG_MODULE['7'], '修改管理员')
    def put(self, request, user_id):
        try:
            data = dict(request.data.items())
            # 校验手机号和账号是否重复
            if 'phone' in data:
                query_set = HyUsers.objects.filter(phone=data['phone']).exclude(id=user_id)
                if len(query_set) > 0:
                    return util_response(code=ecode.ExistedPhone)
            if 'account' in data:
                query_set = HyUsers.objects.filter(account=data['account']).exclude(id=user_id)
                if len(query_set) > 0:
                    return util_response(code=ecode.ExistedAccount)
            HyUsers.objects.filter(id=user_id).update(**data)
            # 删除缓存中的账号信息
            query_set = HyUsers.objects.filter(id=user_id)
            phone = query_set[0].phone
            conn = get_redis_connection("default")
            # print('old', conn.hget(phone, 'right'))
            conn.delete(phone)
            # print('new', conn.hget(phone, 'right'))
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)
            # return Response({'code': 500, 'msg': '服务器异常！'})

    @log_wrapper(LOG_MODULE['7'], '删除管理员')
    def delete(self, request, user_id):
        try:
            HyUsers.objects.filter(id=user_id).delete()
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)
            # return Response({'code': 500, 'msg': '服务器异常！'})
