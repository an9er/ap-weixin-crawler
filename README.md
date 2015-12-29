# ap-weixin-crawler
an weixin crawler via mobile and squid3 agent.
can crawler the gongzhonghao artical and read/like number. 

三个文件运行顺序和作用：
1. ap.py 获取url
2. get_date_git_num.py: 获得author，date
3. patch_read_like.py 获得read和like数目

更换抓取账号修改步骤：
1. 添加要抓取的公众号到wx__gzh;
2. 修改三个文件的select语句中的table:
3. 修改ap 中的over_date 决定获取到的日期。

ps: 
sentiment和data在get_date_git_num中修改
ap.py中make_count修改count,来控制一次获取的url个数。



