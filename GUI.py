import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from tkinter import ttk
from tkinter.font import Font

class Temp_Node:
    @staticmethod
    def upload(file_path):
        # Placeholder for the actual upload logic
        print(f"Uploading file: {file_path}")

    @staticmethod
    def download(file_name):
        # Placeholder for the actual download logic
        print(f"Downloading file: {file_name}")

class GUI:
    def __init__(self, root, node):
        self.root = root
        self.node = node
        self.root.title("File Transfer Application")
        self.root.geometry("400x250")
        self.root.resizable(False, False)

        # Set a style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # You can choose other themes like 'default', 'classic', 'alt'

        # Set custom font
        self.custom_font = Font(family="Helvetica", size=12)
        self.style.configure('TButton', font=self.custom_font)
        self.style.configure('TLabel', font=self.custom_font)
        self.style.configure('Header.TLabel', font=("Helvetica", 16, 'bold'))

        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Label
        self.header_label = ttk.Label(self.main_frame, text="Welcome to File Transfer", style='Header.TLabel')
        self.header_label.pack(pady=(0, 20))

        # Upload Button with icon
        self.upload_icon = tk.PhotoImage(file="upload_icon.jpg")  # Make sure you have an icon file
        self.upload_button = ttk.Button(
            self.main_frame, text=" Upload File", command=self.upload_file, image=self.upload_icon, compound='left'
        )
        self.upload_button.pack(pady=10, fill=tk.X)

        # Download Button with icon
        self.download_icon = tk.PhotoImage(file="download_icon.png")  # Make sure you have an icon file
        self.download_button = ttk.Button(
            self.main_frame, text=" Download File", command=self.download_file, image=self.download_icon, compound='left'
        )
        self.download_button.pack(pady=10, fill=tk.X)

        # Progress Bar
        self.progress = ttk.Progressbar(self.main_frame, orient='horizontal', mode='determinate', length=300)
        self.progress.pack(pady=20)

        # Status Label
        self.status_label = ttk.Label(self.main_frame, text="Status: Ready")
        self.status_label.pack()

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.status_label.config(text="Status: Uploading...")
            self.progress.start(10)  # Simulate progress
            self.root.after(2000, self.finish_upload, file_path)

    def finish_upload(self, file_path):
        self.progress.stop()
        self.status_label.config(text="Status: Upload Complete")
        self.node.upload(file_path)
        messagebox.showinfo("Upload", f"File '{file_path}' uploaded successfully.")

    def download_file(self):
        file_name = simpledialog.askstring("Download File", "Enter the name of the file to download:")
        if file_name:
            self.status_label.config(text="Status: Downloading...")
            self.progress.start(10)  # Simulate progress
            self.root.after(2000, self.finish_download, file_name)

    def finish_download(self, file_name):
        self.progress.stop()
        self.status_label.config(text="Status: Download Complete")
        self.node.download(file_name)
        messagebox.showinfo("Download", f"File '{file_name}' downloaded successfully.")

if __name__ == '__main__':
    root = tk.Tk()
    node = Temp_Node()
    app = GUI(root, node)
    root.mainloop()
