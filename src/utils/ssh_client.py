"""SSH client for remote log retrieval."""
import logging
import os
from typing import Optional, Tuple

import paramiko

logger = logging.getLogger(__name__)


class SSHClient:
    """SSH client wrapper for executing commands on remote hosts."""

    def __init__(
        self,
        hostname: str,
        username: str,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 22,
        timeout: int = 30,
    ):
        """
        Initialize SSH client.

        Args:
            hostname: Remote host address
            username: SSH username
            key_path: Path to SSH private key file
            password: SSH password (if not using key)
            port: SSH port
            timeout: Connection timeout in seconds
        """
        self.hostname = hostname
        self.username = username
        self.key_path = key_path
        self.password = password
        self.port = port
        self.timeout = timeout
        self._client: Optional[paramiko.SSHClient] = None

    def connect(self) -> bool:
        """
        Establish SSH connection.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                "hostname": self.hostname,
                "port": self.port,
                "username": self.username,
                "timeout": self.timeout,
            }

            # Use key-based auth if key_path provided
            if self.key_path and os.path.exists(self.key_path):
                logger.info(f"Connecting to {self.hostname} using key: {self.key_path}")
                connect_kwargs["key_filename"] = self.key_path
            elif self.password:
                logger.info(f"Connecting to {self.hostname} using password")
                connect_kwargs["password"] = self.password
            else:
                logger.error("No authentication method provided (key or password)")
                return False

            self._client.connect(**connect_kwargs)
            logger.info(f"Successfully connected to {self.hostname}")
            return True

        except paramiko.AuthenticationException as e:
            logger.error(f"Authentication failed for {self.hostname}: {e}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH error connecting to {self.hostname}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to {self.hostname}: {e}")
            return False

    def execute_command(
        self, command: str, timeout: Optional[int] = None
    ) -> Tuple[bool, str, str]:
        """
        Execute command on remote host.

        Args:
            command: Command to execute
            timeout: Command execution timeout (defaults to connection timeout)

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self._client:
            logger.error("Not connected. Call connect() first.")
            return False, "", "Not connected"

        timeout = timeout or self.timeout

        try:
            logger.debug(f"Executing command: {command}")
            stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)

            stdout_str = stdout.read().decode("utf-8", errors="replace")
            stderr_str = stderr.read().decode("utf-8", errors="replace")

            exit_code = stdout.channel.recv_exit_status()

            if exit_code != 0:
                logger.warning(f"Command exited with code {exit_code}: {stderr_str}")
                return False, stdout_str, stderr_str

            logger.debug(f"Command executed successfully, output length: {len(stdout_str)}")
            return True, stdout_str, stderr_str

        except paramiko.SSHException as e:
            logger.error(f"SSH error executing command: {e}")
            return False, "", str(e)
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return False, "", str(e)

    def get_logs(self, log_command: str) -> Optional[str]:
        """
        Retrieve logs from remote host.

        Args:
            log_command: Command to execute to get logs (e.g., "tail -n 1000 /var/log/firewall.log")

        Returns:
            Log content or None if failed
        """
        success, stdout, stderr = self.execute_command(log_command)

        if not success:
            logger.error(f"Failed to retrieve logs: {stderr}")
            return None

        return stdout

    def close(self):
        """Close SSH connection."""
        if self._client:
            self._client.close()
            logger.debug(f"Closed connection to {self.hostname}")
            self._client = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def test_ssh_connection(
    hostname: str,
    username: str,
    key_path: Optional[str] = None,
    password: Optional[str] = None,
    port: int = 22,
) -> bool:
    """
    Test SSH connection to a host.

    Args:
        hostname: Remote host address
        username: SSH username
        key_path: Path to SSH private key
        password: SSH password
        port: SSH port

    Returns:
        True if connection successful, False otherwise
    """
    with SSHClient(hostname, username, key_path, password, port) as client:
        return client._client is not None
