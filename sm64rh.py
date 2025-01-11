from re import subn
from functools import lru_cache
import requests, os, shutil, zipfile, subprocess
from urllib.parse import urljoin
from pathlib import Path


# storage class, but won't data class because I dont have all class data at once
class Hack:
    versions: list = None
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
        hack = requests.get(
            urljoin(root, self.url), allow_redirects=False, headers=headers
        )
        with open(
            name / (f"{rpinv(self.hack_name)}_ver_{rpinv(self.version)}.zip"), "wb"
        ) as f:
            f.write(hack.content)
        zip = Path(name / self.FindZip(name))
        with zipfile.ZipFile(Path(name / self.FindZip(name))) as zip_ref:
            zip_ref.extractall(name)
        bps = self.FindBps(name)
        print(
            [
                "flips",
                "--apply",
                name / bps,
                vanilla,
                name / (f"{rpinv(self.hack_name)}.z64"),
                "--ignore-checksum",
            ]
        )
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


def format_version_js(hack_versions: list, hack_name):
    versions = []
    authors = set()
    for version_js in hack_versions:
        version = Hack()
        version.hack_id = version_js["hack_id"]
        version.hack_name = hack_name
        version.version = version_js["name"]
        version.url = str(version_js["id"])
        for author in version_js["authors"]:
            authors.add(author["name"])
        versions.append(version)
    return versions, ", ".join(authors)


# format the json
def format_sm64rh_hacks(js: dict):
    hack_list = []

    for hack in js:
        hack_obj = Hack()
        hack_obj.hack_name = hack["name"]
        hack_obj.url = hack["id"]
        hack_obj.versions, hack_obj.creator = format_version_js(
            hack["versions"], hack_obj.hack_name
        )
        hack_list.append(hack_obj)

    return hack_list


def get_all_sm64rh_hacks():
    url = "https://sm64romhacks.com/api/v1/hacks"
    hack_list = format_sm64rh_hacks(requests.get(url).json())
    return hack_list
