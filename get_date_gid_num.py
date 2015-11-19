#!/usr/bin/python
# encoding=utf8


import re
import json
import requests


class PatchSimple(object):
    def __init__(self, url, key):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 2.3.6; zh-cn; GT-S5660 Build/GINGERBREAD) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1 MicroMessenger/4.5.255'}

    def get_gzh_name(self):
        pass

    @staticmethod
    def get_p_date(content):
        p_date = re.search(r'media_meta_text">(.*?)<', content).groups()[0]
        # year, month, day = re.search(r'media_meta_text">(\d*?)-(\d*?)-(\d*?)<', r.content'").groups()
        return p_date

    def get_read_like_num():
        post_url = 'http://mp.weixin.qq.com/mp/getappmsgext'
        r = requests.post(post_url, headers=self.headers)
        j = json.loads(r.content)
        self.read_num = j[u'appmsgstat'][u'read_num']
        self.like_num = j[u'appmsgstat'][u'like_num']




    def get_content(self):
        pass
