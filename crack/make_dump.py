"""Generate only the six synthetic accounts used by this classroom exercise."""
import argparse
import hashlib
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
DEFAULT_DUMP = DIRECTORY / 'results' / 'synthetic-md5.json'
# Deliberately weak, public teaching values. These are not real account records.
SYNTHETIC_ACCOUNTS = {
    'liwei': '123456',
    'sofia': 'iloveyou',
    'tomk': 'qwerty123',
    'aisha': 'password1',
    'marie': 'mariepw',
    'raj': 'Gv7#pLm2!xQ',
}


def build_dump():
    return {
        'schema': 'notesapp-synthetic-md5-v1',
        'scope': 'Six invented classroom accounts; no application database is read.',
        'accounts': {name: hashlib.md5(password.encode('utf-8')).hexdigest()
                     for name, password in SYNTHETIC_ACCOUNTS.items()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_DUMP)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_dump(), indent=2) + '\n', encoding='utf-8')
    print(f'Wrote six SYNTHETIC account hashes: {args.output.resolve()}')


if __name__ == '__main__':
    main()
