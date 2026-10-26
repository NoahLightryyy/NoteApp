"""Caesar cipher and keyless English frequency analysis (educational only)."""
import argparse
from collections import Counter
import string

FREQUENCIES = [8.167, 1.492, 2.782, 4.253, 12.702, 2.228, 2.015,
               6.094, 6.966, 0.153, 0.772, 4.025, 2.406, 6.749,
               7.507, 1.929, 0.095, 5.987, 6.327, 9.056, 2.758,
               0.978, 2.360, 0.150, 1.974, 0.074]


def caesar(text, shift):
    """Shift ASCII letters only; preserve case, punctuation and other languages."""
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
        elif 'A' <= char <= 'Z':
            result.append(chr((ord(char) - ord('A') + shift) % 26 + ord('A')))
        else:
            result.append(char)
    return ''.join(result)


def score_english(text):
    counts = Counter(c for c in text.lower() if c in string.ascii_lowercase)
    total = sum(counts.values())
    if not total:
        raise ValueError('Enter a message containing English letters.')
    # Chi-square distance between observed and expected English frequencies.
    return sum((counts[c] - total * f / 100) ** 2 / (total * f / 100)
               for c, f in zip(string.ascii_lowercase, FREQUENCIES))


def crack(ciphertext):
    # No key is supplied. Rank all shifts using the frequency distribution.
    return sorted((score_english(caesar(ciphertext, -key)), key,
                   caesar(ciphertext, -key)) for key in range(26))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['encrypt', 'decrypt', 'crack'])
    parser.add_argument('text', nargs='?')
    parser.add_argument('--key', type=int)
    args = parser.parse_args()
    text = args.text if args.text is not None else input('Message: ')
    if len(text) > 10000:
        parser.error('Use at most 10,000 characters for this classroom exercise.')
    if args.mode == 'crack':
        if args.key is not None:
            parser.error('crack ranks all keys; do not supply --key')
        try:
            candidates = crack(text)
        except ValueError as exc:
            parser.error(str(exc))
        print('Top candidates (lower frequency score is better):')
        for score, key, plaintext in candidates[:5]:
            print(f'Key={key:2d} Score={score:.2f}: {plaintext}')
        print('Frequency analysis is a guess: short/non-English text may rank incorrectly.')
    else:
        if args.key is None:
            parser.error('--key is required for encrypt/decrypt')
        print(caesar(text, args.key if args.mode == 'encrypt' else -args.key))


if __name__ == '__main__':
    main()
