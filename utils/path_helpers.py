# utils/path_helpers.py
"""
Enhanced path management with validation and utility functions.

Provides centralized path management with:
- Memory-efficient frozen dataclass with __slots__
- Path validation and existence checking
- Cleanup utilities
- Size calculation helpers
"""

import os
import shutil
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
from typing import Optional, Set, List, Tuple, Union, Dict
from datetime import datetime, timedelta


@dataclass(frozen=True)
class ProjectPaths:
    """
    Container for all project paths. Frozen to prevent accidental modification.

    This class provides standardized access to project directory paths.
    The root path can be set in three ways (in order of precedence):
    1. Explicitly passed to init()
    2. Through the PROJECT_ROOT environment variable
    3. Derived automatically from the location of this file
    """
    __slots__ = [
        'root', 'config', 'data', 'files', 'generated_payloads',
        'logs', 'output', 'payloads', 'schemas', 'tmp', 'wsdl'
    ]

    root: Path
    config: Path
    data: Path
    files: Path
    generated_payloads: Path
    logs: Path
    output: Path
    payloads: Path
    schemas: Path
    tmp: Path
    wsdl: Path

    @classmethod
    @lru_cache(maxsize=1)
    def init(cls, root_path: Optional[Path] = None) -> 'ProjectPaths':
        """
        Get singleton instance with cached paths.

        Args:
            root_path: Explicit root directory path. If None, defaults to the parent
                      of the directory containing this file, or uses PROJECT_ROOT env var

        Returns:
            ProjectPaths instance with all project directory paths configured

        Raises:
            ValueError: If the root_path (explicit or derived) is not a valid directory
        """
        # Use provided root_path, or fallback to env var, or compute from __file__
        if root_path is None:
            env_root = os.getenv("PROJECT_ROOT")
            if env_root:
                root_path = Path(env_root)
            else:
                root_path = Path(__file__).resolve().parent.parent

        # Validate root_path
        if not root_path.is_dir():
            raise ValueError(f"Invalid root path: {root_path} is not a directory")

        return cls(
            root=root_path,
            config=root_path / "config",
            data=root_path / "data",
            files=root_path / "files",
            generated_payloads=root_path / "generated_payloads",
            logs=root_path / "logs",
            output=root_path / "output",
            payloads=root_path / "payloads",
            schemas=root_path / "schemas",
            tmp=root_path / "tmp",
            wsdl=root_path / "wsdl"
        )

    def ensure_dirs(self, skip_dirs: Optional[Set[str]] = None) -> List[str]:
        """
        Create all project directories if they don't exist.

        Args:
            skip_dirs: Set of directory names to skip creating

        Returns:
            List of directory names that were created

        Raises:
            OSError: If directory creation fails due to permissions
        """
        skip_dirs = skip_dirs or set()
        created_dirs = []

        for attr_name in self.__slots__:
            if attr_name == 'root' or attr_name in skip_dirs:
                continue

            path = getattr(self, attr_name)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(attr_name)
                except OSError as e:
                    raise OSError(f"Failed to create directory {path}: {e}")

        return created_dirs

    def validate_structure(self) -> Tuple[List[str], List[str]]:
        """
        Validate that all expected directories exist.

        Returns:
            Tuple of (existing_dirs, missing_dirs)
        """
        existing = []
        missing = []

        for attr_name in self.__slots__:
            if attr_name == 'root':
                continue

            path = getattr(self, attr_name)
            if path.exists():
                existing.append(attr_name)
            else:
                missing.append(attr_name)

        return existing, missing

    def get_dir_sizes(self) -> Dict[str, int]:
        """
        Get the size of each directory in bytes.

        Returns:
            Dictionary mapping directory names to sizes in bytes
        """
        sizes = {}

        for attr_name in self.__slots__:
            path = getattr(self, attr_name)
            if path.exists() and path.is_dir():
                size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                sizes[attr_name] = size

        return sizes


def get_path(category: str, filename: str, ensure_parent: bool = True) -> Path:
    """
    Get the full path for a file in a specified category directory.

    Args:
        category: Directory category (e.g., "logs", "config", "data")
        filename: Target filename (e.g., "config.json")
        ensure_parent: If True, create the parent directory if it doesn't exist

    Returns:
        The full path to the file

    Raises:
        ValueError: If the category is not a valid ProjectPaths attribute
        OSError: If directory creation fails when ensure_parent is True

    Example:
         config_path = get_path('config', 'app-config.json')
         log_path = get_path('logs', 'app.log')
    """
    paths = ProjectPaths.init()

    # Get all valid Path attributes from ProjectPaths
    valid_categories = set(paths.__slots__) - {'root'}

    if category not in valid_categories:
        # Try common variations (singular/plural)
        if category == 'log' and 'logs' in valid_categories:
            category = 'logs'
        elif category == 'file' and 'files' in valid_categories:
            category = 'files'
        elif category == 'schema' and 'schemas' in valid_categories:
            category = 'schemas'
        elif category == 'payload' and 'payloads' in valid_categories:
            category = 'payloads'
        else:
            raise ValueError(
                f"Invalid category '{category}'. Must be one of: {', '.join(sorted(valid_categories))}"
            )

    path = getattr(paths, category) / filename

    if ensure_parent:
        path.parent.mkdir(exist_ok=True, parents=True)

    return path


