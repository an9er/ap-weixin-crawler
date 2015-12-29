#!/usr/bin/python
# encoding=utf8


import requests
import re
import fnvhash
import toolkitv
import time
from get_date_gid_num import PatchSimple
import dbconfig
import sys
db = toolkitv.MySQLUtility(
    dbconfig.mysql_host,
    dbconfig.mysql_db,
    dbconfig.mysql_user,
    dbconfig.mysql_pass
)


TABLE = 'wx_post_simple'


class ApWeixin(object):
    def __init__(self, count=10, logfile=''):
        self.count = count
        self.logfile = logfile
        self.frommsgid = ''

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
        while True:
            self.get_history_list()
            if self.over_date():
                print "[*] date over"
                break
            print "[*] msgid:", self.frommsgid
        print "[*] Over"

    def get_history_list(self):
        '''get url list and last frommsgid from history list'''

        if self.frommsgid == '':
            txt = ''
        else:
            txt = '&frommsgid={0}'.format(self.frommsgid)
        url = self.pre_url + '&count=10' + txt
        print "url-count", url
        headers = {
            'User-Agent':'Mozilla/5.0 (Linux; U; Android 2.3.6; zh-cn; GT-S5660 Build/GINGERBREAD) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1 MicroMessenger/4.5.255'}
        r = requests.get(url, headers=headers)
        if 'no session' in r.content:
            self.wait_for_new_keys()
        self.get_urls_msgid_via_json(r.content)

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

    def get_urls_msgid_via_json(self, content):
        s = content.replace('\"', '"')
        s = s.replace('\\', '')
        s = s.replace('amp;', '')
        with open('json.json', 'w') as f:
            f.write(s)
        self.get_msgid_via_json(s)
        rre = re.findall(r'title":"(.*?)".*?content_url":"(.*?)"', s)
        count = 0
        url = ''
        for r in rre:
            title, url = r
            self.push_db(title, url)
            count += 1
        print "[*] Push success:", count
        self.last_url = url

    def get_msgid_via_json(self, content):
        data = re.findall(r'"id":(\d+?),', content)
        self.frommsgid = data[-1]
        # if self.last_url == url:
        #     print "[*] not more over"
        #     exit()

    def over_date(self):
        r = requests.get(self.last_url)
        print self.last_url
        time.sleep(3)
        # open('zz.html', 'w').write(r.content)
        date = PatchSimple.get_p_date(r.content, ap=True)
        print "date", date
        # day = int(date.split('-')[2])
        month = int(date.split('-')[1])
        year = int(date.split('-')[0])
        if year < 2015 or month < 12:
        # if year < 2015 or month < 12 or day < 27:
            print date, "over"
            return True
        return False

    def get_read_num(self):
        pass

    def get_like_num(self):
        pass

    def push_db(self, title, url):
        global TABLE
        if 'mp.weixin.qq.com' not in url:
            print "not mp url"
            return

        url_hash = fnvhash.fnv_32a_str(url)
        d = {'title': title,
             'p_url': url,
             'url_hash': url_hash,
             }
        try:
            db.item_to_table(TABLE, d)
        except Exception, e:
            print Exception, e


def main():
    logfile = '/var/log/squid3/access.log'
    aw = ApWeixin(count=10, logfile=logfile)
    aw.start()


if __name__ == '__main__':
    main()
