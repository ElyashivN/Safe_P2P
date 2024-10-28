# Safe P2P File Management Tool - Overview

**SAFE P2P** is a privacy-focused peer-to-peer (P2P) file-sharing network designed to allow secure file downloads without revealing specific data requests. Traditional P2P systems expose users to potential surveillance as network observers can monitor which files are being requested. SAFE P2P mitigates this risk to prevent data exposure. This approach supports secure data retrieval in decentralized networks, ideal for users requiring enhanced privacy and reliability.

## Table of Contents
- [Requirements](#requirements)
- [Setup and running the code](#setup-and-running-the-code)
- [GUI Components](#gui-components)
- [Main Features](#main-features)
- [API Functions](#api-functions)

### Requirements

To run the code, you’ll need:
- Python 3.8+
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
_To test the functionality of SAFE P2P, you must run multiple instances of the GUI in parallel. This setup allows you to simulate peer-to-peer interactions. You can also run tests that does the same_

1. **Clone the Repository**:
   First, download the project files from GitHub by running:

   ```bash
   git clone https://github.com/ElyashivN/Safe_P2P.git
   ```

2. **Start the GUI**:
   Run the following command to launch the graphical interface:

   ```bash
   python GUI.py
   ```

Upon starting, you’ll see options to either create a new node or load an existing one. Once a node is active from one of these options, you can use the features described below.

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


This README provides a comprehensive guide for setting up, running, and using the GUI in this decentralized file management project. For more details, refer to the [GitHub repository](https://github.com/ElyashivN/Safe_P2P/tree/main).
