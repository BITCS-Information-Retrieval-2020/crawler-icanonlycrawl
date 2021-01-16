# coding=utf-8
import requests
import os
import json
from tqdm import tqdm
import re
from pytube import YouTube
from crossminds_saver import crossminds_saver
import time
from multiprocessing.dummy import Pool
from istarmap import istarmap


def pdf_download(title, pdfUrl):
    os.makedirs('./data/PDFs/', exist_ok=True)
    root_dirs = './data/PDFs/'

    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, " ", title)  # 替换为下划线

    headers = {
        "User-Agent":
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36",
    }
    r = requests.get(pdfUrl, headers=headers, stream=True)
    pdf_path = root_dirs + new_title + '.pdf'
    with open(pdf_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    print("Download " + title + " done \n")
    crossminds_saver().save_PDFUrl(title, pdf_path)
    # return pdf_path


def downloadVideoFromYouTube(videoUrl, title, root='./data/videos/'):
    yt = YouTube(videoUrl)
    video_path = root
    video = yt.streams.filter(resolution='240p', subtype='mp4').first()
    video.download(video_path)
    video_path = root + video.title + ".mp4"

    print("Download " + video.title + " done\n")
    return video_path


def downloadVideoFromCrossminds(videoUrl, title, root='./data/videos/'):

    i = len(videoUrl) - 1
    while i > 0:
        if videoUrl[i] == '/':
            break
        i = i - 1

    filename = videoUrl[i + 1: len(videoUrl)]
    base_url = videoUrl[0: i + 1]
    # print(base_url)
    # print(filename)
    doc_m3u8 = requests.get(videoUrl)
    m3u8_path = root + "tmp/" + filename
    with open(m3u8_path, 'wb') as f:
        f.write(doc_m3u8.content)

    ts_urls = []
    with open(m3u8_path, "r") as file:
        lines = file.readlines()
        for line in lines:
            if line.endswith(".ts\n"):
                ts_urls.append(base_url + line.strip("\n"))

    # print(ts_urls)
    for i in range(len(ts_urls)):
        ts_url = ts_urls[i]
        ts_file_name = ts_url.split("/")[-1]
        try:
            response = requests.get(ts_url, stream=True, verify=False)
        except Exception as e:
            print("异常请求：%s" % e.args)
            return

        ts_path = root + "tmp/" + ts_file_name
        with open(ts_path, "wb+") as file:
            for chunk in response.iter_content(chunk_size=1024 * 5):
                if chunk:
                    file.write(chunk)

    file_list = []
    for root_os, dirs, files in os.walk(root + "tmp/"):
        for fn in files:
            p = str(root_os + '/' + fn)
            if(".ts" in p):
                file_list.append(p)

    # print(file_list)

    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, " ", title)  # 替换为下划线

    file_path = root + new_title + '.ts'
    with open(file_path, 'wb+') as fw:
        for i in range(len(file_list)):
            fw.write(open(file_list[i], 'rb').read())

    ls = os.listdir(root + "tmp/")
    for i in ls:
        c_path = os.path.join(root + "tmp/", i)
        if os.path.isdir(c_path):
            print("dictionary!\n")
        else:
            os.remove(c_path)
    print("download " + title + "done")
    return file_path


def downloadVideoFromVimeo(videoUrl, title, root='./data/videos/'):

    headers = {
        "User-Agent":
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    r = requests.get(
        videoUrl + "?action=load_download_config", headers=headers)
    videoUrls = []
    for file in json.loads(r.content)['files']:
        file_name = file['file_name']
        download_url = file["download_url"]
        height = file["height"]
        videoUrls.append((download_url, file_name, height))

    # 将url按照分辨率排序
    print(videoUrls)
    sorted(videoUrls, key=lambda video: video[2])
    video_download_url = videoUrls[0][0]
    video_name = videoUrls[0][1]
    r = requests.get(video_download_url, headers=headers, stream=True)

    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, " ", video_name)  # 替换为下划线
    video_path = root + new_title
    with open(video_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 5):
            if chunk:
                f.write(chunk)
    return video_path


def oral_video_download(title, url):
    os.makedirs('./data/videos/tmp/', exist_ok=True)
    root_dirs = './data/videos/'
    # m3u8
    if ("crossminds" in url):
        video_path = downloadVideoFromCrossminds(url, title, root_dirs)
        crossminds_saver().save_VideoUrl(title, video_path)
        # return video_path
    elif ("vimeo" in url):
        video_path = downloadVideoFromVimeo(url, title, root_dirs)
        crossminds_saver().save_VideoUrl(title, video_path)
        # return video_path
    elif ("youtube" in url):
        video_path = downloadVideoFromYouTube(url, title, root_dirs)
        crossminds_saver().save_VideoUrl(title, video_path)
        # return video_path
    else:
        print("video source error!\n")
        return


if __name__ == '__main__':

    # url = "https://stream.crossminds.ai/
    # 5fa9d52a8a1378120d965136-1604965683584/hls-5fa9d52a8a1378120d965136.m3u8"
    # title = "A Multi-Hypothesis Approach to Color Constancy"
    # url = "https://vimeo.com/423554135"
    # title = "FANG Leveraging Social Context
    # for Fake News Detection Using Graph Representation"
    # url ="https://www.youtube.com/embed/mo079YBVTzE"
    # title = "Multi-Drone Delivery using Transit
    # (ICRA 2020 Best Paper Finalist in Multi-Robot Systems)"

    # PDFUrls = crossminds_saver().get_PDFUrls()
    # print(len(PDFUrls))
    # for pdf_url in PDFUrls:
    #     pdf_path = pdf_download(pdf_url[0], pdf_url[1])
    #     crossminds_saver().save_PDFUrl(pdf_url[0], pdf_path)

    PDFUrls = crossminds_saver().get_PDFUrls()
    print(len(PDFUrls))
    start = time.time()
    pool = Pool()
    # for _ in tqdm(pool.istarmap(pdf_download, PDFUrls), total=len(PDFUrls)):
    #     pass
    pool.istarmap(pdf_download, PDFUrls)
    end = time.time()
    pool.close()
    pool.join()
    print('PDFfinished--timestamp:{:.3f}'.format(end - start))

    VideoUrls = crossminds_saver().get_VideoUrls()
    print(len(VideoUrls))
    start = time.time()
    pool = Pool()
    # for _ in tqdm(pool.istarmap(oral_video_download, VideoUrls[:5]),total=len(VideoUrls[:5])):
    #     pass
    pool.starmap(oral_video_download, VideoUrls)
    end = time.time()
    pool.close()
    pool.join()
    print('VIDEOfinished--timestamp:{:.3f}'.format(end - start))
    # print(result)

    # VideoUrls = crossminds_saver().get_VideoUrls()
    # print(len(VideoUrls))
    # request_num = 60
    # for video_url in VideoUrls:
    #     if(request_num > 0 and ("crossminds" or "youtube" in video_url[1])):
    #         print(video_url)
    #         video_path = oral_video_download(video_url[0], video_url[1])
    #         crossminds_saver().save_VideoUrl(video_url[0], video_path)
    #         request_num = request_num - 1

    # crossminds_saver().update_videoUrls()
