import zipfile
import re

from book import Book

import logging

class Archive(object):
    def __init__(self, stream):
        self.logger=logging.getLogger('performance')
        self.logger.info("Opening archive ")

        are_urls = len(stream) > 0 and \
            (stream.lower().startswith("http://") or \
             stream.lower().startswith("https://"))

        are_blobs = len(stream) > 0 and \
            (stream.lower().startswith("blob:"))

        if (are_urls):
            import requests
 
            from cStringIO import StringIO
            mmap = StringIO(requests.get(stream, stream=True).raw.read())
 
        elif (are_blobs):
            from azure.storage.blob import BlobService
            import os
            import io

            sas_token = os.environ['BLOB_SAS_TOKEN']
            if (sas_token[0] == '?'):
                 sas_token = sas_token[1:]

            blob_service = BlobService(account_name = os.environ['BLOB_ACCOUNT_NAME'], sas_token = sas_token)
            stream = stream[5:]
            blob=blob_service.get_blob_to_bytes(os.environ['BLOB_CONTAINER_NAME'], stream)
            mmap = io.BytesIO(blob)

        else:
            from cStringIO import StringIO

            mmap=StringIO(open(stream).read())

        self.logger.debug("Opened archive")
 
        self.logger.info("Slurped archive")
        self.zip = zipfile.ZipFile(mmap)
        self.logger.debug("Examining books in archive")
        self.filenames = [entry.filename for entry in self.zip.infolist()]
        book_pattern = re.compile('([0-9]*)_metadata\.xml')
        page_pattern = re.compile('ALTO\/([0-9]*?)_([0-9_]*)\.xml')
        self.logger.debug("Enumerating books")
        bookmatches=filter(None, [ book_pattern.match(name) for name in self.filenames ])
        pagematches=filter(None, [ page_pattern.match(name) for name in self.filenames ])
        self.book_codes={ match.group(1) : [] for match in bookmatches }
        for match in pagematches:
            self.book_codes[ match.group(1) ].append(match.group(2))
        self.logger.info("Enumerated books")


    def zip_info_for_book(self, book_code):
        return self.zip.getinfo(book_code + '_metadata.xml')

    def zip_info_for_page(self, book_code, page):
        return self.zip.getinfo('ALTO/' + book_code + '_' + page + '.xml')

    def metadata_file(self, book_code):
        return self.zip.open(book_code + '_metadata.xml')

    def page_file(self, book_code, page):
        return self.zip.open('ALTO/' + book_code + '_' + page + '.xml')

    def __getitem__(self, index):
        self.logger.debug("Creating book")
        return Book(self.book_codes.keys()[index],self)

    def __iter__(self):
        for book in self.book_codes:
            self.logger.debug("Creating book")
            yield Book(book, self)

    def __len__(self):
        return len(self.book_codes)
