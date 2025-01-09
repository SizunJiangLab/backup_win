# %%
import hashlib
import logging
import os
import subprocess
from pathlib import Path

import pandas as pd
from tqdm import tqdm

################################################################################
# Logging
################################################################################


def setup_logging(
    log_file=os.path.join(os.getcwd(), "output.log"),
    log_format="%(asctime)s - %(levelname)s - %(message)s",
    log_mode="w",
    logger_level=logging.INFO,
    file_handler_level=logging.INFO,
    stream_handler_level=logging.WARNING,
):
    """
    Configures logging to output messages to both a file and the console.

    Parameter
    ---------
    log_file : str, optional
        Path to the log file. Default is 'output.log' in the current working directory.
    log_format : str, optional
        Format for log messages. Default includes timestamp, log level, and message.
    log_mode : str, optional
        File mode for the log file. Default is 'w' (write mode, overwrites file).
    logger_level : int, optional
        Logging level for the root logger. Default is logging.WARNING.
    file_handler_level : int, optional
        Logging level for the FileHandler. Default is logging.INFO.
    stream_handler_level : int, optional
        Logging level for the StreamHandler (console output). Default is logging.WARNING.

    Return
    -------
    None
        This function configures the logger and does not return any value.

    Notes
    -----
    - The logger level controls the global filtering of messages.
    - The FileHandler writes log messages to a file.
    - The StreamHandler displays log messages in the console.
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logger_level)

    # Create a FileHandler for writing logs to a file
    file_handler = logging.FileHandler(log_file, mode=log_mode)
    file_handler.setLevel(file_handler_level)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Create a StreamHandler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_handler_level)
    stream_handler.setFormatter(logging.Formatter(log_format))

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Optional: Print confirmation to the console
    print(f"Logging is configured. Logs are saved to: {log_file}.")


################################################################################
# SFTP download
################################################################################


def sftp_get_list_of_files(
    sftp, dir_remote: str, pb_desc: str = "Finding files"
) -> list[str]:
    """
    Walks remote directory tree and returns list of files.

    Parameter
    ---------
    sftp : paramiko.SFTPClient
        An active SFTP client connection.
    dir_remote : str
        Path of the remote directory to walk.

    Return
    ------
    list of str
        List of file paths in the remote directory.
    """

    def progress_callback(file_path):
        files.append(file_path)
        progress.update(1)  # Update the progress bar for each file

    def do_nothing(*args, **kwargs):
        pass

    files = []
    progress = tqdm(desc=pb_desc, unit=" file", leave=True)
    sftp.walktree(
        dir_remote,
        fcallback=progress_callback,
        dcallback=do_nothing,
        ucallback=do_nothing,
    )
    progress.close()

    return files


def sftp_download_file(sftp, file_remote: str, file_local: str) -> None:
    """
    Download a single file from SFTP server to local.

    Parameter
    ---------
    sftp : paramiko.SFTPClient
        An active SFTP client connection.
    file_remote : str
        Path of the file on the remote server.
    file_local : str
        Path to save the file locally.
    """
    try:
        sftp.get(file_remote, file_local)
        logging.info(f"Downloaded {file_remote} to {file_local}")
    except Exception as e:
        logging.error(f"Failed to download {file_remote}: {e}")


################################################################################
# MD5 checksum
################################################################################


def calculate_md5_md5sum(input_file: str) -> str:
    """
    Calculate the MD5 checksum of a file using the md5sum command.

    Parameter
    ---------
    input_file : str
        The path to the file to calculate the MD5 checksum for.

    Return
    ------
    str
        The MD5 checksum of the file.
    """
    result = subprocess.run(
        ["md5sum", str(input_file)], text=True, capture_output=True, check=True
    )
    return result.stdout.split()[0]


def calculate_md5_hashlib(input_file: str) -> str:
    """
    Calculate the MD5 checksum of a file using the hashlib library.

    Parameter
    ---------
    input_file : str
        The path to the file to calculate the MD5 checksum for.

    Return
    ------
    str
        The MD5 checksum of the file.
    """
    hash_md5 = hashlib.md5()
    with open(input_file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def calculate_md5_md5sum_batch(
    path: str,
    pb_desc: str = "Calculating MD5 checksums",
) -> dict:
    """
    Calculate the MD5 checksums of file(s) using the `md5sum` command.

    Parameter
    ---------
    path : str
        The path to the file or directory to calculate the MD5 checksums for.
    pb_desc : str, optional
        Description for the tqdm progress bar.
        Default is "Calculating MD5 checksums".

    Return
    ------
    dict
        A dictionary containing the relative file paths as keys and MD5
        checksums as values.

    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Path '{path}' not found.")

    if path.is_file():
        path_files = [path]
    elif path.is_dir():
        path_files = [path_file for path_file in path.rglob("*") if path_file.is_file()]

    md5_dict = {}
    for path_file in tqdm(path_files, desc=pb_desc):
        try:
            md5_checksum = calculate_md5_md5sum(path_file)
            md5_dict[str(path_file.relative_to(path))] = md5_checksum
        except Exception as e:
            logging.error(f"{str(path_file.relative_to(path))}: {e}")
            continue
    return md5_dict


