#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ======================================================
#  EA .DLF DECRYPTOR - GUI Version
#  Developed by HackSucks with ❤ 2025
#  "By the sailor, for the sailor"
# ======================================================

import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from xml.dom.minidom import parseString
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

FIXED_AES_KEY = bytes([
    65, 50, 114, 45, 208, 130, 239, 176,
    220, 100, 87, 197, 118, 104, 202, 9
])

def decrypt_license(data: bytes) -> str:
    iv = bytes(16)
    backend = default_backend()

    def try_decrypt(buf: bytes) -> bytes:
        if len(buf) % 16 != 0:
            buf += b"\x00" * (16 - len(buf) % 16)
        cipher = Cipher(algorithms.AES(FIXED_AES_KEY), modes.CBC(iv), backend=backend)
        decryptor = cipher.decryptor()
        return decryptor.update(buf) + decryptor.finalize()

    try:
        decrypted = try_decrypt(data)
        return decrypted.rstrip(b"\x00").decode("utf-8")
    except UnicodeDecodeError:
        decrypted = try_decrypt(data[0x41:])
        return decrypted.rstrip(b"\x00").decode("utf-8", errors="ignore")
    except Exception as e:
        raise RuntimeError(f"Unable to decrypt .dlf file: {e}")

def extract_info(text: str) -> dict:
    try:
        dom = parseString(text)
    except Exception:
        return {"error": "Invalid XML", "rawXML": text}

    def get_tag(tag):
        elems = dom.getElementsByTagName(tag)
        return elems[0].firstChild.nodeValue if elems else None

    return {
        "productId": get_tag("ContentId"),
        "cipherKey": get_tag("CipherKey"),
        "token": get_tag("GameToken"),
        "rawXML": text
    }

def auto_select_dlf():
    dir_path = r"C:\ProgramData\Electronic Arts\EA Services\License"
    if not os.path.exists(dir_path):
        messagebox.showerror("Error", "EA License directory not found.")
        return None
    files = [f for f in os.listdir(dir_path) if f.endswith(".dlf")]
    if not files:
        messagebox.showerror("Error", "No .dlf files found.")
        return None
    preferred = [f for f in files if f.endswith("_sc.dlf")]
    selected = preferred[0] if preferred else files[0]
    return os.path.join(dir_path, selected)

def manual_select_dlf():
    path = filedialog.askopenfilename(
        title="Select EA .DLF file",
        filetypes=[("DLF files", "*.dlf")]
    )
    return path if path else None

def decrypt_and_display(file_path, product_entry, cipher_text, token_text):
    if not file_path:
        return
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        decrypted = decrypt_license(data)
        info = extract_info(decrypted)
        with open("dlf_report.json", "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)

        # Clear previous content
        product_entry.config(state='normal')
        cipher_text.config(state='normal')
        token_text.config(state='normal')
        product_entry.delete(0, tk.END)
        cipher_text.delete(1.0, tk.END)
        token_text.delete(1.0, tk.END)

        # Insert new content
        product_entry.insert(0, info.get("productId", "(none)"))
        cipher_text.insert(tk.END, info.get("cipherKey", "(none)"))
        token_text.insert(tk.END, info.get("token", "(none)"))

        # Disable editing
        product_entry.config(state='readonly')
        cipher_text.config(state='disabled')
        token_text.config(state='disabled')

        messagebox.showinfo("Success", "Decrypted successfully! Report saved to dlf_report.json")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI
root = tk.Tk()
root.title("EA .DLF DECRYPTOR")

banner = tk.Label(root, text="EA .DLF DECRYPTOR\nDeveloped by HackSucks with ❤ 2025\nCredit to anadius for decryption logic\n\"By the pirate, for the pirate\"", font=("Consolas", 12), justify="center")
banner.pack(pady=10)

frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=5)

frame_outputs = tk.Frame(root)
frame_outputs.pack(pady=10)

# Product ID
tk.Label(frame_outputs, text="Product ID:").grid(row=0, column=0, sticky="w")
product_entry = tk.Entry(frame_outputs, width=100, state='readonly')
product_entry.grid(row=0, column=1, padx=5, pady=2)

# Cipher Key
tk.Label(frame_outputs, text="Cipher Key (you can ignore this):").grid(row=1, column=0, sticky="nw")
cipher_text = scrolledtext.ScrolledText(frame_outputs, width=80, height=5, state='disabled')
cipher_text.grid(row=1, column=1, padx=5, pady=2)

# Denuvo Token
tk.Label(frame_outputs, text="Denuvo Token (this is most likely the one you want):").grid(row=2, column=0, sticky="nw")
token_text = scrolledtext.ScrolledText(frame_outputs, width=80, height=10, state='disabled')
token_text.grid(row=2, column=1, padx=5, pady=2, sticky="n")

# Copy button for Denuvo Token
def copy_token():
    # Temporarily enable the text box to read content
    token_text.config(state='normal')
    token_content = token_text.get(1.0, tk.END).strip()
    token_text.config(state='disabled')
    if token_content:
        root.clipboard_clear()
        root.clipboard_append(token_content)
        root.update()  # Make sure clipboard is updated
        messagebox.showinfo("Copied", "Denuvo Token copied to clipboard!")


btn_copy_token = tk.Button(frame_outputs, text="Copy Token", command=copy_token)
btn_copy_token.grid(row=2, column=2, padx=5, pady=2, sticky="n")

# Buttons
btn_auto = tk.Button(frame_buttons, text="Auto-select latest EA license", width=30,
                     command=lambda: decrypt_and_display(auto_select_dlf(), product_entry, cipher_text, token_text))
btn_auto.grid(row=0, column=0, padx=5, pady=5)

btn_manual = tk.Button(frame_buttons, text="Manual select .dlf file", width=30,
                       command=lambda: decrypt_and_display(manual_select_dlf(), product_entry, cipher_text, token_text))
btn_manual.grid(row=0, column=1, padx=5, pady=5)

btn_exit = tk.Button(frame_buttons, text="Exit", width=10, command=root.destroy)
btn_exit.grid(row=0, column=2, padx=5, pady=5)

root.mainloop()
