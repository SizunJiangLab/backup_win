# %%
import hashlib
import logging
import os
import subprocess
import time
from pathlib import Path

import pandas as pd
from IPython.core.interactiveshell import InteractiveShell
from tqdm import tqdm

InteractiveShell.ast_node_interactivity = "all"

################################################################################
# Basic functions
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


def compare_md5(md5_file_1: str, md5_file_2: str, output_dir: str) -> None:
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
    None
    """

    def read_md5_file(md5_file: str) -> pd.DataFrame:
        data = []
        with open(md5_file, "r", encoding="utf-8") as f:
            for line in f:
                md5, file = line.split("  ", 1)
                data.append({"md5": md5.strip(), "file": file.strip()})
        return pd.DataFrame(data)

    output_dir = Path(output_dir)
    output_log = output_dir / "md5sum.log"
    output_md5 = output_dir / "md5sum.csv"
    output_diff = output_dir / "md5sum_diff.csv"
    output_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(output_log)

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
    else:
        print("Integrity test passed. All MD5 checksums match.")
        logging.info("Integrity test passed. All MD5 checksums match.")


# %%
################################################################################
# Main function
################################################################################


def run_md5_compare(path_1, path_2, output_dir):
    """
    Calculate MD5 checksums for two paths and compare the results.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_1 = output_dir / "md5sum_1.txt"
    output_2 = output_dir / "md5sum_2.txt"

    md5_dict_1 = calculate_md5_md5sum_batch(
        path_1, pb_desc="Calculating MD5 checksums for path 1"
    )
    md5_dict_2 = calculate_md5_md5sum_batch(
        path_2, pb_desc="Calculating MD5 checksums for path 2"
    )

    write_md5_from_dict(md5_dict_1, output_1)
    write_md5_from_dict(md5_dict_2, output_2)

    compare_md5(output_1, output_2, output_dir)


# if __name__ == "__main__":
#     path_1 = "/mnt/nfs/home/wenruiwu/projects/backup/data/test_1"
#     path_2 = "/mnt/nfs/home/wenruiwu/projects/backup/data/test_2"
#     tag = time.strftime("%Y%m%d_%H%M%S")
#     output_dir = f"/mnt/nfs/home/wenruiwu/projects/backup/data/output/{tag}"
#     run_md5_compare(path_1, path_2, output_dir)

if __name__ == "__main__":
    ############################################################################
    cosmx_name = "testname_tmaname_sectionid_version"
    ############################################################################

    dir_cosmx = Path("/mnt/nfs/storage/CosMX") / cosmx_name
    path_1 = dir_cosmx / "AtoMx"
    path_2 = dir_cosmx / "AtoMx_copy"

    if not path_1.exists():
        raise FileNotFoundError("AtoMx not found.")
    if not path_2.exists():
        raise FileNotFoundError("AtoMx_copy not found.")

    tag = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path("/mnt/nfs/storage/cosmx_md5sum") / cosmx_name / tag
    output_dir.mkdir(parents=True, exist_ok=True)

    run_md5_compare(path_1, path_2, output_dir)
