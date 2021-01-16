import requests

headers = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"
}
url = "https://www.aclweb.org/anthology/sigs/sigann/"
# r = requests.get("https://vimeo.com/383950369?action=load_download_config",headers=headers)
r = requests.get(url, headers=headers)
r.raise_for_status()

# print(r.content)

with open("test.html", "wb") as f:
    f.write(r.content)
