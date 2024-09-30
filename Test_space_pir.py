import time
import unittest
import os
from Space_PIR import SpacePIR  # Ensure the SpacePIR class is in the space_pir.py file
import numpy as np

class TestSpacePIR(unittest.TestCase):
    def setUp(self):
        # Set up a base directory for testing storage
        self.test_directory = "test_storage"
        if not os.path.exists(self.test_directory):
            os.makedirs(self.test_directory)

        # Initialize the SpacePIR object with a max capacity of 5 for testing
        self.pir = SpacePIR(max_capacity=5, base_directory=self.test_directory)

    def tearDown(self):
        """Clean up the test directory and its contents."""
        # Retry logic to handle potential PermissionError on Windows
        for root, dirs, files in os.walk(self.test_directory, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    os.remove(file_path)
                except PermissionError:
                    time.sleep(0.1)  # Wait a bit and try again
                    os.remove(file_path)  # Try removing again
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_directory)

    def test_add_and_store_single_file(self):
        file_name = "test1.txt"
        file_content = b"This is a test file."
        self.pir.add(file_name, file_content)
        expected_space = [(file_name, os.path.join(self.test_directory, file_name))]
        self.assertEqual(self.pir.get_space(), expected_space)

        stored_file_path = os.path.join(self.test_directory, file_name)
        with open(stored_file_path, 'rb') as f:
            stored_content = f.read()
        self.assertEqual(stored_content, file_content)

    def test_file_already_stored(self):
        file_name = "test1.txt"
        file_content = b"This is a test file."
        self.pir.add(file_name, file_content)
        self.pir.add(file_name, file_content)
        expected_space = [(file_name, os.path.join(self.test_directory, file_name))]
        self.assertEqual(len(self.pir.get_space()), 1)
        self.assertEqual(self.pir.get_space(), expected_space)

    def test_add_multiple_files(self):
        files = {"file3.txt": b"Content of file 3", "file1.txt": b"Content of file 1", "file2.txt": b"Content of file 2"}
        for file_name, content in files.items():
            self.pir.add(file_name, content)

        expected_space = sorted([(name, os.path.join(self.test_directory, name)) for name in files.keys()])
        self.assertEqual(self.pir.get_space(), expected_space)

        for file_name, content in files.items():
            stored_file_path = os.path.join(self.test_directory, file_name)
            with open(stored_file_path, 'rb') as f:
                stored_content = f.read()
            self.assertEqual(stored_content, content)

    def test_existing_file_not_overwritten(self):
        file_name = "test1.txt"
        initial_content = b"Initial content."
        new_content = b"Updated content."
        self.pir.add(file_name, initial_content)

        stored_file_path = os.path.join(self.test_directory, file_name)
        initial_mod_time = os.path.getmtime(stored_file_path)
        self.pir.add(file_name, new_content)
        expected_space = [(file_name, stored_file_path)]
        self.assertEqual(self.pir.get_space(), expected_space)

        with open(stored_file_path, 'rb') as f:
            stored_content = f.read()
        self.assertEqual(stored_content, initial_content)

        final_mod_time = os.path.getmtime(stored_file_path)
        self.assertEqual(initial_mod_time, final_mod_time)

    def test_no_redundant_store_on_same_file(self):
        file_name = "test1.txt"
        file_content = b"This content stays the same."
        self.pir.add(file_name, file_content)

        file_path = os.path.join(self.test_directory, file_name)
        initial_mod_time = os.path.getmtime(file_path)
        self.pir.add(file_name, file_content)

        final_mod_time = os.path.getmtime(file_path)
        self.assertEqual(initial_mod_time, final_mod_time)

    def test_path_correctness_in_space(self):
        file_name = "example.txt"
        file_content = b"Example file content."
        self.pir.add(file_name, file_content)

        expected_file_path = os.path.join(self.test_directory, file_name)
        self.assertEqual(self.pir.get_space()[0][1], expected_file_path)

    def test_add_new_file_only_when_not_stored(self):
        file_name_1 = "file1.txt"
        file_name_2 = "file2.txt"
        content_1 = b"Content for file 1"
        content_2 = b"Content for file 2"

        self.pir.add(file_name_1, content_1)
        expected_space = [(file_name_1, os.path.join(self.test_directory, file_name_1))]
        self.assertEqual(self.pir.get_space(), expected_space)

        self.pir.add(file_name_2, content_2)
        expected_space.append((file_name_2, os.path.join(self.test_directory, file_name_2)))
        expected_space = sorted(expected_space, key=lambda x: x[0])
        self.assertEqual(self.pir.get_space(), expected_space)

    def test_get_file_names(self):
        self.pir.add("fileB.txt", b"Content for file B")
        self.pir.add("fileA.txt", b"Content for file A")
        self.pir.add("fileC.txt", b"Content for file C")

        expected_file_names = ["fileA.txt", "fileB.txt", "fileC.txt"]
        file_names = self.pir.get_file_names()
        self.assertEqual(file_names, expected_file_names, f"Expected file names {expected_file_names}, but got {file_names}")



    def create_binary_file(self, file_name, binary_string):
        """
        Helper function to create a binary file with the given binary string.
        Always calls `self.pir.add()` to register the file in the SpacePIR space.
        """
        file_path = os.path.join(self.test_directory, file_name)

        # Convert the binary string to bytes if provided; otherwise, set as an empty byte string
        if binary_string:
            byte_content = int(binary_string, 2).to_bytes((len(binary_string) + 7) // 8, 'big')
        else:
            byte_content = b""  # Set empty content for empty files

        # Call add to register the file, whether it is empty or not
        self.pir.add(file_name, byte_content)

        return file_path

    def test_upload_limit(self):
        # Test that only up to `max_capacity` files can be uploaded
        self.pir.add("file1.txt", b"Content 1")
        self.pir.add("file2.txt", b"Content 2")
        self.pir.add("file3.txt", b"Content 3")
        self.pir.add("file4.txt", b"Content 4")
        self.pir.add("file5.txt", b"Content 5")
        # Attempt to add a sixth file, which should not be allowed
        self.pir.add("file6.txt", b"Content 6")

        # Expected: Only 5 files in the space as max_capacity is 3
        expected_file_names = ["file1.txt", "file2.txt", "file3.txt","file4.txt","file5.txt"]
        self.assertEqual(self.pir.get_file_names(), expected_file_names)

    def test_upload_permission(self):
        # Test that uploads can be toggled on and off
        self.pir.turn_off_upload()
        self.assertFalse(self.pir.is_upload_allowed(), "Upload should be disabled.")

        # Try to add a file when uploads are disabled
        self.pir.add("file1.txt", b"Content 1")
        self.assertEqual(self.pir.get_file_names(), [], "No files should be uploaded when uploads are disabled.")

        # Enable uploads and add a file
        self.pir.turn_on_upload()
        self.assertTrue(self.pir.is_upload_allowed(), "Upload should be enabled.")

        self.pir.add("file1.txt", b"Content 1")
        self.assertEqual(self.pir.get_file_names(), ["file1.txt"], "File should be uploaded when uploads are enabled.")

    def test_is_upload_allowed(self):
        # Test the `is_upload_allowed` method
        # Initially, uploads should be allowed
        self.assertTrue(self.pir.is_upload_allowed(), "Uploads should be allowed by default.")

        # Disable uploads and check
        self.pir.turn_off_upload()
        self.assertFalse(self.pir.is_upload_allowed(), "Uploads should be disabled after calling `turn_off_upload`.")

        # Enable uploads again and check
        self.pir.turn_on_upload()
        self.assertTrue(self.pir.is_upload_allowed(), "Uploads should be enabled after calling `turn_on_upload`.")

    def test_get_cross_product_basic(self):
        """Test the basic functionality of the `get` function with a simple input vector."""
        # Adding three files with specific byte contents
        self.pir.add("file1.txt", b'\x01\x02\x03')  # Sum = 6
        self.pir.add("file2.txt", b'\x04\x05\x06')  # Sum = 15
        self.pir.add("file3.txt", b'\x07\x08\x09')  # Sum = 24

        # Create a vector A matching the number of files
        A = [1, 2, 3]

        # Expected cross product result: 6*1 + 15*2 + 24*3 = 6 + 30 + 72 = 108
        result = self.pir.get(A)
        self.assertEqual(result, 108, f"Expected 108, but got {result}")

    def test_get_cross_product_small_numpy(self):
        """Test the functionality of the `get` function using numpy with few files and simple binary content."""
        # Adding three files with binary content
        self.pir.add("file1.txt", b'\x01\x02')  # Content as binary (Sum = 1 + 2 = 3)
        self.pir.add("file2.txt", b'\x03\x04')  # Content as binary (Sum = 3 + 4 = 7)
        self.pir.add("file3.txt", b'\x05\x06')  # Content as binary (Sum = 5 + 6 = 11)

        # Create a smaller vector A with simple values
        A = [1, 2, -1]

        # Using numpy directly to compute the expected result
        expected_matrix = np.array([
            np.frombuffer(b'\x01\x02', dtype=np.uint8),  # [1, 2]
            np.frombuffer(b'\x03\x04', dtype=np.uint8),  # [3, 4]
            np.frombuffer(b'\x05\x06', dtype=np.uint8)   # [5, 6]
        ], dtype=object)

        A_vector = np.array(A, dtype=np.int32)

        # Perform matrix multiplication and get the sum as expected output
        expected_result = np.dot(A_vector, expected_matrix).sum()

        # Get the result from the `get` method
        result = self.pir.get(A)
        self.assertEqual(result, expected_result, f"Expected {expected_result}, but got {result}")


    def test_get_cross_product_large_numpy(self):
        """Test the functionality of the `get` function using numpy with larger files and varied binary content."""
        # Adding five files with binary content
        self.pir.add("file1.txt", b'\x01\x02\x03\x04')  # Content as binary
        self.pir.add("file2.txt", b'\x05\x06\x07\x08')  # Content as binary
        self.pir.add("file3.txt", b'\x09\x0A\x0B\x0C')  # Content as binary
        self.pir.add("file4.txt", b'\x0D\x0E\x0F\x10')  # Content as binary
        self.pir.add("file5.txt", b'\x11\x12\x13\x14')  # Content as binary

        # Create a larger vector A with more varied values
        A = [2, -1, 3, 4, -2]

        # Using numpy directly to compute the expected result
        expected_matrix = np.array([
            np.frombuffer(b'\x01\x02\x03\x04', dtype=np.uint8),
            np.frombuffer(b'\x05\x06\x07\x08', dtype=np.uint8),
            np.frombuffer(b'\x09\x0A\x0B\x0C', dtype=np.uint8),
            np.frombuffer(b'\x0D\x0E\x0F\x10', dtype=np.uint8),
            np.frombuffer(b'\x11\x12\x13\x14', dtype=np.uint8)
        ], dtype=object)

        A_vector = np.array(A, dtype=np.int32)

        # Perform matrix multiplication and get the sum as expected output
        expected_result = np.dot(A_vector, expected_matrix).sum()

        # Get the result from the `get` method
        result = self.pir.get(A)
        self.assertEqual(result, expected_result, f"Expected {expected_result}, but got {result}")



    def test_get_vector_size_mismatch(self):
        """Test that `get` raises a ValueError when vector size does not match the number of files."""
        self.pir.add("file1.txt", b'\x01\x02\x03')  # Sum = 6
        self.pir.add("file2.txt", b'\x04\x05\x06')  # Sum = 15

        # Create a vector A with incorrect size
        A = [1]

        # Should raise a ValueError due to size mismatch
        with self.assertRaises(ValueError):
            self.pir.get(A)



    def test_get_no_files(self):
        """Test that `get` raises a ValueError when no files are stored."""
        # Create a vector A, but no files are stored yet
        A = [1]

        # Should raise a ValueError due to no files being present
        with self.assertRaises(ValueError):
            self.pir.get(A)


# Run the tests
if __name__ == "__main__":
    unittest.main()
