# Safe P2P File Management Tool - GUI Overview

This project is a decentralized file management system enabling secure file upload, download, and peer-to-peer (P2P) data management with privacy and redundancy. The graphical user interface (GUI) offers a straightforward way to interact with network nodes, Distributed Hash Table (DHT), and file handling features in this P2P network.

## Table of Contents
- [Requirements](#requirements)
- [Setup and Running the Code](#setup-and-running-the-code)
- [GUI Components](#gui-components)
- [Main Features](#main-features)
- [API Functions](#api-functions)

### Requirements

To run the code, you’ll need:
- Python 
- The following Python libraries:
  - `tkinter` (usually included with Python)
  - `socket`
  - `hashlib`
  - `cryptography`
  - `unittest`
  - `zfec`
  - `paillier` (for homomorphic encryption, part of `phe` library)

You can install these dependencies using:

```bash
pip install cryptography zfec phe
```

### Setup and Running the Code

1. **Clone the Repository**:
   First, download the project files from GitHub by running:

   ```bash
   git clone https://github.com/ElyashivN/Safe_P2P.git
   ```

2. **Navigate to the Project Directory**:
   Change to the project’s main directory:

   ```bash
   cd Safe_P2P
   ```

3. **Start the GUI**:
   Run the following command to launch the graphical interface:

   ```bash
   python GUI.py
   ```

Upon starting, you’ll see options to either create a new node or load an existing one. Once a node is active, you can use the features described below.

### GUI Components

1. **Upload Button**  
   Upload a file to the network. The file is divided, encrypted, and distributed among peers.

2. **Download Button**  
   Retrieve a file by its name. You must enter the file name, and additional parameters (`n` and `k`) to reconstruct the file.

3. **Add to DHT**  
   Adds a new node or a new DHT to the network, which can store file references.

4. **Get List Files**  
   Displays a list of files available in the current network.

5. **Test Button**  
   Runs various tests to verify network functions, such as messaging and file transfer.

6. **Exit**  
   Exits the application.

### Main Features

- **File Upload**: Select a file from your local system to upload it to the network. The GUI handles file division, encryption, and distribution across peers.
- **File Download**: Enter the file name to retrieve it from the network. The system requests parts from various nodes and reconstructs the file.
- **DHT Management**: Allows adding nodes or entire DHT instances to enhance network resilience and data redundancy.
- **Testing Module**: Validates network operations, including file uploads/downloads and inter-node communication, ensuring system reliability.

### API Functions

#### `upload_file`
Prompts the user to select a file from their system and uploads it to the network. Uses the `upload` method from the `Node` class.

#### `download_file`
Requests a file from the network. The user provides the file name and parameters `n` and `k` for file reconstruction.

#### `add_to_dht_action`
Opens a window with options to add a DHT or a new node to the current DHT, enhancing the network's peer structure.

#### `display_file_list`
Displays the list of files stored across the network, using the `get_file_names` method from the `spacePIR` module.

#### `test_action`
Runs a series of tests to validate the network's file management capabilities, displaying results in real-time.

---

This README provides a comprehensive guide for setting up, running, and using the GUI in this decentralized file management project. For more details, refer to the [GitHub repository](https://github.com/ElyashivN/Safe_P2P/tree/main).
