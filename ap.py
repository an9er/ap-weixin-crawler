#!/usr/bin/python
# encoding=utf8


import requests
import re
import fnvhash
import toolkitv
import time
from get_date_gid_num import PatchSimple
import dbconfig
db = toolkitv.MySQLUtility(
    dbconfig.mysql_host,
    dbconfig.mysql_db,
    dbconfig.mysql_user,
    dbconfig.mysql_pass
)


class ApWeixin(object):
    def __init__(self, count=10, logfile=''):
        self.count = count
        self.logfile = logfile

    def get_parameter(self):
        '''get key uni etc..'''
        pass

    def get_history_list(self):
        '''get wx-posts from history list'''
        pass

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

    def make_url(self):
        url_pre = 'http://mp.weixin.qq.com/mp/getmasssendmsg?__biz=%s&uin=%s&key=%s&f=json'
        self.pre_url = url_pre % (self.biz, self.uin, self.key)

    def update_key(self):
        self.ori_key = self.key

    def start(self):
        self.parse_key_from_squid()
        self.update_key()
        self.make_url()
        self.list_go()

    def list_go(self):
        for count in self.make_count():
            self.get_artical_urls(count)
            print "[*] To serve count:", count
            if self.over_date():
                print "[*] Over"
                break

    def get_artical_urls(self, count):
        url = self.pre_url + '&count=%s' % count
        r = requests.get(url)
        if 'no session' in r.content:
            self.wait_for_new_keys()

        self.get_urls_via_json(r.content)

    def wait_for_new_keys(self):
        print "[**] The key is invirified,and not find new key, sleep per 5s."
        while 1:
            self.parse_key_from_squid()
            if self.key != self.ori_key:
                self.ori_key = self.key
                print "[*] Get new key, continue work!"
                return
            time.sleep(5)

    def get_urls_via_json(self, content):
        s = content.replace('\"', '"')
        s = s.replace('\\', '')
        s = s.replace('amp;', '')
        rre = re.findall(r'title":"(.*?)".*?content_url":"(.*?)"', s)
        count = 0
        url = ''
        for r in rre:
            title, url = r
            self.push_db(title, url)
            count += 1
        print "[*] Push success:", count
        self.last_url = url

    def over_date(self):
        r = requests.get(self.last_url)
        print self.last_url
        time.sleep(3)
        open('zz.html', 'w').write(r.content)
        date = PatchSimple.get_p_date(r.content)
        if int(date.split('-')[0]) < 2015:
            print date, "over"
            return True
        return False

    def make_count(self):
        count = 30
        while count < 10000:
            yield count
            count += 30

    def get_read_num(self):
        pass

    def get_like_num(self):
        pass

    def push_db(self, title, url):
        url_hash = fnvhash.fnv_32a_str(url)
        d = {'title': title,
             'p_url': url,
             'url_hash': url_hash,
             }
        db.item_to_table('wx_post_simple', d)


if __name__ == '__main__':
    logfile = '/var/log/squid3/access.log'
    aw = ApWeixin(count=10, logfile=logfile)
    aw.start()
