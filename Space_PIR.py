import os

class SpacePIR:
    def __init__(self, base_directory="path"):
        # Initialize an empty list to hold the file names and their storage locations
        self.space = []
        self.base_directory = base_directory  # Allow dynamic base directory

    def add(self, file_name, file_content):
        """
        Add a file to the space and store it only if it is not already stored.
        """
        # Define the storage path for this file (assuming a base directory)

        file_path = os.path.join(self.base_directory, file_name)

        # Check if the file is already in the space list
        for name, path in self.space:
            if name == file_name:
                print(f"File '{file_name}' already stored at {path}. No action needed.")
                return  # Exit the function as the file is already stored

        # If the file is not in the space, add it and store it
        self.space.append((file_name, file_path))
        self.space.sort(key=lambda x: x[0])  # Keep the list sorted by file_name

        # Call store to save the new file on the hard drive
        self.store(file_path, file_content)

    def store(self, file_path, file_content):
        """
        Store a single file at the given file path.
        """
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Write content to the file
        with open(file_path, 'w') as file:
            file.write(file_content)
        print(f"Stored file: {file_path}")

    def get_space(self):
        """
        Return the current sorted space list.
        """
        return self.space
