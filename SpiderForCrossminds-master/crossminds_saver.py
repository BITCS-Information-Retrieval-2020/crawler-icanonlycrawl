import pymongo
from crossminds_config import crossminds_config


class crossminds_saver:
    def __init__(self):
        super().__init__()
        self.database = crossminds_config.db
        self.collection = "crossmindspaper1"
        #self.collection = "crossmindtesttest"
        self.connection = pymongo.MongoClient(
            host=crossminds_config.host,
            port=crossminds_config.port,
            username=crossminds_config.username,
            password=crossminds_config.pwd,
            authSource=self.database)

    def save_paperinfo(self, paperinfo):
        db = self.connection[self.database]
        col = db[self.collection]
        # 使用标题和pdfurl来判断冗余
        if (col.find_one({"_id": paperinfo["_id"]}) is not None):
            return
        if (col.find_one({"title": paperinfo["title"]}) is not None):
            return
        if (col.find_one({"pdfUrl": paperinfo["pdfUrl"]}) is not None
                and paperinfo["pdfUrl"] != ''):
            return
        col.insert_one(paperinfo)
        # print("save successfully!")

    def save_PDFUrl(self, title, pdf_path):
        db = self.connection[self.database]
        col = db[self.collection]

        col.update_one({"title": title}, {"$set": {"pdfPath": pdf_path}})
        # print("save successfully!")

    def save_VideoUrl(self, title, video_path):
        db = self.connection[self.database]
        col = db[self.collection]

        col.update_one({"title": title}, {"$set": {"videoPath": video_path}})
        # print("save successfully!")

    def get_PDFUrls(self):
        db = self.connection[self.database]
        col = db[self.collection]

        PDFUrls = []
        results = col.find({"pdfUrl": {"$ne": None}})
        for rcd in results:
            if(rcd['pdfPath'] == '' and rcd['pdfUrl'] != ""):
                PDFUrls.append((rcd['title'], rcd['pdfUrl']))
            else:
                # print("Already download or null pdfurl!\n")
                pass

        return PDFUrls

    def get_VideoUrls(self):
        db = self.connection[self.database]
        col = db[self.collection]

        results = col.find({"videoUrl": {"$ne": None}})
        VideoUrls = []
        for rcd in results:
            if(rcd['videoPath'] == "" and rcd['videoUrl'] != ""):
                VideoUrls.append((rcd['title'], rcd['videoUrl']))
            else:
                continue
                # print("Already download\n")
        return VideoUrls

    def update_videoUrls(self):
        db = self.connection[self.database]
        col = db[self.collection]
        title = "A Simplified Framework for Zero-Shot Cross-Modal Sketch Data Retrieval"
        col.update_one({"title": title}, {"$set": {"videoUrl": ""}})
        # results = col.find({"videoUrl": {"$ne": None}})
        # count = 0
        # for rcd in results:
        #     if (rcd['title'] == title ):
        #         col.update_one({"title": rcd['videoUrl']}, {"$set": {"videoPath": ""}})
        #         count = count + 1
        # print(count)
