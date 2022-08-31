# tti.py
Encode text to images.

## Samples

![Encoded linux kernel](/linux.png)
<br>
Arch Linux stable kernel (linux 5.19.5.arch1-1)
```bash
python encode.py /boot/vmlinuz-linux linux.png --max-ratio 1.78
```

![Mystery image](/code.png)
<br>
Decode it to find out
```bash
# Encode
python encode.py image.png code.png --max-ratio 1.0

# Decode
python decode.py code.png image.png
```