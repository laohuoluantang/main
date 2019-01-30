import os, re, time, configparser, threading, operator, subprocess
''''

#功能选择，0：抓包， 1：安装版本， 2：取日志
[FUNC_SELECT]
func = 0

#设备数量
[DEVICE_NUM]
num = 1

#设备类型：M3S M4S为1，其余为0，后缀作为不同设备区分
[DEVICE_TYPE]
type_0 = 1
type_1 = 0

#设备ip，后缀作为不同设备区分
[DEVICE_IP]
ip_0 = 20.1.88.192:5555
ip_1 = 20.1.88.193:5555

#本地log地址
[LOG_BASE_DIR]
base_dir = D:\test_log\

'''
#adb需要添加到系统环境变量
#M3S M4S
adb_M3_4S_cmd = 'cd /data/data/com.homedoor2.tvlauncher/files && chmod 777 tcpdump && tcpdump -i any -p -s 0 -G 10 -w /sdcard/998.pcap && exit'

class Self_def_shell(object):
    def run_cmd(self, cmd) :
        res = subprocess.Popen(cmd, shell = False, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        time.sleep(1)
        return res

# 检查所有设备是否连接成功，需配置文件中的所有设备连接后返回True
def devices_connect_check(cfg_devices_ip_list_sorted):
    devices_connect_mes = os.popen('adb devices').read()
    if re.search('offline', devices_connect_mes) != None:
        return False, devices_connect_mes
    pattern_ip = re.compile(r'\d\S+')  # 查找数字，忽略换行
    devices_connect_mes_list_sorted = sorted(pattern_ip.findall(devices_connect_mes))
    return operator.eq(devices_connect_mes_list_sorted, cfg_devices_ip_list_sorted), devices_connect_mes

# 连接/断开配置文件中的设备
def devices_connect_dis(devices_ip_list, flag = True):
    for i in devices_ip_list:
        shell = Self_def_shell()
        if flag:
            shell.run_cmd('adb connect %s' % i)
            print("连接%s" % str(i) + '设备')
        else:
            shell.run_cmd('adb disconnect %s' % i)
            print("断开%s" % str(i) + '设备')
        time.sleep(1)

'''
type 设备类型
ip_addr 设备ip
tcpdump_time 抓包时长
time_flag 时间标志，用于区分抓包文件
'''
def excute(func_select, type, ip_addr, tcpdump_time, log_dir, device_num, apk_dir):
    if func_select == '0':
        time_now = str(time.strftime("%Y%m%d%H%M%S", time.localtime()))
        shell_generate_pcap = Self_def_shell()
        if type == '1':
            cmd = r'adb -s ' + ip_addr + r' shell cd /data/data/com.homedoor2.tvlauncher/files && chmod 777 tcpdump && tcpdump -i any -p -s 0 ' + r' -w /sdcard/' + time_now + r'.pcap '
        if type == '0':
            cmd = r'adb -s ' + ip_addr + r' shell cd /data/data/com.homedoor2.tvlauncher/files && chmod 777 tcpdump && ./tcpdump -i any -p -s 0 ' + r' -w /sdcard/' + time_now + r'.pcap'
        shell_generate_pcap.run_cmd(cmd)
        print('等待设备'+ device_num + "抓包 抓包时长%s秒"%tcpdump_time)
        time.sleep(int(tcpdump_time))
        shell_kill_tcpdump = Self_def_shell()
        kill_cmd = r'adb -s ' + ip_addr + r' shell busybox killall tcpdump'
        shell_kill_tcpdump.run_cmd(kill_cmd)
        print('取回' + ip_addr + '抓包文件中')
        shell_pull_pcap = Self_def_shell()
        ret = shell_pull_pcap.run_cmd(r'adb -s ' + ip_addr +' pull -a /sdcard/' + time_now + r'.pcap ' + log_dir)
        print(ret.stdout.read())
        print('删除' + ip_addr + '盒子内部抓包数据中')
        shell_rm_pcap = Self_def_shell()
        ret = shell_rm_pcap.run_cmd(r'adb -s ' + ip_addr + r' shell cd /sdcard && rm ' + time_now + r'.pcap')
        print(ret.stdout.read())

    if func_select == '1':
        print('设备' + device_num + '安装中')
        shell_install_apk = Self_def_shell()
        cmd = r'adb -s ' + ip_addr + r' install -r ' + apk_dir
        ret = shell_install_apk.run_cmd(cmd)
        print(ret.stdout.read())

    if func_select == '2':
        print('设备' + device_num + '取回日志中')
        shell_get_mx_log = Self_def_shell()
        cmd_mx_log = r'adb -s ' + ip_addr + r' pull -a /sdcard/MXlog ' + log_dir
        ret = shell_get_mx_log.run_cmd(cmd_mx_log)
        print(ret.stdout.read())
        shell_get_anr_log = Self_def_shell()
        cmd_anr = r'adb -s ' + ip_addr + r' pull -a /data/anr ' + log_dir
        ret = shell_get_mx_log.run_cmd(cmd_anr)
        print(ret.stdout.read())


if __name__ == '__main__':
    #配置文件读取
    cfg = configparser.ConfigParser()
    cfg.readfp(open('cfg.ini', encoding='UTF-8'))
    device_num = cfg.get('DEVICE_NUM', 'num')
    base_dir = cfg.get('LOG_BASE_DIR', 'base_dir')
    func_select = cfg.get('FUNC_SELECT', 'func_select')
    apk_dir = cfg.get('APK_DIR', 'apk_dir')
    #excute参数构造
    log_dir_list = list(map(lambda i: str(base_dir) + str(i), range(0, int(device_num))))
    devices_ip_list = list(map(lambda i: cfg.get('DEVICE_IP', 'ip_' + str(i)), range(0, int(device_num))))
    devices_type_list = list(map(lambda i: cfg.get('DEVICE_TYPE', 'type_' + str(i)), range(0, int(device_num))))
    tcpdump_time_list = list(map(lambda i: cfg.get('DEVICE_TCPDUMP_TIME', 'dev_time_' + str(i)), range(0, int(device_num))))

    #连接设备
    devices_connect_dis(devices_ip_list)

    # 检查设备连接
    connect_mes = devices_connect_check(sorted(devices_ip_list))
    if connect_mes[0] == True:
        print("设备连接检查成功")

        #创建log文件夹
        for i in range(0, int(device_num)):
            if (not (os.path.exists(str(base_dir) + str(i)))):
                os.makedirs(str(base_dir) + str(i))
                print('创建文件夹%s成功' % str(i) )
            else:
                print('文件夹%s已存在' % str(i))

        #测试指令创建
        excute_commands = []
        for i in range(0, int(device_num)):
            cmd = [func_select, devices_type_list[i], devices_ip_list[i], tcpdump_time_list[i], log_dir_list[i], str(i), apk_dir]
            excute_commands.append(cmd)

        threads = []
        threads_count = len(excute_commands)

        #创建测试线程
        for i in range(threads_count):
            t = threading.Thread(target = excute, args=(*excute_commands[i], ))
            threads.append(t)
            print('thread' + str(i) + ' append')

        for i in range(threads_count):
            time.sleep(1)
            threads[i].start()
            print('thread' + str(i) + ' start')

        for i in range(threads_count):
            threads[i].join()
            print('thread' + str(i) + ' join')

        if (func_select == '2' or func_select == '0'):
            devices_connect_dis(devices_ip_list, False)

    else:
        devices_connect_dis(devices_ip_list, False)
        print("设备连接错误 连接状态")
        print(connect_mes[1])
        os.system("error")
