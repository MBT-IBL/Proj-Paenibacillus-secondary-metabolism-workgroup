# Archive output of bakta annotations
# Keep only .gbff and .faa files in place, remove others

import logging
from pathlib import Path
from subprocess import CalledProcessError, run

SCRIPT_ROOT = Path(__file__).parent.resolve()
ANNOTATION_ROOT = SCRIPT_ROOT.parent.resolve() / "Annotation" / "20250727_bakta"

THREADS = 16

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(filename)s - %(levelname)s - %(message)s"
)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
# create file handler
log_file = ANNOTATION_ROOT / ("Annotation_using_bakta_cleanup.log")
fh = logging.FileHandler(log_file)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)


annotation_dirs = list(ANNOTATION_ROOT.glob("*/"))
logger.info("Found %d annotation directories.", len(annotation_dirs))

for d in annotation_dirs:
    if not d.is_dir():
        continue

    logger.info("Processing directory: %s", d.name)

    # Create archive name
    archive_name = f"{d.name}_bakta.tar.xz"
    archive_path = d / archive_name

    # Check if archive already exists
    if archive_path.exists():
        logger.info("Archive already exists: %s", archive_name)
    else:
        # Create tar.xz archive of all files in the directory
        logger.info("Creating archive: %s", archive_name)
        try:
            cmd = (
                f"cd '{d}' && tar -cf - . | xz -T {THREADS} > '{archive_name}'"
            )
            result = run(
                cmd, shell=True, check=True, capture_output=True, text=True
            )
            logger.info("Successfully created archive: %s", archive_name)
        except (OSError, CalledProcessError) as e:
            logger.error("Failed to create archive %s: %s", archive_name, e)
            continue

    # Find files to keep (*.gbff and *.faa files, plus the archive)
    gbff_files = list(d.glob("*.gbff"))
    faa_files = list(d.glob("*.faa"))
    files_to_keep = gbff_files + faa_files + [archive_path]

    # Find all files in the directory
    all_files = [f for f in d.glob("*") if f.is_file()]

    # Remove files that are not in the keep list
    files_to_remove = [f for f in all_files if f not in files_to_keep]

    logger.info(
        "Keeping %d files (1 archive, %d .gbff, %d .faa)",
        len(files_to_keep),
        len(gbff_files),
        len(faa_files),
    )
    logger.info("Removing %d files", len(files_to_remove))

    for file_to_remove in files_to_remove:
        try:
            file_to_remove.unlink()
            logger.debug("Removed: %s", file_to_remove.name)
        except OSError as e:
            logger.error("Failed to remove %s: %s", file_to_remove.name, e)
