Multi-threaded python image grabber
===================================

Generic "imagegrabber" python module for parsing text e.g. in an IRC logfile for image URLs and downloading the images in multiple threads. Comes with an example script "fatpita-parser" using the module for the image site http://www.fatpita.net. Requires python 2.

Example usage:
--------------
python fatpita_parser.py -t "(13:37:00) (@phooey) http://fatpita.net/?i=4995" pictures/
python fatpita_parser.py -f data/irc.log pictures/
python fatpita_parser.py -f data/huge_irc.log pictures/ -n 4