from queue import Queue
import requests
from scraper import scrape_chapter

def test_scrape_chapter():
    content = requests.get("https://www2.bible.com/bible/2615/GEN.1.IGL70").text
    queue = Queue(500)
    queue = scrape_chapter(content, queue)
    for i in range(31):
        try:
            _ = queue.get_nowait()
        except:
            assert False
    assert True
