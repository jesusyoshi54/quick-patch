from html.parser import HTMLParser
from collections import namedtuple
from re import subn
from functools import lru_cache
import requests


class romhacksParser(HTMLParser):
    mainMap = {1: "HackName", 2: "Creator", 3: "Release", 4: "Tags"}
    HackMap = {
        1: "HackName",
        2: "Version",
        3: "Link",
        4: "Creator",
        5: "Star_Count",
        6: "Release",
    }

    def start(self, main):
        self.HackTable = False
        self.hacks = []
        self.main = main
        self.lastHack = 0
        self.header = 0
        self.cell = None

    def handle_data(self, data):
        if self.HackTable and self.cell:
            if self.main:
                setattr(self.lastHack, self.mainMap[self.cell], data)
            else:
                setattr(self.lastHack, self.HackMap[self.cell], data)

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            for a in attrs:
                if a[0] == "id" and a[1] == "myTable":
                    self.HackTable = True
        if tag == "tr" and self.HackTable:
            if not self.header:
                self.header = 1
            else:
                self.cell = 0
                self.lastHack = Hack()
                self.hacks.append(self.lastHack)
        if tag == "td" and self.HackTable:
            self.cell += 1
        if tag == "a" and self.HackTable:
            for a in attrs:
                if a[0] == "href":
                    self.lastHack.url = a[1]

    def handle_endtag(self, tag):
        if tag == "table" and self.HackTable:
            self.HackTable = False


# storage class, but won't data class because I dont have all class data at once
class Hack:
    def print_dat(self):
        print(self.__dict__)

    def DownloadAndPatch(self, root, vanilla):
        invalid = r'<>:"/\|?*'

        def rpinv(x):
            for a in invalid:
                x = x.replace(a, " ")
            return x

        name = Path(f"hacks/{rpinv(self.HackName)}/{rpinv(self.Version)}")
        if os.path.exists(name):
            shutil.rmtree(name)
        name.mkdir(exist_ok=True, parents=True)
        hack = requests.get(urljoin(root, self.url))
        with open(
            name / (f"{rpinv(self.HackName)}_ver_{rpinv(self.Version)}.zip"), "wb"
        ) as f:
            f.write(hack.content)
        with zipfile.ZipFile(
            name / (f"{rpinv(self.HackName)}_ver_{rpinv(self.Version)}.zip")
        ) as zip_ref:
            zip_ref.extractall(name)
        bps = self.FindBps(name)
        subprocess.call(
            [
                "flips",
                "--apply",
                name / bps,
                vanilla,
                name / (f"{rpinv(self.HackName)}.z64"),
                "--ignore-checksum",
            ]
        )

    def FindBps(self, path):
        p = os.path.join(os.getcwd(), path)
        for f in os.listdir(p):
            if ".bps" in Path(f).suffixes:
                return f
        return None


@lru_cache(maxsize=25)
def get_sm64rh_hack_page(hack):
    url = "https://sm64romhacks.com/" + hack.url
    r = requests.get(url)
    p = romhacksParser()
    p.start(0)
    p.feed(r.text)
    p.root = url
    return p


# format the json
def format_sm64rh_hacks(js):
    h_list = namedtuple("hack_list", "hacks")
    h = []
    base = "hacks/"

    def get_creator(hack):
        creators = set()
        for v in hack["versions"]:
            creators.update(v["creators"])
        return ", ".join(creators)

    for hack in js:
        h_obj = Hack()
        h_obj.HackName = hack["name"]
        h_obj.Creator = get_creator(hack)
        link = subn("[ ()]", "_", hack["name"])[0]
        link = subn("[':/]", "", link)[0]
        link = base + link.strip().lower()
        h_obj.url = link
        h.append(h_obj)
    return h_list(h)


def get_all_sm64rh_hacks():
    url = "https://sm64romhacks.com/_data/hacks.json"
    p = format_sm64rh_hacks(requests.get(url).json()["hacks"])
    return p
