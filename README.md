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
```json
{
  "_id": 1,
  "title": "...",
  "authors": "author1, author2, ...",
  "abstract": "...",
  "publicationOrg": "CVPR",
  "year": 2020,
  "pdfUrl": "...",
  "pdfPath": "./data/PDFs/xx.pdf",
  "publicationUrl": "https://...",
  "codeUrl": "...",
  "videoUrl": "...",
  "videoPath": "./data/videos/xx.mp4"
}
```
## 二、小组成员及分工
|  成员   | 分工  |
|  ----  | ----  |
| 詹亘泽  | ACL Anthology所有信息增量式爬取 |
| 谭小焱  | CrossMinds基本信息增量式爬取 |
| 徐伊玲  | CrossMinds视频及pdf增量式爬取 |
| 张峄天  | IP池 + Papers With Code所有信息增量式爬取 |
| 何亮丽  | 线程池 + 协调与整合 |
| 张悉伦  | 增量式爬取学习 + 实现定时运行功能 |
## 三、爬虫内容及统计信息
|  网站   | 论文总量 |  视频数量   | pdf数量  |  IP池   | 线程池  | 增量式  |
|  ----  | ----  |  ----  | ----  |  ----  | ----  |  ----  |
| ACL Anthology  | 61462 |  1283  | 59789  |  ✔  | ✔  | ✔  |
|  CrossMinds  | 3553 | 278 | 561 |  ✔  | ✔  |  ✔  |
|  Papers With Code | 519 | 0 | 519  | ✔ | ✔  |  ✔  |

## 四、基础爬虫模块说明
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
cd SpiderForACL-master
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
- 爬取基础信息：  
```bash
cd SpiderForCrossminds-master
python main.py
```
- 爬取视频和pdf：(也可以和基础信息一起爬取) 
```bash
cd SpiderForCrossminds-master
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
cd SpiderForPwC-master
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



## 五、性能提升模块说明
该部分分别对IP池、线程池和增量式的实现进行相关说明
### 1. 线程池
由于项目爬取时单线程的爬取速度慢，会耗费过多时间，所以本项目实现了线程池进行并发爬虫。  
#### 1.1  关于线程池的选取
- 多进程：密集CPU任务，需要充分使用多核CPU资源（服务器，大量的并行计算）的时候，用多进程。
- 多线程：密集I/O任务（网络I/O，磁盘I/O，数据库I/O）使用多线程合适。
由于爬虫为密集型的I/O任务，因此选取多线程/线程池实现。  
在配置线程池之前，对一个小的视频集（8个视频）的爬取下载进行性能提升的验证实验，其中进程池使用的是multiprocess.Pool，线程池使用的是multiprocessing.dummy.Pool，实验结果如下表所示：  
|  方案  |  爬取时间 |
|  ----  | ----  |
| 单线程  | 178.447s |
| 进程池  | 47.56s |
| 线程池  | 43.23s |

#### 1.2 依赖
```python
import time
from multiprocessing.dummy import Pool

```
#### 1.3 相关函数使用
```python
def func(msg):
    return
    
pool = Pool(processes=3)
#map/imap和apply/apply_async的区别是：map/imap可以多任务执行，即第二个参数为多任务的所有输入的列表，而apply_async/apply为单任务执行，需要写在循环内部才能实现并发。
pool.imap(func,[msg,])        # imap可以尽快返回一个Iterable的结果，而map则需要等待全部Task执行完毕，返回list。
pool.map(func, [msg, ])       # 阻塞 相当于把多个任务map为n个组，每个组分配一个线程。

pool.apply_async(func, (msg,))  # 单次任务异步执行。一个任务执行完再进行下一个任务
pool.apply(func,(msg,))       # 单次任务同步执行。单次启动一个任务，但是异步执行，启动后不等这个进程结束又开始执行新任务

pool.starmap(func, [msg, ]) #starmap 与 map 的区别是，starmap 可以传入多个参数。

pool.close()
pool.join()  # 调用join之前，先调用close函数，否则会出错。执行完close后不会有新的进程加入到pool,join函数等待所有子进程结束

# 使用imap函数可以结合tqdm进度条
for _ in tqdm(pool.imap(func,[msg,]),total=len([msg,])):
		pass
```

#### 1.4 工作模式
- ACL Anthology：利用线程池解析爬取下来的论文url获得论文信息；线程池爬取pdf和视频。
- Crossminds：利用线程池爬取网站得到json数据；线程池解析并存储论文信息；线程池爬取pdf和视频。
- PaperWithCOde：利用线程池解析论文url获得论文信息；线程池爬取pdf。
### 2. IP Pool
由于项目爬取的网站中有视频以及PDF的下载需求，并且由于目标网站的特殊性，项目需要同时具有**科学上网**以及**防止反爬虫**的能力。因此，本项目配合[clash](https://github.com/Dreamacro/clash) 来实现IP池，让爬虫更加高效可用。

#### 2.1 相关代码

本部分的实现在各项目中的`ClashControl.py`文件中，针对不同项目的特点有些许不同。实现了类`ClashControl`其中主要的函数有：

```python
class ClashControl:
    def getProxies(self)
    def checkProxy(self, proxyName)
    def getRandomProxy(self)
    def changeProxyByProxyName(self, proxyName)
    def changeRandomAvailableProxy(self)
```

#### 2.2 工作模式

1. 首先在本地/远程主机配置好clash，并导入代理节点信息，之后保持clash打开状态。本项目中所涉及的clash信息及配置如下：

   ```json
   clash_host = "127.0.0.1"
   controller_port = "65117"
   proxy_port = "1717"
   ```

2. 调用clash提供的RESTful AP进行代理控制，具体见代码；

3. 在项目中对应的位置加入下载和切换策略，并根据目标网站的反爬策略等进行相应的调整，保证爬虫的可用性。

#### 2.3 使用方法

在需要使用到的类中，引入`ClashControl`类并创建对象，设置http请求的代理为clash提供的代理端口，使用类中构造的函数进行爬取策略设计即可。

#### 2.4 依赖

```
Proxy Software ： clash
Python Libraries：
    random
    psutil==5.8.0
    requests==2.23.0
```


### 3. 增量式爬取

由于目标网站经常新增页面，本项目采取增量式爬虫，定期从网站上爬取新的论文信息。

#### 3.1 工作模式

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

#### 3.2 运行方法

直接运行根目录下ACL_Inc.py，PwC_Inc.py，CrossMind_Inc.py，即可每天按时爬取新论文。
```
python ACL_Inc.py
python CrossMind_Inc.py
python PwC_Inc.py
```

#### 3.3 依赖

```
apscheduler==3.6.3
datetime
```





