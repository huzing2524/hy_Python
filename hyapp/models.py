import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField


# Create your models here.
# todo 核对字段


class HyLogs(models.Model):
    objects = models.Manager()

    # id = models.AutoField(primary_key=True)
    operator = models.CharField(max_length=20)
    operation = models.CharField(max_length=20, null=False)
    result = models.BooleanField(default=True)
    module = models.CharField(max_length=20)
    ip = models.CharField(max_length=15, null=True)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hy_logs'
        ordering = ['-time']


class HyCustomers(models.Model):
    objects = models.Manager()

    LOCK_STATE_IN_CHOICES = [
        ('0', '未锁定'),
        ('1', '锁定'),
    ]

    # 公司id
    customer_id = models.IntegerField(primary_key=True, blank=True)
    # 中文名称
    name_cn = models.CharField(max_length=50, blank=True)
    # 英文名称
    name_en = models.CharField(max_length=50, blank=True, null=True)
    # 简称
    name_short = models.CharField(max_length=20, blank=True, null=True)
    # 助记码，要不要限制长度
    code_mnemonic = models.CharField(max_length=10, blank=True, null=True)
    # 地址
    address = models.CharField(max_length=50, blank=True, null=True)
    province = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    district = models.CharField(max_length=20, blank=True, null=True)
    # 联系人
    contact = models.CharField(max_length=20, blank=True, null=True)
    # 联系人手机号
    phone = models.CharField(max_length=11, blank=True, null=True)
    # 客户类别
    customer_category = models.CharField(max_length=20, blank=True, null=True)
    # 经营范围
    business = models.CharField(max_length=200, blank=True, null=True)
    # 人民币账号
    account_rmb = models.CharField(max_length=100, blank=True, null=True)
    # 美元账号
    account_dollar = models.CharField(max_length=100, blank=True, null=True)
    # 组织机构代码
    code_organization = models.CharField(max_length=20, blank=True, null=True)
    # 税号
    ein = models.CharField(max_length=20, blank=True, null=True)
    # 税收号
    tax_no = models.CharField(max_length=20, null=True, blank=True)
    # 个税类型
    tax_types = models.CharField(max_length=100, blank=True, null=True)
    # 经营许可证照片
    business_license = models.CharField(max_length=50, blank=True, null=True)
    # 锁定状态
    lock_status = models.CharField(max_length=1, default='0', choices=LOCK_STATE_IN_CHOICES, blank=True)
    email = models.CharField(max_length=20, blank=True, null=True)
    remark = models.CharField(max_length=100, default='', blank=True)
    delete_state = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hy_customers'
        ordering = ['-time']


class HyUsers(models.Model):
    objects = models.Manager()

    ROLE_IN_CHOICES = [
        ('0', '普通管理员'),
        ('1', '企业管理员'),
        ('2', '超级管理员')
    ]
    # 用户唯一编码
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(HyCustomers, related_name='customer_user', on_delete=models.CASCADE,
                                 default='1566801102')
    # 用户账号
    account = models.CharField(max_length=20, unique=True)
    # 用户手机号（手机号不能为空）
    phone = models.CharField(max_length=11, blank=False, null=False, unique=True)
    # 用户名称
    name = models.CharField(max_length=20, default='')
    # 用户密码
    password = models.CharField(max_length=60)
    # 用户角色
    role = models.CharField(max_length=1, default='0', choices=ROLE_IN_CHOICES)
    # 创建者
    creator = models.CharField(max_length=36, null=False)
    # 权限
    right = ArrayField(models.CharField(max_length=10, blank=True), default=list)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hy_users'
        ordering = ['-time']


class HySites(models.Model):
    objects = models.Manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.IntegerField()
    site_name = models.CharField(max_length=20, null=False)
    province = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=20, blank=True)
    district = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=40, default='', blank=True)
    remark = models.CharField(max_length=100, default='', blank=True)
    lng = models.FloatField(blank=True, default=0)
    lat = models.FloatField(blank=True, default=0)
    delete_state = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hy_sites'
        ordering = ['-time']


