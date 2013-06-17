#coding=utf-8
'''
Created on 2013-3-20

@author: Newton
'''
import sys
import urllib2
import re


class Extractor(object):

    def __init__(self, url='', blockSize=3):
        self.url = url
        self.blockSize = blockSize

        # Compile re
        self.reDATA = re.compile('<!DOCTYPE.*?>', re.I | re.S)
        # HTML comment
        self.reComment = re.compile('<!--[\s\S]*?-->')
        # Scripts
        self.reScript = re.compile('<\s*script[^>]*>[\w\W]*?<\s*/\s*script\s*>', re.I)
        # CSS
        self.reStyle = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)
        # HTML Tag
        self.reTag = re.compile('<[\s\S]*?>')
        # Special charcaters
        self.reSpecial = re.compile('&.{1,5};|&#.{1,5};')
        # Spaces
        self.reSpace = re.compile('\s+')
        # Word wrap transform
        self.reWrap = re.compile('\r\n|\r')
        # Reduce redundancy
        self.reRedun = re.compile('\n{%s,}' % (self.blockSize+1))

    def reset(self):
        self.url = ''
        self.rawPage = ''
        self.text = ''
        self.isGB = True
        self.textLines = []
        self.blocksLen = []
        self.isCharsetGB = True

    def getRawPage(self, sourceType):
        if sourceType == 'url':
            self.rawPage = urllib2.urlopen(self.url).read()
        elif sourceType == 'path':
            f = open(self.url)
            self.rawPage = f.read()
            f.close()
        elif sourceType == 'text':
            self.rawPage = self.url

    def handleEncoding(self):
        match = re.search('charset\s*=\s*"?([\w\d-]*)"?', self.rawPage, re.I)
        if match:
            charset = match.group(1).lower()
            if charset.find('gb') == -1:
                self.isCharsetGB = False

    def preProcess(self, doc):
        doc = self.reDATA.sub('', doc)
        doc = self.reComment.sub('', doc)
        doc = self.reScript.sub('', doc)
        doc = self.reStyle.sub('', doc)
        doc = self.reTag.sub('', doc)
        doc = self.reSpecial.sub('', doc)
        doc = self.reWrap.sub('\n', doc)
        doc = self.reRedun.sub('\n'*(self.blockSize+1), doc)
        return doc

    # Split the preprocessed text into lines by '\n'
    def getTextLines(self, text):
        lines = text.split('\n')
        for line in lines:
            if line:
                line = self.reSpace.sub('', line)
            self.textLines.append(line)

    # Calculate the length of every block
    def calcBlockLens(self):
        textLinesCnt = len(self.textLines)
        blockLen = 0
        blockSize = min([textLinesCnt, self.blockSize])
        for i in range(blockSize):
            blockLen = blockLen + len(self.textLines[i])
        self.blocksLen.append(blockLen)

        if(blockSize != self.blockSize):
            return

        for i in range(1, textLinesCnt - self.blockSize):
            blockLen = self.blocksLen[i-1]\
                + len(self.textLines[i-1+self.blockSize])\
                - len(self.textLines[i-1])
            self.blocksLen.append(blockLen)

    # Merge the most possibile blocks as the final plaintext
    def getPlainText(self, data='', sourceType='url'):
        self.reset()
        self.url = data
        self.getRawPage(sourceType)
        self.handleEncoding()
        preProcDoc = self.preProcess(self.rawPage)
        # f = open('dump')
        # preProcDoc = f.read()
        self.getTextLines(preProcDoc)
        self.calcBlockLens()

        i = maxTextLen = 0
        blocksCnt = len(self.blocksLen)
        curTextLen = 0
        part = ''
        while i < blocksCnt:
            if self.blocksLen[i] > 0:
                if self.textLines[i]:
                    part = '%s%s\n' % (part, self.textLines[i])
                    curTextLen += len(self.textLines[i])
            else:
                curTextLen = 0
                part = ''
            if curTextLen > maxTextLen:
                self.text = part
                maxTextLen = curTextLen
            i += 1

        if self.isCharsetGB:
            try:
                self.text = self.text.decode('gb2312').encode('utf-8')
            except Exception:
                pass
        return self.text


if __name__ == '__main__':
    args = sys.argv
    if len(args) <= 1:
        print 'Usage: extractor.py [url]'
    else:
        ext = Extractor()
        f = open('plain.txt', 'w')
        f.write(ext.getPlainText(args[1]))
        f.close
