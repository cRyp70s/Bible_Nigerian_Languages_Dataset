import csv
import os
import os.path as pth
import typer
import threading
from urllib.parse import urljoin
import requests
from queue import Queue, Empty
from bs4 import BeautifulSoup

DONE_STRING = "<<DONE>>"

def scrape_chapter(html_text: str, 
                    out_queue: Queue,
                    chapters_queue: Queue) -> str:
    """
        Scrape verses and add to queue
        :param html_text: source code of the page
        :param out_queue: Queue object to write verses to

        Returns the next chapter's url
    """
    bs = BeautifulSoup(html_text, "lxml")
    next_page = get_nextpage(bs)
    if next_page:
        chapters_queue.put(next_page)
    chapter = bs.select_one(".reader > h1").text
    verses = bs.select(".verse")
    chapter_verse = []
    for verse in verses:
        verse_no = verse.select_one(".label")
        if not verse_no or verse_no.text == "#":
            continue
        # To Add preprocess
        verse_text = verse.select_one(".content").text
        try:
            chapter_verse.append((int(verse_no.text), verse_text))
        except Exception as e:
            print(e)
    out_queue.put((chapter, chapter_verse))
    return next_page

def scrape(chapters_queue: Queue, out_queue: Queue, id: int):
    while True:
        url = chapters_queue.get()
        print(f"Got {url} - Thread {id}")
        if url == DONE_STRING:
            chapters_queue.put(DONE_STRING)
            return
        res = requests.get(url)
        if not res.ok:
            res.raise_for_status()
        next_chapter = scrape_chapter(res.text, out_queue, chapters_queue)
        print(f"Scraping: {next_chapter}")

def get_nextpage(bs4_obj: BeautifulSoup):
    next_ = bs4_obj.select_one(".next-arrow > a")
    if not next_:
        return DONE_STRING
    relative =  next_.get("href")
    return urljoin("https://www2.bible.com/", relative)

def create_if_not_exists(dir_: str):
    if not pth.exists(dir_):
        os.mkdir(dir_)
    if not pth.isdir(dir_):
        raise Exception("Exists but isn't directory")

def outputer(book: str, chapter: int, verses: list,
             data_folder):
    print(f"Writing for {book} - {chapter}")
    create_if_not_exists(data_folder)
    book_pth = pth.join(data_folder, book)
    create_if_not_exists(book_pth)
    chapter_pth = pth.join(book_pth, f"{chapter}.csv")
    with open(chapter_pth, "w") as fileobject:
        csv_writer = csv.writer(fileobject)
        csv_writer.writerow(["Verse", "Text"])
        csv_writer.writerows(verses)

def outputer_thread(out_queue: Queue, chapters_queue: Queue, data_folder: str):
    while True:
        print("Waiting: ")
        try:
            output = out_queue.get(timeout=10)
            book_chapter, verses = output
            book_chapter = book_chapter.split()
            book, chapter = '_'.join(book_chapter[:-1]), int(book_chapter[-1])
            outputer(book, chapter, verses, data_folder)
        except Empty:
            is_done = chapters_queue.get()
            if is_done == DONE_STRING:
                return
            else:
                chapters_queue.put(is_done)


def main(start_url: str, thread_no: int = 3, data_folder: str = "data"):
    """
        Scrape data for a specific bible version
        from bible.com
    """
    chapters_queue = Queue()
    chapters_queue.put(start_url)
    out_queue = Queue()
    threads = [threading.Thread(target=scrape,
                args=(chapters_queue, out_queue, id)) for id in range(thread_no)]
    for thread in threads:
        thread.start()
    out_thread = threading.Thread(target=outputer_thread, args=(out_queue, chapters_queue, data_folder))
    out_thread.start()
    for thread in threads+[out_thread]:
        thread.join()
        
if __name__ == "__main__":
    typer.run(main)