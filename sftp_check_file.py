# %%
import logging
import os
import shutil
from io import StringIO
from pathlib import Path

import pandas as pd
import pysftp
from tqdm import tqdm

from src.utils import (
    setup_logging,
    sftp_get_list_of_files,
)

TQDM_FORMAT = "{desc}: {percentage:3.0f}%|{bar:15}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"


def run_sftp_check_file(name_remote, name_local):
    """
    Double check if all files in the remote directory have been downloaded
    """
    # Directories
    ## Remote
    dir_remote = os.path.join("/", name_remote)
    ## Local
    dir_log = "/mnt/nfs/storage/cosmx_log"
    dir_sftp = "/mnt/nfs/storage/cosmx_backup/"
    dir_local_2 = os.path.join(dir_sftp, name_local, "AtoMx_copy")
    dir_check = Path("/mnt/nfs/storage/cosmx_log/done/check/")
    dir_check_fail = dir_check / "fail"
    dir_check_fail.mkdir(parents=True, exist_ok=True)

    # Logging
    log_file = os.path.join(dir_log, name_local, f"{name_local}_check_file.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    setup_logging(
        log_file, file_handler_level=logging.INFO, stream_handler_level=logging.INFO
    )

    # SFTP
    hostname = "na.export.atomx.nanostring.com"
    username = "sjiang3@bidmc.harvard.edu"
    password = "JiangLab123!"
    # sftp = pysftp.Connection(host=hostname, username=username, password=password)

    with pysftp.Connection(host=hostname, username=username, password=password) as sftp:
        logging.info("Connected to SFTP server.")

        # List all files in the remote directory
        paths_remote = sftp_get_list_of_files(
            sftp, dir_remote, pb_desc=f"{name_local}|Finding"
        )
        logging.info(f"Found {len(paths_remote)} remote files in {dir_remote}.")

    with open(os.path.join(dir_log, name_local, "paths_remote.txt"), "r") as f:
        paths_remote_0 = f.read().splitlines()

    # intersect
    paths_remote_0 = set(paths_remote_0)
    paths_remote = set(paths_remote)
    paths_remote_missing = paths_remote_0 - paths_remote
    if len(paths_remote_missing) > 0:
        with open(os.path.join(dir_check_fail, f"{name_local}"), "w") as f:
            f.write("\n".join(paths_remote_missing))
        logging.warning(f"File list is not complete: {name_local}.")
    else:
        with open(os.path.join(dir_check, f"{name_local}"), "w") as f:
            None
        logging.info(f"File list is complete: {name_local}.")

        shutil.rmtree(dir_local_2)
        logging.info(f"Removed copy: {name_local}.")


# %%

