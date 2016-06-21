#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time


class Traffice(object):
    def __init__(self):
        # 端口总流量字典
        self.port_traffic_dict = {}
        # 端口间隔流量字典
        self.port_traffic_day_dict = {}
        # 配置文件名
        self.conf_file_name = 'conf'
        # 临时文件名
        self.dict_dump_file_name = 'dict.dump'
        # 总量log文件名
        self.traffic_all_log = 'traffic.log'
        # 间隔量log文件名
        self.traffic_day_log = 'traffic_day.log'
        # 取值间隔
        self.sleep_time = 1800
        # 取值次数写入log
        self.cycles = 48
        # 主机ip
        self.host_ip = '192.168.1.1'

    def port_traffic(self):
        """"读取配置或临时文件 获取端口 流量字典"""
        if os.path.exists(self.dict_dump_file_name):
            # 临时文件存在则读取临时文件
            with open(self.dict_dump_file_name, 'r') as f:
                for i in f.readlines():
                    i = i.split(' ')
                    self.port_traffic_dict[int(i[0])] = int(i[1].strip('\n'))
        elif os.path.exists(self.conf_file_name):
            # 读取配置文件
            with open(self.conf_file_name, 'r') as f:
                for i in f.readlines():
                    i = i.strip()
                    self.port_traffic_dict[int(i)] = 0
        else:
            # 程序异常退出
            print('找不到配置文件！')
            exit()

    @staticmethod
    def shell_command(command):
        return os.popen(command)

    def iptables_rules(self):
        """清空规则并添加规则"""
        traffic_f = 'iptables -F OUTPUT'
        # 清空OUTPUT链规则
        self.shell_command(traffic_f)
        # 添加规则
        for k in self.port_traffic_dict:
            add_rules = 'iptables -A OUTPUT -s %s/32 -p tcp -m tcp --sport %d' % (self.host_ip, k)
            self.shell_command(add_rules)

    def traffic_day(self):
        for k in self.port_traffic_dict:
            self.port_traffic_day_dict[k] = 0

    def traffic_sum(self):
        """获取流量值并相加放入字典"""
        for k in self.port_traffic_dict:
            # 流量
            port_traffic_value = int(self.port_traffic_dict[k])
            port_traffic_day_value = int(self.port_traffic_day_dict[k])
            # 获取流量shell语句
            o = "iptables -nvxL -t filter |grep -w 'spt:%d' |awk -F' ' '{print $2}'" % k
            # 获取流量值
            result = self.shell_command(o)
            result_str = result.read()
            if result_str:
                k_traffic = int(result_str)
            else:
                k_traffic = 0
            # 加上流量值
            port_traffic_value += k_traffic
            port_traffic_day_value += k_traffic
            # 添加到字典
            self.port_traffic_dict[k] = port_traffic_value
            self.port_traffic_day_dict[k] = port_traffic_day_value

    def dump_dict(self):
        """端口流量写入到文件"""
        dict_dump_file_list = []
        for k in self.port_traffic_dict:
            value = "%s %s\n" % (k, self.port_traffic_dict[k])
            dict_dump_file_list.append(value)
        with open(self.dict_dump_file_name, 'w') as f:
            for i in dict_dump_file_list:
                f.write(i)

    def write_list(self):
        """要写入日志的列表"""
        traffic_all_log_list = [self.traffic_all_log, self.port_traffic_dict]
        traffic_day_log_list = [self.traffic_day_log, self.port_traffic_day_dict]
        return traffic_all_log_list, traffic_day_log_list

    def write_log(self):
        """写入日志"""
        write_list_return = self.write_list()
        for i in range(len(write_list_return)):
            write_list = write_list_return[i]
            file_name = write_list[0]
            file_dict = write_list[1]
            if os.path.exists(file_name):
                a = '\n'
            else:
                a = ''
            # 获取当前日期
            log_time = '%s%s\n' % (a, time.strftime('%Y-%m-%d %H:%M:%S'))
            # 写入文件
            with open(file_name, 'a') as f:
                f.write(log_time)
                file_dict = sorted(file_dict.items(), key=lambda x: x[0])
                for k in file_dict:
                    # 转换成MB,并保留小数两位
                    value_ai = round((k[1] / 1024 / 1024), 2)
                    f.write("%s:%sMB; " % (k[0], value_ai))

    def run(self):
        # 读取配置或临时文件 获取端口 流量字典
        self.port_traffic()
        while True:
            # 间隔流量字典置空添加
            self.traffic_day()
            for _ in range(self.cycles):
                # 清空规则并添加规则
                self.iptables_rules()
                # 睡眠等结果
                time.sleep(self.sleep_time)
                # 获取流量值并相加放入字典
                self.traffic_sum()
                # 端口流量写入到临时文件
                self.dump_dict()
            # 写入日志
            self.write_log()

if __name__ == '__main__':
    traffic = Traffice()
    traffic.run()
