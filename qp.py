import requests, json, zipfile, subprocess, sys, os, shutil
from pathlib import Path
from urllib.parse import urljoin
from functools import partial
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# the themes
import breeze_resources

# these are submodules stuff I wrote
from sm64rh import *

"""
The GUI works by getting a list of hacks from scraping sm64RH or RHDC (in the future).
Given a list of hacks, they are displayed in the left column, you can search/filter hacks from the top bar.
On the top right will display versions of hacks for the selected hack.
If you double click a version, or click and hit the download button, the hack will download and patch.
At the bottom right is a library of hacks. It is filtered by game name and version.
The hack library is retrieved by scanning the OS for hacks in the folder 'hacks' in the same directory as quick patch.
Launching a ROM will launch it via the selected emulator.

At the very top of the GUI should be a status, the status will be updated on each user action to let them
know what actions are being taken by the GUI.

A JSON file is used to store settings for this program. The settings are the vanilla ROM, which is used for patching.
The emulator which is used to launch a ROM.
The JSON can easily be extended to hold settings used for ROM launching such as plugins.
These settings will need to be emulator dependent.
"""


class Main_Window(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(800, 900)  # idk
        self.setWindowTitle("Quick Patch")
        self.setAcceptDrops(True)
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

    # these are overrides from the base QWidget class
    def closeEvent(self, event):
        self.settings.close()

    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            if "file" in e.mimeData().text() and (
                ".bps" or ".z64" in e.mimeData().text()
            ):
                e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        f = Path(e.mimeData().text()[8:])
        d = f.parent
        name = f.stem
        if not self.vanilla:
            van = self.getFile()
            if not van:
                self.updateStatus("choose vanilla rom to patch")
                return
        if ".bps" in f.suffixes:
            subprocess.call(
                [
                    "flips",
                    "--apply",
                    f,
                    self.vanilla,
                    d / (f"{name}.z64"),
                    "--ignore-checksum",
                ]
            )
            self.updateStatus(f"{name}.z64 rom created")
        if ".z64" in f.suffixes:
            subprocess.call(
                [
                    "flips",
                    "--create",
                    self.vanilla,
                    f,
                    d / (f"{name}.bps"),
                    "--ignore-checksum",
                ]
            )
            self.updateStatus(f"{name}.bps patch created")

    # base methods to make building GUI easier
    def add_widget(self, x, y):
        if y == None:
            self.layout.addWidget(x)
        else:
            y.addWidget(x)

    def add_label(self, text=None, Bind=None, layout=None):
        lab = QLabel(text)
        self.add_widget(lab, layout)
        return lab

    def add_button(self, text=None, Bind=None, layout=None):
        btn = QPushButton(text)
        if Bind:
            btn.clicked.connect(Bind)
        self.add_widget(btn, layout)
        return btn

    def add_entry(self, text=None, Bind=None, layout=None):
        ent = QLineEdit(text)
        if Bind:
            ent.returnPressed.connect(Bind)
        self.add_widget(ent, layout)
        return ent

    def add_layout(self, LY, layout=None):
        if layout:
            layout.addLayout(LY)
        else:
            self.layout.addLayout(LY)
        return LY

    # GUI functions

    # display site content, search/versions
    def ChooseHack(self, widg):
        hack = widg.get_hack()
        self.verlist.clear()
        self.verlist.add_versions(hack.versions)

    def update_hack_list_widget(self, hack_list_widget, text):
        hack_list_widget.clear()
        for hack in self.hack_list:
            if (
                text.lower() in hack.hack_name.lower()
                or text.lower() in hack.creator.lower()
            ):
                hack_list_widget.add_item(f"{hack.hack_name} - {hack.creator}", hack)

    def updateStatus(self, s):
        self.status.setText(s)

    # settings
    def chng_settings(self, settings):
        settings.show()

    # launching a ROM
    def launchRomBtn(self):
        a = self.downloaded.widget.currentItem()
        if a:
            self.TreeLaunch(a)

    def TreeLaunch(self, a):
        if a.childCount() == 0:
            ver = a.text(0)
            p = Path(os.getcwd())
            p = p / "hacks" / a.parent().text(0) / ver
            r = self.FindRom(p)
            self.launchRom(str(Path("hacks") / a.parent().text(0) / ver / r))

    def FindRom(self, p):
        for f in os.listdir(p):
            if ".z64" in Path(f).suffixes:
                return f
        return None

    def launchRom(self, hack):
        if not js.get("emulator"):
            fname = QFileDialog.getOpenFileName(
                self, "choose emulator", "c:\\", "executables (*.exe)"
            )[0]
            if fname:
                self.emulator = fname
                self.js["emulator"] = fname
                jsF = open(self.jsPath, "w")
                jsF.write(json.dumps(self.js))
                jsF.close()
            else:
                self.updateStatus("Choose emu to launch roms")
                return
        if self.pj16.isChecked():
            subprocess.Popen(
                f"{self.emulator} {hack}",
                stdin=None,
                stdout=None,
                stderr=None,
                text=True,
            )
        else:
            subprocess.Popen(
                f'{self.emulator} "{hack}"',
                stdin=None,
                stdout=None,
                stderr=None,
                text=True,
            )

    # settings updates
    def UpdateEmu(self):
        fname = QFileDialog.getOpenFileName(
            self, "choose emulator", "c:\\", "executables (*.exe)"
        )[0]
        if fname:
            self.emulator = Path(fname)
            self.js["emulator"] = fname
            jsF = open(self.jsPath, "w")
            jsF.write(json.dumps(self.js))
            jsF.close()
        else:
            self.updateStatus("Choose emu to launch roms")

    def UpdateVan(self):
        fname = self.getFile()
        if fname:
            self.vanilla = Path(fname)
            self.js["vanilla"] = fname
            jsF = open(self.jsPath, "w")
            jsF.write(json.dumps(self.js))
            jsF.close()
        else:
            self.updateStatus("Choose good ROM")

    # downloading a hack
    def DownloadHack(self, widg):
        if not self.vanilla:
            van = self.getFile()
            if not van:
                self.updateStatus("choose vanilla rom to patch")
                return
        widg.get_hack().DownloadAndPatch(
            "https://sm64romhacks.com/hacks/download/", self.vanilla
        )
        self.updateStatus(
            f"{widg.get_hack().hack_name} ver {widg.get_hack().version} downloaded and patched"
        )
        self.update_downloaded_hacks_widget(self.downloaded)

    def getFile(self):
        fname = QFileDialog.getOpenFileName(
            self, "choose vanilla", "c:\\", "z64 files (*.z64)"
        )[0]
        if not fname:
            self.updateStatus("no ROM selected")
            return None
        with open(fname, "rb") as mario:
            m = mario.read()
            if b"cZ+\xff\x8b\x02#&" == m[16:24]:
                self.updateStatus("Vanilla Rom Chosen Sucessfully")
                return fname
            else:
                self.updateStatus("Wrong ROM chosen")
                self.getFile()

    # updating list after download
    def update_downloaded_hacks_widget(self, downloaded):
        downloaded.clear()
        Path("hacks").mkdir(exist_ok=True, parents=True)
        for a in os.listdir(os.path.join(os.getcwd(), "hacks")):
            item = downloaded.add_item(a, downloaded.widget)
            self.AddDownloadedVers(downloaded, a, item)

    def AddDownloadedVers(self, downloaded, name, item):
        vers = downloaded.get_folder(name)
        for a in vers:
            b = downloaded.add_item(f"{a}", item)


class PJ64_Settings(QWidget):
    def __init__(self, window, app):
        super().__init__()
        self.resize(200, 100)  # idk
        self.setWindowTitle("Quick Patch Settings")
        font = QFont()
        font.setPointSize(12)
        self.setFont(font)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.window = window
        btn = QPushButton("Change Vanilla Rom")
        btn.clicked.connect(window.UpdateVan)
        self.layout.addWidget(btn)
        btn = QPushButton("Change Emulator Path")
        btn.clicked.connect(window.UpdateEmu)
        self.layout.addWidget(btn)
        window.pj16 = QCheckBox("emu is pj64 1.6")
        self.layout.addWidget(window.pj16)

    def closeEvent(self, event):
        self.window.updateStatus("Settings saved")

    def addRadio(self, txt, ly, app):
        btn = QRadioButton((f"{txt} Theme"))
        btn.clicked.connect(partial(self.ChangeTheme, app, txt))
        ly.addWidget(btn)

    def ChangeTheme(self, app, t):
        file = QFile((f":/{t.lower()}/stylesheet.qss"))
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())


