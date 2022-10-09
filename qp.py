import requests, json, zipfile, subprocess, sys, os, shutil
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
from functools import partial, lru_cache
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import shutil
import breeze_resources

#storage class, but won't data class because I dont have all class data at once
class Hack():
	def print_dat(self):
		print(self.__dict__)
	def DownloadAndPatch(self,root,vanilla):
		invalid = r'<>:"/\|?*'
		def rpinv(x):
			for a in invalid:
				x = x.replace(a,' ')
			return x
		name = Path(f'hacks/{rpinv(self.HackName)}/{rpinv(self.Version)}')
		if os.path.exists(name):
			shutil.rmtree(name)
		name.mkdir(exist_ok=True,parents=True)
		hack = requests.get(urljoin(root,self.url))
		with open(name / (f'{rpinv(self.HackName)}_ver_{rpinv(self.Version)}.zip'),'wb') as f:
			f.write(hack.content)
		with zipfile.ZipFile(name / (f'{rpinv(self.HackName)}_ver_{rpinv(self.Version)}.zip')) as zip_ref:
			zip_ref.extractall(name)
		bps = self.FindBps(name)
		subprocess.call(['flips','--apply',name / bps, vanilla, name / (f'{rpinv(self.HackName)}.z64'),'--ignore-checksum'])
	def FindBps(self, path):
		p = os.path.join(os.getcwd(),path)
		for f in os.listdir(p):
			if '.bps' in Path(f).suffixes:
				return f
		return None

class romhacksParser(HTMLParser):
	mainMap = {
	1: 'HackName',
	2: 'Creator',
	3: 'Release',
    4: 'Tags'
	}
	HackMap = {
	1: 'HackName',
	2: 'Version',
	3: 'Link',
	4: 'Creator',
	5: 'Star_Count',
	6: 'Release',
	}
	def start(self,main):
		self.HackTable = False
		self.hacks = []
		self.main = main
		self.lastHack = 0
		self.header = 0
		self.cell = None
	def handle_data(self,data):
		if self.HackTable and self.cell:
			if self.main:
				setattr(self.lastHack,self.mainMap[self.cell],data)
			else:
				setattr(self.lastHack,self.HackMap[self.cell],data)
	def handle_starttag(self,tag,attrs):
		if tag=='table':
			for a in attrs:
				if a[0]=='id' and a[1]=='myTable':
					self.HackTable = True
		if tag=='tr' and self.HackTable:
			if not self.header:
				self.header = 1
			else:
				self.cell = 0
				self.lastHack = Hack()
				self.hacks.append(self.lastHack)
		if tag=='td' and self.HackTable:
			self.cell += 1
		if tag=='a' and self.HackTable:
			for a in attrs:
				if a[0]=='href':
					self.lastHack.url = a[1]
	def handle_endtag(self,tag):
		if tag=='table' and self.HackTable:
			self.HackTable = False

def GetAllHacks():
	url = "https://sm64romhacks.com/"
	r = requests.get(url)
	p = romhacksParser()
	p.start(1)
	p.feed(r.text)
	return p

@lru_cache(maxsize=25)
def GetHackPageVersions(hack):
	url = "https://sm64romhacks.com/" + hack.url
	r = requests.get(url)
	p = romhacksParser()
	p.start(0)
	p.feed(r.text)
	p.root = url
	return p

