#!/usr/bin/env python

import argparse
import re
import time
from imagegrabber import ImageParser, ImageGrabber

"""
Parses text for fatpita.net URLs and downloads the images

Parses a provided logfile or text for URLs to fatpita.net
images and downloads them. This can be done in a given amount of 
multiple threads to speed the up the parsing and downloading.

Example:
    $ python fatpita_parser.py -f irc.log -n 3 pictures/
"""

class FatpitaImageParser(ImageParser):
    """
    HTMLParser for fatpita.net image URLs
   
    HTMLParser that parses the URL to a fatpita image file
    from a fatpita HTML page.
    """

    FATPITA_IMAGE_URL_PATH = "http://fatpita.net/images/"

    def __init__(self):
        ImageParser.__init__(self)
        self.reset()
    
    def handle_starttag(self, tag, attrs):
        if tag == 'img' and attrs:
            # Magic hard-coded fetching of the image URL
            if attrs[0][1][:7] == 'images/':
                image = attrs[0][1][7:]
                # Remove trailing metadata from the image filename
                self.image_filename = image.split('?', 1)[0]

    def get_image_url(self):
        if self.image_filename:
            return (FatpitaImageParser.FATPITA_IMAGE_URL_PATH +
                    self.image_filename)
        else:
            return None
            
    def reset(self):
        ImageParser.reset(self)
        self.image_filename = ""

FATPITA_URL_PATTERN = re.compile(r"http://fatpita.net/\?i=\d+")
    
def parse_logfile(file):
    print("Parsing log file '%s' for fatpita URLs" % file)
    with open(file) as log:
        text = log.read()
    return FATPITA_URL_PATTERN.findall(text)

def parse_line(line):
    print("Parsing line '%s' for fatpita URLs" % line)
    return FATPITA_URL_PATTERN.findall(line)

def main():
    description = ("Parse a log file or provided text for fatpita URLs and"
                " download the images to the specified path.")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('download_path', type=str,
                        help='Path to logfile to parse',
                        metavar="download_path")
    parser.add_argument('-f', '--logfile', action="store", type=str,
                        help='Path to logfile to parse',
                        metavar="LOGFILEPATH")
    parser.add_argument('-t', '--text', action="store", type=str,
                        help='Path to logfile to parse',
                        metavar="TEXT")
    parser.add_argument('-n', '--threads', action="store", type=int,
                        help='Number of threads to run in',
                        metavar="NR_THREADS")
    args = parser.parse_args()

    timestamp_start = time.time()

    if args.logfile:
        urllist = parse_logfile(args.logfile)
    elif args.text:
        urllist = parse_line(args.text)
    else:
        print("Error: Must provide either text or logfile")
        parser.print_usage()
        exit(1)
    nr_threads = args.threads if (args.threads and args.threads > 0) else 2
    image_grabber = ImageGrabber(args.download_path)
    image_grabber.grab_images(urllist, FatpitaImageParser, nr_threads)

    print("Finished. Time taken: %.2f seconds" %
            (time.time() - timestamp_start))

if __name__ == '__main__':
    main()