import threading
from contextlib import closing
from HTMLParser import HTMLParser, HTMLParseError
from urllib import urlretrieve, ContentTooShortError
from urllib2 import urlopen, URLError
from Queue import Queue

"""
Image grabber for downloading images

This module contains classes for both parsing HTML pages for image URLs
and then downloading them in a multithreaded fashion. A list of URLs to
HTML pages, an HTMLParser to parse them for image URLs, a download path and
the number of threads to be used is passed to the ImageGrabber class.

The ImageGrabber class then feeds the URL list to a queue, and starts multiple
threads to open the HTML pages in the list and parse them for URLs with the
given HTMLParser. All image URLs found are then feed to a different queue from
which the images are then downloaded in multiple threads to the provided path.
"""

class ImageParser(HTMLParser):
    """
    Interface class subclassing HTMLParser for parsing an HTML page for an
    image URL.

    This should be subclassed with an HTMLParser that parses out the URL
    for the image to be downloaded and implements a get_image_url method
    that returns it.
    """

    def get_image_url(self):
        """Method that should return URL to the image, empty if not found."""
        return ""

class ParseThread(threading.Thread):
    """
    Thread that parses an HTML page for image URLs
    
    Thread that uses a supplied ImageParser to parse URLs for images
    to download from an HTML page grabbed from a queue of URLs of pages
    to parse.
    """

    def __init__(self, number, image_parser, page_url_queue, image_url_queue,
                 print_queue):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.number = number
        self.page_url_queue = page_url_queue
        self.image_url_queue = image_url_queue
        self.print_queue = print_queue
        self.image_parser = image_parser

    def run(self):
        self.print_queue.put("Parse Thread %d running" % self.number)
        while True:
            page_url = self.page_url_queue.get()
            html_data = self.__read_page(page_url)
            image_url = self.__find_image_url(html_data, page_url)
            if image_url:
                self.image_url_queue.put(image_url)
            self.page_url_queue.task_done()

    def __read_page(self, page_url):
        self.print_queue.put('Opening page: %s' % page_url)
        html_data = ""
        try:
            with closing(urlopen(page_url)) as page:
                html_data = page.read()
        except URLError:
            self.print_queue.put("Oops! URLError at %s" % page_url)
        return html_data

    def __find_image_url(self, html_data, page_url):
        try:
            self.image_parser.reset()
            self.image_parser.feed(html_data)
            image_url = self.image_parser.get_image_url()
            if image_url:
                self.print_queue.put('Found image: %s' % image_url)
            else:
                self.print_queue.put('No image found at: %s' % page_url)
            return image_url
        except HTMLParseError:
            self.print_queue.put("Oops! HTMLParseError at %s" % page_url)
            self.print_queue.put("HTML data: %s" % html_data)
            return None

class PrintThread(threading.Thread):
    """
    Thread for printing messages to standard output
    
    Prints messages grabbed from a queue of messages to be printed in a 
    synchronized manner.
    """

    def __init__(self, message_queue):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.message_queue = message_queue

    def run(self):
        self.message_queue.put("PrintThread running")
        while True:
            message = self.message_queue.get()
            print(message)
            self.message_queue.task_done()

class DownloadThread(threading.Thread):
    """
    Thread for downloading images
    
    Downloads image files grabbed from a queue with URLs to images.
    """

    def __init__(self, number, dl_path, image_url_queue, print_queue):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.number = number
        self.image_url_queue = image_url_queue
        self.dl_path = dl_path
        self.print_queue = print_queue

    def run(self):
        self.print_queue.put("Download Thread %d running" % self.number)
        while True:
            filename = self.image_url_queue.get()
            self.__download_image(filename)
            self.image_url_queue.task_done()

    def __download_image(self, image_url):
        try:
            filename = image_url.split('/')[-1]
            self.print_queue.put("Downloading %s to %s" %
                (image_url,(self.dl_path + filename)))
            urlretrieve(image_url, self.dl_path + filename)
        except ContentTooShortError:
            self.print_queue.put(("Oops! ContentTooShortError,"
                " could not download %s") % image_url)
        except IOError:
            self.print_queue.put("Oops! IOError, could not download %s" %
                image_url)

class ImageGrabber():
    """
    Downloads images from a list of URLs
    
    ImageGrabber that grabs images from a provided list of URLs
    using a provided ImageParser and downloads them to the provided path.
    """

    def __init__(self, download_path):
        self.download_path = download_path

        self.page_url_queue = Queue()
        self.image_download_queue = Queue()
        self.print_queue = Queue()

        self.print_thread = PrintThread(self.print_queue)
        self.print_thread.start()

    def grab_images(self, urllist, image_parser, nr_threads):
        """
        Grab images from the provided list of URLs.

        Keyword arguments:

        urllist      -- list of URLs to HTML pages to open and parse
        image_parser -- image parser class to use to parse HTML page for
                        image URLs 
        nr_threads   -- number of image parsing and image download threads
                        to use.
        """
        for i in range(nr_threads):
            download_thread = DownloadThread(i, self.download_path,
                self.image_download_queue, self.print_queue)
            download_thread.start()
            parse_thread = ParseThread(i, image_parser(), self.page_url_queue,
                self.image_download_queue, self.print_queue)
            parse_thread.start()

        for url in urllist:
            self.page_url_queue.put(url)

        self.page_url_queue.join()
        self.image_download_queue.join()
        self.print_queue.join()
