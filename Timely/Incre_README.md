### 增量式

由于目标网站经常新增页面，本项目采取增量式爬虫，定期从网站上爬取新的论文信息。

#### 工作模式

1. 增量式改进分为两部分，一是定期爬取，选择apscheduler库的定时任务实现。

```python
sched = BlockingScheduler()
sched.add_job(run_spider, 'cron', hour=10, minute=0)
sched.start()
```

2. 另一部分是去重，本项目的具体方法是将论文的url、pdf的url和视频的url保存在在mongo数据库中，并为每条url数据设置visit字段。在爬取论文时检查url是否已经爬取，并在下载时根据visit字段判断内容是否已经下载。
去重代码主要实现于以下函数中：
.  
```
SpiderForACL/utils/ACLUrlCrawler/saveUrls,
SpiderForACL/utils/ACLUrlCrawler/getUnvisitedUrls, 
SpiderForPwC/utils/UrlCrawler/saveUrls,
SpiderForPwC/utils/PDFDownloader/addUrl,
scrapy/crossminds_saver/save_paperinfo
```

#### 运行方法

直接运行根目录下ACL_Inc.py，PwC_Inc.py，CrossMind_Inc.py，即可每天按时爬取新论文。
```
python ACL_Inc.py
python CrossMind_Inc.py
python PwC_Inc.py
```

#### 依赖

```
apscheduler==3.6.3
datetime
```

#### 分工

- 张悉伦：增量式改进爬虫



