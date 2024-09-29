import unittest
import os
from Space_PIR import SpacePIR  # Ensure the SpacePIR class is in the space_pir.py file

class TestSpacePIR(unittest.TestCase):
    def setUp(self):
        # Set up a base directory for testing storage
        self.test_directory = "test_storage"
        if not os.path.exists(self.test_directory):
            os.makedirs(self.test_directory)

        # Initialize the SpacePIR object with a max capacity of 5 for testing
        self.pir = SpacePIR(max_capacity=5, base_directory=self.test_directory)

    def tearDown(self):
        # Clean up by removing the test directory and its contents after each test
        for root, dirs, files in os.walk(self.test_directory, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
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

    def test_small_binary_files(self):
        polynome = [30, 15, 10]
        self.create_binary_file("file1.bin", "110")
        self.create_binary_file("file2.bin", "101")
        self.create_binary_file("file3.bin", "1001")

        result = self.pir.get(polynome)
        self.assertEqual(result, 1355)

    def test_large_binary_files(self):
        polynome = [1, 2, 3, 4]
        self.create_binary_file("file1_large.bin", "1" * 2048)
        self.create_binary_file("file2_large.bin", "0" * 1024 + "1" * 1024)
        self.create_binary_file("file3_large.bin", "1" * 1536 + "0" * 512)
        self.create_binary_file("file4_large.bin", "1" * 4096)

        result = self.pir.get(polynome)
        self.assertTrue(isinstance(result, int))

    def test_non_multiple_of_chunk_size(self):
        polynome = [1, 2]
        self.create_binary_file("file1_non_multiple.bin", "1" * 1500)
        self.create_binary_file("file2_non_multiple.bin", "0" * 600 + "1" * 400)

        result = self.pir.get(polynome)
        self.assertTrue(isinstance(result, int))

    def test_empty_binary_files(self):
        polynome = [1, 2, 3]
        self.create_binary_file("file1_empty.bin", "")
        self.create_binary_file("file2_empty.bin", "")
        self.create_binary_file("file3_empty.bin", "")

        result = self.pir.get(polynome)
        self.assertEqual(result, 0)

    def test_single_bit_binary_files(self):
        polynome = [1, 2]
        self.create_binary_file("file2_single_bit.bin", "0")
        self.create_binary_file("file1_single_bit.bin", "1")

        result = self.pir.get(polynome)
        self.assertEqual(result, 1)

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

    def test_max_capacity_reached(self):
        # Check that `number_file_uploaded` correctly tracks the number of files uploaded
        self.assertEqual(self.pir.number_file_uploaded, 0, "Initially, no files should be uploaded.")

        # Add files up to the new maximum capacity of 5
        self.pir.add("file1.txt", b"Content 1")
        self.assertEqual(self.pir.number_file_uploaded, 1, "One file should have been uploaded.")

        self.pir.add("file2.txt", b"Content 2")
        self.assertEqual(self.pir.number_file_uploaded, 2, "Two files should have been uploaded.")

        self.pir.add("file3.txt", b"Content 3")
        self.assertEqual(self.pir.number_file_uploaded, 3, "Three files should have been uploaded.")

        self.pir.add("file4.txt", b"Content 4")
        self.assertEqual(self.pir.number_file_uploaded, 4, "Four files should have been uploaded.")

        self.pir.add("file5.txt", b"Content 5")
        self.assertEqual(self.pir.number_file_uploaded, 5, "Five files should have been uploaded.")

        # Try to add a sixth file, which should not be allowed due to max capacity
        self.pir.add("file6.txt", b"Content 6")
        self.assertEqual(self.pir.number_file_uploaded, 5,
                         "Number of files uploaded should not increase beyond capacity.")

        # Verify that the space only contains 5 files and no more
        expected_file_names = ["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"]
        self.assertEqual(self.pir.get_file_names(), expected_file_names, "There should only be 5 files in the space.")


# Run the tests
if __name__ == "__main__":
    unittest.main()
