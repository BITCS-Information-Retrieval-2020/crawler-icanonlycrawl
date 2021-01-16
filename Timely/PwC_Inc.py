# coding : utf-8

from utils.PcWCrawler import PcWCrawler
from apscheduler.schedulers.blocking import BlockingScheduler
import datetime


def run_spider():
    print("启动爬虫")
    starttime = datetime.datetime.now()
    pcWCrawler = PcWCrawler()
    pcWCrawler.run()
    endtime = datetime.datetime.now()
    print("爬虫运行结束，用时为：")
    print(endtime - starttime)


if __name__ == '__main__':
    sched = BlockingScheduler()
    sched.add_job(run_spider, 'cron', hour=10, minute=0)
    sched.start()
