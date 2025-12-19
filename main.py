import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import os

from llm.gwt_generator import generate_gwt_scenarios


class GWTGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Test Gen - Tahap 1: Buat User Scenario")
        self.root.geometry("900x700")

        tk.Label(root, text="User Story:", font=("Arial", 10, "bold")).pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        self.user_story = scrolledtext.ScrolledText(root, height=6, wrap=tk.WORD)
        self.user_story.pack(padx=10, fill=tk.X)

        tk.Label(root, text="HTML Code:", font=("Arial", 10, "bold")).pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        self.html_code = scrolledtext.ScrolledText(root, height=12, wrap=tk.WORD)
        self.html_code.pack(padx=10, fill=tk.X)

        self.btn_process = tk.Button(
            root,
            text="Generate GWT Scenarios",
            command=self.on_process,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.btn_process.pack(pady=10)

        tk.Label(
            root,
            text="Generated GWT Scenarios (Output):",
            font=("Arial", 10, "bold"),
        ).pack(anchor="w", padx=10)

        self.output = scrolledtext.ScrolledText(
            root, height=15, wrap=tk.WORD, bg="#f0f0f0"
        )
        self.output.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)

    def on_process(self):
        user_story = self.user_story.get("1.0", tk.END).strip()
        html_code = self.html_code.get("1.0", tk.END).strip()

        if not user_story or not html_code:
            messagebox.showwarning(
                "Input Kosong", "Harap isi User Story dan HTML Code."
            )
            return

        self.btn_process.config(state="disabled", text="Processing...")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "Menghubungi LLM...\n")

        thread = threading.Thread(target=self.run_llm, args=(user_story, html_code))
        thread.start()

    def run_llm(self, user_story, html_code):
        result = generate_gwt_scenarios(user_story, html_code)
        self.root.after(0, self.display_result, result)

    def display_result(self, result):
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, result)
        self.btn_process.config(state="normal", text="Generate GWT Scenarios")

        self.save_scenarios_to_file(result)
        self.root.after(200, self.run_parser)

    def save_scenarios_to_file(self, content):
        os.makedirs("outputs", exist_ok=True)
        filepath = os.path.join("outputs", "generated_scenarios.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def run_parser(self):
        try:
            from parser.gwt_parser import convert_scenarios_to_files

            files = convert_scenarios_to_files("outputs/generated_scenarios.txt")

            msg = "\n[SUCCESS] File Selenium siap dijalankan:\n"
            for f in files:
                msg += f"  - {os.path.basename(f)}\n"

            self.output.insert(tk.END, msg)

        except Exception as e:
            self.output.insert(tk.END, f"\n[ERROR] Gagal parsing: {str(e)}\n")
            import traceback

            print(traceback.format_exc())


if __name__ == "__main__":
    root = tk.Tk()
    app = GWTGeneratorApp(root)
    root.mainloop()
