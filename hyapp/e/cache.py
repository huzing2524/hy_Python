# 存储chart对应customer site
CHART = 'Chart'
# 存储device返回数据的类型列表
DeviceTags = "deviceTags"
# 存储device在线时间戳
DeviceOnline = "DeviceOnline"
# 存储device最新一次上传的数据
DeviceMonitorData = "DeviceMonitorData"
# 使用手册
Manual = "manual"

# 实时数据 设备数据存储
AnalysisRealTimeDeviceItems = "RealTimeDeviceItems"

# 图表展示的设备数据
ChartItems = "ChartItems"
AnalysisChartItems = "AnalysisChartItems"


def get_chart_key(chart_id):
    return CHART + '_' + chart_id


def get_device_tag_key(device_id):
    return DeviceTags + '_' + device_id


def get_all_device_online_key():
    return DeviceOnline + '*'


def get_device_online_key(device_id):
    return DeviceOnline + '_' + device_id


def get_device_monitor_data_key(device_id):
    return DeviceMonitorData + '_' + device_id


def get_manual_key():
    return Manual


def get_realtime_device_items_key(site_id):
    return AnalysisRealTimeDeviceItems + '_' + str(site_id)


def get_chart_items_key(chart_id):
    return ChartItems + '_' + str(chart_id)


def get_analysis_chart_items_key(chart_id):
    return AnalysisChartItems + '_' + str(chart_id)
