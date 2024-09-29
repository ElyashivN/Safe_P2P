import unittest
import os
from Space_PIR import SpacePIR  # Ensure the SpacePIR class is in the space_pir.py file

class TestSpacePIR(unittest.TestCase):

    def setUp(self):
        # Set up a base directory for testing storage
        self.test_directory = "test_storage"
        if not os.path.exists(self.test_directory):
            os.makedirs(self.test_directory)

        # Initialize the SpacePIR object and set the base directory path for testing
        self.pir = SpacePIR(base_directory=self.test_directory)

    def tearDown(self):
        # Clean up by removing the test directory and its contents after each test
        for root, dirs, files in os.walk(self.test_directory, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_directory)

    def test_add_and_store_single_file(self):
        # Test adding and storing a single file
        file_name = "test1.txt"
        file_content = "This is a test file."
        self.pir.add(file_name, file_content)

        # Check if the file is correctly added to the space
        expected_space = [(file_name, os.path.join(self.test_directory, file_name))]
        self.assertEqual(self.pir.get_space(), expected_space)

        # Verify that the file is stored at the correct path
        stored_file_path = os.path.join(self.test_directory, file_name)
        with open(stored_file_path, 'r') as f:
            stored_content = f.read()
        self.assertEqual(stored_content, file_content)

    def test_file_already_stored(self):
        # Test behavior when a file is already stored
        file_name = "test1.txt"
        file_content = "This is a test file."
        self.pir.add(file_name, file_content)  # Add for the first time

        # Try to add the same file again with the same content
        self.pir.add(file_name, file_content)

        # There should be only one instance in the space
        expected_space = [(file_name, os.path.join(self.test_directory, file_name))]
        self.assertEqual(len(self.pir.get_space()), 1)
        self.assertEqual(self.pir.get_space(), expected_space)

    def test_add_multiple_files(self):
        # Test adding multiple files and check sorting order
        files = {
            "file3.txt": "Content of file 3",
            "file1.txt": "Content of file 1",
            "file2.txt": "Content of file 2",
        }

        # Add the files in an unsorted order
        for file_name, content in files.items():
            self.pir.add(file_name, content)

        # Verify that the space is sorted by file_name
        expected_space = sorted([(name, os.path.join(self.test_directory, name)) for name in files.keys()])
        self.assertEqual(self.pir.get_space(), expected_space)

        # Check that all files were stored correctly
        for file_name, content in files.items():
            stored_file_path = os.path.join(self.test_directory, file_name)
            with open(stored_file_path, 'r') as f:
                stored_content = f.read()
            self.assertEqual(stored_content, content)

    def test_existing_file_not_overwritten(self):
        # Test that an existing file is not overwritten if the filename is the same, even with different content
        file_name = "test1.txt"
        initial_content = "Initial content."
        new_content = "Updated content."

        # Add the file with initial content
        self.pir.add(file_name, initial_content)

        # Get the modification time of the file after the first addition
        stored_file_path = os.path.join(self.test_directory, file_name)
        initial_mod_time = os.path.getmtime(stored_file_path)

        # Attempt to add the same file with new content
        self.pir.add(file_name, new_content)

        # The space list should still contain only one entry with the same file path
        expected_space = [(file_name, stored_file_path)]
        self.assertEqual(self.pir.get_space(), expected_space)

        # Verify that the file content is still the initial content
        with open(stored_file_path, 'r') as f:
            stored_content = f.read()
        self.assertEqual(stored_content, initial_content)

        # Verify that the modification time has not changed
        final_mod_time = os.path.getmtime(stored_file_path)
        self.assertEqual(initial_mod_time, final_mod_time)

    def test_no_redundant_store_on_same_file(self):
        # Test that store is not called when the same file is added without changes
        file_name = "test1.txt"
        file_content = "This content stays the same."
        self.pir.add(file_name, file_content)

        # Check the initial modification time
        file_path = os.path.join(self.test_directory, file_name)
        initial_mod_time = os.path.getmtime(file_path)

        # Call add again with the same content, it should not store again
        self.pir.add(file_name, file_content)

        # Check that the modification time has not changed
        final_mod_time = os.path.getmtime(file_path)
        self.assertEqual(initial_mod_time, final_mod_time)

    def test_path_correctness_in_space(self):
        # Test that the file paths in the space list are correct
        file_name = "example.txt"
        file_content = "Example file content."
        self.pir.add(file_name, file_content)

        # Verify the file path
        expected_file_path = os.path.join(self.test_directory, file_name)
        self.assertEqual(self.pir.get_space()[0][1], expected_file_path)

    def test_add_new_file_only_when_not_stored(self):
        # Test that store is called only if a new file is not already stored
        file_name_1 = "file1.txt"
        file_name_2 = "file2.txt"
        content_1 = "Content for file 1"
        content_2 = "Content for file 2"

        # Add first file
        self.pir.add(file_name_1, content_1)
        expected_space = [(file_name_1, os.path.join(self.test_directory, file_name_1))]
        self.assertEqual(self.pir.get_space(), expected_space)

        # Add second file, check that the space list is updated
        self.pir.add(file_name_2, content_2)
        expected_space.append((file_name_2, os.path.join(self.test_directory, file_name_2)))
        expected_space = sorted(expected_space, key=lambda x: x[0])  # Ensure sorting by filename
        self.assertEqual(self.pir.get_space(), expected_space)

# Run the tests
if __name__ == "__main__":
    unittest.main()