def set_project_root(path: Union[str, Path]) -> None:
    """
    Set the project root path for the application.

    Args:
        path: The path to set as the project root

    Raises:
        ValueError: If the path doesn't exist or isn't a directory

    Example:
         set_project_root('/path/to/project')
         config_file = get_path('config', 'settings.json')
    """
    root_path = Path(path) if isinstance(path, str) else path

    if not root_path.exists() or not root_path.is_dir():
        raise ValueError(f"Invalid project root: {root_path} (must be an existing directory)")

    # Clear the lru_cache to force reinitialization with the new path
    ProjectPaths.init.cache_clear()

    # Initialize with the new path
    ProjectPaths.init(root_path)


def get_project_root() -> Path:
    """
    Get the current project root path.

    Returns:
        The project root Path
    """
    return ProjectPaths.init().root


def cleanup_old_files(category: str, days: int = 30,
                      pattern: str = "*", dry_run: bool = False) -> List[Path]:
    """
    Clean up old files from a category directory.

    Args:
        category: Directory category to clean
        days: Delete files older than this many days
        pattern: File pattern to match (default: "*")
        dry_run: If True, only report what would be deleted

    Returns:
        List of deleted (or would-be deleted) file paths

    Example:
         # Delete logs older than 7 days
         deleted = cleanup_old_files('logs', days=7, pattern="*.log")
    """
    paths = ProjectPaths.init()

    if not hasattr(paths, category):
        raise ValueError(f"Invalid category: {category}")

    directory = getattr(paths, category)
    if not directory.exists():
        return []

    cutoff_time = datetime.now() - timedelta(days=days)
    deleted_files = []

    for file_path in directory.glob(pattern):
        if file_path.is_file():
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mtime < cutoff_time:
                deleted_files.append(file_path)
                if not dry_run:
                    try:
                        file_path.unlink()
                    except OSError:
                        # Continue processing other files
                        pass

    return deleted_files


def cleanup_tmp(max_age_hours: int = 24) -> int:
    """
    Clean up temporary files older than specified hours.

    Args:
        max_age_hours: Maximum age of tmp files in hours

    Returns:
        Number of files deleted
    """
    paths = ProjectPaths.init()
    tmp_dir = paths.tmp

    if not tmp_dir.exists():
        return 0

    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    deleted_count = 0

    for item in tmp_dir.iterdir():
        try:
            item_mtime = datetime.fromtimestamp(item.stat().st_mtime)
            if item_mtime < cutoff_time:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
                deleted_count += 1
        except OSError:
            # Continue with other items
            pass

    return deleted_count


def get_dir_size(category: str, human_readable: bool = True) -> Union[str, int]:
    """
    Get the total size of a category directory.

    Args:
        category: Directory category
        human_readable: If True, return formatted string, else bytes

    Returns:
        Directory size as formatted string or integer bytes

    Example:
         size = get_dir_size('output', human_readable=True)
         print(f"Output directory size: {size}")
    """
    paths = ProjectPaths.init()

    if not hasattr(paths, category):
        raise ValueError(f"Invalid category: {category}")

    directory = getattr(paths, category)
    if not directory.exists():
        return "0 B" if human_readable else 0

    total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())

    if not human_readable:
        return total_size

    # Format as human-readable
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if total_size < 1024.0:
            return f"{total_size:.2f} {unit}"
        total_size /= 1024.0

    return f"{total_size:.2f} PB"


def list_files(category: str, pattern: str = "*",
               recursive: bool = False) -> List[Path]:
    """
    List files in a category directory.

    Args:
        category: Directory category
        pattern: File pattern to match
        recursive: If True, search recursively

    Returns:
        List of file paths matching the pattern

    Example:
         json_files = list_files('config', pattern="*.json")
    """
    paths = ProjectPaths.init()

    if not hasattr(paths, category):
        raise ValueError(f"Invalid category: {category}")

    directory = getattr(paths, category)
    if not directory.exists():
        return []

    if recursive:
        return sorted([f for f in directory.rglob(pattern) if f.is_file()])
    else:
        return sorted([f for f in directory.glob(pattern) if f.is_file()])


def ensure_file_backup(category: str, filename: str, max_backups: int = 5) -> Optional[Path]:
    """
    Create a backup of a file before overwriting it.

    Args:
        category: Directory category
        filename: File to backup
        max_backups: Maximum number of backups to keep

    Returns:
        Path to backup file if created, None if file doesn't exist

    Example:
         backup_path = ensure_file_backup('config', 'settings.json')
    """
    original_path = get_path(category, filename, ensure_parent=False)

    if not original_path.exists():
        return None

    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{original_path.stem}_backup_{timestamp}{original_path.suffix}"
    backup_path = original_path.parent / backup_name

    # Copy file to backup
    try:
        shutil.copy2(original_path, backup_path)

        # Clean up old backups
        backup_pattern = f"{original_path.stem}_backup_*{original_path.suffix}"
        backups = sorted(original_path.parent.glob(backup_pattern))

        if len(backups) > max_backups:
            for old_backup in backups[:-max_backups]:
                old_backup.unlink()

        return backup_path

    except OSError as e:
        raise OSError(f"Failed to create backup of {original_path}: {e}")