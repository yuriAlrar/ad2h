import os
import re
import urllib3
import requests
import time
import json
from lxml import etree
class debugIO():
    def __init__(self):
        self.vm = True
        self.standard = ""
        self.error = "\n"
        self.eflag = False
    def mode(self, flag):
        self.vm = True if flag else False
    def tostr(self, prt):
        text = ""
        if not self.vm:
            return
        if type(prt) is str:
            text = prt
        elif type(prt) is list:
            for i in prt:
                text = text + i + "\n"
        elif type(prt) is dict:
            for i in prt:
                text = str(i) + "\t" + str(prt[i]) + "\n"
        else:
            text = ">> invalid type"
        return text
    def sprint(self, prt, *, flag=True, end="\n"):
        self.standard = self.tostr(prt)
        if self.vm and flag:
            print(self.standard, end=end)
    def eprint(self, prt):
        self.eflag = True
        self.error = self.error + "\n" + self.tostr(prt)
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
        #view list
        self.vl = []
        #image url list
        self.il = []
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
            self.eprint("ad::connector:connection failed")
            return False
        if res.status_code > 399:
            #ステータスコードが400以上
            self.eprint("http status code:" + str(res.status_code))
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
    def dump(self, flag=True):
        '''
        ilとvlをダンプする
        '''
        if flag:
            with open(self.work_dir + "/.vl", "w") as f:
                json.dump(self.vl, f)
            with open(self.work_dir + "/.il", "w") as f:
                json.dump(self.il, f)
        else:
            os.remove(self.work_dir + "/.vl")
            os.remove(self.work_dir + "/.il")
        return
    def setSaveDir(self, title):
        self.title = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '_', title)
        abs_path = self.work_dir + "/" + self.title
        abs_path = abs_path.replace("//", "/")
        self.work_dir = abs_path
        if not os.path.exists(self.work_dir):
            os.mkdir(self.work_dir)
        else:
            if os.path.exists(self.work_dir + "/.vl") and os.path.exists(self.work_dir + "/.il"):
                with open(self.work_dir + "/.vl", "r") as f:
                    self.vl = json.load(f)
                with open(self.work_dir + "/.il", "r") as f:
                    self.il = json.load(f)

        return True
    def downloadImage(self, path, *, save_directory = ""):
        ext = path.split(".")[-1]
        if path in self.il:
            self.sprint(" aD::dI:already downloaded > skip")
            return
        res = requests.get(path)
        if res.status_code > 400:
            return False
        fina = str( len(self.il) ).zfill(4) + "." + ext
        #genereate absolute path
        if save_directory:
            save_directory = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '_', save_directory)
            abs_path = self.work_dir + "/" + save_directory
            abs_path = abs_path.replace("//", "/")
            if not os.path.exists(abs_path):
                os.mkdir(abs_path)
        else:
            abs_path = self.work_dir
        with open( abs_path + "/" + fina , "wb") as f:
            f.write(res.content)
            self.sprint(" Download > " + fina)
        self.name_rule = self.name_rule + 1
        #ダウンロード完了リスト
        self.il.append(path)
        return True
class modEhentai(autoDownloader):
    def __init__(self, work_directory=""):
        super().__init__(work_directory)
        self.title = ""
        self.index = ""
        self.nextUrl = ""
    def firstInit(self, url):
        '''
        titleを取得，ディレクトリ作成
        nexturlをセット
        '''
        self.index = url
        #タイトル名取得のため予め接続
        self.connector(url)
        #タイトル，保存ディレクトリを作成
        titles = self.html.xpath("//h1")
        for t in titles:
            if "id" in t.attrib and t.attrib["id"] == "gj":
                self.setSaveDir(t.text)
                self.sprint("TITLE : \t" + self.title)
                self.sprint("SAVE DIR : \t" + self.work_dir)
        anchors = self.getAnchors(url, False)
        if not anchors:
            self.eprint("failed top page analysis")
            return False
        for anchor in anchors:
            for img in anchor.xpath("img"):
                if "alt" in img.attrib and img.attrib["alt"].isdecimal() and int( img.attrib["alt"] ) == 1:
                    self.nextUrl = anchor.attrib["href"]
                    return True
        self.eprint("mE::fI:cannot find next page...")
        return False
    def nextAnchor(self):
        self.vl.append(self.nextUrl)
        self.sprint("TRACE : \t" + self.nextUrl, end="")
        anchors = self.getAnchors(self.nextUrl)
        if not anchors:
            self.eprint("mE::nA:connection failed")
            return False
        for a in anchors:
            for img in a.xpath("img"):
                if "id" in img.attrib and img.attrib["id"] == "img":
                    self.downloadImage( img.attrib["src"] )
                    if self.nextUrl == str( a.attrib["href"] ):
                        self.eprint("next url :"+ str( a.attrib["href"] )+" visited")
                        return False
                    else:
                        self.nextUrl = str( a.attrib["href"] )
                        self.dump()
                        return True
        self.eprint("mE::nA:cannot find next page...")
        return False
    def traceImage(self, url):
        flag = self.firstInit(url)
        while flag:
            flag = self.nextAnchor()
            if self.eflag:
                print(self.error)
            time.sleep(2)
        self.dump(flag)
        return flag

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