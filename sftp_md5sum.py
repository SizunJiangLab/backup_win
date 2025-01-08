# %%
import logging
import os

import pysftp

from src.utils import (
    calculate_md5_md5sum_batch,
    compare_md5,
    download_folder_2copy,
    setup_logging,
    write_md5_from_dict,
)


def run_sftp_md5sum(name_remote, name_local):
    print(f"Processing: {name_local}")

    # Directories
    dir_log = "/mnt/nfs/storage/cosmx_log"
    dir_sftp = "/mnt/nfs/storage/cosmx_backup/"

    # Logging
    log_file = os.path.join(dir_log, name_local, f"{name_local}.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    setup_logging(
        log_file, file_handler_level=logging.INFO, stream_handler_level=logging.INFO
    )

    # SFTP
    hostname = "na.export.atomx.nanostring.com"
    username = "sjiang3@bidmc.harvard.edu"
    password = "JiangLab123!"

    dir_remote = os.path.join("/", name_remote)
    dir_local_1 = os.path.join(dir_sftp, name_local, "AtoMx")
    dir_local_2 = os.path.join(dir_sftp, name_local, "AtoMx_copy")
    with pysftp.Connection(host=hostname, username=username, password=password) as sftp:
        logging.info("Connected to SFTP server.")
        download_folder_2copy(sftp, dir_remote, dir_local_1, dir_local_2)
        logging.info(f"Download completed for {name_local}.")

    # MD5 comparison
    output_dir = os.path.join(dir_log, name_local, "md5sum")
    os.makedirs(output_dir, exist_ok=True)
    path_md5sum_1 = os.path.join(output_dir, "AtoMx.txt")
    path_md5sum_2 = os.path.join(output_dir, "AtoMx_copy.txt")

    md5_dict_1 = calculate_md5_md5sum_batch(dir_local_1, pb_desc="md5sum for AtoMx")
    md5_dict_2 = calculate_md5_md5sum_batch(
        dir_local_2, pb_desc="md5sum for AtoMx_copy"
    )
    write_md5_from_dict(md5_dict_1, path_md5sum_1)
    write_md5_from_dict(md5_dict_2, path_md5sum_2)
    compare_md5(path_md5sum_1, path_md5sum_2, output_dir)


# %%
if __name__ == "__main__":
    name_remote = "RCC_TMA541_section09_3ug_v132_06_01_2025_18_26_39_743"
    name_local = "RCC_TMA541_section09_3ug_v132"
    run_sftp_md5sum(name_remote, name_local)
