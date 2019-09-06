from django.urls import path

from .views import device, customers, operation_logs, login, sys_settings, alarm_management, rights, analysis
from .views import users, monitor, history_data, manual

urlpatterns = [
    path('monitor/main/map/', monitor.MainMap.as_view()),
    path('monitor/main/chart/', monitor.MainChat.as_view()),
    path('monitor/chart/', monitor.ChartAPI.as_view()),
    path('monitor/chart/img/', monitor.ChartImg.as_view()),
    path('monitor/chart/data/<str:chart_id>/', monitor.ChartDataAPI.as_view()),
    path('monitor/chart/device_items/', monitor.DeviceItems.as_view()),
    path('monitor/chart/<str:chart_id>/', monitor.ChartAPI.as_view()),

    path('equipment/site/<str:site_id>', device.SiteDeviceList.as_view()),
    path('equipment/items/<str:device_id>', device.DeviceItems.as_view()),
    path('equipment/<str:id>', device.DeviceAPI.as_view()),
    path('equipment', device.DeviceAPI.as_view()),
    path('histroydata/excel/', history_data.HistoryExcel.as_view()),
    path('histroydata/', history_data.History.as_view()),
    path('service/manual/', manual.Manual.as_view()),

    path('customer/', customers.Customer.as_view()),
    path('customer/detail/<slug:customer_id>', customers.CustomerDetail.as_view()),
    path('customer/list', customers.CustomerList.as_view()),
    path('customer/<slug:customer_id>/', customers.Customer.as_view()),
    path('customer/<slug:customer_id>/site/', customers.CustomerSite.as_view()),
    path('customer/site/<slug:id_>', customers.CustomerSite.as_view()),
    path('customer/lock/<slug:customer_id>', customers.CustomerLock.as_view()),
    path('customer/unlock/<slug:customer_id>', customers.CustomerUnlock.as_view()),
    path('log/managementlist/', operation_logs.OperationLogs.as_view()),
    path('log/managementlist/table', operation_logs.OperationLogsExcel.as_view()),
    path('region/customer', customers.RegionCustomer.as_view()),
    # 登录和重置密码
    path('login/', login.LogIn.as_view()),
    path('send/code/', login.SendVerificationCode.as_view()),
    path('reset/', login.ChangePassword.as_view()),
    path('account/', login.MineAccount.as_view()),
    # 报警管理
    path('police/real', alarm_management.RealTimeAlarm.as_view()),
    path('police/history', alarm_management.AlarmHistory.as_view()),
    path('police/history/excel', alarm_management.AlarmHistoryExcel.as_view()),
    path('police/notice', alarm_management.AlarmNotice.as_view()),
    path('police/notice/<slug:customer_id>', alarm_management.AlarmNotice.as_view()),
    path('police/noticer/<slug:id_>', alarm_management.AlarmNotifiers.as_view()),
    path('police/level', alarm_management.AlarmLevel.as_view()),
    path('police/level/<slug:id_>', alarm_management.AlarmLevel.as_view()),
    path('police/predict', alarm_management.AlarmPredict.as_view()),
    path('police/<slug:event_id>', alarm_management.RealTimeAlarm.as_view()),
    path('police/detail/<slug:event_id>', alarm_management.AlarmDetail.as_view()),
    # 系统配置
    path('system/message/', sys_settings.SystemInfo.as_view()),
    path('system/message/logo/', sys_settings.SystemInfoLogo.as_view()),
    path('system/message/bg/', sys_settings.BackgroundImg.as_view()),
    path('system/message/name/', sys_settings.SystemInfoName.as_view()),
    path('system/message/failureTimes/', sys_settings.SystemInfoFailTimes.as_view()),
    # 权限管理
    path('authority', rights.UserRight.as_view()),
    path('authority/<slug:user_id>', rights.UserRight.as_view()),

    # 数据分析
    path('analysis/realtime/items/<str:item_id>/', analysis.DeviceItemDetail.as_view()),
    path('analysis/realtime/items/<str:item_id>/excel/', analysis.DeviceItemDetailExcel.as_view()),
    path('analysis/realtime/', analysis.RealTime.as_view()),
    path('analysis/realtime/items/', analysis.DeviceItems.as_view()),
    path('analysis/chart/', analysis.ChartAPI.as_view()),
    path('analysis/chart/main/', analysis.ChartAPI.as_view()),
    path('analysis/chart/data/<str:chart_id>/', analysis.ChartData.as_view()),
    path('analysis/chart/device_items/', analysis.ChartDeviceItems.as_view()),

]
