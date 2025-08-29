import tkinter as tk
from tkinter import messagebox
import ast
import speech_recognition as sr
from word2number import w2n

# -------------------- Safe Eval --------------------
def safe_eval(expr):
    try:
        node = ast.parse(expr, mode="eval")
        return eval_(node.body)
    except Exception:
        return "Error"

def eval_(node):
    if isinstance(node, ast.Constant):  # Python 3.8+
        return node.value
    elif isinstance(node, ast.Num):  # Python <=3.7
        return node.n
    elif isinstance(node, ast.BinOp):
        left, right = eval_(node.left), eval_(node.right)
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        if isinstance(node.op, ast.Div): return left / right
    raise TypeError(node)

# -------------------- Calculator Logic --------------------
def click(button_text):
    if button_text == "=":
        calculate()
    elif button_text == "C":
        entry.delete(0, tk.END)
    else:
        entry.insert(tk.END, button_text)

def calculate():
    expression = entry.get()
    result = safe_eval(expression)
    entry.delete(0, tk.END)
    entry.insert(tk.END, str(result))

# -------------------- Voice Input --------------------
def voice_input():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            messagebox.showinfo("Voice Input", "Speak your calculation (e.g., 'five plus three')")
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source)

        text = r.recognize_google(audio)
        print("You said:", text)

        # Convert words to numbers if possible
        try:
            text = text.lower().replace("plus", "+").replace("minus", "-").replace("times", "*").replace("into", "*").replace("divide", "/")
            words = text.split()
            converted = []
            for word in words:
                try:
                    converted.append(str(w2n.word_to_num(word)))
                except:
                    converted.append(word)
            text = " ".join(converted)
        except:
            pass

        entry.delete(0, tk.END)
        entry.insert(tk.END, text)
        calculate()

    except sr.UnknownValueError:
        messagebox.showerror("Error", "Could not understand your voice.")
    except sr.RequestError:
        messagebox.showerror("Error", "Speech recognition service unavailable.")

# -------------------- Keyboard Support --------------------
def key_press(event):
    char = event.char
    if char.isdigit() or char in "+-*/.":
        entry.insert(tk.END, char)
    elif event.keysym == "Return":
        calculate()
    elif event.keysym == "BackSpace":
        current = entry.get()
        entry.delete(0, tk.END)
        entry.insert(tk.END, current[:-1])

# -------------------- GUI --------------------
root = tk.Tk()
root.title("Echo Calculator")

entry = tk.Entry(root, width=25, font=("Arial", 18), borderwidth=5, relief="ridge")
entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

buttons = [
    "7", "8", "9", "/",
    "4", "5", "6", "*",
    "1", "2", "3", "-",
    "0", ".", "=", "+"
]

row, col = 1, 0
for b in buttons:
    tk.Button(root, text=b, width=5, height=2, font=("Arial", 14),
              command=lambda bt=b: click(bt)).grid(row=row, column=col, padx=5, pady=5)
    col += 1
    if col > 3:
        col = 0
        row += 1

tk.Button(root, text="C", width=5, height=2, font=("Arial", 14), command=lambda: click("C")).grid(row=row, column=0, padx=5, pady=5)
tk.Button(root, text="🎤", width=12, height=2, font=("Arial", 14), command=voice_input).grid(row=row, column=1, columnspan=3, padx=5, pady=5)

# Bind keyboard events
root.bind("<Key>", key_press)

root.mainloop()
