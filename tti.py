import os
from pathlib import Path
from PIL import Image
import typing as t

def prime_factors(n: int) -> t.Dict[int, int]:
    """
    Find the prime factors of an integer raised to the appropriate powers.
    
    Example
    -------
    >>> prime_factors(45)
    {3: 2, 5: 1}
    """
    pf = {}
    count = 0
    while n % 2 == 0:
        n //= 2
        count += 1
    if count > 0:
        pf[2] = count
    for prime in range(3, int(n**0.5)+1, 2):
        count = 0
        while n % prime == 0:
            n //= prime
            count += 1
        if count > 0:
            pf[prime] = count
    if n > 1:
        pf[n] = 1
    return pf

def closest_factors_to_sqrt(n: int) -> t.Tuple[int, int]:
    """
    Find the 2 factors of an integers that are closest to the its square root.
    This function is useful for calculating the dimensions for a 2D image which
    you want to be a square as close as possible.
    
    Example
    -------
    >>> closest_factors_to_sqrt(256)
    (16, 16)
    >>> closest_factors_to_sqrt(255)
    (17, 15)
    >>> closest_factors_to_sqrt(254)
    (127, 2)
    """
    pfs = prime_factors(n)
    pfs_queue = []
    for prime, occurrence in sorted(pfs.items(), key=lambda kv: kv[0], reverse=True):
        pfs_queue.extend([prime]*occurrence)
    a, b = 1, 1
    while len(pfs_queue) > 0:
        if a <= b:
            a *= pfs_queue.pop(0)
        else:
            b *= pfs_queue.pop(0)
    return a, b

def recommend_img_dim(pixels: int, portrait: bool = False) -> t.Tuple[int, int]:
    """
    Calculate suitable dimensions for an image given the number of pixels it
    has.
    
    Parameters
    ----------
    pixels: int
        Number of pixels
    
    portrait: bool = False
        Whether to make the dimensions of the image a portrait.
    
    Returns
    -------
    Tuple[int, int]
        Width and height
    
    Examples
    --------
    >>> closest_factors_to_sqrt(255)
    (17, 15)
    >>> closest_factors_to_sqrt(255, portrait=True)
    (15, 17)
    """
    a, b = closest_factors_to_sqrt(pixels)
    if portrait:
        if a < b:
            return a, b
        else:
            return b, a
    else:
        if a > b:
            return a, b
        else:
            return b, a

# Find a pixel dimension such that the ratio between h:w or w:h is less than max_ratio
def find_optimal_dim(x: int, y: int, max_ratio: float = 2.0) -> t.Tuple[int, int]:
    """
    Find an image dimension whose ratio between width and height or that between
    height and width is lower than `max_ratio` while minimising the number of
    new pixels required to fill the gap.
    
    Parameters
    ----------
    x: int
        Width
        
    y: int
        Height
        
    max_ratio: float = 2.0
        Maximum ratio between width and height.
    
    Returns
    -------
    Tuple[int, int]
        The optimum dimensions.
    
    Examples
    --------
    >>> find_optimal_dimensions(51, 25, max_ratio=2.0)
    (44, 29)
    >>> find_optimal_dimensions(25, 51, max_ratio=2.0)
    (44, 29)
    >>> find_optimal_dimensions(10, 20, max_ratio=3.0)
    (10, 20)
    """
    # while not within ratio
    while ((x/y) > max_ratio) or ((y/x) > max_ratio):
        pixels = (x*y)+1
        x, y = recommend_img_dim(pixels)
    return x, y

