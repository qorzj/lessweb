import base64
import os
import hashlib
import time
import requests
import xml.etree.ElementTree as ET
import logging


# 统一下单接口
URL_ACCESS_TOKEN = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&"
URL_JS_TICKET = "https://api.weixin.qq.com/cgi-bin/ticket/getticket?"
UNIFIED_ORDER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"
SEND_REDPACK_URL = "https://api.mch.weixin.qq.com/mmpaymkttransfers/sendredpack"


class Weixin:
    appid: str
    appsecret: str
    mchid: str  # (支付必需)商户ID，微信商户平台(pay.weixin.qq.com)->产品中心->开发配置->商户号
    paykey: str  # (支付必需)签名用Key，微信商户平台(pay.weixin.qq.com)->账户中心->账户设置->API安全->密钥设置
    certpath: str  # (退款、发红包等必需)证书所在路径，此路径下需包含apiclient_cert.pem和apiclient_key.pem两个文件
    debug: bool  # 是否打印debug日志

    def __init__(self, *, appid, appsecret, mchid='', paykey='', certpath='', debug=False):
        self.appid = appid
        self.appsecret = appsecret
        self.mchid = mchid
        self.paykey = paykey
        self.debug = debug
        if certpath != '/' and certpath.endswith('/'):
            self.certpath = certpath[:-1]
        else:
            self.certpath = certpath

    @staticmethod
    def make_nonce():
        return base64.b64encode(os.urandom(40)).decode().replace('+', 'a').replace('/', 'd')[:32]

    def create_unified_order_sign(self, params):
        raw_str = '&'.join(k + '=' + str(v) for k, v in sorted(params.items()))
        raw_str += '&key=' + self.paykey
        return hashlib.md5(raw_str.encode()).hexdigest().upper()

    def create_unified_order_xml(self, params):
        xml = "<xml>\n" + \
              ''.join('  <{k}>{v}</{k}>\n'.format(k=k, v=v) for k, v in params.items()) + \
              "</xml>"
        return xml

    def debug_log(self, content):
        if self.debug:
            logging.debug(content)

    def request_prepay_and_get_jspay_sign(self, body, billno, fee, ip, openid, notifyurl):
        """
        :param body: 说明
        :param billno: 订单编号
        :param fee: 总费用（分）
        :param ip: 手机端IP
        :param openid: 微信用户openid
        :param notifyurl: 微信的回调URL
        :return 如果获取预支付ID成功则返回{package, nonce, timestamp, paySign}，否则返回None

        前端使用示例：
        function readyPay(billno) {
            $.ajax({
                type: 'post',
                url: '/your_readypay_api', //预支付请求
                data: {...},
                success:function(data){
                    //发起微信支付
                    wx.chooseWXPay({
                        timestamp: data.timestamp, // 支付签名时间戳，注意微信jssdk中的所有使用timestamp字段均为小写。但最新版的支付后台生成签名使用的timeStamp字段名需大写其中的S字符
                        nonceStr: data.nonce, // 支付签名随机串，不长于 32 位
                        package: data.package, // 统一支付接口返回的prepay_id参数值，提交格式如：prepay_id=***）
                        signType: 'MD5', // 签名方式，默认为'SHA1'，使用新版支付需传入'MD5'
                        paySign: data.paySign, // 支付签名
                        success: function (res) { /*支付成功后的回调函数*/ },
                        fail: function (res) { },
                        cancel: function (res) { }
                    });
                },
            });
        }
        """
        params = {
            'appid': self.appid,
            'mch_id': self.mchid,
            'nonce_str': self.make_nonce(),
            'body': body,
            'out_trade_no': billno,
            'total_fee': fee,
            'spbill_create_ip': ip,
            'notify_url': notifyurl,
            'trade_type': 'JSAPI',
            'openid': openid
        }
        params['sign'] = self.create_unified_order_sign(params)
        xml = self.create_unified_order_xml(params)
        self.debug_log('request: ' + xml)
        ret = requests.post(UNIFIED_ORDER_URL, data=xml.encode('utf-8'))
        ret.encoding = 'utf-8'
        self.debug_log('response: ' + ret.text)
        root = ET.fromstring(ret.text)
        node = root.find('prepay_id')
        if node is None:
            return {'error': ret.text}
        prepay_id = node.text
        nonce = self.make_nonce()
        timestamp = int(time.time())
        package_str = "prepay_id=" + prepay_id
        params = {
            'appId': self.appid,
            'nonceStr': nonce,
            'timeStamp': timestamp,
            'package': package_str,
            'signType': 'MD5',
        }
        paysign = self.create_unified_order_sign(params)
        return dict(
            package=package_str,
            nonce=nonce,
            timestamp=timestamp,
            paySign=paysign,
        )

    def send_redpack(self, billno, fee, ip, openid, send_name, wishing, act_name, remark):
        """
        # 官方文档： https://pay.weixin.qq.com/wiki/doc/api/tools/cash_coupon.php?chapter=13_4&index=3
        :param billno:
        :param fee:
        :param ip:
        :param openid: 接收红包的用户的openid
        :param send_name: 红包发送者名称
        :param wishing: 红包祝福语
        :param act_name: 活动名称
        :param remark: 备注信息
        :return: 返回{return_code, result_code}，含义参见官方文档
        """

        params = {
            'nonce_str': self.make_nonce(),
            'mch_billno': billno,
            'mch_id': self.mchid,
            'wxappid': self.appid,
            'send_name': send_name,
            're_openid': openid,
            'total_amount': fee,
            'total_num': '1',
            'wishing': wishing,
            'client_ip': ip,
            'act_name': act_name,
            'remark': remark,
        }
        params['sign'] = self.create_unified_order_sign(params)
        xml = self.create_unified_order_xml(params)
        logging.warning('req: ' + xml)
        ret = requests.post(SEND_REDPACK_URL, data=xml.encode('utf-8'),
                            cert=(f'{self.certpath}/apiclient_cert.pem', f'{self.certpath}/apiclient_key.pem'),
                            verify=True)
        ret.encoding = 'utf-8'
        logging.warning('rsp: ' + ret.text)
        root = ET.fromstring(ret.text)
        node = root.find('return_code')
        return_code = None if node is None else node.text
        node = root.find('result_code')
        result_code = None if node is None else node.text
        return {'return_code': return_code, 'result_code': result_code}

    def access_token(self):
        """
        获取新的access_token和多少秒后过期
        :return: {access_token, expires_in}
        """
        url = f"{URL_ACCESS_TOKEN}appid={self.appid}&secret={self.appsecret}"
        ret = requests.get(url)
        ret.encoding = 'utf-8'
        self.debug_log('response: ' + ret.text)
        obj = ret.json()
        access_token = obj['access_token']
        expires_in = obj['expires_in']
        return {'access_token': access_token, 'expires_in': expires_in}

    def js_ticket(self, access_token):
        """
        获取新的js_ticket和多少秒后过期
        :return: {js_ticket, expires_in}
        """
        url = f"{URL_JS_TICKET}access_token={access_token}&type=jsapi"
        self.debug_log('response: ' + url)
        ret = requests.get(url)
        ret.encoding = 'utf-8'
        self.debug_log('response: ' + ret.text)
        obj = ret.json()
        js_ticket = obj['ticket']
        expires_in = obj['expires_in']
        return {'js_ticket': js_ticket, 'expires_in': expires_in}

    def config_sign(self, js_ticket, url):
        """
        :return: 返回{appid, timestamp, nonce, sign}

        前端使用示例：
        var jsApiList = [ 'checkJsApi', 'onMenuShareTimeline', 'onMenuShareAppMessage', 'onMenuShareQQ',
            'onMenuShareWeibo', 'hideMenuItems', 'showMenuItems', 'hideAllNonBaseMenuItem', 'showAllNonBaseMenuItem',
            'getNetworkType', 'hideOptionMenu', 'showOptionMenu', 'closeWindow', 'chooseImage','previewImage',
            'uploadImage', 'downloadImage','scanQRCode', 'chooseWXPay', 'startRecord', 'stopRecord', 'playVoice'];
        $.post('/your_wx_config_api', {url: location.href}),
            function(data) {
                wx.config({
                    debug: false,
                    appId: data.appid,
                    timestamp: data.timestamp,
                    nonceStr: data.nonce,
                    signature: data.sign,
                    jsApiList: jsApiList
                });
            }
        )
        """
        nonce = self.make_nonce()
        timestamp = int(time.time())
        raw_str = f"jsapi_ticket={js_ticket}&noncestr={nonce}&timestamp={timestamp}&url={url}"
        sign = hashlib.sha1(raw_str.encode()).hexdigest().upper()
        return dict(
            appid=self.appid,
            timestamp=timestamp,
            nonce=nonce,
            sign=sign,
        )

    def payed(self, data: bytes):
        """
        # 官方文档：https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_1
        :return: 返回{return_content_type, return_content, appid, ..., transaction_id}

        注意：在回调接口收到微信的请求后，应返回return_content的文本，且Content-Type的header需设置为return_content_type的值。
        微信支付回调接口的请求数据是明文的xml(不强制要求https，也不需解密加密)，字段如下(含义参见官方文档)。
        b'<xml><appid><![CDATA[wx1ef0************c2]]></appid>\n
        <bank_type><![CDATA[CFT]]></bank_type>\n
        <cash_fee><![CDATA[1]]></cash_fee>\n
        <fee_type><![CDATA[CNY]]></fee_type>\n
        <is_subscribe><![CDATA[Y]]></is_subscribe>\n
        <mch_id><![CDATA[12******00]]></mch_id>\n
        <nonce_str><![CDATA[bjn20bSNWe2h************n3RIks6dz]]></nonce_str>\n
        <openid><![CDATA[otMXzjlNNMr************p4t7U]]></openid>\n
        <out_trade_no><![CDATA[gp2018************02]]></out_trade_no>\n
        <result_code><![CDATA[SUCCESS]]></result_code>\n
        <return_code><![CDATA[SUCCESS]]></return_code>\n
        <sign><![CDATA[0E7869564E563B****************6ECE]]></sign>\n
        <time_end><![CDATA[20180409123456]]></time_end>\n
        <total_fee>1</total_fee>\n
        <trade_type><![CDATA[JSAPI]]></trade_type>\n
        <transaction_id><![CDATA[4200000073201804**********60]]></transaction_id>\n</xml>'
        """
        self.debug_log('payed: ' + repr(data))
        root = ET.fromstring(data)
        ret = {
            'return_content_type': 'text/xml;charset=utf-8',
            'return_content': '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>',
        }
        for key in ['appid', 'bank_type', 'cash_fee', 'fee_type', 'is_subscribe', 'mch_id',
                    'nonce_str', 'openid', 'out_trade_no', 'result_code', 'return_code',
                    'sign', 'time_end', 'total_fee', 'trade_type', 'transaction_id',]:
            ret[key] = root.find(key).text
        return ret
