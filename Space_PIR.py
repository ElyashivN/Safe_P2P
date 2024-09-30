import os
import numpy as np


class SpacePIR:
    def __init__(self, max_capacity, base_directory="path"):
        # Initialize an empty list to hold the file names and their storage locations
        self.space = []  # Space should store (filename, path) tuples
        self.base_directory = base_directory  # Allow dynamic base directory
        self.max_capacity = max_capacity
        self.number_file_uploaded = 0
        self.allowed_upload = True

    def get_file_names(self):
        """
        Return a list of file names without the paths in the same order as stored in `space`.
        """
        return [file_name for file_name, _ in self.space]

    def turn_off_upload(self):
        self.allowed_upload = False

    def turn_on_upload(self):
        self.allowed_upload = True

    def is_upload_allowed(self):
        return self.allowed_upload

    def add(self, file_name, file_content=None):
        """
        Add a file to the space and store it only if it is not already stored.
        The file content must be in binary format (`bytes` or `bytearray`).
        `file_content` can be `None` to create an empty file.
        """
        if self.number_file_uploaded < self.max_capacity and self.allowed_upload:
            # Define the storage path for this file using the base directory
            file_path = os.path.join(self.base_directory, file_name)
            # Check if the file is already in the space list
            for name, path in self.space:
                if name == file_name:
                    print(f"File '{file_name}' already stored at {path}. No action needed.")
                    return  # Exit the function as the file is already stored

            # If the file is not in the space, add it
            self.space.append((file_name, file_path))
            self.space.sort(key=lambda x: x[0])  # Keep the list sorted by file_name

            # Ensure that the file content is in binary format, if provided
            if file_content is None:
                # Create an empty file
                print(f"File '{file_name}' will be created as an empty file.")
                file_content = b""
            elif isinstance(file_content, str):
                # Convert binary strings (e.g., "1101") to bytes
                if all(c in "01" for c in file_content):
                    file_content = int(file_content, 2).to_bytes((len(file_content) + 7) // 8, 'big')
                else:
                    raise ValueError("String content is not binary. Provide bytes or a valid binary string.")

            # Store the file with the given byte content
            self.store(file_path, file_content)
        else:
            print("You are not allowed to upload or you reached the maximum capacity")

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

    def get(self, A):
        """
        Takes a vector A, validates its size, and performs a cross product using numpy.

        Args:
            A (list): Vector A whose size should match the number of stored files.

        Returns:
            int: The cross product result using numpy.
        """
        # Step 1: Validate the input vector size
        if len(A) != len(self.space):
            raise ValueError(
                f"Size of vector A ({len(A)}) does not match the number of stored files ({len(self.space)}).")
        # Step 2: Create a matrix B where each row is the binary content of a file
        B = []
        for _, file_path in self.space:
            with open(file_path, 'rb') as file:
                file_content = np.frombuffer(file.read(), dtype=np.uint8)
                B.append(file_content)

        # Step 3: Use numpy to calculate the cross product (A @ B)
        B_matrix = np.array(B, dtype=object)  # Create numpy matrix with binary file contents
        A_vector = np.array(A, dtype=np.int32)

        # Matrix multiplication (dot product of B and A)
        cross_product_result = np.dot(A_vector, B_matrix)

        # Return the sum of the cross product results
        return cross_product_result.sum()




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
