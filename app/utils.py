# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 上午12:51
# @Author  : sudoskys
# @File    : utils.py
# @Software: PyCharm
def parse_command(command):
    if not command:
        return None, None
    parts = command.split(" ", 1)
    if len(parts) > 1:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], None
    else:
        return None, None


def generate_uuid():
    import shortuuid

    return str(shortuuid.uuid())


def get_unix_time():
    import time

    return int(time.time())


def calculate_compound_interest(principal, rate, hours):
    """
    计算以小时为周期的复利
    :param principal: 初始本金
    :param rate: 年利率（百分比）
    :param hours: 计算的小时数
    :return: 最终金额
    """
    return principal * (1 + rate / 100 / 365 / 24) ** hours
