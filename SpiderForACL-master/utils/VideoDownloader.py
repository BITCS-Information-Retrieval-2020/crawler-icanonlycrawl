import time

import pymongo
import requests
from tqdm import tqdm
from ContentDownloader import ContentManager
from ClashControl import ClashControl
import LevelUrls as lu
import utils.config as config
import pdb
import subprocess
import json


class VideoManager():
    '''
    爬取论文视频
    '''
    database = config.db
    collection = "Video"
    paper = ContentManager.collection
    clashControl = ClashControl()
    clash_proxy = {}

    def __init__(self):
        # self.database = "ACLAnthology"
        # self.collection = "Video"
        # self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        # self.ACLAnthology = "ACLAnthology"
        self.client = pymongo.MongoClient(host=config.host,
                                          port=config.port,
                                          username=config.username,
                                          password=config.psw,
                                          authSource=self.database)
        self.VideoUrl = self.getVideoUrlsfromDB()
        self.clash_proxy = {
            "http": "http://" + self.clashControl.clash_host + ":" + self.clashControl.proxy_port,
            "https": "http://" + self.clashControl.clash_host + ":" + self.clashControl.proxy_port
        }

    def getVideoUrlsfromDB(self):
        '''
        从数据库中获取需要爬取视频的url
        :return:
        '''
        db = self.client[self.database]
        col = db[self.collection]
        urls = [url['url'] for url in col.find({"visit": False})]
        # TODO: 目前只下载了vimeo，slideslive下载太慢了
        vimeoUrls = []
        for url in urls:
            if ("vimeo" in url):
                vimeoUrls.append(url)
        # return urls
        return vimeoUrls

    def addUrl(self, url):
        '''
            加入待爬取的视频的url
        :param url:
        :return:
        '''
        if (url == ""):
            return
        db = self.client[self.database]
        col = db[self.collection]
        if col.find_one({"url": url}) is None:
            col.insert_one({"url": url, "visit": False})
        return

    def updateUrl(self, url, filePath):
        '''
            已经爬过的pdf更新数据库的visit标记
        :param url:
        :return:
        '''
        db = self.client[self.database]
        col = db[self.collection]
        ACLAnthology = db[self.paper]
        # visit标记设为true
        col.update_one({"url": url}, {"$set": {"visit": True}})
        # 更新paper信息中的video的文件路径
        ACLAnthology.update_one({"videoUrl": url},
                                {"$set": {
                                    "videoPath": filePath
                                }})

    def getVideoUrlFromVimeo(self, siteUrl):
        '''
        :param siteUrl:https://vimeo.com/ 网站中的视频链接 例如 https://vimeo.com/383950369
        :return: 对应视频资源的url和文件名
        '''
        headers = {
            "User-Agent":
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }
        # jumpover
        if "vimeo.com/28" in siteUrl:
            return None, None
        # r = requests.get(siteUrl + "?action=load_download_config",
        #                  headers=headers, proxies=self.clash_proxy)
        r = requests.get(siteUrl + "?action=load_download_config",
                         headers=headers, proxies=self.clash_proxy)
        print(siteUrl + "?action=load_download_config")
        videoUrls = []
        print(r.content)
        if "display_message" in json.loads(r.content):
            return None, None
        for file in json.loads(r.content)['files']:
            file_name = file['file_name']
            download_url = file["download_url"]
            height = file["height"]
            videoUrls.append((download_url, file_name, height))

        # 将url按照分辨率排序
        # pdb.set_trace()
        sorted(videoUrls, key=lambda video: video[2])
        if (len(videoUrls) != 0):
            # 下载分辨率最低的文件
            return videoUrls[0][0], videoUrls[0][1]
        else:
            return None, None

    def getVideoUrlFromslideslive(self, siteUrl):
        '''
        :param siteUrl:https://slideslive.com/ 网站中的视频链接
            例如 https://slideslive.com/38928775/guiding-variational-response-generator-to-exploit-persona
        :return: 对应视频资源的url和视频格式
        '''
        pass

    # def getVideoUrl(self, siteUrl):
    # if ("slideslive" in siteUrl):
    #     videoUrl, suffix = self.getVideoUrlFromslideslive(siteUrl)
    # elif ("vimeo" in siteUrl):
    #     videoUrl, suffix = self.getVideoUrlFromVimeo(siteUrl)

    def reset(self):
        '''
        所有的video url visit置false
        :return:
        '''
        db = self.client[self.database]
        col = db[self.collection]
        col.update_many({}, {"$set": {"visit": False}})

    def downloadVideo(self, url):
        '''
        根据视频网站的url 下载视频，并返回视频的文件名
        :param url:
        :return:
        '''
        videoName = ""
        # TODO: 下载视频逻辑
        if ("vimeo" in url):
            # videoUrlSplit = url.split("/")
            # videoName += videoUrlSplit[len(videoUrlSplit) - 1]
            # pdb.set_trace()
            videoUrl, videoName = self.getVideoUrlFromVimeo(url)
            # jumpover
            if videoUrl is None:
                return None
            intab = "?*/\\|:><"
            for s in intab:
                if s in videoName:
                    videoName = videoName.replace(s, '')

            headers = {
                "User-Agent":
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36",
            }

            r = requests.get(videoUrl, headers=headers, proxies=self.clash_proxy, stream=True)
            # length = r.headers['content-length']
            # print(videoName+"."+suffix+"size: "+length)

            with open("./data/videos/" + videoName, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 5):
                    if chunk:
                        f.write(chunk)
            # pdb.set_trace()
            return videoName
        elif ("slideslive" in url):
            # 只能调用youtubde-dl下载，俺实在不会了呀orz...555
            # cmdForName = "youtube-dl --get-filename -o '%(title)s%-%(id)s.%(ext)s' +
            #               http://slideslive.com/38929437 --restrict-filenames"
            cmdForName = "youtube-dl --get-filename -o '%(title)s%-%(id)s.%(ext)s'" + url + " --restrict-filenames"
            cmd = "youtube-dl " + url

            download = subprocess.Popen(cmd,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
            download.wait()

            getFileName = subprocess.Popen(cmdForName,
                                           shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)
            getFileName.wait()

            fileName = getFileName.stdout.read().decode('utf-8')
            return fileName
            # 处理ls的返回值

    def run(self):
        pbar = tqdm(self.VideoUrl)

        count = 0  # change proxy per 20 videos
        for videoUrl in pbar:
            pbar.set_description("Crawling %s" % videoUrl)
            fileName = self.downloadVideo(videoUrl)
            # jumpover
            if fileName is None:
                print("No permission, pass this video")
                continue
            # pdb.set_trace()
            self.updateUrl(videoUrl, "/data/videos/" + fileName)
            # try:
            #     pbar.set_description("Crawling %s" % videoUrl)
            #     fileName = self.downloadVideo(videoUrl)
            #     # pdb.set_trace()
            #     self.updateUrl(videoUrl, "/data/videos/" + fileName)
            # except Exception as e:
            #     print("error: "+videoUrl)
            # print(type(e)+":"+e)
            #     lu.ErrorUrlManeger(videoUrl)
            count = count + 1
            if count > 10:
                if self.clashControl.changeRandomAvailableProxy():
                    count = 0
                    time.sleep(15)
        print("videos downloading done")


if __name__ == '__main__':
    videoManager = VideoManager()
    videoManager.reset()
# aclscrawler.updateUrl("")
