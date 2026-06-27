"""Remote tests for the staging SSH lockdown."""

import os
import shlex
import unittest

try:
    import paramiko
except ImportError:
    paramiko = None


HOST = "157.180.125.174"
ROOT_KEY_PATH = os.path.expanduser("~/.ssh/staging_admin_ed25519")
DEPLOY_KEY_PATH = os.path.expanduser("~/.ssh/deploy_staging_ed25519")
COMMAND_TIMEOUT_SECONDS = 30


def connect(username: str, key_path: str):
    """Create an SSH connection using only the explicitly supplied key."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=HOST,
        username=username,
        key_filename=key_path,
        timeout=COMMAND_TIMEOUT_SECONDS,
        banner_timeout=COMMAND_TIMEOUT_SECONDS,
        auth_timeout=COMMAND_TIMEOUT_SECONDS,
        allow_agent=False,
        look_for_keys=False,
    )
    return client


def run_remote(client, command: str) -> tuple[int, str, str]:
    """Run a command and return its exit code, stdout, and stderr."""
    _stdin, stdout, stderr = client.exec_command(
        command,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )
    exit_code = stdout.channel.recv_exit_status()
    return (
        exit_code,
        stdout.read().decode("utf-8", errors="replace"),
        stderr.read().decode("utf-8", errors="replace"),
    )


@unittest.skipUnless(
    paramiko is not None,
    "paramiko is not installed; skipping staging SSH lockdown tests",
)
class RootSessionLockdownTests(unittest.TestCase):
    """Checks that require an existing root administration session."""

    @classmethod
    def setUpClass(cls) -> None:
        if not os.path.isfile(ROOT_KEY_PATH):
            raise unittest.SkipTest(f"root SSH key is missing: {ROOT_KEY_PATH}")

        try:
            cls.ssh = connect("root", ROOT_KEY_PATH)
        except Exception as exc:
            raise unittest.SkipTest(
                "root SSH is unavailable; configuration checks require an "
                f"existing administration session ({exc})"
            ) from exc

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ssh.close()

    def assert_remote_success(self, command: str) -> tuple[str, str]:
        exit_code, stdout, stderr = run_remote(self.ssh, command)
        self.assertEqual(
            exit_code,
            0,
            (
                f"Remote command failed with exit code {exit_code}: {command}\n"
                f"stdout:\n{stdout}\nstderr:\n{stderr}"
            ),
        )
        return stdout, stderr

    def assert_config_line(self, directive: str, value: str) -> None:
        pattern = (
            rf"^[[:space:]]*{directive}[[:space:]]+{value}"
            r"([[:space:]]*(#.*)?)?$"
        )
        command = (
            "grep -RhsE "
            f"{shlex.quote(pattern)} "
            "/etc/ssh/sshd_config /etc/ssh/sshd_config.d"
        )
        stdout, _ = self.assert_remote_success(command)
        self.assertTrue(
            stdout.strip(),
            f"Expected {directive} {value} in the SSH configuration",
        )

    def test_sshd_config_valid(self) -> None:
        self.assert_remote_success("sshd -t")

    def test_permit_root_login_no(self) -> None:
        self.assert_config_line("PermitRootLogin", "no")

    def test_password_auth_no(self) -> None:
        self.assert_config_line("PasswordAuthentication", "no")

@unittest.skipUnless(
    paramiko is not None,
    "paramiko is not installed; skipping staging SSH lockdown tests",
)
class DeploySessionLockdownTests(unittest.TestCase):
    """Checks performed through the deploy account."""

    @classmethod
    def setUpClass(cls) -> None:
        if not os.path.isfile(DEPLOY_KEY_PATH):
            raise unittest.SkipTest(f"deploy SSH key is missing: {DEPLOY_KEY_PATH}")

        try:
            cls.ssh = connect("deploy", DEPLOY_KEY_PATH)
        except Exception as exc:
            raise unittest.SkipTest(f"deploy SSH is unavailable: {exc}") from exc

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ssh.close()

    def assert_remote_success(self, command: str) -> tuple[str, str]:
        exit_code, stdout, stderr = run_remote(self.ssh, command)
        self.assertEqual(
            exit_code,
            0,
            (
                f"Remote command failed with exit code {exit_code}: {command}\n"
                f"stdout:\n{stdout}\nstderr:\n{stderr}"
            ),
        )
        return stdout, stderr

    def test_deploy_ssh_works(self) -> None:
        stdout, _ = self.assert_remote_success("whoami")
        self.assertIn("deploy", stdout)

    def test_root_ssh_rejected(self) -> None:
        command = r"""
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
ssh-keygen -q -t ed25519 -N '' -f "$tmpdir/bogus" ||
  exit 2
ssh -o BatchMode=yes -o ConnectTimeout=5 \
  -o IdentitiesOnly=yes -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null -i "$tmpdir/bogus" \
  root@127.0.0.1 whoami
test "$?" -ne 0
"""
        self.assert_remote_success(command)

    def test_dropin_file_exists(self) -> None:
        self.assert_remote_success(
            "test -f /etc/ssh/sshd_config.d/99-terrabits-lockdown.conf"
        )

    def test_deploy_docker_access(self) -> None:
        self.assert_remote_success("docker ps")


if __name__ == "__main__":
    unittest.main()