class settings(QWidget):
	def __init__(self, wnd, app):
		super().__init__()
		self.resize(200,100) #idk
		self.setWindowTitle("Quick Patch Settings")
		font = QFont()
		font.setPointSize(12)
		self.setFont(font)
		self.layout = QVBoxLayout(self)
		self.setLayout(self.layout)
		self.wnd = wnd
		btn = QPushButton("Change Vanilla Rom")
		btn.clicked.connect(wnd.UpdateVan)
		self.layout.addWidget(btn)
		btn = QPushButton("Change Emulator Path")
		btn.clicked.connect(wnd.UpdateEmu)
		self.layout.addWidget(btn)
		wnd.pj16 = QCheckBox("emu is pj64 1.6")
		self.layout.addWidget(wnd.pj16)
		#themes
		# Hbox = QHBoxLayout()
		# DThemes = ["Dark"]
		# [self.addRadio(t,Hbox,app) for t in DThemes]
		# self.layout.addLayout(Hbox)
		# Hbox = QHBoxLayout()
		# LThemes = ["Light"]
		# [self.addRadio(t,Hbox,app) for t in LThemes]
		# self.layout.addLayout(Hbox)
	def closeEvent(self,event):
		self.wnd.updateStatus("Settings saved")
	def addRadio(self,txt,ly,app):
		btn = QRadioButton((f"{txt} Theme"))
		btn.clicked.connect(partial(self.ChangeTheme,app,txt))
		ly.addWidget(btn)
	def ChangeTheme(self,app,t):
		file = QFile((f":/{t.lower()}/stylesheet.qss"))
		file.open(QFile.ReadOnly | QFile.Text)
		stream = QTextStream(file)
		app.setStyleSheet(stream.readAll())

