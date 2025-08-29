
import threading
import tkinter as tk
from tkinter import messagebox
import ast
import operator as op

import speech_recognition as sr
from word2number import w2n

# ---------- Safe Evaluator (AST-based) ----------
# Allowed operators
_ALLOWED_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
}
_ALLOWED_UNARY_OPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Num):  # Python <=3.7
        return node.n
    if isinstance(node, ast.Constant):  # Python 3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers are allowed.")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        operand = _eval_ast(node.operand)
        return _ALLOWED_UNARY_OPS[type(node.op)](operand)
    if isinstance(node, ast.Paren):
        return _eval_ast(node.value)
    if isinstance(node, ast.Expr):
        return _eval_ast(node.value)
    if isinstance(node, ast.Call):
        raise ValueError("Function calls are not allowed.")
    if isinstance(node, ast.Name):
        raise ValueError("Names/variables are not allowed.")
    if isinstance(node, ast.Subscript):
        raise ValueError("Subscripts are not allowed.")
    raise ValueError("Invalid or unsupported expression.")

def safe_eval(expr: str) -> float:
    """Safely evaluate arithmetic expression with + - * / ** % and parentheses."""
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval_ast(tree)
    except ZeroDivisionError:
        raise
    except Exception as e:
        raise ValueError(str(e))

# ---------- Speech to Math Conversion ----------
import re

# Order matters: replace longer phrases first
PHRASE_REPLACEMENTS = [
    (r"\bto the power of\b", "**"),
    (r"\bpower of\b", "**"),
    (r"\bpower\b", "**"),
    (r"\bdivided by\b", "/"),
    (r"\bdivide by\b", "/"),
    (r"\bdivide\b", "/"),
    (r"\bover\b", "/"),
    (r"\bmultiplied by\b", "*"),
    (r"\btimes\b", "*"),
    (r"\binto\b", "*"),
    (r"\bminus\b", "-"),
    (r"\bplus\b", "+"),
    (r"\badd\b", "+"),
    (r"\bsubtract\b", "-"),
    (r"\bopen parenthesis\b", "("),
    (r"\bclose parenthesis\b", ")"),
    (r"\bpoint\b", "."),
    (r"\bx\b", "*"),  # often recognized as 'x' for multiply
]

NUMBER_WORDS = set("""
zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen
seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million
and a an point
""".split())

def words_chunk_to_number(tokens):
    """Convert a sequence of number words to a numeric string using word2number."""
    phrase = " ".join(tokens)
    # Normalize common artifacts
    phrase = phrase.replace(" a ", " one ")
    try:
        n = w2n.word_to_num(phrase)
        return str(n)
    except Exception:
        return " ".join(tokens)  # fallback

def text_to_math(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r",", "", s)
    # Replace phrases
    for pat, repl in PHRASE_REPLACEMENTS:
        s = re.sub(pat, repl, s)

    # Tokenize by space and keep operators/parentheses/dots separate
    # Split operators to own tokens
    s = re.sub(r"([\+\-\*\/\(\)\%])", r" \1 ", s)
    tokens = s.split()

    result_tokens = []
    number_buffer = []

    def flush_number_buffer():
        if number_buffer:
            # If buffer contains any number-words, convert them
            if any(t in NUMBER_WORDS for t in number_buffer):
                result_tokens.append(words_chunk_to_number(number_buffer))
            else:
                # Join digits or mixed tokens
                result_tokens.append("".join(number_buffer))
            number_buffer.clear()

    for t in tokens:
        if t in {"+", "-", "*", "/", "(", ")", "%", "**"}:
            flush_number_buffer()
            result_tokens.append(t)
        else:
            # Accumulate potential number words/digits/decimal points
            number_buffer.append(t)

    flush_number_buffer()
    # Post-clean: join repeated ** that might have been split
    expr = " ".join(result_tokens)
    expr = expr.replace("* *", "**")
    # Remove accidental spaces around dots in numbers
    expr = re.sub(r"\s*\.\s*", ".", expr)
    return expr

# ---------- GUI ----------
class VoiceCalculatorApp:
    def __init__(self, root):
        self.root = root
        root.title("Voice Calculator")
        root.geometry("360x500")

        self.entry = tk.Entry(root, font=("Segoe UI", 20), bd=6, relief=tk.GROOVE, justify="right")
        self.entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Configure grid
        for i in range(6):
            root.rowconfigure(i, weight=1)
        for j in range(4):
            root.columnconfigure(j, weight=1)

        # Buttons layout
        buttons = [
            ("C", 1, 0), ("(", 1, 1), (")", 1, 2), ("⌫", 1, 3),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2), ("/", 2, 3),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2), ("*", 3, 3),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2), ("-", 4, 3),
            ("0", 5, 0), (".", 5, 1), ("=", 5, 2), ("+", 5, 3),
        ]

        for (text, r, c) in buttons:
            tk.Button(root, text=text, font=("Segoe UI", 16), command=lambda t=text: self.on_button(t)).grid(
                row=r, column=c, padx=6, pady=6, sticky="nsew"
            )

        # Voice button spans all columns
        self.voice_btn = tk.Button(root, text="🎤 Speak", font=("Segoe UI", 16), command=self.on_voice_click)
        self.voice_btn.grid(row=6, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    def on_button(self, char):
        if char == "C":
            self.entry.delete(0, tk.END)
        elif char == "⌫":
            current = self.entry.get()
            if current:
                self.entry.delete(len(current)-1, tk.END)
        elif char == "=":
            self.evaluate()
        else:
            self.entry.insert(tk.END, char)

    def evaluate(self):
        expr = self.entry.get().strip()
        if not expr:
            return
        try:
            result = safe_eval(expr)
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, str(result))
        except ZeroDivisionError:
            messagebox.showerror("Math Error", "Division by zero.")
        except Exception as e:
            messagebox.showerror("Invalid Expression", str(e))

    def on_voice_click(self):
        # Use a thread so the UI doesn't freeze while listening
        self.voice_btn.config(state=tk.DISABLED, text="Listening... 🎤")
        threading.Thread(target=self._listen_and_process, daemon=True).start()

    def _listen_and_process(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
            text = recognizer.recognize_google(audio)
            expr = text_to_math(text)
            # Update UI back on main thread
            self.root.after(0, self._set_expression_and_eval, expr)
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: messagebox.showwarning("Timeout", "No speech detected."))
        except sr.UnknownValueError:
            self.root.after(0, lambda: messagebox.showwarning("Try Again", "Could not understand audio."))
        except sr.RequestError as e:
            self.root.after(0, lambda: messagebox.showerror("Speech Service Error", str(e)))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, lambda: self.voice_btn.config(state=tk.NORMAL, text="🎤 Speak"))

    def _set_expression_and_eval(self, expr):
        self.entry.delete(0, tk.END)
        self.entry.insert(tk.END, expr)
        # Optional: auto-evaluate after voice input
        try:
            result = safe_eval(expr)
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, str(result))
        except Exception:
            # If invalid, just leave the expression as-is for user to edit
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceCalculatorApp(root)
    root.mainloop()
