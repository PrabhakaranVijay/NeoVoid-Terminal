<br/>
<a id="top"></a>

<h1 align="center">NeoVoid – Native Terminal Emulator</h1>

<p align="center">
  <img alt="profile views" src="https://komarev.com/ghpvc/?username=PrabhakaranVijay&label=Profile%20Views&color=7F00FF&style=flat"/>
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/PrabhakaranVijay/neovoid-terminal?color=7F00FF">
  <img alt="Github language count" src="https://img.shields.io/github/languages/count/PrabhakaranVijay/neovoid-terminal?color=7F00FF">
  <img alt="Repository size" src="https://img.shields.io/github/repo-size/PrabhakaranVijay/neovoid-terminal?color=7F00FF">
  <img alt="License" src="https://img.shields.io/github/license/PrabhakaranVijay/neovoid-terminal?color=7F00FF">
  <img alt="Github forks" src="https://img.shields.io/github/forks/PrabhakaranVijay/neovoid-terminal?color=7F00FF" />
  <img alt="Github stars" src="https://img.shields.io/github/stars/PrabhakaranVijay/neovoid-terminal?color=7F00FF" />
</p>

<h4 align="center"> 
	🚧 Project under active development 🚀
</h4> 

<hr>

<p align="center">
  <a href="#-project-overview">Project Overview</a> &#xa0; | &#xa0; 
  <a href="#-architecture">Architecture</a> &#xa0; | &#xa0; 
  <a href="#-tech-stack">Tech Stack</a> &#xa0; | &#xa0;
  <a href="#-getting-started">Starting</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="https://github.com/PrabhakaranVijay" target="_blank">Author</a>
</p>

<br>

> NeoVoid is a **native macOS terminal emulator** built from scratch using **Python and PyQt**, directly interfacing with the system shell via **Unix PTY**. The project explores how real terminals work internally — without using browsers, Electron, or web technologies.

---

## 🚀 Project Overview ##

A terminal emulator is responsible for translating **keyboard input**, **shell output**, and **ANSI control sequences** into a graphical interface.

NeoVoid demonstrates:

* Direct PTY-based communication with `zsh`
* Real-time shell input/output inside a native GUI
* Foundational terminal rendering concepts
* Scrollback buffer handling
* Minimal black & white aesthetic (NeoVoid design)

---

## 🧠 Architecture ##
```
┌────────────────────┐
│   NeoVoid GUI App  │  ← PyQt (QMainWindow + QTextEdit)
│  (Keyboard Input)  │
└─────────┬──────────┘
          │ write()
          ▼
┌────────────────────┐
│        PTY         │  ← os.openpty()
│  (Master / Slave)  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│        zsh         │  ← /bin/zsh (login shell)
│   (System Shell)   │
└────────────────────┘
```


* The GUI captures keyboard events
* Input is written to the PTY master
* `zsh` runs on the PTY slave
* Output is read from the PTY and rendered in the GUI

<!--
## ✨ Features ##

✔ Native macOS desktop application  
✔ Direct PTY integration with system shell  
✔ Real-time keyboard input and output  
✔ Scrollable terminal buffer  
✔ Minimal black & white UI design  
-->

---

## 🛠️ Tech Stack ##

The following tools were used in this project:

- [Python](https://www.python.org/)
- [PyQt5 / PyQt6](https://riverbankcomputing.com/software/pyqt/)
- Unix PTY APIs (`os.openpty`, `fork`, `exec`)
- zsh (default macOS shell)
- macOS (Apple Silicon / M1)

---

## 📂 Project Structure
```
NeoVoid-Terminal/
├── neo_void.py        # Main application source
├── README.md          # Project documentation
└── assets/            # (optional) fonts, images, icons
```
---

## 🚀 Getting Started ##

### 1️⃣ Prerequisites

* macOS (tested on **MacBook Air M1**)
* Python 3.9+
* zsh (default on macOS)

Install dependencies:

```bash
pip install PyQt5
# or
pip install PyQt6
```

---

### 2️⃣ Run NeoVoid

```bash
python neo_void.py
```
A native terminal window will open and automatically launch `zsh`.

---

## 🧪 Current Behavior (Expected)

You may notice:

* ANSI escape sequences like:

  ```
  ESC[?2004h
  ESC[H
  ESC[2J
  ```
* Repeated prompt redraws
* Raw control codes printed

✅ **This is expected**
NeoVoid currently displays **unparsed terminal control sequences**, which is normal at this development stage.

---

## 🧠 Learning Goals ##

NeoVoid was built to deeply understand:

* How **real terminals** communicate with shells
* PTY internals and Unix process control
* Keyboard input handling at application level
* Why terminal emulation is **hard**
* Foundations behind tools like `iTerm2`, `Alacritty`, `Kitty`

### 🧩 Known Limitations (Current Version)

* ❌ No ANSI escape sequence parsing yet
* ❌ Cursor positioning not visually rendered
* ❌ No color rendering (monochrome output)
* ❌ No alternate screen buffer support
* ❌ Basic text rendering (QTextEdit-based)

These are **intentional trade-offs** to keep the foundation simple and understandable.

### ⚠️ Notes for Developers

* The project uses `fork()` — macOS may emit warnings for multi-threaded contexts
* PTY resizing and signal handling are minimal
* This is an **educational + experimental** project, not production-ready (yet)

---

## :memo: License ##

This project is under license from MIT. For more details, see the [LICENSE](LICENSE.md) file.


Made with ❤️ by <a href="https://github.com/PrabhakaranVijay" target="_blank">Prabhakaran Vijay</a>

&#xa0;

---
<div align="center">
  <h2>⭐ If You Like This Project</h2>

  <p>Give it a ⭐ on GitHub and feel free to fork or improve it!</p>
</div>

	
<br/>
<br/>

<p align="center">
  <a href="#top">Back to top</a>
</p>


