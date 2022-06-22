import typer
import threading
import requests
from queue import Queue
from bs4 import BeautifulSoup

def scrape_chapter(html_text: str, queue: Queue) -> Queue:
    bs = BeautifulSoup(html_text, "lxml")
    verses = bs.select(".verse > .content")
    for verse in verses:
        queue.put(verse.text)
    return queue
