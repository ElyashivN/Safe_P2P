import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
import threading
from Node import Node
from dht import DHT
import test_Node
import unittest




class GUI:
    def __init__(self, root, node):
        self.root = root
        self.root.title("File Management Tool")
        self.root.geometry("300x410")
        print("GUI initialized.")

        # Create a Canvas for background pattern
        self.background_canvas = tk.Canvas(root, width=500, height=300, highlightthickness=0)
        self.background_canvas.pack(fill="both", expand=True)

        # Main Frame on top of Canvas
        main_frame = tk.Frame(self.background_canvas, bg="#f0f0f0")
        main_frame.place(relwidth=1, relheight=1)

        # Button Frame for centralizing buttons
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(pady=20, expand=True)

        # Upload button
        upload_button = ttk.Button(button_frame, text="Upload", command=self.upload_file, width=20)
        upload_button.pack(pady=10)

        # Download button
        download_button = ttk.Button(button_frame, text="Download", command=self.download_file, width=20)
        download_button.pack(pady=10)

        # Test button
        test_button = ttk.Button(button_frame, text="Test", command=self.test_action, width=20)
        test_button.pack(pady=10)

        # Add to DHT button
        add_dht_button = ttk.Button(button_frame, text="Add to DHT", command=self.add_to_dht_action, width=20)
        add_dht_button.pack(pady=10)

        # Get List Files button
        get_list_button = ttk.Button(button_frame, text="Get List Files on node", command=self.display_file_list, width=20)
        get_list_button.pack(pady=10)

        # Get List Files button
        get_list_button = ttk.Button(button_frame, text="Get the files node uploaded", command=self.display_uploaded_files, width=20)
        get_list_button.pack(pady=10)


        # Exit button
        exit_button = ttk.Button(button_frame, text="Exit", command=self.root.quit, width=20)
        exit_button.pack(pady=10)

        # Footer Label
        footer_label = tk.Label(main_frame, text="Developed by Eitan & Elyashiv", font=("Helvetica", 10),
                                bg="#f0f0f0", pady=10)
        footer_label.pack(side='bottom', fill='x')

        self.node = node

    def display_uploaded_files(self):
        """open a ist of all the uploaded files"""
        file_names = self.node.get_uploaded_files()
        print(f"Retrieved file names: {file_names}")

        # Create a new window to display the file names
        file_list_window = tk.Toplevel(self.root)
        file_list_window.title("List of Files uploaded")
        file_list_window.geometry("300x200")

        if file_names:
            files_text = "\n".join(file_names)
            label = tk.Label(file_list_window, text=files_text)
        else:
            label = tk.Label(file_list_window, text="No files available.")

        label.pack(pady=10)

    def add_to_dht_action(self):
        """Open a new window with 'Add DHT' and 'Add Node' buttons."""
        dht_window = tk.Toplevel(self.root)
        dht_window.title("Add to DHT")
        dht_window.geometry("300x150")

        # Add DHT button
        add_dht_button = ttk.Button(dht_window, text="Add DHT", command=self.add_dht_to_dht)
        add_dht_button.pack(pady=10)

        # Add Node button
        add_node_button = ttk.Button(dht_window, text="Add Node", command=self.add_node_to_dht)
        add_node_button.pack(pady=10)

    def add_node_to_dht(self):  #todo we have a running time warning
        """Call the _add_node method of the DHT class."""
        # Ask the user to enter the port
        port = simpledialog.askinteger("Add Node", "Enter the Port:")

        # Ask the user to enter the node_id
        node_id = simpledialog.askstring("Add Node", "Enter the Node ID:")

        # Ask the user to enter the host
        host = simpledialog.askstring("Add Node", "Enter the Host:")
        self.node.DHT.add_node(port, node_id, host)
        print(f"here is all the nodes:{self.node.DHT.get_dht()}") #todo check that it prints what we want

    def add_dht_to_dht(self):
        """Prompt the user for a port and call the add_DHT method of the DHT class with the specified port."""

        # Ask the user to enter the port for the new DHT
        port = simpledialog.askinteger("Add DHT", "Enter the Port for the new DHT:")

        # Create a new DHT instance with the user-specified port
        new_dht = DHT(port)

        # Add the new DHT to the current node's DHT list
        self.node.add_DHT(new_dht)

        print(f"DHT with Port {port} added to the current node's DHT.")

    def display_file_list(self):
        """Display the list of file names retrieved from the SpacePIR instance."""
        file_names = self.node.spacePIR.get_file_names()  # Call the get_file_names method
        print(f"Retrieved file names: {file_names}")

        # Create a new window to display the file names
        file_list_window = tk.Toplevel(self.root)
        file_list_window.title("List of Files")
        file_list_window.geometry("300x200")

        if file_names:
            files_text = "\n".join(file_names)
            label = tk.Label(file_list_window, text=files_text)
        else:
            label = tk.Label(file_list_window, text="No files available.")

        label.pack(pady=10)


    def add_hover_effect(self, button):
        def on_enter(event):
            button.config(style="Hover.TButton")

        def on_leave(event):
            button.config(style="TButton")

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            n,k = self.node.upload(file_path)
            print(file_path, n, k)

    def download_file(self):
        file_name = simpledialog.askstring("Download File", "Enter the name of the file to download:")
        if file_name:
            print(f"Initiating download for file: {file_name}")
            new_window = tk.Toplevel(self.root)
            label = tk.Label(new_window, text=f"Downloading {file_name}")
            label.pack(pady=20)
            # Ask the user for `n` and `k`
            n = simpledialog.askinteger("Download", "Enter n:")
            k = simpledialog.askinteger("Download", "Enter k:")
            self.node.download(file_name, n, k)

    def run_tests(self, progress, result_labels):  #todo maybe elyashiv changed the tests or the names
        test_cases = [
            {"name": "Test Message Exchange", "func": test_Node.TestNodeMessaging("test_message_exchange")},
            {"name": "Test Send Receive", "func": test_Node.TestNodeMessaging("test_send_recieve")},
            {"name": "Test Mock Download", "func": test_Node.TestNodeMessaging("test_mock_download")},
            {"name": "Test Upload Download", "func": test_Node.TestNodeMessaging("test_upload_download")}
        ]

        total_tests = len(test_cases)
        for i, test in enumerate(test_cases):
            print(f"Running {test['name']}...")
            result_labels[i].config(text=f"{test['name']}: Running... ⏳", fg="blue")

            # Run the test function and check if it passes
            result = unittest.TextTestRunner().run(test["func"])
            passed = result.wasSuccessful()

            # Update progress bar
            progress["value"] = (i + 1) / total_tests * 100
            self.root.update_idletasks()

            # Update result label based on test outcome
            result_labels[i].config(
                text=f"{test['name']}: ✔️ Passed" if passed else "❌ Failed",
                fg="green" if passed else "red"
            )
            print(f"{test['name']} {'Passed' if passed else 'Failed'}.")

    def test_action(self):
        new_window = tk.Toplevel(self.root)
        new_window.title("Test Results")
        new_window.geometry("400x300")
        print("Test window opened.")

        label = tk.Label(new_window, text="Running Tests...", font=("Helvetica", 14))
        label.pack(pady=10)

        progress = ttk.Progressbar(new_window, length=300, mode='determinate')
        progress.pack(pady=10)

        test_names = ["Test 1", "Test 2", "Test 3"]
        result_labels = [tk.Label(new_window, text=f"{test_name}: Pending", font=("Helvetica", 12))
                         for test_name in test_names]
        for label in result_labels:
            label.pack()

        test_thread = threading.Thread(target=self.run_tests, args=(progress, result_labels,))
        test_thread.start()

        def check_tests_done():
            if not test_thread.is_alive():
                close_button = ttk.Button(new_window, text="Close", command=new_window.destroy)
                close_button.pack(pady=10)
                self.add_hover_effect(close_button)
                print("Tests completed.")
            else:
                new_window.after(100, check_tests_done)

        check_tests_done()


