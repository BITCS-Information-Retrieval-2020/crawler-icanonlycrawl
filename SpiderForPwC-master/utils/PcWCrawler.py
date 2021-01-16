# coding : utf-8
import sys
sys.path.append('./utils/')  # noqa
from utils.UrlCrawler import UrlCrawler  # noqa
from utils.PDFDownloader import PDFDownloader  # noqa
from utils.detailInfoCrawler import detailInfoCrawler  # noqa
from tqdm import tqdm  # noqa


class PcWCrawler:
    def __init__(self):
        self.urlCrawler = UrlCrawler()
        self.pdfDownloader = PDFDownloader()
        self.detailInfoCrawler = detailInfoCrawler()

    def run(self):
        self.urlCrawler.crawlAll()
        self.detailInfoCrawler.crawlAllInfo()
        self.pdfDownloader.downloadAll()
        print("All crawlers finished.")


if __name__ == '__main__':
    pcWCrawler = PcWCrawler()
    pcWCrawler.run()
