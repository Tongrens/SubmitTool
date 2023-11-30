import json
import time
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

base_url = 'https://api-xcx-qunsou.weiyoubot.cn/xcx/enroll'


def get_history_data(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'dashboard_page.html')
    result = json.loads(requests.get(f'{base_url}/v1/user/history?access_token=' + token).text)
    history_data, extra_info = [], {}
    # 获取历史记录
    for i in result['data']:
        if i['status'] < 2:  # status状态码：0(未开始) 1(进行中) 2(已截至)
            history_data.append({'name': i['title'], 'status': '进行中' if i['status'] else '未开始', 'eid': i['eid']})
    # 获取用户信息
    user_info = json.loads(requests.get(f'{base_url}/v1/userinfo?access_token={token}').text)
    for i in user_info['data']['extra_info']:
        if isinstance(i['name'], list):  # 判断name是否为列表
            for j in i['name']:
                extra_info[j] = i['value']
        else:
            extra_info[i['name']] = i['value']

    return render(request, 'dashboard_page.html',
                  {'history_data': history_data, 'extra_info': extra_info, 'token': token})


@csrf_exempt
def put_info(request):
    data = json.loads(request.body)
    eid = data['eid']
    access_token = data['token']
    extra_info = data['extra_info']
    auto_fill_flag = data['auto_fill_flag']
    if data.get('need_fill'):
        extra_info.extend(data['need_fill'])
    req_info, need_fill, info = [], [], ''
    # 获取报名信息
    try:
        info = json.loads(requests.get(f'{base_url}/v1/req_detail?access_token={access_token}&eid={eid}').text)
    except json.decoder.JSONDecodeError:
        print(access_token + '获取数据失败，将再次获取')
        return JsonResponse({'sta': False, 'msg': '获取数据失败，将再次获取', 'data': data})
    for i in info['data']['req_info']:
        # 判断是否需要在提交时手动填写
        tmp = ''
        if i['field_name'] in extra_info:
            tmp = extra_info[i['field_name']]
        else:
            if not auto_fill_flag:
                tmp = '12345678910'
            else:
                need_fill.append(i['field_name'])
        # 构造提交的字典
        req_info.append({"field_name": i['field_name'], "field_value": tmp,
                         "field_key": i["field_key"]})
    if not req_info:
        return JsonResponse({'sta': False, 'msg': '报名未开始', 'data': data})
    if need_fill and auto_fill_flag:
        return JsonResponse({'sta': True, 'msg': '需要手动填写信息', 'data': data, 'need_fill': need_fill})
    # 提交数据
    body = {"access_token": access_token, "eid": eid, "info": req_info,
            "on_behalf": 0, "items": [], "referer": "", "fee_type": ""}
    return_info = json.loads(requests.post(f'{base_url}/v5/enroll', json=body).text)
    if not return_info['sta']:  # 提交成功返回的sta为0，不成功为-1
        print(access_token, time.strftime("%H:%M:%S", time.localtime()) + '提交成功！')
        return JsonResponse({'sta': True, 'msg': time.strftime("%H:%M:%S", time.localtime()) + '提交成功！'})
    else:
        if return_info['msg'] == '活动期间，只允许提交1次':  # 超过限制为已提交，不需要再次运行
            return JsonResponse({'sta': True, 'msg': '活动期间，只允许提交1次'})
        else:
            return JsonResponse({'sta': False, 'msg': return_info['msg'], 'data': data})
