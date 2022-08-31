#!/usr/bin/env python3

import argparse
import tti

parser = argparse.ArgumentParser(description="Encode a file into an image")
parser.add_argument("filename", help="file to encode")
parser.add_argument("output", nargs="?", help="output file path")
parser.add_argument("--max-ratio", "-q", type=float, help="maximum ratio for final image")
parser.add_argument("--no-preview", action="store_true", help="do not show preview of image")
parser.add_argument("--show-bytes", "-b", action="store_true", help="show resultant bytes")
args = parser.parse_args()

encoded = tti.Encoder(max_ratio=args.max_ratio).encode_file_with_path(args.filename)
if args.show_bytes:
    tti.print_res(encoded)
image = tti.create_image(encoded)
if not args.no_preview:
    image.show()
if args.output is not None:
    image.save(args.output)
