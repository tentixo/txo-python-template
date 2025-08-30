# utils/load_n_save.py
"""
Enhanced data handler with lazy imports and memory optimizations.

Provides efficient file I/O with:
- Lazy loading of heavy dependencies (pandas, openpyxl)
- Memory-efficient operations
- Comprehensive error handling
- Support for multiple file formats
"""

import json
import os
import gzip
from typing import Union, Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal
from pathlib import Path

from utils.logger import setup_logger
from utils.path_helpers import get_path
from utils.exceptions import FileOperationError

# Type checking imports (not loaded at runtime)
if TYPE_CHECKING:
    import pandas as pd

logger = setup_logger()


class DecimalEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles Decimal objects.

    Converts Decimal to float for JSON serialization.
    """

    def default(self, obj):
        """Convert Decimal to float, pass others to default encoder."""
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class TxoDataHandler:
    """
    Utility class for loading and saving various data formats.

    Features:
    - Lazy loading of pandas and openpyxl (only when needed)
    - Support for JSON, Excel, CSV, binary, and GZip files
    - Automatic Decimal serialization for JSON
    - Consistent error handling and logging
    - Memory-efficient operations
    """

    # Class-level cache for imported modules (lazy loading)
    _pandas: Optional[Any] = None
    _openpyxl: Optional[Any] = None

    @classmethod
    def _get_pandas(cls):
        """Lazy import of pandas - only loaded when needed."""
        if cls._pandas is None:
            logger.debug("Lazy loading pandas module")
            try:
                import pandas as pd_module
                cls._pandas = pd_module
            except ImportError as e:
                logger.error("pandas not installed. Install with: pip install pandas openpyxl")
                raise ImportError("pandas is required for Excel operations") from e
        return cls._pandas

    @classmethod
    def _get_openpyxl(cls):
        """Lazy import of openpyxl - only loaded when needed."""
        if cls._openpyxl is None:
            logger.debug("Lazy loading openpyxl module")
            try:
                import openpyxl
                cls._openpyxl = openpyxl
            except ImportError as e:
                logger.error("openpyxl not installed. Install with: pip install openpyxl")
                raise ImportError("openpyxl is required for Excel operations") from e
        return cls._openpyxl

    @staticmethod
    def load_mapping_sheet(localization_code: str, sheet_name: str,
                           version: str, org_id: str, env_type: str):
        """
        Load the mapping sheet from the Excel file for a given localization and version.

        The file is expected to be named:
        {org_id}-{env_type}-BC_Config-mapping_{localization_code}_v{version}.xlsx

        Args:
            localization_code: Localization code (e.g., 'FR', 'SE')
            sheet_name: The name of the sheet to load from the Excel file
            version: The version to load (e.g., '26.1', '26.2')
            org_id: Organization ID (from arg)
            env_type: Environment type (e.g., 'test', 'prod')

        Returns:
            pd.DataFrame: The loaded mapping sheet as a DataFrame

        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the sheet doesn't exist in the file
            Exception: If loading fails for any other reason
        """
        _logger = setup_logger()

        filename = f"{org_id}-{env_type}-BC_Config-mapping_{localization_code}_v{version}.xlsx"
        _logger.info(f"Loading mapping sheet '{sheet_name}' from file: {filename}")

        try:
            df = TxoDataHandler.load_excel("data", filename, sheet_name=sheet_name)
            # Use lazy pandas reference - fixed shadowing issue
            df = df.astype(object)  # Ensure all columns are objects
            _logger.debug(f"Mapping sheet '{sheet_name}' loaded with {len(df)} rows.")
            return df
        except Exception as e:
            _logger.error(f"Failed to load mapping sheet from {filename}: {e}")
            raise

    @staticmethod
    def load_json(directory: str, filename: str) -> Union[Dict[str, Any], list]:
        """
        Load a JSON file from the specified directory.

        Args:
            directory: The category directory (e.g., "config", "schemas")
            filename: The name of the JSON file to load

        Returns:
            The parsed JSON data as a dictionary or list

        Raises:
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the JSON is invalid
            PermissionError: If access to the file is denied
        """
        file_path: Path = get_path(directory, filename)
        logger.debug(f"Loading JSON from {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Cannot load JSON: {file_path} does not exist") from e
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            raise
        except PermissionError as e:
            logger.error(f"Permission denied accessing {file_path}: {e}")
            raise PermissionError(f"Cannot load JSON: Permission denied for {file_path}") from e

    @staticmethod
    def load_excel(directory: str, filename: str,
                   sheet_name: Union[str, int] = 0,
                   skip_rows: int = 0,
                   usecols: Optional[list] = None,
                   nrows: Optional[int] = None) -> 'pd.DataFrame':
        """
        Load an Excel file from the specified directory with lazy pandas import.

        Args:
            directory: The category directory (e.g., "data")
            filename: The name of the Excel file to load
            sheet_name: The sheet to load, either by name or index (default: 0)
            skip_rows: Number of rows to skip from the beginning (default: 0)
            usecols: Columns to load (for memory efficiency)
            nrows: Number of rows to read (for memory efficiency)

        Returns:
            The loaded Excel data as a pandas DataFrame

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the sheet_name is invalid or the file is corrupted
            PermissionError: If access to the file is denied
        """
        file_path: Path = get_path(directory, filename)
        logger.debug(f"Loading Excel from {file_path}")

        # Verify file extension
        if not filename.lower().endswith(('.xlsx', '.xls')):
            logger.warning(f"File {filename} doesn't have an Excel extension (.xlsx or .xls)")

        # Lazy import pandas
        pd_module = TxoDataHandler._get_pandas()

        try:
            # Use memory-efficient parameters
            return pd_module.read_excel(
                file_path,
                sheet_name=sheet_name,
                skiprows=skip_rows,
                usecols=usecols,
                nrows=nrows,
                engine='openpyxl'
            )
        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Cannot load Excel: {file_path} does not exist") from e
        except ValueError as e:
            logger.error(f"Invalid Excel file or sheet in {file_path}: {e}")
            raise ValueError(f"Cannot load Excel: Invalid file or sheet in {file_path}") from e
        except PermissionError as e:
            logger.error(f"Permission denied accessing {file_path}: {e}")
            raise PermissionError(f"Cannot load Excel: Permission denied for {file_path}") from e

    @staticmethod
    def load_csv(directory: str, filename: str,
                 encoding: str = 'utf-8',
                 delimiter: str = ',',
                 usecols: Optional[list] = None,
                 nrows: Optional[int] = None,
                 chunksize: Optional[int] = None) -> Union['pd.DataFrame', Any]:
        """
        Load a CSV file with memory-efficient options.

        Args:
            directory: The category directory
            filename: The name of the CSV file
            encoding: File encoding (default: utf-8)
            delimiter: Column delimiter (default: comma)
            usecols: Columns to load (for memory efficiency)
            nrows: Number of rows to read
            chunksize: Return iterator for processing large files in chunks

        Returns:
            DataFrame or iterator if chunksize is specified

        Raises:
            FileNotFoundError: If the file does not exist
        """
        file_path: Path = get_path(directory, filename)
        logger.debug(f"Loading CSV from {file_path}")

        # Lazy import pandas
        pd_module = TxoDataHandler._get_pandas()

        try:
            return pd_module.read_csv(
                file_path,
                encoding=encoding,
                delimiter=delimiter,
                usecols=usecols,
                nrows=nrows,
                chunksize=chunksize
            )
        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Cannot load CSV: {file_path} does not exist") from e
        except Exception as e:
            logger.error(f"Error loading CSV {file_path}: {e}")
            raise

    @staticmethod
    def load_package(directory: str, filename: str) -> bytes:
        """
        Load a binary package file (e.g., RapidStart).

        Args:
            directory: The category directory (e.g., "files")
            filename: The name of the package file to load

        Returns:
            The binary content of the package file

        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If access to the file is denied
        """
        file_path: Path = get_path(directory, filename)
        logger.debug(f"Loading package from {file_path}")

        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Cannot load package: {file_path} does not exist") from e
        except PermissionError as e:
            logger.error(f"Permission denied accessing {file_path}: {e}")
            raise PermissionError(f"Cannot load package: Permission denied for {file_path}") from e

    @staticmethod
    def load_gzip(directory: str, filename: str) -> bytes:
        """
        Load and decompress a GZip file.

        Args:
            directory: The category directory
            filename: The name of the GZip file to load

        Returns:
            The decompressed content

        Raises:
            FileOperationError: If the file cannot be loaded or decompressed
        """
        file_path: Path = get_path(directory, filename)
        logger.debug(f"Loading GZip file from {file_path}")

        try:
            with gzip.open(file_path, 'rb') as gz_file:
                content = gz_file.read()
                logger.info(f"Loaded and decompressed {file_path} ({len(content):,} bytes)")
                return content
        except FileNotFoundError as e:
            logger.error(f"GZip file not found: {file_path}")
            raise FileOperationError(f"Cannot load GZip file: {file_path} does not exist",
                                     str(file_path)) from e
        except gzip.BadGzipFile as e:
            logger.error(f"Invalid GZip file: {file_path}")
            raise FileOperationError(f"Invalid GZip file: {file_path}", str(file_path)) from e
        except Exception as e:
            logger.error(f"Failed to load GZip file {file_path}: {e}")
            raise FileOperationError(f"Failed to load GZip file: {e}", str(file_path)) from e

    @staticmethod
    def save(data: Union[Dict, list, 'pd.DataFrame', str, Any],
             directory: str, filename: str,
             **kwargs) -> Path:
        """
        Save data to a file in the specified directory.

        Args:
            data: The data to save (JSON-serializable dict/list, DataFrame,
                  plain string, or openpyxl Workbook)
            directory: The category directory (e.g., "output", "payloads")
            filename: The name of the file to save
            **kwargs: Additional arguments for specific save methods
                      (e.g., index=False for DataFrames)

        Returns:
            The path to the saved file

        Raises:
            TypeError: If the data type is unsupported
            PermissionError: If writing to the file is not allowed
            IOError: If there's an issue writing to the file system
        """
        file_path: Path = get_path(directory, filename)
        logger.info(f"Saving to {file_path}")

        # Validate file extension matches data type
        is_correct_extension = TxoDataHandler._validate_extension(data, filename)
        if not is_correct_extension:
            logger.warning(f"File extension of {filename} may not match data type")

        try:
            # Check if it's a pandas DataFrame (without importing pandas)
            if hasattr(data, 'to_csv') and hasattr(data, 'to_excel'):
                file_ext = file_path.suffix.lower()
                if file_ext == '.csv':
                    # Use kwargs for CSV options
                    index = kwargs.get('index', False)
                    data.to_csv(file_path, index=index)
                else:
                    # Use kwargs for Excel options
                    index = kwargs.get('index', False)
                    sheet_name = kwargs.get('sheet_name', 'Sheet1')
                    data.to_excel(file_path, index=index,
                                  sheet_name=sheet_name, engine='openpyxl')

            elif isinstance(data, (dict, list)):
                # Use DecimalEncoder to handle Decimal objects
                indent = kwargs.get('indent', 2)
                ensure_ascii = kwargs.get('ensure_ascii', False)
                json_content = json.dumps(data, indent=indent,
                                          ensure_ascii=ensure_ascii,
                                          cls=DecimalEncoder)
                file_path.write_text(json_content, encoding='utf-8')

            elif isinstance(data, str):
                encoding = kwargs.get('encoding', 'utf-8')
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(data)

            elif hasattr(data, 'save') and callable(data.save):
                # Handle openpyxl Workbook objects - Fixed: removed str() wrapper
                data.save(file_path)

            else:
                type_name = type(data).__name__
                raise TypeError(
                    f"Unsupported data type: {type_name}. Expected dict, list, "
                    f"DataFrame, str, or object with save method."
                )

            return file_path

        except PermissionError as e:
            logger.error(f"Permission denied saving to {file_path}: {e}")
            raise PermissionError(f"Cannot save data: Permission denied for {file_path}") from e
        except IOError as e:
            logger.error(f"IO error saving to {file_path}: {e}")
            raise IOError(f"Cannot save data: IO error for {file_path}") from e
        except TypeError as e:
            logger.error(f"Type error saving {file_path}: {e}")
            raise

    @staticmethod
    def save_gzip(data: Union[str, bytes], directory: str, filename: str,
                  compression_level: int = 9) -> Path:
        """
        Save data as GZip compressed file.

        Args:
            data: String or bytes to compress
            directory: Output directory
            filename: Output filename (should end with .gz or .rapidstart)
            compression_level: Compression level 0-9 (default: 9 = maximum)

        Returns:
            Path to saved file

        Raises:
            FileOperationError: If the file cannot be saved or compressed
        """
        file_path: Path = get_path(directory, filename)
        logger.info(f"Saving GZip compressed file to {file_path}")

        try:
            # Convert string to bytes if needed
            content = data.encode('utf-8') if isinstance(data, str) else data

            # Write compressed content with specified compression level
            with gzip.open(file_path, 'wb', compresslevel=compression_level) as gz_file:
                gz_file.write(content)

            # Log compression stats
            original_size = len(content)
            compressed_size = file_path.stat().st_size
            ratio = (compressed_size / original_size * 100) if original_size > 0 else 0
            logger.info(f"Compressed {original_size:,} bytes to {compressed_size:,} bytes "
                        f"({ratio:.1f}%, level={compression_level})")

            return file_path

        except Exception as e:
            logger.error(f"Failed to save GZip file {file_path}: {e}")
            raise FileOperationError(f"Failed to save GZip file: {e}", str(file_path)) from e

    @staticmethod
    def _validate_extension(data: Any, filename: str) -> bool:
        """
        Validate that the file extension matches the data type.

        Args:
            data: The data being saved
            filename: The filename with extension

        Returns:
            True if the extension appears to match the data type
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        # Check for pandas DataFrame without importing pandas
        if hasattr(data, 'to_csv') and hasattr(data, 'to_excel'):
            return ext in ('.xlsx', '.xls', '.csv')
        elif isinstance(data, (dict, list)):
            return ext == '.json'
        elif isinstance(data, str):
            # Text files can have many extensions
            return ext not in ('.xlsx', '.xls', '.bin', '.dat', '.pdf')
        elif hasattr(data, 'save') and callable(data.save):
            # For Workbook objects or similar
            return ext in ('.xlsx', '.xlsm', '.xltx', '.xltm')
        else:
            # Can't validate unknown types
            return True

    @staticmethod
    def exists(directory: str, filename: str) -> bool:
        """
        Check if a file exists in the specified directory.

        Args:
            directory: The category directory (e.g., "wsdl")
            filename: The name of the file to check

        Returns:
            True if the file exists, False otherwise
        """
        file_path: Path = get_path(directory, filename)
        logger.debug(f"Checking existence of {file_path}")
        return file_path.exists()

    @staticmethod
    def delete(directory: str, filename: str, safe: bool = True) -> bool:
        """
        Delete a file from the specified directory.

        Args:
            directory: The category directory
            filename: The name of the file to delete
            safe: If True, only delete if file exists (no error if missing)

        Returns:
            True if file was deleted, False if it didn't exist

        Raises:
            PermissionError: If deletion is not allowed
        """
        file_path: Path = get_path(directory, filename)

        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            elif not safe:
                raise FileNotFoundError(f"File not found: {file_path}")
            else:
                logger.debug(f"File already absent: {file_path}")
                return False
        except PermissionError as e:
            logger.error(f"Permission denied deleting {file_path}: {e}")
            raise

    @staticmethod
    def get_size(directory: str, filename: str) -> int:
        """
        Get the size of a file in bytes.

        Args:
            directory: The category directory
            filename: The name of the file

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        file_path: Path = get_path(directory, filename)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        size = file_path.stat().st_size
        logger.debug(f"File {file_path} size: {size:,} bytes")
        return size