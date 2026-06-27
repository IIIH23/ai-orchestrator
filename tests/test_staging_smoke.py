"""Smoke tests for the hermes-staging-01 VPS bootstrap."""

import os
import unittest

try:
    import paramiko
except ImportError:
    paramiko = None


HOST = "157.180.125.174"
USERNAME = "root"
KEY_PATH = os.path.expanduser("~/.ssh/staging_admin_ed25519")
COMMAND_TIMEOUT_SECONDS = 30


@unittest.skipUnless(
    paramiko is not None,
    "paramiko is not installed; skipping hermes-staging-01 SSH smoke tests",
)
class StagingSmokeTests(unittest.TestCase):
    """Verify that bootstrap provisioning completed successfully."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.ssh = paramiko.SSHClient()
        cls.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            cls.ssh.connect(
                hostname=HOST,
                username=USERNAME,
                key_filename=KEY_PATH,
                timeout=COMMAND_TIMEOUT_SECONDS,
                banner_timeout=COMMAND_TIMEOUT_SECONDS,
                auth_timeout=COMMAND_TIMEOUT_SECONDS,
                allow_agent=False,
                look_for_keys=False,
            )
        except Exception:
            cls.ssh.close()
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ssh.close()

    def run_remote(self, command: str) -> tuple[int, str, str]:
        """Run a command over SSH and return its exit code, stdout, and stderr."""
        _stdin, stdout, stderr = self.ssh.exec_command(
            command,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
        exit_code = stdout.channel.recv_exit_status()
        return (
            exit_code,
            stdout.read().decode("utf-8", errors="replace"),
            stderr.read().decode("utf-8", errors="replace"),
        )

    def assert_remote_success(self, command: str) -> tuple[str, str]:
        exit_code, stdout, stderr = self.run_remote(command)
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

    def test_ufw_allows_22_80_443(self) -> None:
        stdout, _ = self.assert_remote_success("ufw status verbose")
        lines = stdout.splitlines()
        for port in ("22/tcp", "80/tcp", "443/tcp"):
            with self.subTest(port=port):
                self.assertTrue(
                    any(port in line and "ALLOW" in line for line in lines),
                    f"Expected an ALLOW rule for {port} in:\n{stdout}",
                )

    def test_sshd_config_valid(self) -> None:
        self.assert_remote_success("sshd -t")

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
