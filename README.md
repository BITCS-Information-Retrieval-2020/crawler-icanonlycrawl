# 爬虫模块
## 一、模块要求
### 1. 课堂要求
- CrossMinds必选，要保证爬到的论文中有一定比例包含oral视频，爬取到的必须是视频的文件，记录下url地址。
- 除CrossMinds外再至少选择一个站点爬取，爬取的站点越多，包含的字段越多，爬到的数据越多，最终得分越高。
- 爬到的数据必须存储到MongoDB( [https://www.mongodb.com](https://www.mongodb.com) )中，供后续模块访问使用。字段必须定义清晰。
- 论文标题，作者等文本字段直接存在数据库里，视频，PDF等二进制文件存在磁盘上，数据库里保存文件的路径。
- 爬虫可以是简单地一次性把数据爬完，也可以是增量式爬取，时时更新，可以是单线程，也可以是多线程，或使用线程池。总之，爬虫的性能越强，越健壮，得分越多。
- 最后需要提供爬到数据的统计信息。
- 推荐使用Python Scrapy爬虫库：( [https://scrapy.org](https://scrapy.org) )
- 用Python的Flake8( [https://flake8.pycqa.org/en/latest/](https://flake8.pycqa.org/en/latest/) )库检查代码是否规范
- 模块接口要求：爬虫模块最终需要交给检索模块一个MongoDB数据库和磁盘文件。
### 2. 与检索组对接要求
<https://github.com/BITCS-Information-Retrieval-2020/search-rattailcollagen1/blob/master/searcher/data/dataFlow/fromCrawler.json>
## 二、小组成员及分工
|  成员   | 分工  |
|  ----  | ----  |
| 詹亘泽  | ACL Anthology所有信息增量式爬取 |
| 谭小焱  | CrossMinds基本信息增量式爬取 |
| 徐伊玲  | CrossMinds视频及pdf增量式爬取 |
| 张峄天  | IP池 + Papers With Code所有信息增量式爬取 |
| 何亮丽  | 线程池 |
| 张悉伦  | 学习增量式爬取并撰写该部分文档 |
## 三、爬虫内容及统计信息
|  网站   | 论文总量 |  视频数量   | pdf数量  |  IP池   | 线程池  | 增量式  |
|  ----  | ----  |  ----  | ----  |  ----  | ----  |  ----  |
| ACL Anthology  | 61462  |  1283  | 59789  |  ✔  | ✔  | ✔  |
|  CrossMinds  | ----  |  ----  | ----  |  ✔  | ✔  |  ✔  |
|  Papers With Code | ----  |  ----  | ----  | ✔ | ✔  |  ✔  |
## 四、基础爬虫模块
该部分分别对ACL Anthology，CrossMinds，Papers With Code三个网站的所有信息的爬取进行说明，包括代码目录结构、代码必要说明、部署过程、启动运行流程、依赖的第三方库及版本。  
### 1. ACL Anthology
基于request+beautifulsoup开发，高效率爬取https://www.aclweb.org/anthology/  网站上的论文，支持爬取论文的基本信息，对应pdf和视频，支持增量式爬取，使用了代理和ip池等技术

#### 1.1 依赖的第三方库
requests==2.23.0  
pymongo==3.11.2  
psutil==5.8.0  
tqdm==4.56.0  
beautifulsoup4==4.9.3  

#### 1.2 运行代码
```bash
cd SpiderForACL
python run.py
```

#### 1.3 代码结构
```
./SpiderForACL
├── README.md  
├── requirements.txt  
├── run.py  
├── statistics.txt  
└── utils  
  ├── ACLScrawler.py  
  ├── ACLUrlsCrawler.py  
  ├── ClashControl.py  
  ├── config.py  
  ├── ContentDownloader.py 
  ├── LevelUrls.py  
  ├── PDFDownloader.py  
  └── VideoDownloader.py
```

#### 1.4 工作流程
1. 从网站https://www.aclweb.org/anthology/ 获取到所有会议的url，再获取对应会议所有年份的url，最后获取所有论文的url并保存在数据库中。、
2. 对于第1步中获取到的论文url, 发送request的get请求获取论文的标题，作者，摘要，发布组织，年份，pdf的url，代码的url，视频url等相关信息，保存至mongodb中，并将pdf和视频的url保存至对应表中
3. 为了实现增量式爬取，我们将论文的url，pdf的url和视频的url保存置mongodb中，并且每条url数据对应一个visit字段以指示是否爬取了此条url对应的数据
4. 根据表中visit字段为false的url分别爬取pdf和视频数据。其中由于视频网站被墙以及反爬虫的策略，我们采用了IP代理和IP的技术

#### 1.5 程序入口
  调用ACLScrawler的run函数  
  1. 调用ACLUrlsCrawler的run函数爬取所有论文的url(按照会议-某年会议的顺序遍历)
  2. 调用ContentDownloader的run函数爬取数据表中所有visit字段为false的url对应的基本论文信息
  3. 调用PDFDownloader的run函数爬取爬取数据表中所有visit字段为false的url对应的pdf
  4. 调用VideoDownloader的run函数爬取爬取数据表中所有visit字段为false的url对应的视频

### 2. CrossMinds

#### 2.1 代码结构
```
│  README.md   
│--crossminds  
│     crossminds_config.py  参数设置  
│     crossminds_parser.py  解析对应的论文的各个字段  
│     crossminds_scrapy.py  按会议类别取论文  
│     crossminds_saver.py   存数据库、重复判断  
│     downloader.py         负责视频和PDF文件的下载  
│     main.py               运行程序的入口  
│
```
#### 2.2 依赖 
- python3
```
pip install requests
pip install beautifulsoup4
pip install lxml
pip install pymongo
pip install pytube
```
#### 2.3 运行代码
2.3.1 爬取基础信息：  
```bash
cd SpiderForCrossminds
python main.py
```
2.3.2 爬取视频和pdf：(也可以和基础信息一起爬取) 
```bash
cd SpiderForCrossminds
python downloader.py
```
#### 2.4 整体流程
1、首先通过 https://api.crossminds.io/web/node/interest-list?offset=0&limit=10 接口获得crossminds中按Knowledge Area分的十个类别

2、通过 https://api.crossminds.io/web/node/video/name/{category}?limit=1500&offset=0 从各个类别中获取相应的论文的json数据，category为第1步中获取到的类别（由于在网站中可以直接看到每个类别的item数量，最大为1471，所以这里的limit先设置为了1500）

3、解析每个论文的json数据  
着重说明以下几个字段的解析
- pdfurl字段  

由于crossminds给到的paperurl并不统一，有些是用paperlink做了链接，而有些直接写在了一篇paper对应的description中，所以这里采用两种方式解析：  
每片paper对应的json文件中都有对应的_id，而它所对应的展示页面对应于https://crossminds.ai/video/_id  通过使用beautifulsoup可以解析对应的页面中的paperlink  
如果页面中没有paperlink链接，则去相应的description中使用正则表达式找到pdf的地址，并做相应的替换，便于后续下载pdf使用  

- abstract字段  

crossminds中paper的description部分包含abstract，有些会明确指出有abstract，对于这种我们用正则表达式提取出abstract部分  
如果没有且之前爬到了对应的pdfurl，比如arxiv网站的url，则用beautifulsoup解析arxiv中论文主页的摘要

- authors字段  

crossminds中paper的json数据中有authors字段，但很多的上传者都是“computor vision”此类，对于没有pdfurl的paper，我们直接使用该字段  
对于爬到了pdfurl的paper，比如arxiv网站的url，则用beautifulsoup解析arxiv中论文主页的作者  

4、数据的存储，使用pymongo存储到了mongodb数据库中  
5、视频和PDF的下载。将视频和PDF文件下载到本地，将存储路径存到mongoDB数据库中。

- 视频下载。
CrossMinds网站中的视频主要来自于CrossMinds、Youtube 和 Vimeo三个网站，根据其存储视频文件不同采用不同的下载方式。

  1. 来自CrossMinds网站的视频URL例如：https://stream.crossminds.ai/5fa9d52a8a1378120d965136-1604965683584/hls-5fa9d52a8a1378120d965136.m3u8 ，视频为m3u8格式，m3u8文件主要以文件列表的形式存在，根据其中记录的索引可以找到多个分段的ts格式的音视频文件，将这些分段的音视频文件下载下来，最后合并成一个完整的ts格式的视频。  
  2. 来自Vimeo网站的视频URL例如：https://vimeo.com/423554135 ，对此url的内容进行解析，得到视频的相关信息包括文件名，分辨率，实际的下载地址等信息，选择最低分辨率对应的视频文件进行下载。  
  3. 来自Youtube网站的视频URL例如：https://www.youtube.com/embed/mo079YBVTzE ，使用第三方工具pytube可以直接对此类URL进行下载。  

   视频下载可以在爬取到一篇论文的基本信息之后就进行，也可以在基本信息都爬完之后，从数据库中获取所有包含视频URL的论文信息，视频文件默认存储在```./data/videos/```路径下

- PDF文件下载。PDF文件和视频的文件名在存储时都需要都标题进行处理，去掉文件名非法字符。PDF文件默认存储在```./data/PDFs/```路径下




### 3. PaperWithCode

PaperWithCode爬虫基于requests和beautifulsoup进行开发，能够爬取[Paper With Code](https://paperswithcode.com)上的论文资料，包括论文的标题、作者、摘要、发表时间、发表地址和官方代码地址，并且能够下载论文对应的PDF文件。

#### 3.1 代码目录结构：

```
./SpiderForPwC
├── README.md
├── progress
├── requirements.txt
├── run.py
└── utils
    ├── ClashControl.py
    ├── PDFDownloader.py
    ├── PcWCrawler.py
    ├── UrlCrawler.py
    ├── __init__.py
    ├── config.py
    ├── detailInfoCrawler.py
    └── progress
```

#### 3.2 工作模式

1. 从https://portal.paperswithcode.com/ 可以得知，paperwithcode中的论文主要分为六类，分别是：Machine Learning, Computer Science, Physics, Mathematics, Astronomy, Statistics，他们各自有对应的二级域名，并且以url参数`/?page=x`来进行翻页操作，其中每页有10篇论文；
2. 对第一步中的论文列表页进行解析，获取每篇文章的paper页面，并获取其Abstract地址，可以获得一个指向[arxiv.org](https://arxiv.org/) 域名下的页面，其上包括了该篇论文的所有详情；
3. 解析第二部中所获得的详情页，即可获得目标论文的基本信息。将获取的基本信息构建成一个dict，写入到MongoDB数据库中，并将论文PDF下载到本地；
4. 该爬虫由两个爬取部分构成，其逻辑是分离的，分别是爬取paperwithcode上的论文链接，以及爬取论文的详情。此外，PDF的下载与这二者分离，三者只在使用数据上有所关联；
5. 爬虫各部分均实现增量式下载和爬取。其中爬取paperwithcode上的论文链接通过读写progress记录文件实现，爬取论文详情以及PDF下载通过检查数据表中的`visit`字段实现。因此爬虫每次运行时都会继续之前未完成的进度；
6. 网站使用的IP池方法详情见IP池文档。

#### 3.3 运行方法

爬虫可通过目录下的`run.py`文件运行：

```bash
cd SpiderForPwC
python run.py
```

#### 3.4 依赖

爬虫基于`Python 3`开发  
```
pymongo==3.11.2
psutil==5.8.0
requests==2.23.0
tqdm==4.56.0
beautifulsoup4==4.9.3
```


