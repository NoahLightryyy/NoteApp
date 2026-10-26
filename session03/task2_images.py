"""Compare AES-ECB and AES-GCM on raw RGB pixels, then verify decryption."""
import argparse
import json
import secrets
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def check_image_size(image):
    if image.width <= 0 or image.height <= 0 or image.width * image.height > 4000000:
        raise ValueError('Use an image with 1 to 4,000,000 pixels for this classroom exercise.')


def compare(original, output):
    check_image_size(original)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    original = original.convert('RGB')
    pixels = original.tobytes()
    key = AESGCM.generate_key(bit_length=256)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(pixels) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    ecb_bytes = encryptor.update(padded) + encryptor.finalize()

    nonce = secrets.token_bytes(12)
    # Authenticate dimensions and pixel format alongside the ciphertext.
    metadata = json.dumps({'size': original.size, 'mode': 'RGB'}, sort_keys=True).encode()
    aesgcm = AESGCM(key)
    gcm_with_tag = aesgcm.encrypt(nonce, pixels, metadata)
    # AESGCM appends the 16-byte authentication tag. It is not image data.
    gcm_bytes = gcm_with_tag[:-16]
    ecb_image = Image.frombytes('RGB', original.size, ecb_bytes[:len(pixels)])
    gcm_image = Image.frombytes('RGB', original.size, gcm_bytes)

    decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    decrypted_padded = decryptor.update(ecb_bytes) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    ecb_plain = unpadder.update(decrypted_padded) + unpadder.finalize()
    gcm_plain = aesgcm.decrypt(nonce, gcm_with_tag, metadata)
    if ecb_plain != pixels or gcm_plain != pixels:
        raise RuntimeError('Encryption/decryption round-trip failed.')
    altered = bytearray(gcm_with_tag)
    altered[0] ^= 1
    try:
        aesgcm.decrypt(nonce, bytes(altered), metadata)
    except InvalidTag:
        print('PASS: GCM rejects modified ciphertext.')
    else:
        raise AssertionError('Modified ciphertext was accepted')

    for name, img in [('original', original), ('ecb_encrypted', ecb_image),
                      ('gcm_encrypted', gcm_image),
                      ('gcm_decrypted', Image.frombytes('RGB', original.size, gcm_plain))]:
        img.save(output / f'{name}.png')
    # Thumbnails preserve aspect ratio. Full-size results are saved separately.
    sheet = Image.new('RGB', (1200, 450), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, (label, img) in enumerate([('Original', original), ('AES-ECB', ecb_image), ('AES-GCM', gcm_image)]):
        thumbnail = ImageOps.contain(img, (390, 410))
        sheet.paste(thumbnail, (i * 400 + (400 - thumbnail.width) // 2, 35))
        draw.text((i * 400 + 15, 10), label, fill='black')
    sheet.save(output / 'comparison.png')
    print('PASS: both modes decrypt to exactly the original RGB bytes.')
    print(f'Results: {output.resolve()}')
    print('Photographs may show no ECB outline. Use --demo to see repeated patterns.')
    print('This is an in-memory lab: key/nonce/full ciphertext are not saved.')
    print('The PNGs visualize ciphertext; they are not encrypted-file archives.')
    return {'width': original.width, 'height': original.height,
            'ecb_roundtrip': True, 'gcm_roundtrip': True, 'gcm_tamper_rejected': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--image', type=Path, help='Path to your own photograph')
    source.add_argument('--demo', action='store_true', help='Generate flat-color rectangles')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'results' / 'aes-demo')
    args = parser.parse_args()
    if args.demo:
        img = Image.new('RGB', (512, 512), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle((64, 64, 224, 448), fill='black')
        draw.rectangle((288, 64, 448, 448), fill='black')
    else:
        with Image.open(args.image) as source_image:
            # Check metadata before decoding an optionally supplied image.
            check_image_size(source_image)
            img = ImageOps.exif_transpose(source_image).convert('RGB')
    compare(img, args.output)


if __name__ == '__main__':
    main()