class window(QWidget):
	def __init__(self):
		super().__init__()
		self.resize(800,900) #idk
		self.setWindowTitle("Quick Patch")
		self.setAcceptDrops(True)
		font = QFont()
		font.setPointSize(11)
		self.setFont(font)
		self.layout = QVBoxLayout(self)
		self.setLayout(self.layout)
	def closeEvent(self,event):
		self.settings.close()
	def Add(self,x,y):
		if y == None:
			self.layout.addWidget(x)
		else:
			y.addWidget(x)
	def dragEnterEvent(self,e):
		if e.mimeData().hasText():
			if 'file' in e.mimeData().text() and ('.bps' or '.z64' in e.mimeData().text()):
				e.accept()
		else:
			e.ignore()
	def dropEvent(self,e):
		f = Path(e.mimeData().text()[8:])
		d = f.parent
		name = f.stem
		if not self.vanilla:
			van = self.getFile()
			if not van:
				self.updateStatus("choose vanilla rom to patch")
				return
		if '.bps' in f.suffixes:
			subprocess.call(['flips','--apply', f, self.vanilla, d / (f'{name}.z64'), '--ignore-checksum'])
			self.updateStatus(f'{name}.z64 rom created')
		if '.z64' in f.suffixes:
			subprocess.call(['flips','--create', self.vanilla, f, d / (f'{name}.bps'),'--ignore-checksum'])
			self.updateStatus(f'{name}.bps patch created')
	def updateStatus(self,s):
		self.status.setText(s)
	def AddLabel(self,text = None, Bind = None, layout = None):
		lab = QLabel(text)
		self.Add(lab,layout)
		return lab
	def AddBtn(self,text = None, Bind = None, layout = None):
		btn = QPushButton(text)
		if Bind:
			btn.clicked.connect(Bind)
		self.Add(btn,layout)
		return btn
	def AddEntry(self,text = None, Bind = None, layout = None):
		ent = QLineEdit(text)
		if Bind:
			ent.returnPressed.connect(Bind)
		self.Add(ent,layout)
		return ent
	def AddLayout(self, LY, layout = None):
		if layout:
			layout.addLayout(LY)
		else:
			self.layout.addLayout(LY)
		return LY
	def ChooseHack(self,widg):
		vers = GetHackPageVersions(widg.GetHack())
		self.vers = vers
		self.verlist.Clear()
		self.verlist.AddVersions(vers.hacks)
	def chng_settings(self,settings):
		settings.show()
	def DownloadHack(self,widg):
		if not self.vanilla:
			van = self.getFile()
			if not van:
				self.updateStatus("choose vanilla rom to patch")
				return
		widg.GetHack().DownloadAndPatch(self.vers.root,self.vanilla)
		self.updateStatus(f'{widg.GetHack().HackName} ver {widg.GetHack().Version} downloaded and patched')
		self.UpdateDownloadedHacks(self.downloaded)
	def getFile(self):
		fname = QFileDialog.getOpenFileName(self, 'choose vanilla', 
			'c:\\',"z64 files (*.z64)")[0]
		if not fname:
			self.updateStatus("no ROM selected")
			return None
		with open(fname,'rb') as mario:
			m = mario.read()
			if b'cZ+\xff\x8b\x02#&' == m[16:24]:
				self.updateStatus("Vanilla Rom Chosen Sucessfully")
				return fname
			else:
				self.updateStatus("Wrong ROM chosen")
				self.getFile()
	def UpdateHackList(self,hacklist,text):
		hacklist.Clear()
		for a in self.rhp.hacks:
			if text.lower() in a.HackName.lower() or text.lower() in a.Creator.lower():
				hacklist.AddItem(f'{a.HackName}',a)
	def launchRomBtn(self):
		a = self.downloaded.widget.currentItem()
		if a:
			self.TreeLaunch(a)
	def launchRom(self,hack):
		if not js.get("emulator"):
			fname = QFileDialog.getOpenFileName(self, 'choose emulator', 
			'c:\\',"executables (*.exe)")[0]
			if fname:
				self.emulator = fname
				self.js["emulator"] = fname
				jsF = open(self.jsPath,'w')
				jsF.write(json.dumps(self.js))
				jsF.close()
			else:
				self.updateStatus("Choose emu to launch roms")
				return
		if self.pj16.isChecked():
			subprocess.Popen(f'{self.emulator} {hack}',stdin=None, stdout=None, stderr=None, text=True)
		else:
			subprocess.Popen(f'{self.emulator} "{hack}"',stdin=None, stdout=None, stderr=None, text=True)
	def UpdateEmu(self):
		fname = QFileDialog.getOpenFileName(self, 'choose emulator', 
		'c:\\',"executables (*.exe)")[0]
		if fname:
			self.emulator = fname
			self.js["emulator"] = fname
			jsF = open(self.jsPath,'w')
			jsF.write(json.dumps(self.js))
			jsF.close()
		else:
			self.updateStatus("Choose emu to launch roms")
	def UpdateVan(self):
		fname = self.getFile()
		if fname:
			self.emulator = fname
			self.js["emulator"] = fname
			jsF = open(self.jsPath,'w')
			jsF.write(json.dumps(self.js))
			jsF.close()
		else:
			self.updateStatus("Choose good ROM")
	def UpdateDownloadedHacks(self,downloaded):
		downloaded.Clear()
		Path("hacks").mkdir(exist_ok=True,parents=True)
		for a in os.listdir(os.path.join(os.getcwd(),"hacks")):
			item = downloaded.AddItem(a,downloaded.widget)
			self.AddDownloadedVers(downloaded,a,item)
	def AddDownloadedVers(self,downloaded,name,item):
		vers = downloaded.GetFolder(name)
		for a in vers:
			b = downloaded.AddItem(f"{a}",item)
	def TreeLaunch(self,a):
		if a.childCount()==0:
			ver = a.text(0)
			p = Path(os.getcwd())
			p = p / "hacks" / a.parent().text(0) / ver
			r = self.FindRom(p)
			self.launchRom(str(Path("hacks") / a.parent().text(0) / ver / r))
	def FindRom(self, p):
		for f in os.listdir(p):
			if '.z64' in Path(f).suffixes:
				return f
		return None

#make list widget an attr of this class
class List():
	def __init__(self):
		self.widget = QListWidget()
		self.widget.setWordWrap(True)
		self.D = {}
		self.offset = 0
		self.numInserts = 0
	def AddItem(self,item,hack):
		self.D[self.widget.count()] = hack
		self.widget.addItem(item)
	def AddHacks(self,hacks):
		for h in hacks:
			self.AddItem(f'{h.HackName} - {h.Creator}',h)
	def AddVersions(self,hacks):
		for h in hacks:
			self.AddItem(f'Version {h.Version}',h)
	def Clear(self):
		self.widget.clear()
		self.D = {}
	def GetHack(self):
		return self.D[self.widget.currentRow()]

