import base64
import os
from typing import List

import numpy as np

import config
from encryption import Encryption


class SpacePIR:
    def __init__(self, max_capacity=1000, base_directory="path"):
        # Initialize an empty list to hold the file names and their storage locations
        self.space = []  # Space should store (filename, path) tuples
        self.base_directory = base_directory  # Allow dynamic base directory
        self.max_capacity = max_capacity
        self.number_file_uploaded = 0
        self.is_allow_upload = True

    def change_capacity(self,new_capacity):
        if new_capacity > len(self.space):
            self.max_capacity = new_capacity
            return True
        return False

    def get_file_names(self):
        """
        Return a list of file names without the paths in the same order as stored in `space`.
        """
        return [file_name for file_name, _ in self.space]

    def turn_off_upload(self):
        self.is_allow_upload = False

    def turn_on_upload(self):
        self.is_allow_upload = True

    def is_upload_allowed(self):
        return self.is_allow_upload

    def add(self, data):
        """
        Add a file to the space and store it only if it is not already stored.
        The file content must be in binary format (`bytes` or `bytearray`).
        `file_content` can be `None` to create an empty file.
        """
        file_name = data.decode().split(',')[0]
        if len(file_name) > 256:
            raise ValueError("File name too long")
        if self.number_file_uploaded < self.max_capacity and self.is_allow_upload:
            # Define the storage path for this file using the base directory
            file_path = os.path.join(self.base_directory, file_name)
            # Check if the file is already in the space list
            for name, path in self.space:
                if name == file_name:
                    raise ValueError(f"File '{file_name}' already stored at {path}")
                    # Exit the function as the file is already stored

            # If the file is not in the space, add it
            self.space.append((file_name, file_path))
            self.space.sort(key=lambda x: x[0])  # Keep the list sorted by file_name
            # Store the file with the given byte content
            self.store(file_path, data)
            return True
        else:
            print("You are not allowed to upload or you reached the maximum capacity")
            return False

    def store(self, file_path, file_content):
        """
        Store a single file at the given file path using binary mode.
        All file content should be in bytes.
        """
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Open the file in binary mode and write the content
        with open(file_path, 'wb') as file:
            file.write(file_content)
        self.number_file_uploaded += 1

    def get_space(self):
        """
        for testing purpose
        """
        return self.space

    def get(self, A,public_key)->List[bytes]:
        """
        Multiplies each file in B by the corresponding encrypted element in A without decryption.

        Args:
            A (list): Vector A containing encrypted values.

        Returns:
            int: The cumulative result of element-wise file multiplications with A.
        """
        # Step 1: Validate the input vector size
        if len(A) != len(self.space):
            raise ValueError(
                f"Size of vector A ({len(A)}) does not match the number of stored files ({len(self.space)}).")

        # Initialize cumulative result
        chunks_len = config.MESSAGE_SIZE//config.BUFFER_SIZE
        cumulative_result_vector = [0 for i in range(chunks_len)]

        # Step 2: Process each encrypted element in A and corresponding file in B
        for encrypted_value, (_, file_path) in zip(A, self.space):
            # Read the binary file content and interpret it as a large integer
            with open(file_path, 'rb') as file:
                file_content = file.read()
                # print(f"file_content)
                file_ints = [int.from_bytes(file_content[i:i+config.BUFFER_SIZE], byteorder='big') for i in range
                (0, config.MESSAGE_SIZE,config.BUFFER_SIZE)]
                file_int = int.from_bytes(file_content, byteorder='big')  # Convert entire binary to a large integer


            # Multiply the encrypted value directly by the file's integer content
            # Here, we assume that the multiplication operation is valid in the encrypted domain
            # bytedebug = base64.b64decode(encrypted_value)
            # encrypted_value = int.from_bytes(bytedebug, byteorder='big')
            encrypted_value = int.from_bytes(encrypted_value, byteorder='big')
            for i in range(chunks_len):
                encrypted_file = Encryption.encrypt(public_key, file_ints[i])
                encrypted_file_int = int.from_bytes(encrypted_file, byteorder='big')
                cumulative_result_vector[i] += encrypted_value * encrypted_file_int  # encrypted_value is used directly
                # encryption(pailier object)

        # Return the cumulative result of all multiplications
        result_vector = [cumulative_result_vector[i].to_bytes(
                    (cumulative_result_vector[i].bit_length() + 7) // 8, byteorder='big') for i in range(chunks_len)]

        return result_vector



    # def get(self, polynome):
    #     """
    #     Calculate the sum of polynomial evaluations multiplied by the corresponding binary file values.
    #     Each file path is retrieved from the stored space in the order of the polynomial coefficients.
    #     """
    #     def evaluate_polynomial(coefficients, x_value):
    #         """
    #         Evaluates the polynomial for a given x value.
    #         The polynomial is represented by a list of coefficients, where
    #         coefficients[i] corresponds to the coefficient of x^i.
    #         """
    #         return sum(coeff * (x_value ** i) for i, coeff in enumerate(coefficients))
    #
    #     total_sum = 0
    #
    #     # Iterate over each value of x (1-based index), using each value in the polynomial as x value
    #     for index, x_value in enumerate(range(0, len(polynome))):
    #         # Evaluate the polynomial value
    #         result = evaluate_polynomial(polynome, x_value)
    #         print(result)
    #         # Retrieve the corresponding file path from the space list at index `index`
    #         if index < len(self.space):
    #             file_path = self.space[index][1]
    #         else:
    #             raise IndexError(f"No file in space corresponds to index {index}")
    #
    #         # Process the binary file incrementally to calculate the integer value
    #         file_int_value = 0
    #         with open(file_path, 'rb') as binary_file:
    #             # Check if the file is empty before reading
    #             file_content = binary_file.read()
    #             if not file_content:
    #                 print(f"File {file_path} is empty.")  # File is empty
    #                 file_int_value = 0
    #             else:
    #
    #                 binary_file.seek(0)  # Reset the file pointer to the beginning
    #
    #                 # Read the binary file in chunks to construct the integer value
    #                 while chunk := binary_file.read(1024):  # Read in chunks of 1024 bytes (adjust as needed)
    #                     # Convert each chunk to an integer and accumulate
    #                     chunk_value = int.from_bytes(chunk, 'big')
    #                     file_int_value = (file_int_value << (8 * len(chunk))) + chunk_value
    #
    #         # Multiply the polynomial result by the large integer value from the file
    #         total_sum += result * file_int_value
    #     return total_sum