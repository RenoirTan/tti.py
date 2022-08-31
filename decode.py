#!/usr/bin/env python3

import argparse
from pathlib import Path
import tti

parser = argparse.ArgumentParser(description="Decode a tti image back to the original input")
parser.add_argument("image", help="image to decode")
parser.add_argument("output", nargs="?", help="output file path")
parser.add_argument("--print-decoded", action="store_true", help="print original input")
parser.add_argument("--print-encoded", action="store_true", help="print encoded input")
args = parser.parse_args()

decoded = tti.Decoder(print_intermediate=args.print_encoded).decode_image_with_path(args.image)
if args.print_decoded:
    print(decoded)
if args.output is not None:
    with Path(args.output).open("wb+") as f:
        f.write(decoded)
