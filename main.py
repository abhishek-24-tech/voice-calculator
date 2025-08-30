import tkinter as tk
from tkinter import messagebox
import ast
import threading
import speech_recognition as sr
from word2number import w2n
from datetime import datetime, timedelta

# ---------------- Safe evaluator ----------------
import operator as op
_ALLOWED_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
}
_ALLOWED_UNARY_OPS = {ast.UAdd: op.pos, ast.USub: op.neg}

def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant):  # numbers
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers allowed")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        return _ALLOWED_UNARY_OPS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("Invalid or unsupported expression")

def safe_eval(expr: str):
    tree = ast.parse(expr, mode='eval')
    return _eval_ast(tree)

# ---------------- Speech to math (simple) ----------------
import re
PHRASE_REPLACEMENTS = [
    (r"\bto the power of\b", "**"),
    (r"\bpower of\b", "**"),
    (r"\bpower\b", "**"),
    (r"\bdivided by\b", "/"),
    (r"\bdivide by\b", "/"),
    (r"\bmultiplied by\b", "*"),
    (r"\btimes\b", "*"),
    (r"\bminus\b", "-"),
    (r"\bplus\b", "+"),
    (r"\bover\b", "/"),
    (r"\bpoint\b", "."),
    (r"\bx\b", "*"),
]

NUMBER_WORDS = set("""zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen
sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million and""".split())

def words_chunk_to_number(tokens):
    phrase = " ".join(tokens)
    phrase = phrase.replace(" a ", " one ")
    try:
        n = w2n.word_to_num(phrase)
        return str(n)
    except Exception:
        return " ".join(tokens)

def text_to_math(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r",", "", s)
    for pat, repl in PHRASE_REPLACEMENTS:
        s = re.sub(pat, repl, s)
    s = re.sub(r"([\+\-\*\/\(\)\%])", r" \1 ", s)  # separate operators
    tokens = s.split()
    result_tokens = []
    number_buffer = []
    def flush():
        if number_buffer:
            if any(t in NUMBER_WORDS for t in number_buffer):
                result_tokens.append(words_chunk_to_number(number_buffer))
            else:
                result_tokens.append("".join(number_buffer))
            number_buffer.clear()
    for t in tokens:
        if t in {"+", "-", "*", "/", "(", ")", "%", "**"}:
            flush()
            result_tokens.append(t)
        else:
            number_buffer.append(t)
    flush()
    expr = " ".join(result_tokens)
    expr = expr.replace("* *", "**")
    expr = re.sub(r"\s*\.\s*", ".", expr)
    return expr

# ---------------- GUI & Calculator ----------------
root = tk.Tk()
root.title("Echo Calculator")
root.geometry("360x500")

entry = tk.Entry(root, font=("Segoe UI", 20), bd=6, relief=tk.GROOVE, justify="right")
entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

for i in range(7):
    root.rowconfigure(i, weight=1)
for j in range(4):
    root.columnconfigure(j, weight=1)

def evaluate():
    expr = entry.get().strip()
    if not expr:
        return
    try:
        res = safe_eval(expr)
        entry.delete(0, tk.END)
        entry.insert(tk.END, str(res))
    except ZeroDivisionError:
        messagebox.showerror("Math Error", "Division by zero.")
    except Exception as e:
        messagebox.showerror("Invalid Expression", str(e))

def on_button(ch):
    if ch == "C":
        entry.delete(0, tk.END)
    elif ch == "⌫":
        cur = entry.get()
        entry.delete(0, tk.END)
        entry.insert(tk.END, cur[:-1])
    elif ch == "=":
        evaluate()
    else:
        entry.insert(tk.END, ch)

# Buttons
buttons = [
    ("C",1,0), ("(",1,1), (")",1,2), ("⌫",1,3),
    ("7",2,0), ("8",2,1), ("9",2,2), ("/",2,3),
    ("4",3,0), ("5",3,1), ("6",3,2), ("*",3,3),
    ("1",4,0), ("2",4,1), ("3",4,2), ("-",4,3),
    ("0",5,0), (".",5,1), ("=",5,2), ("+",5,3),
]

