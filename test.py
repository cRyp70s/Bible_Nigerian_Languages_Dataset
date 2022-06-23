from queue import Queue
import requests
from scraper import scrape_chapter

def test_scrape_chapter():
    """
        Test scraper for Genesis chapter 1
    """
    content = requests.get("https://www2.bible.com/bible/2615/GEN.1.IGL70").text
    queue = Queue(500)
    next = scrape_chapter(content, queue)
    for i in range(31):
        try:
            _ = queue.get_nowait()
        except:
            assert False
    assert next == "https://www2.bible.com/bible/2615/GEN.2.IGL70"
