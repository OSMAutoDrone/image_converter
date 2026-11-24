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

    def test_finds_supported_files_in_folder_recursively(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "nested").mkdir()
            (folder / "nested" / "photo.HEIC").touch()
            (folder / "nested" / "scan.JPEG").touch()
            (folder / "photo.jpg").touch()
            (folder / "ignored.png").touch()

            found = image_converter.find_images([tmp])

            self.assertEqual(
                [path.name for path in found],
                ["photo.HEIC", "scan.JPEG", "photo.jpg"],
            )

    def test_converts_jpeg_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "source.jpeg"
            Image.new("RGB", (20, 10), "white").save(source, format="JPEG")

            destination = image_converter.convert_image(
                source, folder / "output", "png", 100
            )

            self.assertEqual(destination.name, "source.png")
            with Image.open(destination) as converted:
                self.assertEqual(converted.size, (20, 10))

    def test_jpeg_quality_is_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "source.png"
            Image.new("RGB", (32, 32), "white").save(source)

            low_quality = image_converter.convert_image(
                source, folder / "low", "jpg", 100, 10
            )
            high_quality = image_converter.convert_image(
                source, folder / "high", "jpg", 100, 100
            )

            with Image.open(low_quality) as low, Image.open(high_quality) as high:
                self.assertNotEqual(low.quantization, high.quantization)

    def test_resize_rejects_values_outside_range(self):
        parser = image_converter.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["--resize", "101", "photo.heic"])

    def test_resize_accepts_valid_integer(self):
        parser = image_converter.build_parser()
        args = parser.parse_args(["--resize", "80", "photo.heic"])
        self.assertEqual(args.resize, 80)

    def test_quality_defaults_to_100(self):
        parser = image_converter.build_parser()
        args = parser.parse_args(["photo.heic"])
        self.assertEqual(args.quality, 100)

    def test_quality_accepts_values_between_10_and_100(self):
        parser = image_converter.build_parser()
        for value in ("10", "75", "100"):
            with self.subTest(value=value):
                args = parser.parse_args(["--quality", value, "photo.heic"])
                self.assertEqual(args.quality, int(value))

    def test_quality_rejects_values_outside_range(self):
        parser = image_converter.build_parser()
        for value in ("9", "101"):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                parser.parse_args(["--quality", value, "photo.heic"])


if __name__ == "__main__":
    unittest.main()
