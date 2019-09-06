from rest_framework import serializers
from hyapp.models import HyCustomers, HySites, HyLogs, Device, HyAlarmEvent, HyConfirmAlarm, HyNotifier, HyUsers, Chart, \
    AnalysisChart

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from hyapp.utils import get_device_online_state

import datetime


class CustomersSerializer(serializers.ModelSerializer):
    time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)

    class Meta:
        model = HyCustomers
        fields = ['customer_id', 'time', 'name_cn', 'name_en', 'name_short', 'code_mnemonic', 'address', 'province',
                  'city', 'district', 'contact', 'phone', 'customer_category', 'business', 'account_rmb',
                  'account_dollar', 'code_organization', 'ein', 'tax_no', 'tax_types', 'business_license',
                  'lock_status', 'email', 'remark']


class CustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = HyCustomers
        fields = ['customer_id', 'name_cn']


class CustomerBigListSerializer(serializers.ModelSerializer):
    class Meta:
        model = HyCustomers
        fields = ['customer_id', 'name_cn', 'name_short', 'customer_category', 'code_mnemonic', 'lock_status']


class UserSerializer(serializers.ModelSerializer):
    time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)

    class Meta:
        model = HyUsers
        fields = ['id', 'account', 'name', 'phone', 'role', 'right', 'creator', 'time']


class RegionToCustomersSerializer(serializers.ModelSerializer):
    class Meta:
        model = HyCustomers
        fields = ['customer_id', 'name_cn', 'name_en']


class CustomerSiteSerializer(serializers.ModelSerializer):
    time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)

    class Meta:
        model = HySites
        fields = '__all__'


class OperationLogsSerializer(serializers.ModelSerializer):
    time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    result = serializers.SerializerMethodField()

    class Meta:
        model = HyLogs
        fields = ['id', 'operator', 'operation', 'result', 'module', 'ip', 'time']

    def get_result(self, obj):
        if obj.result:
            return '成功'
        else:
            return '失败'


class AlarmEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = HyAlarmEvent
        fields = ['id', 'name', 'content', 'value', 'status', 'time']


class ConfirmAlarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = HyConfirmAlarm
        fields = ['customer_name', 'confirm_person', 'plan_description', 'problem', 'confirm_time']


class NotifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = HyNotifier
        fields = ['id', 'name', 'phone', 'level', 'remark']


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'row'
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            {'code': 200, 'msg': 'ok', 'data': {'list': data, 'total': self.page.paginator.count}})


class DeviceSerializer(serializers.ModelSerializer):
    time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    customer_name = serializers.SerializerMethodField('get_customer_name')
    site_name = serializers.SerializerMethodField('get_site_name')
    state = serializers.SerializerMethodField('get_state')
    offline_time = serializers.SerializerMethodField('get_offline_time')

    class Meta:
        model = Device
        fields = ('id', 'name', 'time', 'customer_name', 'site_name', 'state', 'pwd',
                  'customer_id', 'site_id', 'offline_time')

    def get_customer_name(self, obj):
        return obj.customer.name_cn

    def get_site_name(self, obj):
        return obj.site.site_name

    def get_state(self, obj):
        state, online_time = get_device_online_state(obj.id)
        return state

    def get_offline_time(self, obj):
        state, online_time = get_device_online_state(obj.id)
        if online_time > 0:
            return datetime.datetime.fromtimestamp(online_time).strftime("%Y-%m-%d %H:%M:%S")
        else:
            return '-'


class ChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chart
        fields = ('id', 'chart_type', 'name')


class AnalisysChartSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField('get_type')

    class Meta:
        model = AnalysisChart
        fields = ('id', 'chart_type', 'name', 'type')

    def get_type(self, obj):
        if obj.forecast:
            return '1'
        else:
            return '0'


class DeviceList(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('id', 'name', 'time')
