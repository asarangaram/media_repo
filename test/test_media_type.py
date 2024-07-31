import unittest
from io import BytesIO

from src.endpoint.media.media_types import determine_media_type, MediaType


class TestMediaTypeDetection(unittest.TestCase):

    def setUp(self):
        self.test_cases = {
            'images/Screenshot 2024-07-17 at 19.30.57.jpeg': MediaType.IMAGE,
        }

    def read_file(self, file_path):
        with open(file_path, 'rb') as file:
            return file.read()

    def test_media_types(self):
        for file_path, expected_media_type in self.test_cases.items():
            with self.subTest(file=file_path):
                file_content = self.read_file(file_path)
                bytes_io = BytesIO(file_content)
                result = determine_media_type(bytes_io)
                self.assertEqual(result, expected_media_type, f"Failed for {file_path}")

    def tearDown(self):
        # Clean up if needed
        pass

if __name__ == '__main__':
    unittest.main()
