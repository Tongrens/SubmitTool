import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

base_url = 'https://api-xcx-qunsou.weiyoubot.cn/xcx/enroll'


def login_page(request):
    result = json.loads(requests.get(f'{base_url}_web/v1/pc_code').text)
    code = result['data']['code']
    image = result['data']['qrcode'][22:]
    return render(request, 'login_page.html', {'qr_image': image, 'code': code})


@csrf_exempt
def check_qr_login(request):
    correct_value, token = False, ''
    code = request.GET.get('code')[:-1]
    login_data = json.loads(requests.get(f'{base_url}_web/v1/pc_login?code=' + code).text)
    if not login_data['sta']:
        print(code + '登录成功！')
        correct_value = True
        token = login_data['data']['access_token']
    return JsonResponse({'correct_value': correct_value, 'token': token})


@csrf_exempt
def check_phone_login(request):
    correct_value, token, msg = False, '', ''
    phone = request.GET.get('phone')
    password = request.GET.get('password')[:-1]
    data = {"phone": phone, "password": password}
    res = json.loads(requests.post(f'{base_url}/v1/login_by_phone', json=data).text)
    if res['sta'] == -1:
        print(f"{phone}登录失败，{res['msg']}")
        msg = res['msg']
    else:
        correct_value = True
        token = res['data']['access_token']
    return JsonResponse({'correct_value': correct_value, 'token': token, 'msg': msg})
