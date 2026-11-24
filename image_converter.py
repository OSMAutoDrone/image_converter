#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from pathlib import Path

SUPPORTED_INPUT_EXTENSIONS = {".heic", ".heif", ".jpg", ".jpeg"}
SUPPORTED_OUTPUT_FORMATS = {"jpg", "jpeg", "png", "webp"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image_converter",
        description="Convert HEIC/HEIF or JPEG images to JPG, PNG, or WebP.",
    )
    parser.add_argument(
        "--format",
        choices=("jpg", "png", "webp"),
        default="webp",
        help="output image format (default: webp)",
    )
    parser.add_argument(
        "--resize",
        type=validate_resize,
        default=100,
        metavar="PERCENT",
        help="percentage of original width, from 0 to 100 (default: 100)",
    )
    parser.add_argument(
        "--quality",
        type=validate_quality,
        default=100,
        metavar="QUALITY",
        help="JPEG output quality, from 10 to 100 (default: 100)",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("."),
        metavar="OUTPUT_DIR",
        help="directory for converted images (default: ./)",
    )
    parser.add_argument(
        "input",
        nargs="+",
        metavar="INPUT",
        help="HEIC/HEIF/JPEG file or folder",
    )
    return parser


def validate_resize(value: str) -> int:
    try:
        resize = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("resize must be an integer from 0 to 100") from None

    if not 0 <= resize <= 100:
        raise argparse.ArgumentTypeError("resize must be between 0 and 100")
    return resize


def validate_quality(value: str) -> int:
    try:
        quality = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("quality must be an integer from 10 to 100") from None

    if not 10 <= quality <= 100:
        raise argparse.ArgumentTypeError("quality must be between 10 and 100")
    return quality


def find_images(inputs: Iterable[str]) -> list[Path]:
    images: list[Path] = []
    for raw_path in inputs:
        path = Path(raw_path).expanduser()
        if path.is_file():
            if path.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS:
                images.append(path)
            else:
                print(f"Warning: unsupported input file skipped: {path}", file=sys.stderr)
        elif path.is_dir():
            images.extend(
                sorted(
                    item
                    for item in path.rglob("*")
                    if item.is_file() and item.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS
                )
            )
        else:
            print(f"Error: input does not exist: {path}", file=sys.stderr)
    return images


def convert_image(
    source: Path,
    output_dir: Path,
    output_format: str,
    resize_percent: int,
    quality: int = 100,
) -> Path:
    try:
        import pillow_heif
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependencies. Install them with: python -m pip install -r requirements.txt"
        ) from exc

    pillow_heif.register_heif_opener()

    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        if resize_percent != 100:
            width = max(1, round(image.width * resize_percent / 100))
            height = max(1, round(image.height * resize_percent / 100))
            image = image.resize((width, height), Image.Resampling.LANCZOS)

        extension = "jpg" if output_format == "jpg" else output_format
        destination = output_dir / f"{source.stem}.{extension}"
        output_dir.mkdir(parents=True, exist_ok=True)

        if output_format in {"jpg", "jpeg"}:
            if image.mode not in {"RGB", "L"}:
                background = Image.new("RGB", image.size, "white")
                background.paste(image.convert("RGBA"), mask=image.convert("RGBA").getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
            image.save(destination, format="JPEG", quality=quality)
        else:
            image.save(destination, format=output_format.upper())

    return destination


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not 0 <= args.resize <= 100:
        parser.error("--resize must be between 0 and 100")

    images = find_images(args.input)
    if not images:
        print("Error: no supported input images found", file=sys.stderr)
        return 1

    failures = 0
    for source in images:
        try:
            destination = convert_image(
                source, args.output_dir, args.format, args.resize, args.quality
            )
            print(destination)
        except Exception as exc:
            failures += 1
            print(f"Error: could not convert {source}: {exc}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
