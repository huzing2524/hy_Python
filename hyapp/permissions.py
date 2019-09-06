
from rest_framework.permissions import BasePermission


# 权限
# '0': '全部权限',
# '1': '监控管理',
# '2': '设备管理',
# '3': '报警管理',
# '4': '客户管理',
# '5': '数据分析',
# '6': '权限管理',
# '7': '系统设置',
class SuperAdminPermission(BasePermission):
    """超级管理员权限: 0"""

    # 无权限的显示信息
    message = "您没有权限查看！"

    def has_permission(self, request, view):
        rights = request.redis_cache["rights"]
        if rights:
            if "0" in rights:
                return True
            else:
                return False
        else:
            return False


class MonitorPermission(BasePermission):
    """监控管理权限: 1"""

    # 无权限的显示信息
    message = "您没有权限查看！"

    def has_permission(self, request, view):
        rights = request.redis_cache["rights"]
        if rights:
            if "0" in rights or "1" in rights:
                return True
            else:
                return False
        else:
            return False


class DevicePermission(BasePermission):
    """设备管理权限: 2"""

    # 无权限的显示信息
    message = "您没有权限查看！"

    def has_permission(self, request, view):
        rights = request.redis_cache["rights"]
        if rights:
            if "0" in rights or "2" in rights:
                return True
            else:
                return False
        else:
            return False


class AlarmPermission(BasePermission):
    """报警管理权限: 3"""

    # 无权限的显示信息
    message = "您没有权限查看！"

    def has_permission(self, request, view):
        rights = request.redis_cache["rights"]
        if rights:
            if "0" in rights or "3" in rights:
                return True
            else:
                return False
        else:
            return False


class CustomerPermission(BasePermission):
    """客户管理权限: 4"""

    # 无权限的显示信息
    message = "您没有权限查看！"

    def has_permission(self, request, view):
        rights = request.redis_cache["rights"]
        if rights:
            if "0" in rights or "4" in rights:
                return True
            else:
                return False
        else:
            return False


class DataAnalysisPermission(BasePermission):
    """数据分析权限: 5"""

    # 无权限的显示信息
    message = "您没有权限查看！"

    def has_permission(self, request, view):
        rights = request.redis_cache["rights"]
        if rights:
            if "0" in rights or "5" in rights:
                return True
            else:
                return False
        else:
            return False


# class HistoryDataPermission(BasePermission):
#     """历史数据权限: 6"""
#
#     # 无权限的显示信息
#     message = "您没有权限查看！"
#
#     def has_permission(self, request, view):
#         rights = request.redis_cache["rights"]
#         if rights:
#             if "0" in rights or "6" in rights:
#                 return True
#             else:
#                 return False
#         else:
#             return False


class RightsPermission(BasePermission):
    """权限管理权限: 6"""

    # 无权限的显示信息
    message = "您没有权限查看！"

    def has_permission(self, request, view):
        rights = request.redis_cache["rights"]
        if rights:
            if "0" in rights or "6" in rights:
                return True
            else:
                return False
        else:
            return False


class SysSettingsPermission(BasePermission):
    """系统设置权限: 7"""

    # 无权限的显示信息
    message = "您没有权限查看！"

    def has_permission(self, request, view):
        rights = request.redis_cache["rights"]
        if rights:
            if "0" in rights or "7" in rights:
                return True
            else:
                return False
        else:
            return False


# class LogsPermission(BasePermission):
#     """系统设置权限: 9"""
#
#     # 无权限的显示信息
#     message = "您没有权限查看！"
#
#     def has_permission(self, request, view):
#         rights = request.redis_cache["rights"]
#         if rights:
#             if "0" in rights or "9" in rights:
#                 return True
#             else:
#                 return False
#         else:
#             return False