class Tree():
	def __init__(self):
		self.widget = QTreeWidget()
		self.widget.setColumnCount(1)
		self.widget.setHeaderHidden(True)
		self.widget.setWordWrap(True)
	def AddItem(self,item,parent):
		a = QTreeWidgetItem(parent)
		a.setText(0,item)
		self.widget.addTopLevelItem(a)
		return a
	def Clear(self):
		self.widget.clear()
	def GetFolder(self,name):
		return os.listdir(os.path.join(os.getcwd(),Path(f"hacks/{name}")))

def InitGui(rhp,js,jsPath):
	#build GUI
	app = QApplication([])
	wnd = window()
	wnd.rhp = rhp
	TopRow = QHBoxLayout()
	wnd.status = wnd.AddLabel('Boot Success')
	wnd.status.setAlignment(Qt.AlignCenter)
	ent = wnd.AddEntry(Bind = None)
	wnd.AddLayout(TopRow)
	#make hack list widget
	HackList = List()
	HackList.widget.clicked.connect(partial(wnd.ChooseHack,HackList))
	HackList.widget.setAlternatingRowColors(True)
	ent.textChanged.connect(partial(wnd.UpdateHackList,HackList))
	#version list and downloaded hacks
	DownloadedHacks = Tree()
	DownloadedHacks.widget.itemDoubleClicked.connect(wnd.TreeLaunch)
	VersionList = List()
	VersionList.widget.doubleClicked.connect(partial(wnd.DownloadHack,VersionList))
	MidRow = QHBoxLayout()
	VerSplit = QVBoxLayout()
	MidRow.addWidget(HackList.widget)
	vers = wnd.AddLabel('Versions', layout = VerSplit)
	VerSplit.addWidget(VersionList.widget)
	wnd.AddLabel('Downloaded Hacks', layout = VerSplit)
	VerSplit.addWidget(DownloadedHacks.widget)
	#adding layouts
	wnd.AddLayout(MidRow)
	wnd.AddLayout(VerSplit,layout = MidRow)
	wnd.show()
	wnd.hacklist = HackList
	wnd.verlist = VersionList
	wnd.downloaded = DownloadedHacks
	wnd.UpdateDownloadedHacks(DownloadedHacks)
	wnd.hacklist.AddHacks(rhp.hacks)
	#bottom buttons layout
	BotRow = QHBoxLayout()
	wnd.AddLayout(BotRow)
	#settings window
	qp_set = settings(wnd,app)
	wnd.settings = qp_set
	btn = wnd.AddBtn("Change Settings", Bind = partial(wnd.chng_settings,qp_set),layout = BotRow)
	#launch rom button
	btn = wnd.AddBtn("Launch Rom", Bind = wnd.launchRomBtn,layout = BotRow)
	#add js vars
	wnd.js = js
	wnd.jsPath = jsPath
	
	#start with dark theme as default
	file = QFile(":/dark/stylesheet.qss")
	file.open(QFile.ReadOnly | QFile.Text)
	stream = QTextStream(file)
	app.setStyleSheet(stream.readAll())
	if not js.get('Vanilla'):
		dg = QFileDialog()
		# dg.setacceptMode(QFileDialog.AcceptOpen)
		# dg.setFilter("rom files (*.z64)")
		van = wnd.getFile()
		if van:
			js["Vanilla"] = van
		else:
			js["Vanilla"] = None
		jsF = open(jsPath,'w')
		jsF.write(json.dumps(js))
		jsF.close()
	wnd.vanilla = js["Vanilla"]
	wnd.emulator = js.get("emulator")
	sys.exit(app.exec_())


if __name__=='__main__':
	jsPath = Path("config.json")
	if jsPath.exists():
		jsF = open(jsPath,'r')
	else:
		#create file
		jsF = open(jsPath,'w')
		jsF.write('{}')
		jsF.close()
		jsF = open(jsPath,'r')
	js = json.load(jsF)
	jsF.close()
	rhp = GetAllHacks()
	InitGui(rhp,js,jsPath)