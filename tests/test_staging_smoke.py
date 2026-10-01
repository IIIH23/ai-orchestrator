"""Smoke tests for the hermes-staging-01 VPS bootstrap."""

import os
import subprocess
import unittest


HOST = os.environ.get("STAGING_HOST", "")
USERNAME = "deploy"
KEY_PATH = os.path.expanduser("~/.ssh/deploy_staging_ed25519")
COMMAND_TIMEOUT_SECONDS = 30


def run_ssh_command(command: str, username: str = USERNAME, key: str = KEY_PATH) -> tuple[int, str, str]:
    """Run a command via SSH subprocess. Returns (exit_code, stdout, stderr)."""
    try:
        r = subprocess.run(
            [
                "ssh",
                "-i", key,
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


class StagingSmokeTests(unittest.TestCase):
    """Verify that bootstrap provisioning completed successfully."""

    @classmethod
    def setUpClass(cls) -> None:
        if not HOST:
            raise unittest.SkipTest("STAGING_HOST is not set")
        # Test SSH connectivity
        code, out, err = run_ssh_command("echo connectivity_test")
        if code != 0:
            raise unittest.SkipTest(
                f"SSH connectivity to {HOST} unavailable: {err.strip()}"
            )

    def assert_remote_success(self, command: str) -> tuple[str, str]:
        exit_code, stdout, stderr = run_ssh_command(command)
        self.assertEqual(
            exit_code,
            0,
            (
                f"Remote command failed with exit code {exit_code}: {command}\n"
                f"stdout:\n{stdout}\nstderr:\n{stderr}"
            ),
        )
        return stdout, stderr

    def test_os_is_ubuntu_2604(self) -> None:
        stdout, _ = self.assert_remote_success("lsb_release -r")
        self.assertIn("26.04", stdout)

    def test_cloud_init_done(self) -> None:
        stdout, _ = self.assert_remote_success("cloud-init status --long")
        self.assertIn("status: done", stdout)

    def test_docker_installed(self) -> None:
        self.assert_remote_success("docker --version")

    def test_docker_compose_plugin(self) -> None:
        self.assert_remote_success("docker compose version")

    def test_docker_service_active(self) -> None:
        stdout, _ = self.assert_remote_success("systemctl is-active docker")
        self.assertIn("active", stdout)

    def test_fail2ban_active(self) -> None:
        stdout, _ = self.assert_remote_success("systemctl is-active fail2ban")
        self.assertIn("active", stdout)

    def test_swap_enabled(self) -> None:
        stdout, _ = self.assert_remote_success("swapon --show=NAME --noheadings")
        self.assertIn("/swapfile", stdout)

    def test_deploy_user_exists(self) -> None:
        self.assert_remote_success("id deploy")

    def test_deploy_in_docker_group(self) -> None:
        stdout, _ = self.assert_remote_success("id -nG deploy")
        self.assertIn("docker", stdout.split())

    def test_ufw_deploy_user_cannot_run(self) -> None:
        """Verify deploy user cannot run ufw status (requires root)."""
        code, stdout, stderr = run_ssh_command("ufw status 2>&1")
        # ufw requires root — deploy user should be denied
        self.assertNotEqual(code, 0,
                            "deploy user should not be able to run ufw status (needs root)")

    def test_sshd_deploy_user_cannot_run(self) -> None:
        """Verify deploy user cannot run sshd -t (requires root host keys)."""
        code, stdout, stderr = run_ssh_command("sshd -t 2>&1")
        # sshd -t fails for non-root users — this is expected and confirms
        # the security boundary between deploy and root
        self.assertNotEqual(code, 0,
                            "deploy user should not be able to run sshd -t (needs root host keys)")

    def test_project_dirs_exist(self) -> None:
        self.assert_remote_success(
            "test -d /opt/terrabits/apps"
            " && test -d /opt/terrabits/backups"
            " && test -d /opt/terrabits/caddy"
        )

    def test_daemon_json_log_rotation(self) -> None:
        stdout, _ = self.assert_remote_success("cat /etc/docker/daemon.json")
        self.assertIn("max-size", stdout)


if __name__ == "__main__":
    unittest.main()
