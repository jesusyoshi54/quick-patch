from re import subn
from functools import lru_cache
import requests, os, shutil, zipfile, subprocess
from urllib.parse import urljoin
from pathlib import Path


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

        name = Path(f"hacks/{rpinv(self.hack_name)}/{rpinv(self.version)}")
        if os.path.exists(name):
            shutil.rmtree(name)
        name.mkdir(exist_ok=True, parents=True)
        # this is very unintuitive
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        hack = requests.head(root + self.url, allow_redirects=False, headers=headers)
        print(urljoin(root, hack.headers["Location"]))
        hack = requests.get(urljoin(root, hack.headers["Location"]))
        with open(
            name / (f"{rpinv(self.hack_name)}_ver_{rpinv(self.version)}.zip"), "wb"
        ) as f:
            f.write(hack.content)
        zip = Path(name / self.FindZip(name))
        print(zipfile.is_zipfile(zip), zip.exists(), zip)
        with zipfile.ZipFile(Path(name / self.FindZip(name))) as zip_ref:
            zip_ref.extractall(name)
        bps = self.FindBps(name)
        subprocess.call(
            [
                "flips",
                "--apply",
                name / bps,
                vanilla,
                name / (f"{rpinv(self.hack_name)}.z64"),
                "--ignore-checksum",
            ]
        )

    def FindBps(self, path):
        p = os.path.join(os.getcwd(), path)
        for f in os.listdir(p):
            if ".bps" in Path(f).suffixes:
                return f
        return None

    def FindZip(self, path):
        p = os.path.join(os.getcwd(), path)
        for f in os.listdir(p):
            if ".zip" in Path(f).suffixes:
                return f
        return None


def format_version_js(hack_url: str, hack_name: str):
    hack_versions = requests.get(
        f"https://sm64romhacks.com/api/hacks/?hack_name={hack_url}"
    ).json()["patches"]
    versions = []
    for version_js in hack_versions:
        version = Hack()
        version.hack_id = version_js["hack_id"]
        version.hack_name = hack_name
        version.version = version_js["hack_version"]
        version.url = str(version_js["hack_id"])
        version.version_url = hack_url
        versions.append(version)
    return versions


# format the json
def format_sm64rh_hacks(js: dict):
    hack_list = []

    for hack in js:
        hack_obj = Hack()
        hack_obj.hack_name = hack["hack_name"]
        hack_obj.creator = hack["hack_author"]
        hack_obj.url = hack["hack_url"]
        hack_list.append(hack_obj)
    return hack_list


def get_all_sm64rh_hacks():
    url = "https://sm64romhacks.com/api/hacks"
    hack_list = format_sm64rh_hacks(requests.get(url).json()["hacks"])
    return hack_list
