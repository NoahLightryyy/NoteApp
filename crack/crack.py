"""Bounded MD5 wordlist demonstration against the bundled synthetic fixture only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time

from make_dump import DEFAULT_DUMP, DIRECTORY, build_dump

MAX_WORDS = 10000
MAX_WORDLIST_BYTES = 1024 * 1024


def load_fixture(path):
    if path.stat().st_size > 8192:
        raise ValueError('Unexpected fixture size.')
    fixture = json.loads(path.read_text(encoding='utf-8'))
    if fixture != build_dump():
        raise ValueError('Only the exact six synthetic classroom accounts are supported. Run make_dump.py.')
    return fixture['accounts']


def load_wordlist(path):
    if path.stat().st_size > MAX_WORDLIST_BYTES:
        raise ValueError('Wordlist exceeds the 1 MiB classroom limit.')
    words = [line.strip() for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(words) > MAX_WORDS or any(len(word) > 256 for word in words):
        raise ValueError('Use at most 10,000 words, each at most 256 characters.')
    return words


def demonstrate(accounts, words):
    if accounts != build_dump()['accounts']:
        raise ValueError('Only the bundled synthetic fixture is supported.')
    if len(words) > MAX_WORDS or any(len(word) > 256 for word in words):
        raise ValueError('Classroom wordlist limit exceeded.')
    recovered = {}
    cpu_start = time.process_time()
    start = time.perf_counter()
    for candidate in words:
        digest = hashlib.md5(candidate.encode('utf-8')).hexdigest()
        for username, expected in accounts.items():
            if username not in recovered and digest == expected:
                recovered[username] = candidate
    elapsed = time.perf_counter() - start
    cpu_elapsed = time.process_time() - cpu_start
    return {
        'schema': 'notesapp-synthetic-md5-result-v1',
        'run_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'New run on the exact synthetic classroom fixture; not historical report evidence.',
        'python': platform.python_version(),
        'wordlist_entries': len(words),
        'accounts': len(accounts),
        'recovered_synthetic_passwords': recovered,
        'not_found_in_this_wordlist': [name for name in accounts if name not in recovered],
        'elapsed_ms': elapsed * 1000,
        'process_cpu_ms': cpu_elapsed * 1000,
        'measurement': 'Hashing and comparisons only; file loading is excluded. Timing varies by machine.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dump', type=Path, default=DEFAULT_DUMP)
    parser.add_argument('--wordlist', type=Path, default=DIRECTORY / 'wordlist.txt')
    parser.add_argument('--output', type=Path, default=DIRECTORY / 'results' / 'md5-result.json')
    args = parser.parse_args()
    try:
        result = demonstrate(load_fixture(args.dump), load_wordlist(args.wordlist))
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot run synthetic exercise: {error}\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    recovered = result['recovered_synthetic_passwords']
    print(f'SYNTHETIC fixture: recovered {len(recovered)} / {result["accounts"]} using {result["wordlist_entries"]} bundled candidates.')
    print(f'New measurement: {result["elapsed_ms"]:.6f} ms wall / {result["process_cpu_ms"]:.6f} ms process CPU.')
    print('Not in this wordlist: ' + ', '.join(result['not_found_in_this_wordlist']))
    print('Not found does not mean uncrackable; no historical prediction or timing is reconstructed.')
    print(f'Result: {args.output.resolve()}')


if __name__ == '__main__':
    main()
