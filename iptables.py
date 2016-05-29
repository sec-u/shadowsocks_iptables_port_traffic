#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time


class Traffice(object):
    def __init__(self):
        # 端口流量字典
        self.port_traffic_dict = {}
        # 配置文件名
        self.conf_file_name = 'conf'
        # 临时文件名
        self.dict_dump_file_name = 'dict.dump'
        # 取值间隔
        self.sleep_time = 1800
        # 主机ip
        self.host_ip = '192.168.1.1'

    def port_traffic(self):
        """"读取配置或临时文件 获取端口 流量字典"""
        if os.path.exists(self.dict_dump_file_name):
            # 临时文件存在则读取临时文件
            with open(self.dict_dump_file_name, 'r') as f:
                for i in f.readlines():
                    i = i.split(' ')
                    self.port_traffic_dict[i[0]] = i[1].strip('\n')
        elif os.path.exists(self.conf_file_name):
            # 读取配置文件
            with open(self.conf_file_name, 'r') as f:
                for i in f.readlines():
                    i = i.strip()
                    self.port_traffic_dict[i] = 0
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
            add_rules = 'iptables -A OUTPUT -s %s/32 -p tcp -m tcp --sport %s' % (self.host_ip, k)
            self.shell_command(add_rules)

    def traffic_sum(self):
        """获取流量值并相加放入字典"""
        for k in self.port_traffic_dict:
            # 流量
            port_traffic_value = int(self.port_traffic_dict[k])
            # 获取流量shell语句
            o = "iptables -nvxL -t filter |grep -i 'spt:%s' |awk -F' ' '{print $2}'" % k
            # 获取流量值
            result = self.shell_command(o)
            k_traffic = int(result.read())
            # 加上流量值
            port_traffic_value += k_traffic
            self.port_traffic_dict[k] = port_traffic_value  # 添加到字典里面


    def dump_dict(self):
        """端口流量写入到文件"""
        dict_dump_file_list = []
        for k in self.port_traffic_dict:
            value = "%s %s\n" %(k, self.port_traffic_dict[k])
            dict_dump_file_list.append(value)
        with open(self.dict_dump_file_name, 'w') as f:
            for i in dict_dump_file_list:
                f.write(i)

    def write_log(self):
        """写入日志"""
        if os.path.exists('traffic.log'):
            a = '\n'
        else:
            a = ''
        # 获取当前日期
        log_time = '%s%s\n' %(a, time.strftime('%Y-%m-%d %H:%M:%S'),)
        # 写入文件
        with open('traffic.log', 'a') as f:
            f.write(log_time)
            for k in self.port_traffic_dict:
                # 转换成MB,并保留小数两位
                value_ai = round((self.port_traffic_dict[k] / 1024 / 1024), 2)
                f.write("%s:%sMB; " % (k, value_ai))
    
    def run(self):
        # 读取配置或临时文件 获取端口 流量字典
        self.port_traffic()
        while True:
            for i in list(range(48)):
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
