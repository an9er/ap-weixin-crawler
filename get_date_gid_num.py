#!/usr/bin/python
# encoding=utf8


import re
import json
import requests


class PatchSimple(object):
    def __init__(self, url):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 2.3.6; zh-cn; GT-S5660 Build/GINGERBREAD) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1 MicroMessenger/4.5.255'}
        self.p_url = url

    def parse_key_from_squid(self):
        lines = open(self.logfile).readlines()
        lines.reverse()
        p = re.compile(r'__biz=([^&]+).*?uin=([^& ]+).*?key=([^& ]+)')
        for l in lines:
            m = p.findall(l)
            if not m:
                continue
            self.biz = m[0][0]
            self.uin = m[0][1]
            self.key = m[0][2]
            print 'parse_key_from_squid:', m[0]
            break

    @staticmethod
    def get_p_date(content):
        p_date = re.search(r'media_meta_text">(.*?)<', content).groups()[0]
        # year, month, day = re.search(r'media_meta_text">(\d*?)-(\d*?)-(\d*?)<', r.content'").groups()
        return p_date

    def get_p_author(self):
        author = re.search(r'rich_media_meta_nickname">(.*?)<\/sp', content).groups()[0]
        self.author = author


    def get_read_like_num(self):
        post_url = 'http://mp.weixin.qq.com/mp/getappmsgext'
        r = requests.post(post_url, headers=self.headers)
        j = json.loads(r.content)
        self.read_num = j[u'appmsgstat'][u'read_num']
        self.like_num = j[u'appmsgstat'][u'like_num']

    def mk_url(self):
        self.parse_key_from_squid()
        pre_url_2 = '&uin=%s&key=%s'
        pre_url = slef.p_url.replace('#wechat_redirect', '')
        self.num_url = pre_url + pre_url_2 % (self.uin, self.key)

    def get_author_and_date(self):
        self.mk_url()
        r = requests.get(self.num_url)
        open('nn.html', 'w').write(r.content)
        self.date = self.get_p_date(r.content)
        self.get_p_author()

    def start(self):
        self.get_author_and_date()
        self.get_read_like_num()
        self.push_db()

    def push_db(self):
        gzh_id = self.get_gzh_id(self.author)
        gzh_patch = {
                'p_date': self.date,
                'read_num': self.read_num,
                'like_num': self.like_num,
                'gzh_id': gzh_id,
                }
        db.item_to_table(gzh_patch)

    def get_gzh_id(self):
        sql = 'select gzh_id from wx_gzh where gzh_name=%s' % (name)
        return db.query(sql)[0]['gzh_id']

    def get_content(self):
        pass


def serve_urls(urls):
    for url in urls:
        ps = PatchSimple(url)
        ps.start()

def product_urls(urls):
    count = 0
    while count < 10000:
        urls = query_urls(count)
        yield urls
        count += 100


def query_urls():
    sql = 'select p_url from wx_post_simple where id >= %s and id < %s' % (count, count+100)
    return db.query(sql)[0]['p_url']


if __name__ == '__main__':
    for urls in product_urls():
        serve_urls()