params_str = """
HCC_TMA006_section05_3ug_v132_07_01_2025_22_50_43_116	HCC_TMA006_section05_3ug_v132
HCC_TMA005_section11_3ug_v132_07_01_2025_22_49_15_796	HCC_TMA005_section11_3ug_v132
HCC_TMA005_section09_01ug_v132_07_01_2025_22_39_55_943	HCC_TMA005_section09_0.1ug_v132
HCC_TMA006_section03_01ug_v132_07_01_2025_22_39_30_265	HCC_TMA006_section03_0.1ug_v132
HCC_TMA009_section12_JL_1ug_v132_06_01_2025_22_05_07_243	HCC_TMA009_section12_JL_1ug_v132
HCC_TMA009_section14_JL_3ug_v132_06_01_2025_21_53_35_115	HCC_TMA009_section14_JL_3ug_v132
HCC_TMA001_section10_3ug_v132_07_01_2025_23_37_33_939	HCC_TMA001_section10_3ug_v132
HCC_TMA001_section09_1ug_v132_07_01_2025_22_30_47_739	HCC_TMA001_section09_1ug_v132
INDEPTHJLL_FusionCosMX_section10_v132_10_01_2025_13_55_21_636	INDEPTHJLL_FusionCosMX_section10_v132
INDEPTHJLL_CosMXonly_section11_v132_10_01_2025_13_57_04_37	INDEPTHJLL_CosMXonly_section11_v132
RCC_TMA541_section07_v132_06_01_2025_19_03_26_836	RCC_TMA541_section07_2ug_v132
RCC_TMA541_section09_3ug_v132_06_01_2025_18_26_39_743	RCC_TMA541_section09_3ug_v132
CRC_TMA1_section5_3ug_v132_10_01_2025_15_16_31_811	CRC_TMA1_section5_3ug_v132
CRC_TMA1_2ug_ml_reexport_10_01_2025_14_38_19_196	CRC_TMA1_section7_v132
RCC_TMA542_section5_07_01_2025_20_54_54_932	RCC_TMA542_section05_v132
RCC_TMA543_section5_07_01_2025_20_58_46_40	RCC_TMA543_section05_v132
RCC_TMA544_section5_07_01_2025_20_59_09_162	RCC_TMA544_section05_v132
RCC_TMA609_section5_07_01_2025_20_59_24_146	RCC_TMA609_section05_v132
HL_DLBCL_TMA1_2ugml_08_01_2025_13_58_14_691	DLBCL_TMA001_section06_v132
HL_DLBCL_TMA1_1ugml_08_01_2025_13_58_04_439	DLBCL_TMA001_section04_v132
AH_TMA001_section02_3ug_30min_v132_08_01_2025_0_36_36_602	AH_TMA001_section02_3ug_30min_v132
AH_TMA001_section01_2ug_20min_v132_08_01_2025_0_36_24_760	AH_TMA001_section01_2ug_20min_v132
CRC_TMA2_Section7_10_01_2025_13_49_33_767	CRC_TMA2_section7_v132
CRC_TMA3_Section7_10_01_2025_13_52_33_461	CRC_TMA3_section7_v132
Indepth_EBV_CosMxOnly_v132_13_01_2025_14_03_47_206	Indepth_TMA971_section01_v132
Indepth_EBV_FusionCosMx_v132_13_01_2025_15_34_39_663	Indepth_TMA971_section02_v132
CRC_TMA2_section11_v132_10_01_2025_14_05_52_335	CRC_TMA2_section11_v132
AIH_TMA001_section05_v132_07_01_2025_21_01_17_587	AIH_TMA001_section05_v132
MCV_TMA001_section01_v132_13_01_2025_13_31_18_909	MCV_TMA001_section01_v132
MCV_TMA002_section01_v132_13_01_2025_13_30_24_175	MCV_TMA001_section02_v132
CRC_TMA3_section9_v132_10_01_2025_16_22_24_25	CRC_TMA3_section9_v132
CRC_TMA4_section9_v132_10_01_2025_16_23_08_75	CRC_TMA4_section9_v132
"""

params_df = pd.read_csv(
    StringIO(params_str), sep="\t", header=None, names=["name_remote", "name_local"]
)
params_dict = {row.name_local: row.name_remote for i, row in params_df.iterrows()}

# name_remote = "CRC_TMA1_section5_3ug_v132_10_01_2025_15_16_31_811"
# name_local = "CRC_TMA1_section5_3ug_v132"
# run_sftp_check_file(name_remote, name_local)

dir_pass = Path("/mnt/nfs/storage/cosmx_log/done/pass/")
dir_check = Path("/mnt/nfs/storage/cosmx_log/done/check/")

names_local = [f.name for f in dir_pass.glob("*")]
names_check = [f.name for f in dir_check.glob("*")]

for name_local in tqdm(
    list(set(names_local) - set(names_check)),
    desc="Checking",
    bar_format=TQDM_FORMAT,
):
    name_remote = params_dict[name_local]

    try:
        run_sftp_check_file(name_remote, name_local)
    except Exception as e:
        logging.error(f"{name_local}: {e}")
