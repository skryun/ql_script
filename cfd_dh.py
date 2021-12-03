"""
cron: 58 59 * * * *
new Env('财富岛兑换红包');
"""

import os
import re
import time
import json
import datetime
import requests

from jd_ua import get_ua
from ql_util import get_envs, disable_env, post_envs, put_envs

# 默认配置(看不懂代码也勿动)
cfd_start_time = 1.85
cfd_offset_time = 0.01

# 基础配置勿动
cfd_start_dist = None
cfd_url = "https://wq.jd.com/jxbfd/user/ExchangePrize?strZone=jxbfd&bizCode=jxbfd&source=jxbfd&dwEnv=4&_cfd_t=1638501821589&ptag=139254.28.26&dwType=3&dwLvl=1&ddwPaperMoney=100000&strPoolName=jxcfd2_exchange_hb_202112&strPgtimestamp=&strPhoneID=&strPgUUNum=&_stk=_cfd_t%2CbizCode%2CddwPaperMoney%2CdwEnv%2CdwLvl%2CdwType%2Cptag%2Csource%2CstrPgUUNum%2CstrPgtimestamp%2CstrPhoneID%2CstrPoolName%2CstrZone&_ste=1&h5st=20211203112341589%3B5624054658696163%3B10032%3Btk01wcfb11ce030nXwVtxFiVx1njFlIiZFrJzYanM9NPvLx90Q1LmUN5yxgZK3r11ZmOzgo%2B3ZnOr62Upv7enih0YljV%3Bb3aa8fe40a1bdce343641d37d1be89a971b3144ec7d6808be91f5120f82a0b96&_=1638501821591&sceneval=2&g_login_type=1&callback=jsonpCBKBB&g_ty=ls"
pin = "null"
u_ck_list = []
pattern_pin = re.compile(r'pt_pin=([\w\W]*?);')
pattern_data = re.compile(r'\(([\w\W]*?)\)')

print("- 参数初始化")

# 从配置文件获取url
cfd_url = os.getenv("CFD_URL", cfd_url)

# 获取cookie
cookies = get_envs("CFD_COOKIE")
for ck in cookies:
    if ck.get('status') == 0:
        u_ck_list.append(ck)
if len(u_ck_list) >= 1:
    cookie = u_ck_list[0]
    re_ck_list = pattern_pin.search(cookie.get('value'))
    if re_ck_list is not None:
        pin = re_ck_list.group(1)
    print('共配置{}条CK,已载入用户[{}]'.format(len(u_ck_list), pin))
else:
    print('共配置{}条CK,请添加环境变量,或查看环境变量状态'.format(len(u_ck_list)))
    cookie = None

# 获取配置
cfd_start_times = get_envs("CFD_START")
if len(cfd_start_times) >= 1:
    cfd_start_dist = cfd_start_times[0]
    cfd_start_time = float(cfd_start_dist.get('value'))
    print('从环境变量中载入CFD_START[{}]'.format(cfd_start_time))
else:
    u_data = post_envs('CFD_START', str(cfd_start_time), '财富岛兑换时间配置,自动生成,勿动')
    if len(u_data) == 1:
        cfd_start_dist = u_data[0]
    print('从默认配置中载入CFD_START[{}]'.format(cfd_start_time))

print("- 初始化结束\n")


def cfd_qq(def_start_time):
    # 进行时间等待,然后发送请求
    end_time = time.time()
    while end_time < def_start_time:
        end_time = time.time()
    # 记录请求时间,发送请求
    t1 = time.time()
    d1 = datetime.datetime.now().strftime("%M:%S.%f")
    res = requests.get(cfd_url, headers=headers)
    t2 = time.time()
    # 正则对结果进行提取
    re_data_list = pattern_data.search(res.text)
    # 进行json转换
    data = json.loads(re_data_list.group(1))
    msg = data['sErrMsg']
    # 根据返回值判断
    if data['iRet'] == 0:
        # 抢到
        msg = "可能抢到了"
        put_envs(cookie.get('_id'), cookie.get('name'), cookie.get('value'), msg)
        disable_env(cookie.get('_id'))
    elif data['iRet'] == 2016:
        # 需要减
        start_time = float(cfd_start_time) - float(cfd_offset_time)
        put_envs(cfd_start_dist.get('_id'), cfd_start_dist.get('name'), str(start_time)[:8])
    elif data['iRet'] == 2013:
        # 需要加
        start_time = float(cfd_start_time) + float(cfd_offset_time)
        put_envs(cfd_start_dist.get('_id'), cfd_start_dist.get('name'), str(start_time)[:8])
    elif data['iRet'] == 1014:
        # URL过期
        pass
    elif data['iRet'] == 2007:
        # 财富值不够
        put_envs(cookie.get('_id'), cookie.get('name'), cookie.get('value'), msg)
        disable_env(cookie.get('_id'))
    elif data['iRet'] == 9999:
        # 账号过期
        put_envs(cookie.get('_id'), cookie.get('name'), cookie.get('value'), msg)
        disable_env(cookie.get('_id'))
    print("实际发送[{}]\n耗时[{:.3f}]\n用户[{}]\n结果[{}]".format(d1, (t2 - t1), pin, msg))


if __name__ == '__main__':
    print("- 主逻辑程序进入")
    if cookie is None:
        print("未读取到CFD_COOKIE,程序强制结束")
        exit()
    headers = {
        'Host': 'wq.jd.com',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Cookie': cookie['value'],
        'User-Agent': get_ua(),
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Referer': 'https://wqs.jd.com/',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    u_start_time = float(int(time.time()) + float(cfd_start_time))
    print("预计发送时间为[{}]".format(datetime.datetime.utcfromtimestamp(u_start_time).strftime("%M:%S.%f")))
    cfd_qq(u_start_time)
    print("- 主逻辑程序结束")
