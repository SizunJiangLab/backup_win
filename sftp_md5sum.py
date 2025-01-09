# %%
import logging
import os

import pandas as pd
import pysftp
from tqdm import tqdm

from src.utils import (
    calculate_md5_md5sum_batch,
    compare_md5,
    setup_logging,
    sftp_get_list_of_files,
    write_md5_from_dict,
)


def run_sftp_md5sum(name_remote, name_local):
    """
    Download files from SFTP server and compare MD5 checksums.
    """
    # Directories
    ## Remote
    dir_remote = os.path.join("/", name_remote)
    ## Local
    dir_log = "/mnt/nfs/storage/cosmx_log"
    dir_sftp = "/mnt/nfs/storage/cosmx_backup/"
    dir_local_1 = os.path.join(dir_sftp, name_local, "AtoMx")
    dir_local_2 = os.path.join(dir_sftp, name_local, "AtoMx_copy")

    # Logging
    log_file = os.path.join(dir_log, name_local, f"{name_local}.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    setup_logging(
        log_file, file_handler_level=logging.INFO, stream_handler_level=logging.WARNING
    )

    # SFTP
    hostname = "na.export.atomx.nanostring.com"
    username = "sjiang3@bidmc.harvard.edu"
    password = "JiangLab123!"
    # sftp = pysftp.Connection(host=hostname, username=username, password=password)

    with pysftp.Connection(host=hostname, username=username, password=password) as sftp:
        logging.info("Connected to SFTP server.")

        # List all files in the remote directory
        paths_remote = sftp_get_list_of_files(sftp, dir_remote)
        logging.info(f"Found {len(paths_remote)} remote files in {dir_remote}.")
        with open(os.path.join(dir_log, name_local, "paths_remote.txt"), "w") as f:
            f.write("\n".join(paths_remote))

        # Download files to local directories
        ## Create local directories
        relpaths = [os.path.relpath(path, dir_remote) for path in paths_remote]
        paths_local_1 = [os.path.join(dir_local_1, relpath) for relpath in relpaths]
        paths_local_2 = [os.path.join(dir_local_2, relpath) for relpath in relpaths]
        dir_local_unique = set(
            [os.path.dirname(path) for path in paths_local_1 + paths_local_2]
        )
        for dir_local in dir_local_unique:
            os.makedirs(dir_local, exist_ok=True)
        logging.info(f"Local directories created for {name_local}.")

        ## Download
        for i in tqdm(range(len(paths_remote)), desc="Downloading files"):
            sftp.get(paths_remote[i], paths_local_1[i])
            logging.info(f"Downloaded {paths_remote[i]} to AtoMx.")
            sftp.get(paths_remote[i], paths_local_2[i])
            logging.info(f"Downloaded {paths_remote[i]} to AtoMx_copy.")
        logging.info(f"Downloaded all files to local directories for {name_local}.")

    # MD5 comparison
    output_dir = os.path.join(dir_log, name_local, "md5sum")
    os.makedirs(output_dir, exist_ok=True)
    path_md5sum_1 = os.path.join(output_dir, "AtoMx.txt")
    path_md5sum_2 = os.path.join(output_dir, "AtoMx_copy.txt")

    md5_dict_1 = calculate_md5_md5sum_batch(dir_local_1, pb_desc="AtoMx md5sum")
    md5_dict_2 = calculate_md5_md5sum_batch(dir_local_2, pb_desc="AtoMx_copy md5sum")
    write_md5_from_dict(md5_dict_1, path_md5sum_1)
    write_md5_from_dict(md5_dict_2, path_md5sum_2)
    compare_md5(path_md5sum_1, path_md5sum_2, output_dir)


# %%
if __name__ == "__main__":
    df_params = pd.read_csv(
        "/mnt/nfs/home/wenruiwu/projects/backup/data/df_run/shuli.csv"
    )
    for i, row in df_params.iterrows():
        name_remote = row["name_atomx"]
        name_local = row["name_storage"]
        try:
            run_sftp_md5sum(name_remote, name_local)
        except Exception as e:
            logging.error(f"Failed to process {name_local}: {e}")

    # name_remote = "RCC_TMA541_section09_3ug_v132_06_01_2025_18_26_39_743"
    # name_local = "RCC_TMA541_section09_3ug_v132"
    # run_sftp_md5sum(name_remote, name_local)
