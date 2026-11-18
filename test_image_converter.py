import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import image_converter


class ImageConverterTests(unittest.TestCase):
    def test_resizes_by_width_and_preserves_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.heic"
            output_dir = Path(tmp) / "output"
            with patch("PIL.Image.open") as mocked_open:
                image = Image.new("RGB", (200, 100), "white")
                mocked_open.return_value.__enter__.return_value = image

                destination = image_converter.convert_image(
                    source, output_dir, "png", 50
                )

            self.assertEqual(destination.name, "source.png")
            self.assertTrue(destination.exists())
            with Image.open(destination) as converted:
                self.assertEqual(converted.size, (100, 50))

    def test_finds_heic_files_in_folder_recursively(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "nested").mkdir()
            (folder / "nested" / "photo.HEIC").touch()
            (folder / "ignored.jpg").touch()

            found = image_converter.find_images([tmp])

            self.assertEqual([path.name for path in found], ["photo.HEIC"])

    def test_resize_rejects_values_outside_range(self):
        parser = image_converter.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["--resize", "101", "photo.heic"])

    def test_resize_accepts_valid_integer(self):
        parser = image_converter.build_parser()
        args = parser.parse_args(["--resize", "80", "photo.heic"])
        self.assertEqual(args.resize, 80)


if __name__ == "__main__":
    unittest.main()