def create_image(encoded: bytes, portrait: bool = False):
    """
    Create an image with a byte string. The length of `encoded` must be a
    multiple of 3.
    
    Parameters
    ----------
    encoded: bytes
        The string of bytes to be turned into an image
    
    portrait: bool = False
        Whether to generate the image as a portrait.
    """
    x, y = recommend_img_dim(len(encoded)//3, portrait)
    img = Image.new("RGB", (x, y), color="black")
    pixels = img.load()
    for j in range(y):
        for i in range(x):
            offset = (j*x + i)*3
            pixels[i, j] = tuple(encoded[offset:offset+3])
    return img

def print_res(thing: bytes):
    for b in thing:
        print(hex(b)[2:].rjust(2, "0"), end=" ")
    print()

class Encoder(object):
    """
    An object which encodes an input into an output byte string that can be
    turned into an image.
    
    Parameters
    ----------
    **kwargs
        max_ratio: Optional[float] = None
            Maximum ratio for an image.
    """
    def __init__(self, **kwargs):
        self.max_ratio = kwargs.get("max_ratio")
        self.portrait = kwargs.get("portrait")
        if self.portrait is None:
            self.portrait = False
    
    def encode(self, bstream: t.Iterable[int]) -> bytes:
        """
        Encode an iterable stream of bytes into an output that can be turned
        into an image.
        
        Parameters
        ----------
        bstream: Iterable[int]
            Iterable of bytes
        
        Returns
        -------
        bytes
            Output bytes
        """
        bstream_it = iter(bstream)
        def fill_buffer() -> bytearray:
            count = 0
            buffer = bytearray()
            for b in bstream_it:
                buffer.append(b)
                count += 1
                if count == 7:
                    break
            return buffer

        # 0bxxxxxxyz
        # x: odd or even set bit count for first 6 bytes
        # y: is_end
        # z: is_ascii
        def get_header(buffer: bytes, is_ascii: bool) -> int:
            def count_set_bits(b: int) -> int:
                count = 0
                for i in range(8):
                    count += (b >> i) & 1
                # print(chr(b), bin(b), count)
                return count
            
            header = 0
            bitter = iter(buffer)
            for i in range(6):
                result = count_set_bits(next(bitter, 0))
                # print(result & 1)
                header |= (result & 1) << (5-i)
            # print(bin(header))
            if count_set_bits(next(bitter, 0)) & 1:
                header = (~header) & 0x3f
            header <<= 2
            header |= int(is_ascii)
            # print(bin(header))
            return header

        output = bytearray()
        last_header_index = None
        last_block_length = 0
        while True:
            buffer = fill_buffer()
            if len(buffer) == 0:
                break
            last_block_length = len(buffer)
            is_ascii = all(map(lambda b: b <= 0x7f, buffer))
            buffer = buffer.ljust(7, b"\x00")
            header = get_header(buffer, is_ascii)
            if is_ascii:
                for i in range(7):
                    buffer[i] <<= 1
            buffer.insert(0, header)
            last_header_index = len(output)
            output.extend(buffer)

        # set last header bit
        if last_header_index is not None:
            output[last_header_index] |= 0b10
            output[last_header_index] &= 0b11100011
            output[last_header_index] |= (last_block_length << 2)

        # missing bytes and optimal ratio
        len_out = len(output)
        missing = (3 - (len(output) % 3)) % 3
        if self.max_ratio is not None:
            cx, cy = recommend_img_dim((len_out+missing)//3)
            ox, oy = find_optimal_dim(cx, cy, self.max_ratio)
            missing += (ox*oy - cx*cy)*3
        div = missing // len_out
        mod = missing % len_out
        output *= (div+1)
        output.extend(output[:mod])

        return bytes(output)
    
    def encode_file_with_path(self, path: os.PathLike) -> bytes:
        """
        Encode a file using the Encoder.
        
        Parameters
        ----------
        path: os.PathLike
            Path to the input file
        
        Returns
        -------
        bytes
            Output bytes
        """
        with Path(path).open("rb") as f:
            encoded = self.encode(f.read())
        return encoded


class Decoder(object):
    """
    The decoder undoes the work done by `Encoder` and retrieves the original
    input.
    
    Parameters
    ----------
    **kwargs
        print_intermediate: Optional[float] = None
            Whether to print the encoded bytes embedded in the pixels of the
            image.
    """
    def __init__(self, **kwargs):
        self.print_intermediate = kwargs.get("print_intermediate")
        if self.print_intermediate is None:
            self.print_intermediate = False
    
    def decode(self, bstream: t.Iterable[int]) -> bytes:
        """
        Decode the encoded image whose pixels have been flattened into bytes.
        
        Parameters
        ----------
        bstream: Iterable[int]
            The pixels of the image as a flattened iterator of bytes.
        
        Returns
        -------
        bytes
            The original input as bytes.
            
        Raises
        ------
        ValueError
            If an unexpected value is encountered.
        """
        bstream_it = iter(bstream)
        
        def fill_buffer() -> bytearray:
            count = 0
            buffer = bytearray()
            for b in bstream_it:
                buffer.append(b)
                count += 1
                if count == 8:
                    break
            return buffer
        
        decoded = bytearray()
        is_end = False
        while not is_end:
            buffer = fill_buffer()
            if len(buffer) < 8:
                raise ValueError("end reached but no is_end bit found")
            if buffer[0] & 2:
                is_end = True
            if buffer[0] & 1:
                processed = bytes(map(lambda b: b >> 1, buffer[1:]))
            else:
                processed = buffer[1:]
            if is_end:
                processed = processed[:((buffer[0]>>2)&7)]
            #print_res(processed)
            decoded.extend(processed)
        return decoded
    
    def decode_image_with_path(self, path: os.PathLike) -> bytes:
        """
        Decode an image at a path.
        
        Parameters
        ----------
        path: os.PathLike
            Path to the image.
        
        Returns
        -------
        bytes
            Original input bytes.
        """
        image = Image.open(path)
        x, y = image.size
        pixels = image.load()
        encoded = bytearray()
        for j in range(y):
            for i in range(x):
                encoded.extend(pixels[i, j])
        if self.print_intermediate:
            print_res(encoded)
        decoded = self.decode(encoded)
        return decoded