def main_window(root, node):
    root.withdraw()  # Hide initial window
    print("Initial window hidden. Opening main GUI window.")
    main_app_window = tk.Toplevel(root)  # New window for main GUI
    GUI(main_app_window, node)  # Launch main GUI


def load_node(root, node):  # todo not working yet
    # Create a new top-level window for password input
    password_window = tk.Toplevel(root)
    password_window.title("Enter Password")
    password_window.geometry("300x150")

    # Label for password instruction
    label = tk.Label(password_window, text="Please enter your password:")
    label.pack(pady=10)

    # Entry widget for password input
    password_entry = tk.Entry(password_window, show="*", width=30)
    password_entry.pack(pady=5)

    # Function to handle password submission
    def submit_password(event=None):
        password = password_entry.get()
        print("[INFO] Password entered.")
        # Call load_node with the entered password
        Node.load_node(node, password)
        password_window.destroy()

    # Bind the Enter key to the submit_password function
    password_entry.bind('<Return>', submit_password)
    # Submit button
    submit_button = ttk.Button(password_window, text="Submit", command=submit_password)
    submit_button.pack(pady=10)

def create_new_node(root, flag_load):
    if not flag_load:
        port = simpledialog.askinteger("Create New Node", "Enter the Port:")
        host = simpledialog.askstring("Create New Node", "Enter the host"
                                                         "(dont enter anything for local host 127.0.0.1:")
        peer_id = simpledialog.askstring("Create New Node", "Enter the Peer ID:")
        if host == None:
            node = Node(port, peer_id)
        # Create the node with the provided port and peer ID
        else:
            node = Node(port, peer_id, host=host)
        print(f"Created new Node with ID: {peer_id} on Port: {port} with host: {host}")
        main_window(root, node)
        return node


def first_window():
    # Initial window to prompt for password or create/load node
    root = tk.Tk()
    root.title("Node Creation")
    root.geometry("300x150")

    style = ttk.Style()
    style.configure("TButton", font=("Helvetica", 12), padding=6)
    style.configure("Hover.TButton", background="#7FFF7F")

    # "Create New Node" Button
    create_button = ttk.Button(root, text="Create New Node", command=lambda: create_new_node(root, False))
    create_button.pack(pady=10)

    # "Load Node" Button
    node = create_new_node(root, True)
    load_button = ttk.Button(root, text="Load Node", command=lambda: load_node(root, node))
    load_button.pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    first_window()
