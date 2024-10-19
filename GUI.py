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
        self.root.title("File Management Tool")
        self.root.geometry("400x300")  # Adjust the window size

        self.node = node

        # Styling
        title_font = ("Helvetica", 18, "bold")
        button_font = ("Helvetica", 12)
        button_color = "#4CAF50"
        button_fg = "white"


        # Create a Frame for the Buttons
        button_frame = tk.Frame(root, bg="#f0f0f0")
        button_frame.pack(pady=20, expand=True)

        # Upload button
        upload_button = tk.Button(
            button_frame, text="Upload", command=self.upload_file, width=20, height=2,
            font=button_font, bg=button_color, fg=button_fg
        )
        upload_button.pack(pady=10)

        # Download button
        download_button = tk.Button(
            button_frame, text="Download", command=self.download_file, width=20, height=2,
            font=button_font, bg=button_color, fg=button_fg
        )
        download_button.pack(pady=10)

        # Test button
        test_button = tk.Button(
            button_frame, text="Test", command=self.test_action, width=20, height=2,
            font=button_font, bg=button_color, fg=button_fg
        )
        test_button.pack(pady=10)

        # Footer Label
        footer_label = tk.Label(root, text="Developed by Eitan & Elyashiv", font=("Helvetica", 10), bg="#f0f0f0", pady=10)
        footer_label.pack(side='bottom', fill='x')


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

    def test_action(self):
        # Action for the Test button
        new_window = tk.Toplevel(self.root)
        label = tk.Label(new_window, text="add test in the future")
        label.pack(pady=20)

if __name__ == '__main__':
    root = tk.Tk()
    node = Temp_Node()
    app = GUI(root, node)
    root.configure(bg="#f0f0f0")  # Set background color for the main window
    root.mainloop()
