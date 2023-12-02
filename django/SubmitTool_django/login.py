import json
import base64
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

base_url = 'https://api-xcx-qunsou.weiyoubot.cn/xcx/enroll'


def login_page(request):
    get_wx_qr_url = 'https://open.weixin.qq.com/connect/qrconnect?appid=wx8b6c33d344f46d19&' \
                    'scope=snsapi_login&redirect_uri=https%3A%2F%2Fbaominggongju.com%2Findex.html'
    # 获取微信登录二维码
    wx_qr_data = requests.get(get_wx_qr_url).text
    img_url = wx_qr_data.split('class="qrcode lightBorder" src="')[1].split('"')[0]
    uuid = img_url.split('qrcode/')[1]
    wxqr_image = base64.b64encode(requests.get(f'{"https://open.weixin.qq.com"}{img_url}').content).decode()
    # 获取公众号登录二维码
    result = json.loads(requests.get(f'{base_url}_web/v1/pc_code').text)
    code = result['data']['code']
    image = result['data']['qrcode'][22:]
    return render(request, 'login_page.html', {'qr_image': image, 'code': code, 'wxqr_image': wxqr_image, 'uuid': uuid})


@csrf_exempt
def check_qr_login(request):
    check_wxqr_url = 'https://lp.open.weixin.qq.com/connect/l/qrconnect?uuid='
    correct_value, token = False, ''
    code = request.GET.get('code')
    uuid = request.GET.get('uuid')[:-1]
    # 检查公众号登录
    login_data = json.loads(requests.get(f'{base_url}_web/v1/pc_login?code=' + code).text)
    if not login_data['sta']:
        print('qr_login:', code + '登录成功！')
        correct_value = True
        token = login_data['data']['access_token']
        return JsonResponse({'correct_value': correct_value, 'token': token})
    # 检查微信登录
    try:
        check_wxqr_data = requests.get(f'{check_wxqr_url}{uuid}', timeout=3).text
    except requests.exceptions.ReadTimeout:
        check_wxqr_data = ''
    if 'window.wx_errcode=405' in check_wxqr_data:
        print('wxqr_login:', uuid + '登录成功！')
        correct_value = True
        wxqr_token = check_wxqr_data.split("window.wx_code='")[1].split("'")[0]
        res = json.loads(requests.post(f'{base_url}_web/v1/login', json={"code": wxqr_token, 'source': 'pc'}).text)
        token = res['data']['access_token']
        return JsonResponse({'correct_value': correct_value, 'token': token})
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
