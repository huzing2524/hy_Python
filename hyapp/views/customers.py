import os
import logging
import requests
from xml.etree import ElementTree
from rest_framework.views import APIView

from hy.settings import BASE_DIR, IMAGE_PATH, LOCATION_API, BAIDU_KEY
from hyapp.e import ecode
from hyapp import serializer
from hyapp.models import HyCustomers, HySites
from hyapp.utils import log_wrapper, generate_customer_id, util_response
from hyapp.constants import LOG_MODULE
from hyapp.permissions import CustomerPermission

# ----------------------------客户管理、站点管理----------------------------


class CustomerDetail(APIView):
    permission_classes = [CustomerPermission]

    def get(self, request, customer_id):
        try:
            query_set = HyCustomers.objects.filter(customer_id=customer_id)
            data = serializer.CustomersSerializer(instance=query_set, many=True).data
            if data:
                return util_response(data[0])
            else:
                return util_response(dict())
            # return Response({'code': 200, 'msg': 'ok', 'data': data})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class Customer(APIView):
    permission_classes = [CustomerPermission]

    # @log_wrapper('customer', '获取客户列表')
    def get(self, request):
        row = int(request.query_params.get('row', 10))
        page = int(request.query_params.get('page', 1))
        # 手动分页
        offset = (page - 1) * row

        condition = dict()
        condition['customer_id__contains'] = self.request.query_params.get('customer_id', '')
        condition['name_short__contains'] = self.request.query_params.get('customer_short_name', '')
        condition['code_mnemonic__contains'] = self.request.query_params.get('code_mnemonic', '')
        condition['customer_category'] = self.request.query_params.get('customer_category', '')
        condition['lock_status'] = self.request.query_params.get('lock_status', '')
        condition['delete_state__exact'] = False
        query_condition = dict()
        for i in condition:
            if condition[i] != '':
                query_condition[i] = condition[i]
        try:
            query_set = HyCustomers.objects.filter(**query_condition)
            total = len(query_set)
            s = serializer.CustomerBigListSerializer(instance=query_set, many=True)
            data = dict()
            data['list'] = s.data[offset:offset + row]
            data['total'] = total
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': data})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['4'], '新增客户')
    def post(self, request):
        try:
            data = dict(request.data.items())
            # 生成客户id随机十位数字
            data['customer_id'] = generate_customer_id()
            # print('data', data)
            business_license = data.get('business_license')
            extension = os.path.splitext(business_license.name)[1]
            if business_license:
                filename = '{}{}'.format(data['customer_id'], extension)
                path = os.path.join(os.path.dirname(BASE_DIR), "static/img/{}".format(filename))
                with open(path, 'wb') as file:
                    file.write(bytes(business_license.read()))
                data['business_license'] = IMAGE_PATH + "img/{}".format(filename)
            post_set = HyCustomers.objects.create(**data)
            post_set.save()
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['4'], '修改客户')
    def put(self, request, customer_id):
        try:
            data = dict(request.data.items())

            business_license = data.get('business_license')
            if business_license:
                extension = os.path.splitext(business_license.name)[1]
                new = '{}{}'.format(customer_id, extension)
                old_business_license = HyCustomers.objects.get(customer_id=customer_id).business_license
                old = old_business_license.split('/')[-1]
                # print('old', old)
                # print('new', new)
                if old == new:
                    delete = False
                else:
                    delete = True
                path = os.path.join(os.path.dirname(BASE_DIR), "static/img/{}".format(new))
                with open(path, 'wb') as file:
                    file.write(bytes(business_license.read()))
                data['business_license'] = IMAGE_PATH + "img/{}".format(new)
                # 当新图片正常保存后再删除旧图片
                if delete:
                    old_path = os.path.join(os.path.dirname(BASE_DIR), 'static/img/{}'.format(old))
                    os.remove(old_path)
            # 返回影响的数据数
            HyCustomers.objects.filter(customer_id=customer_id).update(**data)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['4'], '删除客户')
    def delete(self, request, customer_id):
        try:
            delete = {'delete_state': True}
            HyCustomers.objects.filter(customer_id=customer_id).update(**delete)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class CustomerLock(APIView):
    permission_classes = [CustomerPermission]

    @log_wrapper(LOG_MODULE['4'], '锁定客户')
    def post(self, request, customer_id):
        try:
            # 返回影响的数据数
            HyCustomers.objects.filter(customer_id=customer_id).update(lock_status='1')
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class CustomerUnlock(APIView):
    permission_classes = [CustomerPermission]

    @log_wrapper(LOG_MODULE['4'], '解锁客户')
    def post(self, request, customer_id):
        try:
            # 返回影响的数据数
            HyCustomers.objects.filter(customer_id=customer_id).update(lock_status='0')
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class CustomerList(APIView):
    permission_classes = []

    def get(self, request):
        try:
            query_set = HyCustomers.objects.filter(delete_state__exact=False)
            data = serializer.CustomerListSerializer(instance=query_set, many=True).data
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': data})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class RegionCustomer(APIView):
    permission_classes = []

    def get(self, request):
        try:
            # 参数不能放在路径中，无法匹配中文
            province = request.query_params.get('province')
            if not province:
                query_set = HyCustomers.objects.all()
            else:
                query_set = HyCustomers.objects.filter(province=province)
            s = serializer.RegionToCustomersSerializer(instance=query_set, many=True)
            data = s.data
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': data})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)


class CustomerSite(APIView):
    permission_classes = []

    # 无法用分页
    # pagination_class = BasicPagination

    # @log_wrapper('customer-site', '获取客户站点列表')
    def get(self, request, customer_id):
        row = int(request.query_params.get('row', 10))
        page = int(request.query_params.get('page', 1))
        # 手动分页
        offset = (page - 1) * row
        try:
            query_set = HySites.objects.filter(customer_id=customer_id, delete_state__exact=False)
            total = len(query_set)
            s = serializer.CustomerSiteSerializer(instance=query_set, many=True).data
            data = dict()
            data['list'] = s[offset:offset + row]
            data['total'] = total
            return util_response(data)
            # return Response({'code': 200, 'msg': 'ok', 'data': data})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['4'], '新增站点')
    def post(self, request, id_):  # customer_id
        try:
            data = dict(request.data.items())
            data['customer_id'] = id_
            params = dict()
            params['address'] = ''.join([data['province'], data['city'], data['district']])
            params['city'] = data['city']
            params['key'] = BAIDU_KEY
            response = requests.get(LOCATION_API, params)
            location = ElementTree.XML(response.text)
            data['lat'] = location.findall('.//lat')[0].text
            data['lng'] = location.findall('.//lng')[0].text
            post_set = HySites.objects.create(**data)
            post_set.save()
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['4'], '修改站点')
    def put(self, request, id_):  # site_id
        try:
            data = dict(request.data.items())
            # 返回影响的数据数
            HySites.objects.filter(id=id_).update(**data)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)

    @log_wrapper(LOG_MODULE['4'], '删除站点')
    def delete(self, request, id_):
        try:
            delete = {'delete_state': True}
            HySites.objects.filter(id=id_).update(**delete)
            return util_response()
            # return Response({'code': 200, 'msg': 'ok'})
        except Exception as e:
            logging.error(e)
            return util_response(code=ecode.ERROR)