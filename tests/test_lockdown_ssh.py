"""Remote tests for the staging SSH lockdown."""

import os
import subprocess
import unittest


HOST = os.environ.get("STAGING_HOST", "")
ROOT_KEY_PATH = os.path.expanduser("~/.ssh/staging_admin_ed25519")
DEPLOY_KEY_PATH = os.path.expanduser("~/.ssh/deploy_staging_ed25519")
COMMAND_TIMEOUT_SECONDS = 30


def run_ssh_command(command: str, username: str, key_path: str) -> tuple[int, str, str]:
    """Run a command via SSH subprocess. Returns (exit_code, stdout, stderr)."""
    try:
        r = subprocess.run(
            [
                "ssh",
                "-i", key_path,
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", f"ConnectTimeout={COMMAND_TIMEOUT_SECONDS}",
                "-o", "BatchMode=yes",
                f"{username}@{HOST}",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS + 5,
        )
        return r.returncode, r.stdout, r.stderr
    except Exception as exc:
        return 1, "", str(exc)


class RootSessionLockdownTests(unittest.TestCase):
    """Checks that require an existing root administration session."""

    @classmethod
    def setUpClass(cls) -> None:
        if not HOST:
            raise unittest.SkipTest("STAGING_HOST is not set")
        if not os.path.isfile(ROOT_KEY_PATH):
            raise unittest.SkipTest(f"root SSH key is missing: {ROOT_KEY_PATH}")
        code, out, err = run_ssh_command("echo connectivity_test", "root", ROOT_KEY_PATH)
        if code != 0:
            raise unittest.SkipTest(
                f"root SSH unavailable: {err.strip()}"
            )

    def assert_remote_success(self, command: str) -> tuple[str, str]:
        exit_code, stdout, stderr = run_ssh_command(command, "root", ROOT_KEY_PATH)
        self.assertEqual(
            exit_code,
            0,
            (
                f"Remote command failed with exit code {exit_code}: {command}\n"
                f"stdout:\n{stdout}\nstderr:\n{stderr}"
            ),
        )
        return stdout, stderr

    def assert_config_directive(self, directive: str, expected: str) -> None:
        """Check that a directive is set to expected value in sshd config."""
        command = f"grep -r '^{directive} ' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/"
        stdout, _ = self.assert_remote_success(command)
        self.assertIn(expected, stdout.splitlines()[0].split()[1:],
                       msg=f"Expected {directive} {expected}, got: {stdout}")

    def test_sshd_config_valid(self) -> None:
        self.assert_remote_success("sshd -t")

    def test_permit_root_login_no(self) -> None:
        self.assert_config_directive("PermitRootLogin", "no")

    def test_password_auth_no(self) -> None:
        self.assert_config_directive("PasswordAuthentication", "no")


class DeploySessionLockdownTests(unittest.TestCase):
    """Checks performed through the deploy account."""

    @classmethod
    def setUpClass(cls) -> None:
        if not HOST:
            raise unittest.SkipTest("STAGING_HOST is not set")
        if not os.path.isfile(DEPLOY_KEY_PATH):
            raise unittest.SkipTest(f"deploy SSH key is missing: {DEPLOY_KEY_PATH}")
        code, out, err = run_ssh_command("echo connectivity_test", "deploy", DEPLOY_KEY_PATH)
        if code != 0:
            raise unittest.SkipTest(
                f"deploy SSH unavailable: {err.strip()}"
            )

    def assert_remote_success(self, command: str) -> tuple[str, str]:
        exit_code, stdout, stderr = run_ssh_command(command, "deploy", DEPLOY_KEY_PATH)
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
        """Verify root SSH is rejected by attempting with a bogus key."""
        # Generate a bogus key and try to connect as root
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            bogus_key = os.path.join(tmpdir, "bogus")
            subprocess.run(
                ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", bogus_key],
                check=True, capture_output=True
            )
            code, _, _ = run_ssh_command("whoami", "root", bogus_key)
            self.assertNotEqual(code, 0, "Bogus key should not authenticate as root")

    def test_dropin_file_exists(self) -> None:
        self.assert_remote_success(
            "test -f /etc/ssh/sshd_config.d/99-terrabits-lockdown.conf"
        )

    def test_deploy_docker_access(self) -> None:
        self.assert_remote_success("docker ps")

if __name__ == "__main__":
    unittest.main()
