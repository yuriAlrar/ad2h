import os
import re
import urllib3
import requests
import time
from lxml import etree
class debugIO():
    def __init__(self):
        self.vm = True
    def mode(self, flag):
        self.vm = True if flag else False
    def printf(self, prt):
        if not self.vm:
            return
        if type(prt) is str:
            print(prt)
        elif type(prt) is list:
            for i in prt:
                print(i)
        elif type(prt) is dict:
            for i in prt:
                print(str(i) + "\t" + str(prt[i]))
        else:
            print("invalid type")
        
class autoDownloader(debugIO):
    def __init__(self, work_directory=""):
        super().__init__()
        self.html = ""
        self.name_rule = 0
        if os.path.exists(work_directory):
            self.work_dir = work_directory
            if(self.work_dir[-1:]=="/"):
                self.work_dir = self.work_dir[:-1]
        else:
            self.work_dir = os.getcwd()
        self.work_dir = self.work_dir.replace("\\", "/")
    def connector(self, url):
        '''
        self.htmlへの入力はconnectorのみが行う
        '''
        try:
            headers= {
                "User-Agent"      : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0",
                "Connection"      : "keep-alive",
                "Accept"          : "text/html,application/xhtml+xml,application/xml;",
                "Referrer"        : "https://www.google.co.jp",
                "Accept-Language" : "ja;q=1.0"
            }
            res = requests.get(url, headers=headers)
        except:
            self.printf("ad::connector:connection failed")
            return False
        if res.status_code > 399:
            #ステータスコードが400以上
            self.printf("http status code:" + str(res.status_code))
            return False
        try:
            self.html = etree.fromstring( res.text, etree.HTMLParser() )
        except:
            self.html = False
            return False
        return True
    def getAnchors(self, url, force_connection = True):
        '''
        force_connection: nextUrlに接続，connectorを事前に呼び出した等の場合はFalseを設定すると接続負荷を下げられる
        '''
        cargo = []
        #htmlになにもない > 未接続
        if not len(self.html) or force_connection:
            if not self.connector(url):
                #接続失敗 > 空配列を返す
                return cargo
        for a in self.html.xpath("//a"):
            if "href" in a.attrib:
                cargo.append( a )
        return cargo
    def downloadImage(self, path, *, save_directory = ""):
        ext = path.split(".")[-1]
        self.printf("CONN. : \t" + path)
        res = requests.get(path)
        if res.status_code > 400:
            return False
        fina = str(self.name_rule).zfill(4) + "." + ext
        #genereate absolute path
        save_directory = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '_', save_directory)
        abs_path = self.work_dir + "/" + save_directory
        abs_path = abs_path.replace("//", "/")
        if not os.path.exists(abs_path):
            os.mkdir(abs_path)
        with open( abs_path + "/" + fina , "wb") as f:
            f.write(res.content)
        self.name_rule = self.name_rule + 1
        return True
class modEhentai(autoDownloader):
    def __init__(self, work_directory=""):
        super().__init__(work_directory)
        self.title = ""
        self.index = ""
        self.nextUrl = ""
        self.vl = []
        self.il = []
    def firstInit(self, url):
        self.index = url
        #タイトル名取得のため予め接続
        self.connector(url)
        #タイトル，保存ディレクトリを作成
        titles = self.html.xpath("//h1")
        for t in titles:
            if "id" in t.attrib and t.attrib["id"] == "gj":
                self.title = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '_', t.text)
                self.printf("TITLE : \t" + self.title)
                self.printf("SAVE DIR : \t" + self.work_dir + "/" + self.title)
        anchors = self.getAnchors(url, False)
        if not anchors:
            self.printf("failed top page analysis")
            return False
        for anchor in anchors:
            for img in anchor.xpath("img"):
                if "alt" in img.attrib and ( img.attrib["alt"] == "01" or img.attrib["alt"] == "1" ):
                    self.nextUrl = anchor.attrib["href"]
                    return True
        self.printf("mE::fI:cannot find next page...")
        return False
    def nextAnchor(self):
        #nextUrlが巡回済み > false
        if self.nextUrl in self.vl:
            self.printf("next url : visited")
            return False
        else:
            self.vl.append(self.nextUrl)
            self.printf("TRACE : \t" + self.nextUrl)
            anchors = self.getAnchors(self.nextUrl)
            if not anchors:
                self.printf("mE::nA:connection failed")
                return False
            for a in anchors:
                for img in a.xpath("img"):
                    if "id" in img.attrib and img.attrib["id"] == "img":
                        self.il.append(img.attrib["src"])
                        self.nextUrl = str( a.attrib["href"] )
                        return True
        self.printf("cannot find next page...")
        return False
    def traceImage(self, url):
        flag = self.firstInit(url)
        while flag:
            flag = self.nextAnchor()
            time.sleep(1)
        for i in self.il:
            self.downloadImage(i, save_directory=self.title)
            time.sleep(2)

def main():
    route = "./Incinerator"
    if not os.path.exists(route):
        os.mkdir(route)
    url = ""
    print("Get image from E-hentai.org")
    print("Enter any URL >> ", end="")
    url = input("")
    url = url + "?nw=session"
    index = modEhentai(route)
    index.traceImage(url)
    return
if __name__ == '__main__':
    while True:
        main()