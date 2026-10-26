"""One bounded local measurement of MD5 and Argon2id using invented input only."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import time

from argon2 import PasswordHasher, Type

DIRECTORY = Path(__file__).resolve().parent
SYNTHETIC_INPUT = 'classroom-benchmark-only-not-a-real-password'


def measure(operation):
    cpu_start = time.process_time()
    start = time.perf_counter()
    value = operation()
    wall_ms = (time.perf_counter() - start) * 1000
    cpu_ms = (time.process_time() - cpu_start) * 1000
    return value, {'wall_ms': wall_ms, 'process_cpu_ms': cpu_ms}


def benchmark():
    hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, type=Type.ID)
    def md5_sample():
        for _ in range(10000):
            hashlib.md5(SYNTHETIC_INPUT.encode('utf-8')).digest()
    _, md5_timing = measure(md5_sample)
    encoded, hash_timing = measure(lambda: hasher.hash(SYNTHETIC_INPUT))
    verified, verify_timing = measure(lambda: hasher.verify(encoded, SYNTHETIC_INPUT))
    if not verified:
        raise RuntimeError('Synthetic Argon2 verification failed.')
    return {
        'schema': 'notesapp-bounded-password-benchmark-v1',
        'run_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'New synthetic measurement; no database access, no guessing, no historical report claim.',
        'python': platform.python_version(),
        'argon2_cffi': version('argon2-cffi'),
        'argon2id_parameters': {'memory_kib': 65536, 'time_cost': 3, 'parallelism': 4},
        'md5': {'iterations': 10000, **md5_timing},
        'argon2id_hash': {'iterations': 1, **hash_timing},
        'argon2id_verify': {'iterations': 1, **verify_timing},
        'limitations': 'A single bounded sample is noisy and hardware-dependent; it is not an attacker-speed estimate. MD5 and Argon2 iteration counts differ.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DIRECTORY / 'results' / 'benchmark.json')
    args = parser.parse_args()
    result = benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Synthetic measurement: 10,000 MD5 digests, one Argon2id hash and one verification.')
    for name in ('md5', 'argon2id_hash', 'argon2id_verify'):
        sample = result[name]
        print(f'{name}: {sample["wall_ms"]:.3f} ms wall / {sample["process_cpu_ms"]:.3f} ms process CPU ({sample["iterations"]} iteration(s))')
    print(f'Result: {args.output.resolve()}')
    print(result['limitations'])


if __name__ == '__main__':
    main()
