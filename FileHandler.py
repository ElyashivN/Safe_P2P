import zfec
import os
import math

import config


class FileHandler:
    """
    Handle file division and recombination for any file type (text, binary, images, etc.)
    using Reed-Solomon error correction through the Zfec library.
    """

    def divide(self, file_path, NODE_ID, n=2000, block_size=config.SUBFILE_SIZE):
        """
        Divide any type of file into exactly k parts using Reed-Solomon (RS) error correction.
        This method works with binary data, so it can handle text files, binary files,
        images, and any other type of file.

        Args:
            file_path (str): Path to the input file to be divided.
            NODE_ID (str): The ID of the node to include in the subfile names.
            n (int): Total number of parts to divide the file into.
            block_size (int): block_size

        Returns:
            Tuple[List[str], int, str]: A tuple containing the list of file part filenames,
            the size of the original file, and the NODE_ID.
        """
        # Read the file in binary mode
        with open(file_path, 'rb') as f:
            file_data = f.read()

        original_size = len(file_data)  # Get the original file size

        # Calculate block size dynamically based on the file size and k (minimum parts)
        k = math.ceil(original_size / block_size)

        # Split the file into exactly k blocks
        file_blocks = [file_data[i:i + block_size] for i in range(0, len(file_data), block_size)]

        # Pad the last block to make it equal in size if needed
        if len(file_blocks) < k:
            file_blocks.append(b'\x00' * block_size)
        file_blocks[-1] = file_blocks[-1].ljust(block_size, b'\x00')

        # Create an encoder (Reed-Solomon)
        encoder = zfec.Encoder(k, n)

        # Encode the file blocks into n parts with error correction
        parts = encoder.encode(file_blocks)

        # Save each part to a file with a unique name
        part_files = []
        file_name = os.path.basename(file_path)
        for i, part in enumerate(parts):
            # Unique file name based on original file name, part number, and NODE_ID
            part_filename = f"{file_name}_part{i}"
            with open(part_filename, 'wb') as part_file:  # Write in binary mode
                part_file.write(file_name.encode()+b","+part)
            part_files.append(part_filename)

        return part_files, k, NODE_ID  # Return the list of file parts, the original file size, and NODE_ID

    def combine(self, part_files, n, k, output_file):
        """
        Combine parts into the original file (any file type) using Reed-Solomon error correction.
        This method handles binary data and can combine text, binary, or any type of file.

        Args:
            part_files (List[str]): List of part file paths.
            n (int): Total number of parts.
            k (int): Minimum number of parts required to reconstruct the file.
            output_file (str): Path to the output file.

        Returns:
            None
        """
        # Read each part from the part files in binary mode
        parts_data = []
        indexes = []  # Track the part indexes used
        for i, part_file in enumerate(part_files):
            with open(part_file, 'rb') as f:
                parts_data.append(f.read())
                indexes.append(i)  # Record the index of each part

        # Create a decoder (Reed-Solomon)
        decoder = zfec.Decoder(k, n)

        # Decode the original file data from the parts using their indexes
        decoded_blocks = decoder.decode(parts_data, indexes)

        # Concatenate all the decoded blocks into a single bytes object
        original_data = b''.join(decoded_blocks)

        # # Ensure the file is exactly the original size
        # original_data = original_data[:original_size]

        # Write the original file to disk in binary mode
        with open(output_file, 'wb') as output:
            output.write(original_data)
        return True