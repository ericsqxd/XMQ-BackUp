# -*- coding: utf-8 -*-
"""
实现了适应小密圈API特性的组件
"""

import json
import logging
from urllib.parse import urljoin, quote

from scrapy.http import TextResponse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import url_matches
from selenium.webdriver.support.wait import WebDriverWait

from xmq.settings import CHROME_DRIVER_PATH
from xmq.webdriver.expected_conditions import cookie_is_set, element_is_complete
from xmq.webdriver.support import AutoClosableChrome

logger = logging.getLogger(__name__)


class XmqApi(object):
    """
    小密圈API接口信息
    """

    URL_API = 'https://api.xiaomiquan.com/v1.7/'
    URL_LOGIN = 'https://wx.xiaomiquan.com/dweb/#/login'
    URL_GROUPS = urljoin(URL_API, 'groups')
    URL_TOPICS_FORMAT = urljoin(URL_API, 'groups/{group_id}/topics?count=20&end_time={end_time}')

    # headers中access_token的字段名
    HEADER_TOKEN_FIELD = 'authorization'

    @staticmethod
    def URL_TOPICS(group_id, end_time=''):
        """
        话题数据API

        该API逻辑为，获取截止`end_time`时间最新的`count`条话题，
        并将最后一条话题的`create_time - 1ms`作为下次请求的`end_time`，
        为了避免对毫秒的处理，本项目直接使用`create_time`，并在返回结果中筛去。

        :param group_id: 圈子id
        :param end_time: 截止时间
        :return: 本次应请求的URL
        """
        return XmqApi.URL_TOPICS_FORMAT.format(group_id=group_id, end_time=quote(end_time))

    @staticmethod
    def get_access_token():
        """
        登录并获取access_token
        :param spider: 调用的spider
        :return: access_token
        """

        with AutoClosableChrome(CHROME_DRIVER_PATH) as driver:
            driver.get(XmqApi.URL_LOGIN)

            # 等待跳转至主页
            WebDriverWait(driver, 60).until(url_matches(r'index/\d+'))
            logger.info('登录成功')

            # 等待access_token加载完毕
            access_token = WebDriverWait(driver, 30).until(cookie_is_set('access_token'))
            access_token = access_token['value']

            # 等待头像加载完毕
            # 直接返回的token是不合法的，需要等待浏览器提交某请求使其合法，而该提交先于头像的加载
            # TODO: 似乎是加密了，有空再分析该请求
            avatar_complete = element_is_complete((By.CSS_SELECTOR, 'p.avastar-p img'))
            WebDriverWait(driver, 30).until(avatar_complete)

            logger.info('access_token加载成功: %s' % access_token)

            return access_token


class XmqApiResponse(TextResponse):
    """
    小密圈API的Response
    """

    def __init__(self, *args, **kwargs):
        super(XmqApiResponse, self).__init__(*args, **kwargs)
        if not self.url.startswith(XmqApi.URL_API):
            raise TypeError("不是来自API接口的请求: %s" % self.url)
        self.json = json.loads(self.text)

    @property
    def data(self):
        return self.json.get('resp_data')

    @property
    def code(self):
        return self.json.get('code')