def write_md5_from_dict(md5_dict: dict, output_file: str) -> None:
    """
    Write MD5 checksums from a dictionary to a file in `md5sum` format.

    Parameter
    ----------
    md5_dict : dict
        A dictionary containing the paths as keys and MD5 checksums as values.
    output_file : str
        The path to the file where the MD5 checksums will be saved.

    Return
    ------
    None

    Notes
    -----
    - Each line in the output file have the format: <md5_checksum>  <file_path>.
    """
    output_path = Path(output_file)

    with output_path.open("w", encoding="utf-8") as f_out:
        for file_path, md5_checksum in md5_dict.items():
            f_out.write(f"{md5_checksum}  {file_path}\n")


def compare_md5(md5_file_1: str, md5_file_2: str, output_dir: str) -> bool:
    """
    Compare two MD5 checksum files and log any differences.

    Parameter
    ---------
    md5_file_1 : str
        Path to the first MD5 checksum file.
    md5_file_2 : str
        Path to the second MD5 checksum file.
    output_dir : str
        Path to the directory where the output files will be saved.

    Return
    ------
    bool
        True if all MD5 checksums match, False otherwise.
    """

    def read_md5_file(md5_file: str) -> pd.DataFrame:
        data = []
        with open(md5_file, "r", encoding="utf-8") as f:
            for line in f:
                md5, file = line.split("  ", 1)
                data.append({"md5": md5.strip(), "file": file.strip()})
        return pd.DataFrame(data)

    output_dir = Path(output_dir)
    output_md5 = output_dir / "md5sum.csv"
    output_diff = output_dir / "md5sum_diff.csv"
    output_dir.mkdir(parents=True, exist_ok=True)

    df_1 = read_md5_file(md5_file_1).rename(columns={"md5": "md5_1"})
    df_2 = read_md5_file(md5_file_2).rename(columns={"md5": "md5_2"})

    df_md5 = df_1.merge(df_2, on="file", how="outer")[["file", "md5_1", "md5_2"]]
    df_md5.to_csv(output_md5, index=False)

    df_md5_diff = df_md5[df_md5["md5_1"] != df_md5["md5_2"]]
    df_md5_diff.to_csv(output_diff, index=False)

    if not df_md5_diff.empty:
        print("Integrity test failed. See the log file for details.")
        for _, row in df_md5_diff.iterrows():
            logging.error(f"{row['file']}: MD5 checksums do not match.")
        return False
    else:
        print("Integrity test passed. All MD5 checksums match.")
        logging.info("Integrity test passed. All MD5 checksums match.")
        return True
