import tkinter as tk
from tkinter import filedialog, simpledialog

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
        self.root.title("Upload and Download GUI")
        self.node = node

        upload_button = tk.Button(root, text="Upload", command=self.upload_file)
        upload_button.pack(pady=10)

        download_button = tk.Button(root, text="Download", command=self.download_file)
        download_button.pack(pady=10)

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.node.upload(file_path)

    def download_file(self):
        file_name = simpledialog.askstring("Download File", "Enter the name of the file to download:")
        if file_name:
            new_window = tk.Toplevel(self.root)
            label = tk.Label(new_window, text=f"Downloading {file_name}")
            label.pack(pady=20)
            self.node.download(file_name)

if __name__ == '__main__':
    root = tk.Tk()
    node = Temp_Node()
    app = GUI(root, node)
    root.mainloop()
