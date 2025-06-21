# utils/load_n_save.py
from typing import Union, Dict, Any
import json
import os
import pandas as pd
from openpyxl.workbook import Workbook

from utils.logger import setup_logger
from utils.path_helpers import get_path
from pathlib import Path

logger = setup_logger()


class TxoDataHandler:
    """
    Utility class for loading and saving various data formats.

    This class provides methods to load and save data in different formats,
    including JSON, Excel, and binary files. It handles file paths and error
    reporting in a consistent way.
    """

    @staticmethod
    def load_mapping_sheet(localization_code, sheet_name, config, env_type):
        """
        Load the mapping sheet from the Excel file for a given localization.
        The file is expected to be named: BC_Config-mapping_{localization_code}_v{new_version}.xlsx

        Args:
            localization_code (str): Localization code (e.g., 'FR', 'SE')
            sheet_name (str): The name of the sheet to load from the Excel file
            config (dict): Configuration dictionary containing bc-environments
            env_type (str): Environment type (e.g., 'test', 'prod')

        Returns:
            pd.DataFrame: The loaded mapping sheet as a DataFrame

        Raises:
            KeyError: If new_version not found for the given localization
            Exception: If loading fails for any other reason
        """
        _logger = setup_logger()

        # Get the new_version for the given localization
        new_version = None
        for env in config["bc-environments"][env_type]:
            if env["localization"] == localization_code:
                new_version = env["new_version"]
                break

        if new_version is None:
            error_msg = f"new_version not found for localization '{localization_code}' in env_type '{env_type}'"
            _logger.error(error_msg)
            raise KeyError(error_msg)

        filename = f"BC_Config-mapping_{localization_code}_v{new_version}.xlsx"
        _logger.info(f"Loading mapping sheet '{sheet_name}' from file: {filename}")

        try:
            df = TxoDataHandler.load_excel("data", filename, sheet_name=sheet_name)
            df = df.astype(object)  # Ensure all columns are objects
            _logger.debug(f"Mapping sheet '{sheet_name}' loaded with {len(df)} rows.")
            return df
        except Exception as e:
            _logger.error(f"Failed to load mapping sheet from {filename}: {e}")
            raise

    @staticmethod
    def load_vat_config(org_id: str, env_type: str) -> Dict[str, Any]:
        """
        Load organization and environment specific VAT configuration.

        Args:
            org_id (str): Organization identifier (e.g., 'txo')
            env_type (str): Environment type (e.g., 'test', 'prod')

        Returns:
            Dict[str, Any]: The VAT configuration data
        """
        filename = f"{org_id}-{env_type}-vat-levels.json"
        return TxoDataHandler.load_json("config", filename)  # Note: use class name, not self

    @staticmethod
    def load_json(directory: str, filename: str) -> Union[Dict[str, Any], list]:
        """
        Load a JSON file from the specified directory.

        Args:
            directory (str): The category directory (e.g., "config", "schemas") relative to the project root.
            filename (str): The name of the JSON file to load (e.g., "config.json").

        Returns:
            Union[Dict, list]: The parsed JSON data as a dictionary or list.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the JSON is invalid.
            PermissionError: If access to the file is denied.
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
    def load_excel(directory: str, filename: str, sheet_name: Union[str, int] = 0, skip_rows: int = 0) -> pd.DataFrame:
        """
        Load an Excel file from the specified directory.

        Args:
            directory (str): The category directory (e.g., "data") relative to the project root.
            filename (str): The name of the Excel file to load (e.g., "mapping.xlsx").
            sheet_name (Union[str, int]): The sheet to load, either by name or index (default: 0).
            skip_rows (int): Number of rows to skip from the beginning (default: 0).

        Returns:
            pd.DataFrame: The loaded Excel data as a pandas DataFrame.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the sheet_name is invalid or the file is corrupted.
            PermissionError: If access to the file is denied.
        """
        file_path: Path = get_path(directory, filename)
        logger.debug(f"Loading Excel from {file_path}")

        # Verify file extension
        if not filename.lower().endswith(('.xlsx', '.xls')):
            logger.warning(f"File {filename} doesn't have an Excel extension (.xlsx or .xls)")

        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows, engine='openpyxl')
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
    def load_package(directory: str, filename: str) -> bytes:
        """
        Load a binary package file (e.g., RapidStart) from the specified directory.

        Args:
            directory (str): The category directory (e.g., "files") relative to the project root.
            filename (str): The name of the package file to load (e.g., "PackageTXO-CMN-ESS_9-PV25.0.rapidstart").

        Returns:
            bytes: The binary content of the package file.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If access to the file is denied.
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
    def save(data: Union[Dict, list, pd.DataFrame, str, Workbook], directory: str, filename: str) -> Path:
        """
        Save data to a file in the specified directory.

        Args:
            data (Union[Dict, list, pd.DataFrame, str, Workbook]): The data to save (JSON-serializable dict/list,
                DataFrame, plain string, or openpyxl Workbook).
            directory (str): The category directory (e.g., "output", "payloads") relative to the project root.
            filename (str): The name of the file to save (e.g., "output.json").

        Returns:
            Path: The path to the saved file.

        Raises:
            TypeError: If the data type is unsupported.
            PermissionError: If writing to the file is not allowed.
            IOError: If there's an issue writing to the file system.
            ValueError: If the filename extension doesn't match the data type.
        """
        file_path: Path = get_path(directory, filename)
        logger.info(f"Saving to {file_path}")

        # Validate file extension matches data type
        is_correct_extension = TxoDataHandler._validate_extension(data, filename)
        if not is_correct_extension:
            logger.warning(f"File extension of {filename} may not match data type")

        try:
            if isinstance(data, pd.DataFrame):
                file_ext = file_path.suffix.lower()
                if file_ext == '.csv':
                    data.to_csv(file_path, index=False)
                else:
                    data.to_excel(file_path, index=False, engine='openpyxl')
            elif isinstance(data, (dict, list)):
                # Use write_text instead of open to avoid type hint issues with json.dump
                json_content = json.dumps(data, indent=2, ensure_ascii=False)
                file_path.write_text(json_content, encoding='utf-8')
            elif isinstance(data, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(data)
            elif isinstance(data, Workbook):
                # Handle openpyxl Workbook objects specifically
                data.save(str(file_path))
            else:
                type_name = type(data).__name__
                raise TypeError(
                    f"Unsupported data type: {type_name}. Expected dict, list, DataFrame, str, or object with save method.")

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
    def _validate_extension(data: Any, filename: str) -> bool:
        """
        Validate that the file extension matches the data type.

        Args:
            data: The data being saved
            filename: The filename with extension

        Returns:
            bool: True if the extension appears to match the data type, False otherwise
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if isinstance(data, pd.DataFrame):
            return ext in ('.xlsx', '.xls', '.csv')
        elif isinstance(data, (dict, list)):
            return ext == '.json'
        elif isinstance(data, str):
            # Text files can have many extensions, so just check if it's not binary
            return ext not in ('.xlsx', '.xls', '.bin', '.dat', '.pdf')
        elif hasattr(data, 'save') and callable(data.save):
            # For Workbook objects or similar, check for Excel extensions
            return ext in ('.xlsx', '.xlsm', '.xltx', '.xltm')
        else:
            # Can't validate unknown types
            return True