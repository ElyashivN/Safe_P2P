import unittest
import os
from FileHandler import FileHandler  # Assuming the code is saved in file_handler.py

class TestFileHandler(unittest.TestCase):
    """
    Unit tests for the FileHandler class, which splits and recombines files using Reed-Solomon error correction.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the test environment by creating test files to split and recombine.
        These test files will be used to verify the behavior of the FileHandler class.
        """
        cls.test_file = "test_file.bin"
        cls.reconstructed_file = "reconstructed_file.bin"

        # Create a test binary file with some random content (1MB file)
        with open(cls.test_file, 'wb') as f:
            f.write(os.urandom(1024 * 1024))  # Create a 1MB test file

        cls.file_handler = FileHandler()

    @classmethod
    def tearDownClass(cls):
        """
        Tear down the test environment by removing any created test files.
        This ensures no leftover files remain after the tests are finished.
        """
        if os.path.exists(cls.test_file):
            os.remove(cls.test_file)
        if os.path.exists(cls.reconstructed_file):
            os.remove(cls.reconstructed_file)
        # Clean up any remaining part files
        for part_file in os.listdir():
            if part_file.startswith("test_file.bin.part"):
                os.remove(part_file)

    def test_divide(self):
        """
        Test that the file is successfully divided into parts, the original size is correctly returned,
        and that the expected number of parts are created. Also verify that the part files exist.
        """
        part_files, original_size = self.file_handler.divide(self.test_file, n=10, k=5)

        # Verify that 10 part files were created
        self.assertEqual(len(part_files), 10)

        # Check that the part files exist
        for part_file in part_files:
            self.assertTrue(os.path.exists(part_file))

        # Verify that the original size is correct (should match the 1MB test file size)
        expected_size = os.path.getsize(self.test_file)
        self.assertEqual(original_size, expected_size)

    def test_combine(self):
        """
        Test that the file parts can be recombined back into the original file.
        Ensure that the recombined file matches the original file in size and content.
        """
        part_files, original_size = self.file_handler.divide(self.test_file, n=10, k=5)

        # Combine the first 5 parts to reconstruct the file
        self.file_handler.combine(part_files[:5], n=10, k=5, output_file=self.reconstructed_file, original_size=original_size)

        # Verify that the reconstructed file exists
        self.assertTrue(os.path.exists(self.reconstructed_file))

        # Verify that the reconstructed file matches the original file in size and content
        original_size = os.path.getsize(self.test_file)
        reconstructed_size = os.path.getsize(self.reconstructed_file)
        self.assertEqual(original_size, reconstructed_size)

        # Compare the content of the original file and the reconstructed file
        with open(self.test_file, 'rb') as original, open(self.reconstructed_file, 'rb') as reconstructed:
            self.assertEqual(original.read(), reconstructed.read())

    def test_incomplete_combine(self):
        """
        Test that attempting to combine fewer parts than required (less than k) fails gracefully.
        Ensure that an exception is raised when there aren't enough parts to combine the file.
        """
        part_files, original_size = self.file_handler.divide(self.test_file, n=10, k=5)

        # Attempt to combine only 3 parts (which is less than k)
        with self.assertRaises(Exception):
            self.file_handler.combine(part_files[:3], n=10, k=5, output_file=self.reconstructed_file, original_size=original_size)

    def test_variable_file_size(self):
        """
        Test that the file can be divided and recombined correctly even when the file size
        is not perfectly divisible by the block size. This ensures that the system handles
        padding and recombines the file to its exact original size.
        """
        # Create a variable-sized test file (e.g., 1.5MB)
        variable_size_file = "variable_size_file.bin"
        with open(variable_size_file, 'wb') as f:
            f.write(os.urandom(1024 * 1024 + 512 * 1024))  # Create a 1.5MB test file

        # Divide the file
        part_files, original_size = self.file_handler.divide(variable_size_file, n=15, k=10)

        # Combine the first 10 parts to reconstruct the file
        reconstructed_variable_file = "reconstructed_variable_size_file.bin"
        self.file_handler.combine(part_files[:10], n=15, k=10, output_file=reconstructed_variable_file, original_size=original_size)

        # Verify that the reconstructed file exists and matches the original
        self.assertTrue(os.path.exists(reconstructed_variable_file))

        # Check that the sizes and content match
        original_size = os.path.getsize(variable_size_file)
        reconstructed_size = os.path.getsize(reconstructed_variable_file)
        self.assertEqual(original_size, reconstructed_size)

        with open(variable_size_file, 'rb') as original, open(reconstructed_variable_file, 'rb') as reconstructed:
            self.assertEqual(original.read(), reconstructed.read())

        # Cleanup
        os.remove(variable_size_file)
        os.remove(reconstructed_variable_file)

        for part_file in part_files:
            if os.path.exists(part_file):
                os.remove(part_file)


if __name__ == "__main__":
    unittest.main()
