# utils/path_helpers.py
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
import os
from typing import Optional


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
    root: Path
    config: Path
    data: Path
    files: Path
    generated_payloads: Path
    logs: Path
    output: Path
    payloads: Path
    schemas: Path

    @classmethod
    @lru_cache(maxsize=1)
    def init(cls, root_path: Optional[Path] = None) -> 'ProjectPaths':
        """
        Get singleton instance with cached paths.

        Args:
            root_path (Path, optional): Explicit root directory path. If None, defaults to the parent
                of the directory containing this file, or uses the PROJECT_ROOT environment variable
                if set.

        Returns:
            ProjectPaths: An instance with all project directory paths configured.

        Raises:
            ValueError: If the root_path (explicit or derived) is not a valid directory.
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
            schemas=root_path / "schemas"
        )

    def ensure_dirs(self) -> None:
        """
        Create all project directories if they don't exist.

        This ensures that all directories defined in the ProjectPaths instance
        exist on the filesystem and are ready to use.

        Raises:
            OSError: If directory creation fails due to permissions or other system errors.
        """
        for attr_name in dir(self):
            # Skip special methods and non-Path attributes
            if attr_name.startswith('_') or not isinstance(getattr(self, attr_name), Path):
                continue

            path = getattr(self, attr_name)
            if attr_name != 'root':  # Don't try to create the root directory
                path.mkdir(parents=True, exist_ok=True)


def get_path(category: str, filename: str, ensure_parent: bool = True) -> Path:
    """
    Get the full path for a file in a specified category directory.

    Args:
        category (str): Directory category (e.g., "log", "config", "data") matching a ProjectPaths attribute.
        filename (str): Target filename (e.g., "config.json").
        ensure_parent (bool): If True, create the parent directory if it doesn't exist (default: True).

    Returns:
        Path: The full path to the file.

    Raises:
        ValueError: If the category is not a valid ProjectPaths attribute.
        OSError: If directory creation fails when ensure_parent is True.

    Example:
        >>> config_path = get_path('config', 'app-config.json')
        >>> log_path = get_path('log', 'app.log')
    """
    paths = ProjectPaths.init()

    # Get all valid Path attributes from ProjectPaths
    valid_categories = {
        attr for attr in dir(paths)
        if not attr.startswith('_') and isinstance(getattr(paths, attr), Path)
    }

    if category not in valid_categories:
        raise ValueError(
            f"Invalid category '{category}'. Must be one of: {', '.join(sorted(valid_categories))}"
        )

    path = getattr(paths, category) / filename

    if ensure_parent:
        path.parent.mkdir(exist_ok=True, parents=True)

    return path


def set_project_root(path: str or Path) -> None:
    """
    Set the project root path for the application.

    This function can be used to explicitly set the project root before
    any paths are accessed. It clears the cache to ensure the new root
    is used for all subsequent path operations.

    Args:
        path: The path to set as the project root. Can be a string or Path object.

    Raises:
        ValueError: If the path doesn't exist or isn't a directory.

    Example:
        >>> set_project_root('/path/to/project')
        >>> config_file = get_path('config', 'settings.json')
    """
    root_path = Path(path) if isinstance(path, str) else path

    if not root_path.exists() or not root_path.is_dir():
        raise ValueError(f"Invalid project root: {root_path} (must be an existing directory)")

    # Clear the lru_cache to force reinitialization with the new path
    ProjectPaths.init.cache_clear()

    # Initialize with the new path
    ProjectPaths.init(root_path)