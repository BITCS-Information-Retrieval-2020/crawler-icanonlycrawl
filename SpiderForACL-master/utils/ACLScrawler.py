import sys
sys.path.append('./utils/') # noqa
from utils.ACLUrlsCrawler import ACLUrlsCrawler # noqa
from utils.ContentDownloader import ContentManager # noqa
from utils.PDFDownloader import PDFManager # noqa
from utils.VideoDownloader import VideoManager # noqa
from tqdm import tqdm # noqa
import LevelUrls as lu # noqa
import traceback # noqa


class ACLScrawler:
    def __init__(self):
        self.urlScrawler = ACLUrlsCrawler()
        self.pdfManager = PDFManager()
        self.videoManager = VideoManager()
        self.contenManager = ContentManager()

    def run(self):
        # 爬取论文的基本信息
        urls = self.urlScrawler.getACLUrls()
        pbar = tqdm(urls)
        for url in pbar:
            try:
                pbar.set_description("Crawling %s" % url)
                # 爬取并保存论文基本内容
                pdfUrl, videoUrl = self.contenManager.run(url)
                # 加入待爬取的pdf url
                self.pdfManager.addUrl(pdfUrl)
                # 加入待爬取的视频 url
                self.videoManager.addUrl(videoUrl)
                # 爬取数据后更新url visit字段
                self.urlScrawler.updateUrl(url)
            except Exception as e:
                lu.ErrorUrlManeger(url, e)
                continue
        print("basic information downloading done")
        # 爬取论文的pdfwithpool
        self.pdfManager.run()
        # # 爬取论文的视频withIPpool
        self.videoManager.run()

if __name__ == '__main__':
    aclscrawler = ACLScrawler()
    aclscrawler.run()
# aclscrawler.updateUrl("")
