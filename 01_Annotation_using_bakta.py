import logging
from pathlib import Path
from subprocess import run

from pyBioinfo_modules.wrappers._environment_settings import withActivateEnvCmd

SCRIPT_ROOT = Path(__file__).parent.resolve()
ANNOTATION_ROOT = SCRIPT_ROOT.parent.resolve() / "Annotation" / "test"
ANNOTATION_ROOT.mkdir(parents=True, exist_ok=True)

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
bakta_version_cmd = withActivateEnvCmd(
    "bakta --version", BEKTA_ENV, CONDA_EXE, shell="bash"
)
bakta_version_result = run(
    bakta_version_cmd, shell=True, capture_output=True, text=True
)
if bakta_version_result.returncode != 0:
    logger.error(
        f"Failed to get bakta version: {bakta_version_result.stderr.strip()}"
    )
else:
    logger.info(f"Bakta version: {bakta_version_result.stdout.strip()}")
