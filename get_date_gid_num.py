#!/usr/bin/python
# encoding=utf8


import re
import json
import requests
import toolkitv
import dbconfig
import time
import htmlcontent
hc = htmlcontent.HtmlContentor()
from sentiment_weibo import get_sentiment

db = toolkitv.MySQLUtility(
    dbconfig.mysql_host,
    dbconfig.mysql_db,
    dbconfig.mysql_user,
    dbconfig.mysql_pass,
)
LOGFILE = '/var/log/squid3/access.log'


class PatchSimple(object):
    def __init__(self, url, url_hash):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 2.3.6; zh-cn; GT-S5660 Build/GINGERBREAD) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1 MicroMessenger/4.5.255'}
        self.p_url = url
        self.url_hash = url_hash

    def parse_key_from_squid(self):
        lines = open(LOGFILE).readlines()
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

    def get_p_author(self, content):
        author = re.search(r'rich_media_meta_nickname">(.*?)<\/sp', content).groups()[0]
        self.author = author

    def get_read_like_num(self):
        pre_post_url = self.num_url.replace('mp.weixin.qq.com/s', 'mp.weixin.qq.com/mp/getappmsgext')
        post_url = pre_post_url + '&f=json&uin=%s&key=%s' % (self.uin, self.key)
        print "[*] Post_url", post_url
        r = requests.post(post_url, headers=self.headers)
        time.sleep(1.3)
        if 'appmsgstat' not in r.content:
            self.wait_for_new_keys()
        j = json.loads(r.content)
        self.read_num = j[u'appmsgstat'][u'read_num']
        self.like_num = j[u'appmsgstat'][u'like_num']

    def wait_for_new_keys(self):
        print "[**] The key is invalied,and not find new key, sleep per 5s."
        while 1:
            self.parse_key_from_squid()
            if self.key != self.ori_key:
                self.ori_key = self.key
                print "[*] Get new key, continue work!"
                return
            else: print "wait new key"
            time.sleep(5)

    def mk_url(self):
        print self.p_url
        # self.parse_key_from_squid()
        # self.update_key()
        # pre_url_2 = '&uin=%s&key=%s'
        pre_url = self.p_url.replace('#wechat_redirect', '')
        self.num_url = pre_url
        # self.num_url = pre_url + pre_url_2 % (self.uin, self.key)

    def update_key(self):
        self.ori_key = self.key

    def get_content(self, content):
        _title, content = hc.get_content(content)
        if content is None:
            content = ''
        self.data = content

    def get_author_date_data_senti(self):
        self.mk_url()
        print "[*] num_url:", self.num_url
        try:
            r = requests.get(self.num_url)
        except:
            print "requests.get Error"
            raise
            # self.date = ''
            # self.author = ''
            # return
        time.sleep(1)

        with open('content.html', 'w') as f:
            f.write(r.content)

        try:
            self.date = self.get_p_date(r.content)
            self.get_p_author(r.content)
            self.get_content(r.content)
            self.sentiment = get_sentiment(self.data)
        except:
            print 222222222222222
            if '该内容已被发布者删除' in r.content:
                self.date = ''
                self.author = ''
            if '其转载来源已删除' in r.content:
                self.date = ''
                self.author = ''
            if '该内容已被发布者删除' in r.content:
                self.date = ''
                self.author = ''
            # else:
            #     self.date = ''
            #     self.author = ''
            raise

    def start(self):
        self.get_author_date_data_senti()
        # self.get_read_like_num()
        if self.author == '':
            print '删除'
            return
        self.update_db()

    def update_db(self):
        try:
            gzh_id = self.get_gzh_id(self.author)
            gzh_patch = {
                    'p_date': self.date,
                    'p_data': self.data,
                    # 'read_num': self.read_num,
                    # 'like_num': self.like_num,
                    'gzh_id': gzh_id,
                    'sentiment': self.sentiment
                    }
            print "gzh_patch:", len(gzh_patch['p_data'])
            db.update_table("wx_post_simple_huishi", gzh_patch, 'url_hash', self.url_hash)
        except Exception, e:
            print e
            print self.author
            raise

    def get_gzh_id(self, name):
        sql = 'select gzh_id from wx_gzh where gzh_name="%s"' % (name)
        print sql
        return db.query(sql)[0]['gzh_id']


def serve_urls(urls):
    for url in urls:
        ps = PatchSimple(url['p_url'], url['url_hash'])
        ps.start()


def product_urls():
    global COUNT, MAX_COUNT
    count = COUNT
    # while count > 2000:
    while count < MAX_COUNT:
        urls = query_urls(count)
        len_urls = len(urls)
        if len_urls != 0:
            open('sql_get.log', 'a').write(str(len_urls) + '\n')
            print "[*] Count:", count
            yield urls
        count += 100


def query_urls(count):
    # sql = 'select p_url, url_hash from wx_post_simple where id <= %s and id > %s' % (count, count-100)
    sql = 'select p_url, url_hash from wx_post_simple_huishi where id >= %s and id < %s ' % (count, count+100)
    # sql = 'select p_url, url_hash from wx_post_simple_huishi where id >= %s and id < %s and p_date is null' % (count, count+100)
    print sql
    open('sql_get.log', 'a').write(sql)
    ds =  db.query(sql)
    urls = []
    for d in ds:
        urls.append(d)
    return urls


# COUNT = 9999999999
COUNT = 0
MAX_COUNT = 1656
if __name__ == '__main__':
    from sys import argv
    global COUNT
    COUNT = int(argv[1])
    for urls in product_urls():
        print len(urls)
        serve_urls(urls)
