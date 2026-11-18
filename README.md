# Image Converter

Convert HEIC/HEIF files to JPG, PNG, or WebP.

## Requirements

- Python 3.9 or newer

Install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Usage

```text
image_converter [--format (jpg|png|webp) = webp] [--resize (0-100) = 100] [--output_dir OUTPUT_DIR = ./] INPUT ...
```

Examples:

```powershell
python image_converter.py photo.heic
python image_converter.py --format jpg --resize 50 --output_dir converted photos
python image_converter.py a.heic b.heic c.heic --format png
```

On Windows, the included `image_converter.bat` wrapper can be used instead:

```powershell
image_converter.bat --format webp --resize 75 C:\Pictures
```

Each input may be a HEIC/HEIF file or a folder. Folder inputs are searched recursively.
At 0 percent, the width and height are limited to at least one pixel. Otherwise, the
size is calculated from the original width and the aspect ratio is preserved.
