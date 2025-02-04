#!/usr/bin/env python

import subprocess
import os
import sys
import time
import urllib
from optparse import OptionParser

        
        

class MyFancyUrlopener(urllib.FancyURLopener):
    def retrieve(self, url, filename=None, reporthook=None, data=None):
        """retrieve(url) returns (filename, headers) for a local object
        or (tempfilename, headers) for a remote object."""
        url = urllib.unwrap(urllib.toBytes(url))
        if self.tempcache and url in self.tempcache:
            return self.tempcache[url]
        type, url1 = urllib.splittype(url)
        if filename is None and (not type or type == 'file'):
            try:
                fp = self.open_local_file(url1)
                hdrs = fp.info()
                del fp
                return urllib.url2pathname(urllib.splithost(url1)[1]), hdrs
            except IOError, msg:
                pass
        fp = self.open(url, data)
        try:
            headers = fp.info()
            code = fp.code
            if filename:
                tfp = open(filename, 'wb')
            else:
                import tempfile
                garbage, path = urllib.splittype(url)
                garbage, path = urllib.splithost(path or "")
                path, garbage = urllib.splitquery(path or "")
                path, garbage = urllib.splitattr(path or "")
                suffix = os.path.splitext(path)[1]
                (fd, filename) = tempfile.mkstemp(suffix)
                self.__tempfiles.append(filename)
                tfp = os.fdopen(fd, 'wb')
            try:
                result = filename, headers, code
                if self.tempcache is not None:
                    self.tempcache[url] = result
                bs = 1024*8
                size = -1
                read = 0
                blocknum = 0
                if reporthook:
                    if "content-length" in headers:
                        size = int(headers["Content-Length"])
                    reporthook(blocknum, bs, size)
                while 1:
                    block = fp.read(bs)
                    if block == "":
                        break
                    read += len(block)
                    tfp.write(block)
                    blocknum += 1
                    if reporthook:
                        reporthook(blocknum, bs, size)
            finally:
                tfp.close()
        finally:
            fp.close()
        del fp
        del tfp

        # raise exception if actual size does not match content-length header
        if size >= 0 and read < size:
            raise urllib.ContentTooShortError("retrieval incomplete: got only %i out "
                                       "of %i bytes" % (read, size), result)

        return result
    
class GetCodeFromHttp(object):
    url_template = "https://github.com/hannorein/rebound/archive/{version}.zip"
    filename_template = "{version}.zip"
    version = "7184fb43852a6c3721f87dc8b5f6878a540a8dd0"
    
    def directory(self):
        return os.path.abspath(os.path.dirname(__file__))

    def src_directory(self):
        return os.path.join(self.directory(), 'src')
        
    def unpack_downloaded_file(self, filename):
        print "unpacking", filename
        arguments = ['unzip', '-x']
        arguments.append(filename)
        subprocess.call(
            arguments, 
            cwd = os.path.join(self.src_directory())
        )
        subprocess.call(
            ['mv', 'rebound-{version}'.format(version = self.version), 'rebound'],
            cwd = os.path.join(self.src_directory())
        )
        print "done"
        
        
    def start(self):
        if os.path.exists('src'):
            counter = 0
            while os.path.exists('src.{0}'.format(counter)):
                counter += 1
                if counter > 100:
                    print "too many backup directories"
                    break
            os.rename('src', 'src.{0}'.format(counter))
        
        os.mkdir('src')
        
        url = self.url_template.format(version = self.version)
        filename = self.filename_template.format(version = self.version)
        print "downloading version",self.version,"from", url, "to", filename
        opener = MyFancyUrlopener()
        filename, httpmessage, code = opener.retrieve(url, filename = os.path.join(self.src_directory(),filename))
        if code == 404:
            os.remove(filename)
            url = self.backup_url_template.format(version = self.version)
            filename, httpmessage, code = opener.retrieve(url, filename = os.path.join(self.src_directory(),filename))
            
        print "downloading finished"
        self.unpack_downloaded_file(filename)
    
def main(must_download_from_svn = False, version = ''):
    instance = GetCodeFromHttp()
    instance.version = version
    instance.start()

        
    
def new_option_parser():
    result = OptionParser()
    
    result.add_option(
        "--version", 
        default = '31d117bdc92182073d0941c331f76e95f515bfc6',
        dest="version",
        help="git revision to download from github",
        type="string"
    )
    
    return result
    
if __name__ == "__main__":
    options, arguments = new_option_parser().parse_args()
    main(**options.__dict__)
    

