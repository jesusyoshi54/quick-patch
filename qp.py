import requests
import json
from datetime import date
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
import zipfile
import subprocess
import sys
import os
from functools import partial
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import shutil

#storage class, but won't data class because I dont have all class data at once
class Hack():
	def print_dat(self):
		print(self.__dict__)
	def DownloadAndPatch(self,root,vanilla):
		name = Path(f'hacks/{self.HackName}/{self.Version}')
		if os.path.exists(name):
			shutil.rmtree(name)
		name.mkdir(exist_ok=True,parents=True)
		hack = requests.get(urljoin(root,self.url))
		with open(name / (f'{self.HackName}_ver_{self.Version}.zip'),'wb') as f:
			f.write(hack.content)
		with zipfile.ZipFile(name / (f'{self.HackName}_ver_{self.Version}.zip')) as zip_ref:
			a = zip_ref.extractall(name)
		bps = self.FindBps(name)
		if not bps:
			print('could not find bps file name??')
			return None
		subprocess.call(['flips','--apply',name / bps, vanilla,name / (f'{self.HackName}.z64'),'--ignore-checksum'])
	def FindBps(self, path):
		p = os.path.join(os.getcwd(),path)
		for f in os.listdir(p):
			if '.bps' in Path(f).suffixes:
				return f
		return None

class romhacksParser(HTMLParser):
	#basically an init but I don't feel like dealing with inheritance python nonsense since I never learned it
	mainMap = {
	1: 'HackName',
	2: 'Creator',
	3: 'Release',
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

def GetHackPageVersions(hack):
	url = "https://sm64romhacks.com/" + hack.url
	r = requests.get(url)
	p = romhacksParser()
	p.start(0)
	p.feed(r.text)
	p.root = url
	return p

class window(QWidget):
	def __init__(self):
		super().__init__()
		self.resize(550,900) #idk
		self.setWindowTitle("Quick Patch")
		self.setAcceptDrops(True)
		font = QFont()
		font.setPointSize(12)
		self.setFont(font)
		self.layout = QGridLayout()
		self.setLayout(self.layout)
		self.Add = lambda x,y: self.layout.addWidget(x) if not y else y.addWidget(x)
	def dragEnterEvent(self,e):
		if e.mimeData().hasText():
			if 'file' in e.mimeData().text() and ('.bps' or '.z64' in e.mimeData().text()):
				e.accept()
		else:
			e.ignore()
	def dropEvent(self,e):
		f = Path(e.mimeData().text()[8:])
		d = f.parent
		name = f.name
		if '.bps' in f.suffixes:
			subprocess.call(['flips','--apply',f ,'vanilla.z64', d / (f'{name}.z64'), '--ignore-checksum'])
		if '.z64' in f.suffixes:
			subprocess.call(['flips','--create', 'vanilla.z64', f,d / (f'{name}.bps'),'--ignore-checksum'])
		print('success')

	def AddLabel(self,text = None, Bind = None, layout = None):
		btn = QPushButton(text)
		if Bind:
			Btn.clicked.connect(Bind)
		self.Add(btn,layout)
		return btn
	def AddEntry(self,text = None, Bind = None, layout = None):
		ent = QLineEdit(text)
		if Bind:
			ent.returnPressed.connect(Bind)
		self.Add(ent,layout)
		return ent
	def AddLayout(self, LY, layout = None, dim = None):
		if layout:
			layout.addLayout(LY,*dim)
		else:
			self.layout.addLayout(LY,*dim)
		return LY
	def ChooseHack(self,widg):
		ind = widg.currentRow()
		vers = GetHackPageVersions(self.rhp.hacks[ind])
		self.vers = vers
		self.verlist.widget.clear()
		self.verlist.AddVersions(vers.hacks)
	def DownloadHack(self,widg):
		ind = widg.currentRow()
		self.vers.hacks[ind].DownloadAndPatch(self.vers.root,self.vanilla)
		print('hack patched and downloaded')
	def getFile(self):
		fname = QFileDialog.getOpenFileName(self, 'choose vanilla', 
			'c:\\',"z64 files (*.z64)")[0]
		with open(fname,'rb') as mario:
			m = mario.read()
			print(m[16:24])
			if b'cZ+\xff\x8b\x02#&' == m[16:24]:
				return fname
			else:
				self.getFile()

#make list widget an attr of this class
class List():
	def __init__(self):
		self.widget = QListWidget()
	def AddItem(self,item):
		self.widget.addItem(item)
	def AddHacks(self,hacks):
		for h in hacks:
			self.AddItem(f'{h.HackName} by {h.Creator}')
	def AddVersions(self,hacks):
		for h in hacks:
			self.AddItem(f'Version {h.Version}')


def InitGui(rhp,js,jsF):
	#build GUI
	app = QApplication([])
	wnd = window()
	if not js.get('Vanilla'):
		dg = QFileDialog()
		# dg.setacceptMode(QFileDialog.AcceptOpen)
		# dg.setFilter("rom files (*.z64)")
		js["Vanilla"] = wnd.getFile()
		jsF.close()
		jsF = open(jsPath,'w')
		jsF.write(json.dumps(js))
	wnd.rhp = rhp
	wnd.vanilla = js["Vanilla"]
	TopRow = wnd.AddLayout(QHBoxLayout(),dim = (0,1))
	wnd.AddLabel('search hacks',TopRow)
	wnd.AddEntry(Bind = None, layout = TopRow)
	#make hack list widget
	HackList = List()
	HackList.widget.clicked.connect(partial(wnd.ChooseHack,HackList.widget))
	HackList.widget.setAlternatingRowColors(True)
	VersionList = List()
	VersionList.widget.doubleClicked.connect(partial(wnd.DownloadHack,VersionList.widget))
	wnd.layout.addWidget(HackList.widget)
	wnd.layout.addWidget(VersionList.widget)
	wnd.show()
	wnd.hacklist = HackList
	wnd.verlist = VersionList
	wnd.hacklist.AddHacks(rhp.hacks)
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
	rhp = GetAllHacks()
	InitGui(rhp,js,jsF)