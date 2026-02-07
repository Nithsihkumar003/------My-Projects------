import tkinter as tk
from tkinter import scrolledtext
import threading
from langchain_ollama import ChatOllama
from tools import search_files, get_all_drives
import os


class DesktopAgent:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("PC Agent")
        self.window.configure(bg="#1a1a1a")

        self.last_search_results = []
        self.llm = ChatOllama(model="qwen2.5:7b", temperature=0)
        self.create_widgets()

    def search_and_display(self, query: str, file_type: str = "all") -> str:
        """Search files and store results"""
        result = search_files(query, directory="all", max_results=10, file_type=file_type)

        # Extract file paths from search results
        self.last_search_results = []
        lines = result.split('\n')

        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and line[0].isdigit() and line[1] == '.':
                try:
                    parts = line.split('. ', 1)
                    if len(parts) < 2:
                        continue

                    rest = parts[1]

                    if rest.endswith(' MB)'):
                        last_paren = rest.rfind(' (')
                        if last_paren > 0:
                            path = rest[:last_paren]
                        else:
                            path = rest
                    else:
                        path = rest

                    path = path.strip()

                    if os.path.exists(path):
                        self.last_search_results.append(path)
                        print(f"Added file {len(self.last_search_results)}: {os.path.basename(path)}")
                except Exception as e:
                    print(f"Parse error: {e}")
                    continue

        print(f"Total files ready to open: {len(self.last_search_results)}")
        return result

    def open_file(self, file_number: int) -> str:
        """Open file by number"""
        try:
            print(f"\nTrying to open file #{file_number}")
            print(f"Available files: {len(self.last_search_results)}")

            index = file_number - 1
            if 0 <= index < len(self.last_search_results):
                filepath = self.last_search_results[index]
                print(f"Opening: {filepath}")
                os.startfile(filepath)
                return f"Opening: {os.path.basename(filepath)}"
            else:
                return f"File #{file_number} not found. Only {len(self.last_search_results)} files available."
        except Exception as e:
            return f"Error opening file: {e}"

    def process_command_simple(self, command: str) -> str:
        """Process command - handles ANY file type"""
        cmd = command.lower().strip()

        if 'search' in cmd or 'find' in cmd or 'look' in cmd:
            query = ""
            for keyword in ['search for', 'find', 'look for', 'search', 'find', 'look']:
                if keyword in cmd:
                    parts = command.split(keyword, 1)
                    if len(parts) > 1:
                        query = parts[1].strip()
                    break

            if not query:
                query = command

            file_type = "all"

            if 'music' in cmd or 'audio' in cmd or 'song' in cmd or 'mp3' in cmd:
                file_type = "audio"
            elif 'video' in cmd or 'movie' in cmd or 'mp4' in cmd:
                file_type = "video"
            elif 'image' in cmd or 'photo' in cmd or 'picture' in cmd:
                file_type = "image"
            elif 'document' in cmd or 'pdf' in cmd or 'doc' in cmd:
                file_type = "document"
            elif 'code' in cmd or 'python' in cmd or 'java' in cmd or 'project' in cmd:
                file_type = "code"
            elif 'zip' in cmd or 'rar' in cmd or 'archive' in cmd:
                file_type = "archive"

            return self.search_and_display(query, file_type=file_type)

        elif 'play' in cmd or 'open' in cmd or 'run' in cmd or 'launch' in cmd:
            words = cmd.split()
            for word in words:
                if word.isdigit():
                    return self.open_file(int(word))

            if self.last_search_results:
                return self.open_file(1)
            else:
                return "No files to open. Search for files first!"

        else:
            return f"""Command not understood: "{command}"

Try: "find music" • "search documents" • "open 1" """

    def create_widgets(self):
        """Create elegant professional GUI"""

        # Configure window
        self.window.geometry("750x550")
        self.window.resizable(True, True)

        # Color scheme
        bg_dark = "#1a1a1a"
        bg_medium = "#2d2d2d"
        accent_green = "#00d4aa"
        accent_red = "#ff5252"
        text_white = "#e0e0e0"
        text_gray = "#888888"

        # Header
        header_frame = tk.Frame(self.window, bg=accent_green, height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="PC Agent",
            font=("Segoe UI", 18, "bold"),
            bg=accent_green,
            fg="#000000"
        ).pack(side=tk.LEFT, padx=20, pady=15)

        drives = get_all_drives()
        tk.Label(
            header_frame,
            text=f"Drives: {', '.join(drives)}",
            font=("Segoe UI", 10),
            bg=accent_green,
            fg="#000000"
        ).pack(side=tk.RIGHT, padx=20)

        # Content
        content_frame = tk.Frame(self.window, bg=bg_dark)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(
            content_frame,
            text="Results",
            font=("Segoe UI", 11, "bold"),
            bg=bg_dark,
            fg=text_white
        ).pack(anchor="w", pady=(0, 5))

        self.output_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            width=85,
            height=15,
            font=("Consolas", 9),
            bg=bg_medium,
            fg=accent_green,
            insertbackground=accent_green,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Input
        input_container = tk.Frame(content_frame, bg=bg_dark)
        input_container.pack(fill=tk.X, pady=(15, 0))

        tk.Label(
            input_container,
            text="Command",
            font=("Segoe UI", 10, "bold"),
            bg=bg_dark,
            fg=text_white
        ).pack(anchor="w", pady=(0, 5))

        input_frame = tk.Frame(input_container, bg=bg_medium, highlightthickness=1, highlightbackground=accent_green)
        input_frame.pack(fill=tk.X)

        self.input_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 11),
            bg=bg_medium,
            fg=text_white,
            insertbackground=accent_green,
            relief=tk.FLAT,
            bd=0
        )
        self.input_entry.pack(fill=tk.X, padx=10, pady=10)
        self.input_entry.bind("<Return>", lambda e: self.process_command())

        # Buttons
        button_frame = tk.Frame(content_frame, bg=bg_dark)
        button_frame.pack(pady=(10, 0))

        self.send_button = tk.Button(
            button_frame,
            text="Execute",
            font=("Segoe UI", 10, "bold"),
            bg=accent_green,
            fg="#000000",
            activebackground="#00b894",
            activeforeground="#000000",
            relief=tk.FLAT,
            bd=0,
            padx=30,
            pady=8,
            cursor="hand2",
            command=self.process_command
        )
        self.send_button.pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Clear",
            font=("Segoe UI", 10),
            bg=accent_red,
            fg="#ffffff",
            activebackground="#e74c3c",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.clear_output
        ).pack(side=tk.LEFT, padx=5)

        # Footer
        hint_text = 'Try: "find music" • "search documents" • "open 1"'
        tk.Label(
            content_frame,
            text=hint_text,
            font=("Segoe UI", 8),
            bg=bg_dark,
            fg=text_gray
        ).pack(pady=(8, 0))

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def process_command(self):
        command = self.input_entry.get().strip()
        if not command:
            return

        self.input_entry.delete(0, tk.END)
        self.output_text.insert(tk.END, f"\n{'=' * 80}\n")
        self.output_text.insert(tk.END, f"You: {command}\n")
        self.output_text.insert(tk.END, f"{'=' * 80}\n")
        self.send_button.config(state=tk.DISABLED, text="Processing...")

        thread = threading.Thread(target=self.execute_command, args=(command,))
        thread.start()

    def execute_command(self, command):
        try:
            result = self.process_command_simple(command)
            self.window.after(0, self.display_result, result)
        except Exception as e:
            self.window.after(0, self.display_result, f"Error: {e}")
        finally:
            self.window.after(0, lambda: self.send_button.config(state=tk.NORMAL, text="Execute"))

    def display_result(self, result):
        self.output_text.insert(tk.END, f"\nAgent:\n{result}\n")
        self.output_text.see(tk.END)

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = DesktopAgent()
    app.run()
