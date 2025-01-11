
# Quick Patch

Access all the hacks at sm64romhacks.com with a quick and easy to use interface.

## Features

- Download hacks with double click from sm64romhacks.com
- Keep a library of all your downloaded hacks
- Launch Hacks from your library with any emulator
- Cross platform


## Running without prebuilt

Clone the project

```bash
  git clone https://github.com/jesusyoshi54/quick-patch
```

Go to the project directory

```bash
  cd quick-patch
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Run via python

```bash
  python qp.py
```


## Build

This project packages an .exe created with pyinstaller.

To create your own executable, install pyinstaller, and compile with

```
pyinstaller qp.py -F -w
```