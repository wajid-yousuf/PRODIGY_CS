import argparse
import os
import sys
from PIL import Image
import numpy as np
import random

def load_image_as_array(path):
    img = Image.open(path).convert("RGBA")  # keep alpha to preserve transparency
    arr = np.array(img)  # shape (H, W, 4), dtype=uint8
    return img.mode, img.format, arr

def save_array_as_image(arr, mode, fmt, path):
    # Convert back to PIL Image preserving mode
    img = Image.fromarray(arr.astype('uint8'), 'RGBA')
    # If original didn't have alpha, convert back to original mode
    if mode != 'RGBA':
        img = img.convert(mode)
    # Save (let PIL infer format from ext or use fmt)
    img.save(path)
    return

def make_permutation(n, seed):
    rng = random.Random(seed)
    perm = list(range(n))
    rng.shuffle(perm)
    return np.array(perm, dtype=np.int64)

def inverse_permutation(perm):
    inv = np.empty_like(perm)
    inv[perm] = np.arange(len(perm), dtype=np.int64)
    return inv

def keystream_bytes(shape, seed, channels=3):
    """
    Generate deterministic keystream bytes for XOR.
    shape: number of pixels (n)
    channels: number of channels to XOR per pixel (e.g., 3 for RGB)
    Returns array shape (n, channels) dtype uint8
    """
    rng = random.Random(seed + 0xFEED)  # slight offset to separate from permutation RNG
    n = shape
    out = np.empty((n, channels), dtype=np.uint8)
    # fill with bytes from RNG
    for i in range(n):
        for c in range(channels):
            out[i, c] = rng.getrandbits(8)
    return out

def encrypt_image(in_path, out_path, seed):
    mode, fmt, arr = load_image_as_array(in_path)
    h, w, ch = arr.shape
    # flatten pixels: shape (n, 4)
    pixels = arr.reshape((-1, ch)).copy()
    n = pixels.shape[0]

    # permutation
    perm = make_permutation(n, seed)
    permuted = pixels[perm]

    # keystream for RGB only (don't touch alpha)
    ks = keystream_bytes(n, seed, channels=3)
    # XOR channels 0..2
    permuted[:, :3] = np.bitwise_xor(permuted[:, :3], ks)

    out_arr = permuted.reshape((h, w, ch))
    save_array_as_image(out_arr, mode, fmt, out_path)
    print(f"[+] Encrypted -> {out_path}")
    # Save permutation and keystream seeds info for reproducibility? We rely on seed.
    return

def decrypt_image(in_path, out_path, seed):
    mode, fmt, arr = load_image_as_array(in_path)
    h, w, ch = arr.shape
    pixels = arr.reshape((-1, ch)).copy()
    n = pixels.shape[0]

    # keystream (must be same as used in encrypt)
    ks = keystream_bytes(n, seed, channels=3)
    # reverse XOR first (XOR is symmetric)
    pixels[:, :3] = np.bitwise_xor(pixels[:, :3], ks)

    # inverse permutation
    perm = make_permutation(n, seed)
    inv = inverse_permutation(perm)
    original = np.empty_like(pixels)
    original[inv] = pixels  # place permuted pixels back to original positions

    out_arr = original.reshape((h, w, ch))
    save_array_as_image(out_arr, mode, fmt, out_path)
    print(f"[+] Decrypted -> {out_path}")
    return

def parse_args():
    p = argparse.ArgumentParser(description="Simple image encrypt/decrypt using pixel permutation + XOR.")
    p.add_argument("action", choices=["encrypt", "decrypt"], help="encrypt or decrypt")
    p.add_argument("input", help="input image path")
    p.add_argument("output", help="output image path")
    p.add_argument("--seed", type=int, required=True, help="numeric seed (same for encrypt/decrypt)")
    return p.parse_args()

def main():
    args = parse_args()
    if not os.path.exists(args.input):
        print("Input file not found:", args.input)
        sys.exit(2)
    if args.action == "encrypt":
        encrypt_image(args.input, args.output, args.seed)
    else:
        decrypt_image(args.input, args.output, args.seed)

if __name__ == "__main__":
    main()
