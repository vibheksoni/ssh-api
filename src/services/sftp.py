import os
import base64
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import paramiko

from ..core.config import ConfigManager
from ..core.logger import Logger


class SFTPService:
    """
    SFTP operations handler with progress tracking.

    Args:
        sftp: Paramiko SFTPClient instance.
        config: ConfigManager instance.
    """

    def __init__(
        self,
        sftp: paramiko.SFTPClient,
        config: Optional[ConfigManager] = None
    ) -> None:
        self._sftp = sftp
        self._config = config or ConfigManager()
        self._log = Logger("sftp", self._config)
        self._chunk_size = self._config.get("sftp.chunk_size", 32768)

    def upload_file(
        self,
        remote_path: str,
        local_path: Optional[str] = None,
        content: Optional[str] = None,
        raw_content: Optional[str] = None,
        permissions: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Upload file from local path, base64 content, or raw text.

        Args:
            remote_path: Destination path on server.
            local_path: Source file path.
            content: Base64-encoded file content.
            raw_content: Plain text content.
            permissions: Optional chmod permissions.
        Returns:
            Status dict with file info.
        """
        if raw_content:
            with self._sftp.open(remote_path, "w") as f:
                f.write(raw_content)
        elif content:
            decoded = base64.b64decode(content)
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(decoded)
                tmp_path = tmp.name
            try:
                self._sftp.put(tmp_path, remote_path)
            finally:
                os.unlink(tmp_path)
        elif local_path:
            self._sftp.put(local_path, remote_path)
        else:
            raise ValueError("Either local_path, content, or raw_content required")

        if permissions:
            self._sftp.chmod(remote_path, permissions)

        stat = self._sftp.stat(remote_path)
        self._log.info(f"Uploaded {remote_path}")
        return {"status": "uploaded", "path": remote_path, "size": stat.st_size}

    def download_file(
        self,
        remote_path: str,
        local_path: Optional[str] = None,
        return_content: bool = False
    ) -> Dict[str, Any]:
        """
        Download file from server.

        Args:
            remote_path: Source path on server.
            local_path: Destination local path.
            return_content: Return base64 content.
        Returns:
            Status dict with optional content.
        """
        stat = self._sftp.stat(remote_path)
        if local_path:
            self._sftp.get(remote_path, local_path)
        result = {"status": "downloaded", "path": remote_path, "size": stat.st_size}
        if return_content:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
            try:
                self._sftp.get(remote_path, tmp_path)
                with open(tmp_path, "rb") as f:
                    result["content"] = base64.b64encode(f.read()).decode()
            finally:
                os.unlink(tmp_path)
        self._log.info(f"Downloaded {remote_path}")
        return result

    def list_directory(self, path: str = ".") -> List[Dict[str, Any]]:
        """
        List directory contents with file info.

        Args:
            path: Directory path to list.
        Returns:
            List of file info dicts.
        """
        items = []
        for attr in self._sftp.listdir_attr(path):
            items.append({
                "name": attr.filename,
                "size": attr.st_size,
                "mode": attr.st_mode,
                "is_dir": bool(attr.st_mode & 0o40000),
                "mtime": attr.st_mtime
            })
        return items

    def mkdir(self, path: str, mode: int = 0o755) -> Dict[str, str]:
        """
        Create directory on server.

        Args:
            path: Directory path to create.
            mode: Permission mode.
        Returns:
            Status dict.
        """
        self._sftp.mkdir(path, mode)
        return {"status": "created", "path": path}

    def remove(self, path: str) -> Dict[str, str]:
        """
        Remove file from server.

        Args:
            path: File path to remove.
        Returns:
            Status dict.
        """
        self._sftp.remove(path)
        return {"status": "removed", "path": path}

    def rmdir(self, path: str) -> Dict[str, str]:
        """
        Remove directory from server.

        Args:
            path: Directory path to remove.
        Returns:
            Status dict.
        """
        self._sftp.rmdir(path)
        return {"status": "removed", "path": path}

    def rename(self, old_path: str, new_path: str) -> Dict[str, str]:
        """
        Rename file or directory.

        Args:
            old_path: Current path.
            new_path: New path.
        Returns:
            Status dict.
        """
        self._sftp.rename(old_path, new_path)
        return {"status": "renamed", "old": old_path, "new": new_path}

    def stat(self, path: str) -> Dict[str, Any]:
        """
        Get file statistics.

        Args:
            path: File path.
        Returns:
            File stat dict.
        """
        attr = self._sftp.stat(path)
        return {
            "size": attr.st_size,
            "mode": attr.st_mode,
            "uid": attr.st_uid,
            "gid": attr.st_gid,
            "atime": attr.st_atime,
            "mtime": attr.st_mtime
        }

    def read_file(self, path: str) -> str:
        """
        Read file content as text.

        Args:
            path: Remote file path.
        Returns:
            File content string.
        """
        with self._sftp.open(path, "r") as f:
            return f.read()

    def write_file(self, path: str, content: str, mode: str = "overwrite") -> Dict[str, Any]:
        """
        Write content to file.

        Args:
            path: Remote file path.
            content: Content to write.
            mode: overwrite, append, or prepend.
        Returns:
            Status dict.
        """
        if mode == "append":
            with self._sftp.open(path, "a") as f:
                f.write(content)
        elif mode == "prepend":
            existing = ""
            try:
                existing = self.read_file(path)
            except Exception:
                pass
            with self._sftp.open(path, "w") as f:
                f.write(content + existing)
        else:
            with self._sftp.open(path, "w") as f:
                f.write(content)

        stat = self._sftp.stat(path)
        return {"status": "written", "path": path, "size": stat.st_size, "mode": mode}

    def copy_recursive(self, src: str, dst: str) -> Dict[str, Any]:
        """
        Copy directory recursively.

        Args:
            src: Source path.
            dst: Destination path.
        Returns:
            Status dict with count.
        """
        count = 0
        try:
            self._sftp.mkdir(dst)
        except Exception:
            pass

        for item in self._sftp.listdir_attr(src):
            src_path = f"{src}/{item.filename}"
            dst_path = f"{dst}/{item.filename}"
            if item.st_mode & 0o40000:
                result = self.copy_recursive(src_path, dst_path)
                count += result["count"]
            else:
                with self._sftp.open(src_path, "rb") as sf:
                    with self._sftp.open(dst_path, "wb") as df:
                        df.write(sf.read())
                count += 1
        return {"status": "copied", "source": src, "destination": dst, "count": count}

    def rmdir_recursive(self, path: str) -> Dict[str, Any]:
        """
        Remove directory recursively.

        Args:
            path: Directory path.
        Returns:
            Status dict with count.
        """
        count = 0
        for item in self._sftp.listdir_attr(path):
            item_path = f"{path}/{item.filename}"
            if item.st_mode & 0o40000:
                result = self.rmdir_recursive(item_path)
                count += result["count"]
            else:
                self._sftp.remove(item_path)
                count += 1
        self._sftp.rmdir(path)
        return {"status": "removed", "path": path, "count": count}
