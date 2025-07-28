import logging
import shutil
from pathlib import Path

from pyBioinfo_modules.wrappers.antismash import (
    log_antismash_version,
    runAntismash,
)
from tqdm import tqdm

SCRIPT_ROOT = Path(__file__).parent.resolve()
ANNOTATION_ROOT = SCRIPT_ROOT.parent.resolve() / "Annotation" / "20250727_bakta"
log_file = ANNOTATION_ROOT.parent / ("20250727_bakta_antismash.log")
ANTISMASH_OUT = ANNOTATION_ROOT.parent / "20250727_bakta_antismash"
THREADS = 16

ANTISMASH_ENV = Path("/vol/local/conda_envs/antismash/")
CONDA_EXE = "micromamba"
SHELL = "bash"

# Configure root logger to capture all logging from imported modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(log_file)],
)

logger = logging.getLogger(Path(__file__).name)

# Also configure antismash module logger to use the same handlers
antismash_logger = logging.getLogger("pyBioinfo_modules.wrappers.antismash")
antismash_logger.setLevel(logging.INFO)

gbff_files = list(ANNOTATION_ROOT.glob("*/*.gbff"))

logger.info("Found %d gbff files.", len(gbff_files))

log_antismash_version(
    antismash_env=ANTISMASH_ENV,
    condaexe=CONDA_EXE,
    shell=SHELL,
)

for gbff_file in tqdm(gbff_files, desc="Running antiSMASH"):
    if not gbff_file.is_file():
        continue

    out_dir = ANTISMASH_OUT / gbff_file.stem
    consolidated_zip = ANTISMASH_OUT / f"{out_dir}.zip"
    if consolidated_zip.exists():
        logger.info(
            "Consolidated zip file already exists: %s, skipping",
            consolidated_zip.name,
        )
        continue
    out_dir.mkdir(parents=True, exist_ok=True)

    # Run antiSMASH command
    runAntismash(
        gbff_file,
        title=gbff_file.stem,
        output=out_dir,
        cpu=THREADS,
        condaEnv=ANTISMASH_ENV,
        condaExe=CONDA_EXE,
        shell=SHELL,
        geneFinding="none",
        existsOk=True,
        overwrite=False,
        completeness=2,
    )

# Consolidate zipped results
for out_dir in ANTISMASH_OUT.glob("*/"):
    if not out_dir.is_dir():
        continue

    zip_files = list(out_dir.glob("*.zip"))
    if len(zip_files) == 1:
        if zip_files[0].name != f"{out_dir}.zip":
            logger.warning(
                "Zip file %s does not match output directory name %s",
                zip_files[0].name,
                out_dir.stem,
            )
        zip_files[0].rename(ANTISMASH_OUT / zip_files[0].name)
    else:
        logger.error("Did not find zip file: %s", out_dir)

for out_dir in ANTISMASH_OUT.glob("*/"):
    if not out_dir.is_dir():
        continue
    # Remove the directory and all its contents
    try:
        shutil.rmtree(out_dir)
        logger.info("Removed directory: %s", out_dir)
    except OSError as e:
        logger.error("Failed to remove directory %s: %s", out_dir, e)