# make list widget an attr of this class
class List:
    def __init__(self):
        self.widget = QListWidget()
        self.widget.setWordWrap(True)
        self.hack_data = {}

    def add_item(self, item, hack):
        self.hack_data[self.widget.count()] = hack
        self.widget.addItem(item)

    def add_hacks(self, hacks):
        for h in hacks:
            self.add_item(f"{h.hack_name} - {h.creator}", h)

    def add_versions(self, hack_versions):
        for hack in hack_versions:
            self.add_item(f"Version {hack.version}", hack)

    def clear(self):
        self.widget.clear()
        self.hack_data = {}

    def get_hack(self):
        return self.hack_data[self.widget.currentRow()]


class Tree:
    def __init__(self):
        self.widget = QTreeWidget()
        self.widget.setColumnCount(1)
        self.widget.setHeaderHidden(True)
        self.widget.setWordWrap(True)

    def add_item(self, item, parent):
        a = QTreeWidgetItem(parent)
        a.setText(0, item)
        self.widget.addTopLevelItem(a)
        return a

    def clear(self):
        self.widget.clear()

    def get_folder(self, name):
        return os.listdir(os.path.join(os.getcwd(), Path(f"hacks/{name}")))


def init_main_gui(hack_list, js, jsPath):
    # build GUI
    app = QApplication([])
    window = Main_Window()
    window.hack_list = hack_list
    top_row_ly = QHBoxLayout()
    window.status = window.add_label("Boot Success")
    window.status.setAlignment(Qt.AlignCenter)
    ent = window.add_entry(Bind=None)
    window.add_layout(top_row_ly)
    # make hack list widget
    hack_list_widget = List()
    hack_list_widget.widget.clicked.connect(
        partial(window.ChooseHack, hack_list_widget)
    )
    hack_list_widget.widget.setAlternatingRowColors(True)
    ent.textChanged.connect(partial(window.update_hack_list_widget, hack_list_widget))
    # version list and downloaded hacks
    downloaded_hacks_widget = Tree()
    downloaded_hacks_widget.widget.itemDoubleClicked.connect(window.TreeLaunch)
    version_list_widget = List()
    version_list_widget.widget.doubleClicked.connect(
        partial(window.DownloadHack, version_list_widget)
    )
    mid_row_ly = QHBoxLayout()
    version_split_ly = QVBoxLayout()
    mid_row_ly.addWidget(hack_list_widget.widget)
    vers = window.add_label("Versions", layout=version_split_ly)
    version_split_ly.addWidget(version_list_widget.widget)
    window.add_label("Downloaded Hacks", layout=version_split_ly)
    version_split_ly.addWidget(downloaded_hacks_widget.widget)
    # adding layouts
    window.add_layout(mid_row_ly)
    window.add_layout(version_split_ly, layout=mid_row_ly)
    window.show()
    window.hacklist = hack_list_widget
    window.verlist = version_list_widget
    window.downloaded = downloaded_hacks_widget
    window.update_downloaded_hacks_widget(downloaded_hacks_widget)
    window.hacklist.add_hacks(hack_list)
    # bottom buttons layout
    bottom_row_ly = QHBoxLayout()
    window.add_layout(bottom_row_ly)
    # settings window
    qp_set = PJ64_Settings(window, app)
    window.settings = qp_set
    btn = window.add_button(
        "Change Settings",
        Bind=partial(window.chng_settings, qp_set),
        layout=bottom_row_ly,
    )
    # launch rom button
    btn = window.add_button(
        "Launch Rom", Bind=window.launchRomBtn, layout=bottom_row_ly
    )
    # add js vars
    window.js = js
    window.jsPath = jsPath

    # start with dark theme as default
    file = QFile(":/dark/stylesheet.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())
    if not js.get("vanilla"):
        dg = QFileDialog()
        # dg.setacceptMode(QFileDialog.AcceptOpen)
        # dg.setFilter("rom files (*.z64)")
        van = window.getFile()
        if van:
            js["vanilla"] = van
        else:
            js["vanilla"] = None
        jsF = open(jsPath, "w")
        jsF.write(json.dumps(js))
        jsF.close()
    window.vanilla = Path(js["vanilla"]) if js["vanilla"] else None
    window.emulator = Path(js.get("emulator")) if js.get("emulator") else None
    sys.exit(app.exec_())


if __name__ == "__main__":
    jsPath = Path("config.json")
    if jsPath.exists():
        jsF = open(jsPath, "r")
    else:
        # create file
        jsF = open(jsPath, "w")
        jsF.write("{}")
        jsF.close()
        jsF = open(jsPath, "r")
    js = json.load(jsF)
    jsF.close()
    hack_list = get_all_sm64rh_hacks()
    init_main_gui(hack_list, js, jsPath)