# 通知人
class HyNotifier(models.Model):
    objects = models.Manager()

    LEVEL_IN_CHOICES = [
        ('0', '员工'),
        ('1', '老板')
    ]
    customer_id = models.ForeignKey(HyCustomers, related_name='customer_notifier', on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    phone = models.CharField(max_length=11)
    level = models.CharField(max_length=1, default='0')
    remark = models.CharField(max_length=100, default='')
    status = models.CharField(max_length=1, default='0')
    time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hy_notifier'
        ordering = ['-time']


class Device(models.Model):
    id = models.CharField(max_length=50, primary_key=True, null=False, blank=False)
    name = models.CharField(max_length=20, null=False)
    pwd = models.CharField(max_length=20, default='')
    customer = models.ForeignKey('HyCustomers', related_name="device", on_delete=models.CASCADE, null=True)
    site = models.ForeignKey('HySites', related_name="device", on_delete=models.CASCADE, null=True)
    time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hy_device'
        ordering = ['-time']


class Chart(models.Model):
    # 0: 柱状图，1：折线图 2：条形图 3：饼图
    ChartTypeList = [('0', '柱状图'),
                     ('1', '折线图'),
                     ('2', '条形图'),
                     ('3', '饼图')]
    TimeTypeList = [('0', '分'),
                    ('1', '时'),
                    ('2', '天')]

    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, default='', null=False)
    chart_type = models.CharField(max_length=1, choices=ChartTypeList, null=False)
    time_type = models.CharField(max_length=1, choices=TimeTypeList, null=False)
    customer = models.ForeignKey('HyCustomers', related_name="chart", on_delete=models.CASCADE, null=True)
    site = models.ForeignKey('HySites', related_name="chart", on_delete=models.CASCADE, null=True)
    time = models.DateTimeField(auto_now=True)
    items = JSONField(default=dict)

    class Meta:
        db_table = 'hy_chart'
        ordering = ['-time']


class AnalysisChart(models.Model):
    # 0: 柱状图，1：折线图 2：条形图 3：饼图
    ChartTypeList = [('0', '柱状图'),
                     ('1', '折线图'),
                     ('2', '条形图'),
                     ('3', '饼图')]
    TimeTypeList = [('0', '分'),
                    ('1', '时'),
                    ('2', '天')]

    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, default='', null=False)
    forecast = models.BooleanField(default=False, null=False)
    chart_type = models.CharField(max_length=1, choices=ChartTypeList, null=False)
    time_type = models.CharField(max_length=1, choices=TimeTypeList, null=False)
    customer = models.ForeignKey('HyCustomers', related_name="analysisChart", on_delete=models.CASCADE, null=True)
    site = models.ForeignKey('HySites', related_name="analysisChart", on_delete=models.CASCADE, null=True)
    time = models.DateTimeField(auto_now=True)
    items = JSONField(default=dict)

    class Meta:
        db_table = 'hy_analysis_chart'
        ordering = ['-time']


class HyAlarmEvent(models.Model):
    objects = models.Manager()
    # todo 报警编码
    # code = models.IntegerField()
    device_id = models.ForeignKey(Device, related_name='device_alarm', on_delete=models.PROTECT)
    name = models.CharField(max_length=50, null=True)
    content = models.CharField(max_length=100, null=True)
    value = models.CharField(max_length=15, null=True)
    alarm_type = models.CharField(max_length=15, null=False)
    status = models.CharField(max_length=1, default='0', blank=True)
    time = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hy_alarm_event'
        ordering = ['-create_time']


class HyConfirmAlarm(models.Model):
    objects = models.Manager()
    # OneToOneFiled
    event_id = models.ForeignKey(HyAlarmEvent, related_name='alarm_confirm', on_delete=models.PROTECT)
    confirm_person = models.CharField(max_length=20)
    plan_description = models.CharField(max_length=100)
    problem = models.CharField(max_length=100, default='', blank=True)
    confirm_time = models.DateTimeField()

    class Meta:
        db_table = 'hy_confirm_alarm'
        ordering = ['-confirm_time']


class HyAlarmLevel(models.Model):
    objects = models.Manager()

    LEVEL_IN_CHOICES = [
        ('0', '优先级低'),
        ('1', '优先级高')
    ]

    name = models.CharField(max_length=20)
    info = models.CharField(max_length=100, default='')
    device_id = models.ForeignKey(Device, related_name='device_level', on_delete=models.PROTECT)
    level = models.CharField(max_length=1, default='0', choices=LEVEL_IN_CHOICES)
    remark = models.CharField(max_length=100)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hy_alarm_level'
        ordering = ['-time']
