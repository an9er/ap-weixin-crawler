#!/usr/bin/python
# encoding=utf8


import re
import json
import requests
import toolkitv
import dbconfig
import time
import sys
import config

db = toolkitv.MySQLUtility(
    dbconfig.mysql_host,
    dbconfig.mysql_db,
    dbconfig.mysql_user,
    dbconfig.mysql_pass,
)
LOGFILE = '/var/log/squid3/access.log'
TABLE = config.table


class PatchSimple(object):
    def __init__(self, url):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 2.3.6; zh-cn; GT-S5660 Build/GINGERBREAD) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1 MicroMessenger/4.5.255'}
        self.p_url = url['p_url']
        self.url_hash = url['url_hash']
        self.gzh_id = url['gzh_id']
        self.id = url['id']

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
            # print '\rparse_key_from_squid:', m[0],
            sys.stdout.flush()
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
        if self.url_has_like_num():
            print 'has like num',
            return
        post_url = ''
        pre_post_url = ''
        pre_post_url = self.p_url.replace('#wechat_redirect', '')
        pre_post_url = pre_post_url.replace('mp.weixin.qq.com/s', 'mp.weixin.qq.com/mp/getappmsgext')
        # pre_post_url = self.num_url.replace('mp.weixin.qq.com/s', 'mp.weixin.qq.com/mp/getappmsgext')
        post_url = pre_post_url + '&f=json&uin=%s&key=%s' % (self.uin, self.key)
        # print "[*] Post_url", post_url
        gzh_name = self.get_gzh_name(self.gzh_id)
        print "[*] gzh_name:", gzh_name, self.id
        r = requests.post(post_url, headers=self.headers)
        time.sleep(2)
        if 'appmsgstat' not in r.content:
            time.sleep(10)
            self.wait_for_new_keys()
            print '-' * 10
            self.get_read_like_num()
            print '-' * 10
            return
        j = json.loads(r.content)
        self.read_num = j[u'appmsgstat'][u'read_num']
        self.like_num = j[u'appmsgstat'][u'like_num']
        self.update_db()

    def url_has_like_num(self):
        global TABLE
        sql = 'select read_num from %s where p_url="%s"' % (TABLE, self.p_url)
        if db.query(sql)[0]['read_num'] == None:
            return False
        return True
    def wait_for_new_keys(self):
        print "[**] The key is invalied,and not find new key, sleep per 5s."
        i = 0
        while 1:
            self.parse_key_from_squid()
            # print "ori_key:", self.ori_key
            # print "now_key:", self.key
            if self.key != self.ori_key:
                self.ori_key = self.key
                print "[*] Get new key, continue work!"
                return
            else:
                print "\rwait new key %s" % ('.'*i),
                sys.stdout.flush()
                time.sleep(10)
                i += 1

    def mk_url(self):
        print self.p_url
        self.parse_key_from_squid()
        self.update_key()
        pre_url_2 = '&uin=%s&key=%s'
        pre_url = self.p_url.replace('#wechat_redirect', '')
        self.num_url = pre_url + pre_url_2 % (self.uin, self.key)

    def update_key(self):
        self.ori_key = self.key

    def get_author_and_date(self):
        r = requests.get(self.num_url)
        time.sleep(1)
        open('content.html', 'w').write(r.content)
        try:
            self.date = self.get_p_date(r.content)
            self.get_p_author(r.content)
        except Exception, e:
            if '该内容已被发布者删除' in r.content:
                self.date = ''
                self.author = ''
            else:
                print Exception, e

    def start(self):
        self.mk_url()
        # print "[*] num_url:", self.num_url
        # self.get_author_and_date()
        self.get_read_like_num()

    def update_db(self):
        global TABLE
        try:
            # gzh_id = self.get_gzh_id(self.author)
            gzh_patch = {
                    # 'p_date': self.date,
                    'read_num': self.read_num,
                    'like_num': self.like_num,
                    # 'gzh_id': gzh_id,
                    }
            print "gzh_patch:", gzh_patch
            db.update_table(TABLE, gzh_patch, 'url_hash', self.url_hash)
        except Exception, e:
            print e
            print self.author

    @staticmethod
    def get_gzh_name(id):
        sql = 'select gzh_name from wx_gzh where gzh_id="%s"' % (id)
        print sql
        return db.query(sql)[0]['gzh_name']

    def get_content(self):
        pass


def serve_urls(urls):
    for url in urls:
        ps = PatchSimple(url)
        ps.start()


def product_urls():
    global COUNT, COUNT_MAX
    count = COUNT
    print 'cc', count, COUNT, COUNT_MAX
    while count <= COUNT_MAX:
        print "2"
        urls = query_urls(count)
        len_urls = len(urls)
        if len_urls != 0:
            open('sql.log', 'a').write(str(len_urls) + '\n')
            print "[*] Count:", count
            yield urls
        count += 100


def query_urls(count, gzh_id = ''):
    global TABLE
    sql = 'select id, p_url, gzh_id, url_hash from %s where id >= %s and id < %s and gzh_id is not null and read_num is null' % (TABLE, count, count+100)
    # sql = 'select p_url, gzh_id url_hash from wx_post_simple where id >= %s and id < %s and gzh_id="%s"' % (count, count+100, GZH_ID)
    open('sql.log', 'a').write(sql)
    ds =  db.query(sql)
    urls = []
    for d in ds:
        urls.append(d)
    return urls


cut = 0
name = ''
GZH_ID = ''
COUNT = 999999999
COUNT_MAX = 0


def get_id_is_null(m):
    global TABLE
    sql = 'select %s(id) as mid from %s where like_num is null' % (m, TABLE)
    return db.query(sql)[0]['mid']


def go():
    '''COUNT is from count,
    COUNT_MAX is limit count'''
    global GZH_ID, COUNT, COUNT_MAX

    # from sys import argv
    # if len(argv) > 1:
    #     # gzh_name = argv[1]
    #     COUNT_MAX = int(argv[1])
    #     COUNT = int(argv[2])
    COUNT_MAX = get_id_is_null('max')
    COUNT = get_id_is_null('min')
    print 'mid:', COUNT
    print 'mad:', COUNT_MAX
    time.sleep(2)
    # GZH_ID = PatchSimple.get_gzh_id(gzh_name)
    for urls in product_urls():
        print len(urls)
        serve_urls(urls)


if __name__ == '__main__':
    go()
