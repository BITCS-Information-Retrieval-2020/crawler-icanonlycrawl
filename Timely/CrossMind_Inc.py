from apscheduler.schedulers.blocking import BlockingScheduler
from crossminds_scrapy import crossminds_scrapy
from crossminds_parser import crossminds_parser
import datetime


def run_spider():
    print("启动爬虫")
    starttime = datetime.datetime.now()
    items = crossminds_scrapy().get_items()
    crossminds_parser().parser(items)
    endtime = datetime.datetime.now()
    print("爬虫运行结束，用时为：")
    print(endtime - starttime)


if __name__ == '__main__':
    sched = BlockingScheduler()
    sched.add_job(run_spider, 'cron', hour=14, minute=0)
    sched.start()
