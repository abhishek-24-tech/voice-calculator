
# Voice Calculator (Python GUI + Voice Input)

A simple calculator with a Tkinter GUI that also accepts math expressions via **voice recognition**.

## ✨ Features
- Standard calculator buttons (0-9, +, -, ×, ÷, parentheses, decimal).
- **Voice input** using your microphone (SpeechRecognition + PyAudio).
- Converts common spoken phrases like “plus”, “minus”, “times”, “divided by”, “power” to math.
- Supports spelled numbers via `word2number` (e.g., “twelve plus eight divided by two”).

---

## 🧰 Tech & Dependencies
- Python 3.9+ recommended
- Tkinter (bundled with most Python installers)
- Packages:
  - `SpeechRecognition`
  - `PyAudio`
  - `word2number`

Install them via:
```bash
pip install -r requirements.txt
```

> ⚠️ **PyAudio install tips**  
> - **Windows**: `pip install pipwin && pipwin install pyaudio` (then rerun `pip install -r requirements.txt` if needed)  
> - **macOS**: `brew install portaudio && pip install pyaudio`  
> - **Ubuntu/Debian**: `sudo apt-get install portaudio19-dev && pip install pyaudio`

---

## ▶️ Run
```bash
python main.py
```

Click **🎤 Speak** and say something like:
- "twelve plus eight divided by two"
- "one hundred minus thirty five"
- "five power three"
- "sixty four divided by eight"

---

## 🧪 Examples
- Speech: `twelve plus eight divided by two` → Expression: `12 + 8 / 2` → Result: `16.0`
- Speech: `one hundred minus thirty five` → `100 - 35` → `65`
- Speech: `five power three` → `5 ** 3` → `125`
- Speech: `sixty four divided by eight` → `64 / 8` → `8.0`

---

## 🛡️ Safety
Evaluation uses a **safe arithmetic evaluator** (AST-based) allowing only numbers, `+ - * / **` and parentheses.

---

## 🐙 Save to GitHub (Step-by-step)
From the project folder:

```bash
# 1) (Optional) Create and activate a virtual environment
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Initialize git
git init
git add -A
git commit -m "Initial commit: Voice calculator (GUI + voice input)"

# 4a) Using GitHub CLI (easiest)
gh repo create voice-calculator --public --source=. --remote=origin --push

# 4b) OR create repo on GitHub manually, then:
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/voice-calculator.git
git push -u origin main
```

---

## 🚑 Troubleshooting
- **Microphone not found**: Check OS permissions for Python to use the microphone.
- **Speech not recognized**: Try speaking clearly; ensure you have an internet connection (Google recognizer). For **offline** recognition, consider `vosk`.
- **PyAudio errors**: Install PortAudio as per your OS (see tips above).

---

## 📄 License
MIT
