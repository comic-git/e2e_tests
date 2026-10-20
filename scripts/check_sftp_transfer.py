"""Run prepared packages against disposable localhost OpenSSH (Linux root only).

Usage: sudo python3 check_sftp_transfer.py /path/to/prepared-package
Requires openssh-server, openssh-client, lftp, useradd/userdel/chpasswd.
"""
from pathlib import Path
import json
import os
import pwd
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time


def main(package):
    if sys.platform != 'linux' or os.geteuid() != 0:
        raise SystemExit('Use a disposable Linux environment and run as root.')
    for executable in ['sshd', 'ssh-keygen', 'lftp', 'useradd', 'userdel', 'chpasswd']:
        if not shutil.which(executable):
            raise SystemExit('Missing prerequisite: ' + executable)
    user = 'cge2e_' + secrets.token_hex(4)
    password = secrets.token_hex(24)
    with tempfile.TemporaryDirectory(prefix='comicgit-sftp-e2e-') as temporary:
        root = Path(temporary)
        root.chmod(0o755)
        home = root / 'home'
        home.mkdir()
        process = None
        created = False
        try:
            subprocess.run(['useradd', '--home-dir', str(home), '--no-create-home', '--shell', '/bin/sh', user], check=True)
            created = True
            subprocess.run(['chpasswd'], input=f'{user}:{password}\n', text=True, check=True)
            account = pwd.getpwnam(user)
            os.chown(home, account.pw_uid, account.pw_gid)
            for name in ['host', 'client', 'wrong-host']:
                subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(root / name)], check=True)
            ssh_dir = home / '.ssh'
            ssh_dir.mkdir(mode=0o700)
            os.chown(ssh_dir, account.pw_uid, account.pw_gid)
            authorized = ssh_dir / 'authorized_keys'
            shutil.copyfile(root / 'client.pub', authorized)
            authorized.chmod(0o600)
            os.chown(authorized, account.pw_uid, account.pw_gid)
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            config = root / 'sshd_config'
            config.write_text(f'''ListenAddress 127.0.0.1
Port {port}
HostKey {root / 'host'}
PidFile {root / 'sshd.pid'}
AuthorizedKeysFile {authorized}
PasswordAuthentication yes
PubkeyAuthentication yes
UsePAM no
PermitRootLogin no
AllowUsers {user}
ForceCommand internal-sftp
DisableForwarding yes
Subsystem sftp internal-sftp
''')
            Path('/run/sshd').mkdir(exist_ok=True)
            with (root / 'sshd.log').open('w') as log:
                process = subprocess.Popen([shutil.which('sshd'), '-D', '-e', '-f', str(config)], stdout=log, stderr=log)
                for attempt in range(100):
                    if process.poll() is not None:
                        raise AssertionError((root / 'sshd.log').read_text())
                    try:
                        with socket.create_connection(('127.0.0.1', port), timeout=0.2):
                            break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise AssertionError('Temporary sshd did not start')
                site = home / 'site'
                site.mkdir()
                os.chown(site, account.pw_uid, account.pw_gid)
                def seed(path, data):
                    path.write_bytes(data)
                    os.chown(path, account.pw_uid, account.pw_gid)
                def deploy(name='clean', auth='password', bad_host=False, missing=False):
                    downloaded = root / ('run-' + secrets.token_hex(4))
                    shutil.copytree(package / name / 'downloaded', downloaded)
                    bundle = downloaded / 'deployment'
                    (bundle / 'connection.json').write_text(json.dumps({'host': '127.0.0.1', 'port': port}))
                    if missing:
                        # Only substitute the destination, leaving the real generated mirror intact.
                        script = bundle / 'deploy.lftp'
                        script.write_text(script.read_text().replace('cd "./site"', 'cd "./missing"'))
                    public = (root / ('wrong-host.pub' if bad_host else 'host.pub')).read_text().split()
                    env = {k: v for k, v in os.environ.items() if not k.startswith('SFTP_')}
                    env.update(SFTP_USERNAME=user, SFTP_KNOWN_HOSTS=f'\x5b127.0.0.1\x5d:{port} {public[0]} {public[1]}',
                               SFTP_PASSWORD=password if auth == 'password' else '',
                               SFTP_PRIVATE_KEY=(root / 'client').read_text() if auth == 'key' else '', RUNNER_TEMP=str(root))
                    result = subprocess.run([sys.executable, str(bundle / 'deploy.py'), '--output-dir', str(downloaded / 'site')],
                                            cwd=downloaded, env=env, capture_output=True, text=True, timeout=90)
                    assert not list(root.glob('sftp-auth-*')), 'Temporary credentials survived deployment'
                    if bad_host or missing:
                        assert result.returncode != 0, 'Unsafe transfer unexpectedly succeeded'
                    else:
                        assert result.returncode == 0, result.stdout + result.stderr + (root / 'sshd.log').read_text()
                seed(site / 'unchanged-on-failure.txt', b'protected by failed connection')
                deploy(bad_host=True)
                assert (site / 'unchanged-on-failure.txt').read_bytes() == b'protected by failed connection'
                deploy(missing=True)
                assert not (home / 'missing').exists()
                protected = site / '.well-known'
                protected.mkdir()
                os.chown(protected, account.pw_uid, account.pw_gid)
                seed(protected / 'token', b'host managed')
                for auth in ['password', 'key']:
                    seed(site / 'obsolete.txt', b'delete me')
                    seed(site / '.obsolete', b'delete me too')
                    expected = (package / 'clean/downloaded/site/marker.txt').read_bytes()
                    seed(site / 'marker.txt', b'x' * len(expected))
                    os.utime(site / 'marker.txt', (2000000000, 2000000000))
                    deploy(auth=auth)
                    assert (site / 'marker.txt').read_bytes() == expected
                    assert not (site / 'obsolete.txt').exists()
                    assert not (site / '.obsolete').exists()
                    assert (protected / 'token').read_bytes() == b'host managed'
                    assert (site / '.htaccess').is_file()
                    assert not (site / '.private').exists()
                    assert (site / 'comic/001/index.html').is_file()
                    print(f'{auth}: upload, same-size update, cleanup, hidden files and exclusions PASS', flush=True)
                seed(site / 'keep.txt', b'keep with cleanup disabled')
                deploy(name='keep')
                assert (site / 'keep.txt').exists()
                print('Cleanup disabled, missing destination, host-key rejection and credential cleanup PASS', flush=True)
        finally:
            if process is not None:
                process.terminate()
                process.wait(timeout=10)
            if created:
                subprocess.run(['userdel', user], check=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