for (txt,r,c) in buttons:
    tk.Button(root, text=txt, font=("Segoe UI", 16), command=lambda t=txt: on_button(t)).grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

# Voice button and Date button on bottom row
voice_btn = tk.Button(root, text="🎤 Speak", font=("Segoe UI", 16))
voice_btn.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

date_btn = tk.Button(root, text="📅 Date", font=("Segoe UI", 16))
date_btn.grid(row=6, column=2, columnspan=2, padx=10, pady=10, sticky="nsew")

# ---------------- Keyboard support ----------------
def key_press(event):
    ch = event.char
    if ch.isdigit() or ch in "+-*/().":
        entry.insert(tk.END, ch)
    elif event.keysym == "Return":
        evaluate()
    elif event.keysym == "BackSpace":
        cur = entry.get()
        entry.delete(0, tk.END)
        entry.insert(tk.END, cur[:-1])

root.bind("<Key>", key_press)

# ---------------- Voice handling (threaded) ----------------
def _listen_and_process():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
        text = recognizer.recognize_google(audio)
        expr = text_to_math(text)
        root.after(0, lambda: entry.delete(0, tk.END))
        root.after(0, lambda: entry.insert(tk.END, expr))
        root.after(0, evaluate)
    except sr.WaitTimeoutError:
        root.after(0, lambda: messagebox.showwarning("Timeout", "No speech detected."))
    except sr.UnknownValueError:
        root.after(0, lambda: messagebox.showwarning("Try Again", "Could not understand audio."))
    except sr.RequestError as e:
        root.after(0, lambda: messagebox.showerror("Speech Service Error", str(e)))
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", str(e)))
    finally:
        root.after(0, lambda: voice_btn.config(state=tk.NORMAL, text="🎤 Speak"))

def on_voice_click():
    voice_btn.config(state=tk.DISABLED, text="Listening...")
    threading.Thread(target=_listen_and_process, daemon=True).start()

voice_btn.config(command=on_voice_click)

# ---------------- Date Calculator popup ----------------
def open_date_calculator():
    win = tk.Toplevel(root)
    win.title("Date Calculator")
    win.geometry("360x220")
    # difference
    tk.Label(win, text="First date (YYYY-MM-DD)").pack(pady=(8,0))
    d1 = tk.Entry(win); d1.pack(pady=4)
    tk.Label(win, text="Second date (YYYY-MM-DD)").pack(pady=(6,0))
    d2 = tk.Entry(win); d2.pack(pady=4)
    def calc_diff():
        try:
            dt1 = datetime.strptime(d1.get().strip(), "%Y-%m-%d")
            dt2 = datetime.strptime(d2.get().strip(), "%Y-%m-%d")
            diff = abs((dt2 - dt1).days)
            messagebox.showinfo("Difference", f"{diff} days")
        except Exception as e:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
    tk.Button(win, text="Find Difference (days)", command=calc_diff).pack(pady=6)

    # add days
    tk.Label(win, text="Base date (YYYY-MM-DD)").pack(pady=(10,0))
    base = tk.Entry(win); base.pack(pady=4)
    tk.Label(win, text="Days to add (integer)").pack(pady=(6,0))
    days = tk.Entry(win); days.pack(pady=4)
    def add_days():
        try:
            dt = datetime.strptime(base.get().strip(), "%Y-%m-%d")
            n = int(days.get().strip())
            future = dt + timedelta(days=n)
            messagebox.showinfo("Future date", future.strftime("%Y-%m-%d"))
        except Exception:
            messagebox.showerror("Error", "Invalid input. Date must be YYYY-MM-DD and days an integer.")
    tk.Button(win, text="Add Days", command=add_days).pack(pady=8)

date_btn.config(command=open_date_calculator)

# --------------- Start ---------------
root.mainloop()
