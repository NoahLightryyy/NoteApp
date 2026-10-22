"""Generate a local-only self-signed localhost certificate; preserve existing files."""
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    directory = Path(__file__).resolve().parent / 'secrets' / 'tls'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    cert = directory / 'localhost.crt'
    key = directory / 'localhost.key'
    if cert.exists() or key.exists():
        if not (cert.exists() and key.exists()):
            raise SystemExit('Incomplete TLS certificate/key pair; restore it before continuing.')
        print('Existing TLS certificate and key preserved.')
        return
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        temporary = Path(temporary)
        config = temporary / 'openssl.cnf'
        config.write_text('[req]\ndistinguished_name=dn\nx509_extensions=ext\nprompt=no\n'
                          '[dn]\nCN=localhost\n[ext]\n'
                          'subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1\n'
                          'basicConstraints=critical,CA:FALSE\n'
                          'keyUsage=critical,digitalSignature,keyEncipherment\n'
                          'extendedKeyUsage=serverAuth\n')
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-sha256',
                        '-nodes', '-days', '365', '-config', str(config),
                        '-keyout', str(temporary / 'key'), '-out', str(temporary / 'cert')],
                       check=True, capture_output=True)
        os.chmod(temporary / 'key', 0o600)
        (temporary / 'key').replace(key)
        (temporary / 'cert').replace(cert)
    print('Created local TLS certificate. Trust it explicitly for local testing only.')


if __name__ == '__main__':
    main()
