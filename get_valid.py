import threading
import queue
import requests

q = queue.Queue()
valid_proxies = []

with open("proxy-list.txt", 'r') as f:
    proxies = f.read().split("\n")
    for p in proxies[:20]:
        q.put(p)


def check_proxies():
    global q
    with open("valid-proxies.txt", "a+") as f:
        while not q.empty():
            proxy = q.get()
            try:
                res = requests.get("http://ipinfo.io/json",
                                   proxies={"http": proxy,
                                            "https": proxy})
            except:
                continue
            if res.status_code == 200:
                f.write(proxy + "\n")


for _ in range(10):
    threading.Thread(target=check_proxies).start()