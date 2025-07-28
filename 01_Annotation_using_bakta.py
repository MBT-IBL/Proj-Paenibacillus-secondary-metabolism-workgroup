import logging
from pathlib import Path
from subprocess import run

from pyBioinfo_modules.wrappers._environment_settings import withActivateEnvCmd

SCRIPT_ROOT = Path(__file__).parent.resolve()
ANNOTATION_ROOT = SCRIPT_ROOT.parent.resolve() / "Annotation" / "20250727_bakta"
ANNOTATION_ROOT.mkdir(parents=True, exist_ok=True)

SOURCE_FASTA_DIR = SCRIPT_ROOT.parent.resolve() / "Genome_fastas"
SOURCE_FASTA_EXT = ".fa.gz"
BAKTA_DB = "/vol/local/shared_db/bakta-20250224/db"
THREADS = 16


def strain_from_name(file_name_stem: str) -> str:
    """Extract strain from the file name."""
    return "-".join(file_name_stem.split("_")[2:])


def locus_tag_from_name(file_name_stem: str) -> str:
    """Extract locus tag from the file name."""
    return "P" + "".join(file_name_stem.split("_")[2:]).replace("-", "")


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
log_file = ANNOTATION_ROOT / ("Annotation_using_bakta.log")
fh = logging.FileHandler(log_file)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

BEKTA_ENV = Path("/vol/local/conda_envs/bakta")
CONDA_EXE = "micromamba"

# Check and log bakta version
BAKTA_VERSION_CMD = withActivateEnvCmd(
    "bakta --version", BEKTA_ENV, CONDA_EXE, shell="bash"
)
bakta_version_result = run(
    BAKTA_VERSION_CMD, shell=True, capture_output=True, text=True, check=False
)
if bakta_version_result.returncode != 0:
    logger.error(
        "Failed to get bakta version: %s", bakta_version_result.stderr.strip()
    )
else:
    logger.info("Bakta version: %s", bakta_version_result.stdout.strip())

logger.info("With bakta database at:")
logger.info(BAKTA_DB)
logger.info("Annotation file will be saved to:")
logger.info(ANNOTATION_ROOT)
logger.info("Source FASTA files will be from:")
logger.info(SOURCE_FASTA_DIR)
logger.info("With extension: %s", SOURCE_FASTA_EXT)

# Run bakta annotation
source_fastas = list(SOURCE_FASTA_DIR.glob("*" + SOURCE_FASTA_EXT))
logger.info("Found %d FASTA files to annotate.", len(source_fastas))
for fasta_file in source_fastas:
    logger.info("Annotating %s...", fasta_file.name)
    if fasta_file.is_symlink():
        logger.info("    -> %s", fasta_file.resolve().name)
    file_stem = fasta_file.name.replace(SOURCE_FASTA_EXT, "")
    genus = file_stem.split("_")[0]
    species = file_stem.split("_")[1]
    strain = strain_from_name(file_stem)
    locus_tag = locus_tag_from_name(file_stem)
    outdir = ANNOTATION_ROOT / file_stem
    if outdir.exists():
        logger.warning("Output directory %s already exists.", outdir)
        if (outdir / (file_stem + ".fa.gbff")).exists():
            logger.warning("Output annotations found. Skipping.")
            continue
        else:
            logger.info("Removing existing output directory %s", outdir)
            for item in outdir.iterdir():
                item.unlink()
            outdir.rmdir()

    bakta_cmd = withActivateEnvCmd(
        f"bakta --db {BAKTA_DB} "
        f"--output {outdir} "
        f"--genus {genus} "
        f"--species {species} "
        f"--strain {strain} "
        "--gram + "
        f"--locus-tag {locus_tag} "
        f"--threads {THREADS} "
        f"{fasta_file}",
        BEKTA_ENV,
        CONDA_EXE,
        shell="bash",
    )
    bakta_result = run(
        bakta_cmd, shell=True, capture_output=True, text=True, check=False
    )
    if bakta_result.returncode != 0:
        logger.error("Bakta annotation failed: %s", bakta_result.stderr.strip())
    else:
        logger.info("Bakta annotation completed successfully.")
        logger.info(bakta_result.stdout.strip())
