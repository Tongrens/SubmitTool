import time
import json
import base64
import requests
from PIL import Image
from io import BytesIO


class SubmitTool:
    def __init__(self, eid, access_token):
        self.extra_info, self.req_info, self.auto_fill_flag = {}, [], True
        self.access_token, self.eid = access_token, eid
        self.get_user_info_url = f'{base_url}/v1/userinfo?access_token={self.access_token}'
        self.get_info_url = f'{base_url}/v1/req_detail?access_token={self.access_token}&eid={self.eid}'
        self.post_url = f'{base_url}/v5/enroll'

    # 获取用户已保存数据(extra_info)
    def get_user_info(self):
        user_info = json.loads(requests.get(self.get_user_info_url).text)
        for i in user_info['data']['extra_info']:
            if isinstance(i['name'], list):  # 判断name是否为列表
                for j in i['name']:
                    self.extra_info[j] = i['value']
            else:
                self.extra_info[i['name']] = i['value']
        print('当前已保存用户信息：')
        for i in self.extra_info:
            print(f'{i}：{self.extra_info[i]}')
        if input('是否需要添加用户信息？(y/n)').lower() == 'y':
            print('请输入需要添加的信息(eg:\'姓名:张三\'),输入\'end\'结束')
            while (tmp := input()) != 'end':
                tmp = tmp if ':' in tmp else print('输入格式错误')
                if tmp:
                    self.extra_info[tmp.split(':')[0]] = tmp.split(':')[1]
            print('当前已保存用户信息：')
            for i in self.extra_info:
                print(f'{i}：{self.extra_info[i]}')
        if input('若出现已保存信息外的内容是否提交时手动填写？(y/n)').lower() == 'y':
            self.auto_fill_flag = False

    # 获取需要提交的数据并制作提交的字典(req_info)
    def get_info(self):
        try:
            info = json.loads(requests.get(self.get_info_url).text)  # 获取提交的数据
        except json.decoder.JSONDecodeError:
            print('获取数据失败，将再次获取')
            return False
        for i in info['data']['req_info']:
            # 判断是否需要在提交时手动填写
            tmp = self.extra_info[i['field_name']] if i['field_name'] in self.extra_info else \
                ('12345678910' if self.auto_fill_flag else input(f"请输入{i['field_name']}："))
            # 构造提交的字典
            self.req_info.append({"field_name": i['field_name'], "field_value": tmp,
                                  "field_key": i["field_key"]})
        return True if self.req_info else False

    # 提交数据(req_info)
    def post(self):
        body = {"access_token": self.access_token, "eid": self.eid, "info": self.req_info,
                "on_behalf": 0, "items": [], "referer": "", "fee_type": ""}
        return_info = json.loads(requests.post(self.post_url, json=body).text)
        if not return_info['sta']:  # 提交成功返回的sta为0，不成功为-1
            print(time.strftime("%H:%M:%S", time.localtime()) + '提交成功')
            return True
        else:
            if return_info['msg'] == '活动期间，只允许提交1次':  # 超过限制为已提交，不需要再次运行
                print('活动期间，只允许提交1次')
                return True
            else:
                print(f"提交失败，返回信息：{return_info['msg']}")
                return False

    # 类主入口
    def main(self):
        self.get_user_info()
        while True:
            if self.get_info():  # 判断获取需要提交的数据是否为空(未开始的数据为空)
                if self.post():  # 若提交成功或超过限制则结束，否则再次获取需要提交的数据并进行提交
                    break
            else:
                print('报名未开始')


class GetToken:
    def __init__(self):
        self.get_qr_url = f'{base_url}_web/v1/pc_code'
        self.qr_login_url = f'{base_url}_web/v1/pc_login?code='
        self.phone_login_url = f'{base_url}/v1/login_by_phone'
        self.get_history_url = f'{base_url}/v1/user/history?access_token='

    # 通过qr码方式登录
    def get_token_qr(self):
        result = json.loads(requests.get(self.get_qr_url).text)  # 获取qr码及对应code
        code = result['data']['code']
        image = Image.open(BytesIO(base64.b64decode(result['data']['qrcode'][22:])))
        print('请使用微信扫码登录')
        image.show()
        while True:  # 循环判断登录是否成功，未登录sta为-1，登录成功为0并返回access_token
            login_data = json.loads(requests.get(self.qr_login_url + code).text)
            if not login_data['sta']:
                print('登录成功！')
                return login_data['data']['access_token']
            print('等待登录...')
            time.sleep(1)

    # 通过手机号及密码方式登录
    def get_token_phone(self):
        phone = input('请输入手机号：')
        password = input('请输入密码：')
        data = {"phone": phone, "password": password}
        res = json.loads(requests.post(self.phone_login_url, json=data).text)
        if res['sta'] == -1:
            print(f"登录失败，{res['msg']}")
            return None
        else:
            return res['data']['access_token']

    # 类主入口
    def main(self):
        # 登录
        while True:
            login_type = input('请选择登录方式(1.二维码登录 2.手机号登录)：')
            if login_type == '1':
                token = self.get_token_qr()
                break
            if login_type == '2':
                token = self.get_token_phone()
                break
            print('输入错误，请重新输入')
        if not token:
            return
        # 获取个人历史记录
        result = json.loads(requests.get(self.get_history_url + token).text)
        history_data = []
        for i in result['data']:
            if i['status'] < 2:  # status状态码：0(未开始) 1(进行中) 2(已截至)
                history_data.append({'name': i['title'], 'status': '进行中' if i['status'] else '未开始', 'eid': i['eid']})
        if not history_data:
            print('请将需要提交的报名添加到个人记录中再运行程序')
            return
        else:
            print('请选择需要提交的表单序号')
        for i in range(len(history_data)):
            print(f"序号：{i + 1}\t\t名称：{history_data[i]['name']}\t\t状态：{history_data[i]['status']}")
        while True:
            user_input = input('请输入序号：')
            if user_input.isnumeric() and 0 < int(user_input) <= len(history_data):
                SubmitTool(history_data[int(user_input) - 1]['eid'], token).main()  # 选择eid并进行提交
                break
            else:
                print('请输入正确的序号')


# 主入口
if __name__ == '__main__':
    base_url = 'https://api-xcx-qunsou.weiyoubot.cn/xcx/enroll'
    main = GetToken()
    main.main()
    input('按回车退出...')
