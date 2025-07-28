# Collect faa files from bakta annotations
# Run BUSCO on the folder
# Remove BUSCO temp files
# Collect BUSCO json files
# Plot BUSCO results

import logging
from pathlib import Path
from subprocess import run

from pyBioinfo_modules.wrappers._environment_settings import withActivateEnvCmd

SCRIPT_ROOT = Path(__file__).parent.resolve()
ANNOTATION_ROOT = SCRIPT_ROOT.parent.resolve() / "Annotation" / "20250727_bakta"
log_file = ANNOTATION_ROOT.parent / ("20250727_bakta_faa_busco.log")
DIR_FAA = ANNOTATION_ROOT.parent / "20250727_bakta_faa"
BUSCO_OUT = ANNOTATION_ROOT.parent / "20250727_bakta_faa_busco"
FAA_REL = Path("..")
DIR_FAA.mkdir(exist_ok=True)
BUSCO_DB = "/vol/local/shared_db/busco/"
THREADS = 16
busco_cmd = (
    "busco -m protein --offline -l paenibacillus_odb12 "
    f"--download_path {BUSCO_DB} --out_path {BUSCO_OUT} "
    f"-i {DIR_FAA} --cpu {THREADS}"
)

BUSCO_ENV = Path("/vol/local/conda_envs/busco/")
CONDA_EXE = "micromamba"
SHELL = "bash"

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
fh = logging.FileHandler(log_file)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Collect faa files from bakta annotations
faa_files = list(ANNOTATION_ROOT.glob("*/*.faa"))
# Remove hypothetical protein files from list
faa_files = [f for f in faa_files if "hypothetical" not in f.name.lower()]
logger.info("Found %d faa files.", len(faa_files))

for faa_file in faa_files:
    if not faa_file.is_file():
        continue

    # Symlink faa file to the directory
    dest_file = DIR_FAA / faa_file.name
    if dest_file.exists():
        logger.info("File already exists: %s", dest_file.name)
        continue
    try:
        # Calculate relative path from DIR_FAA to the target file
        faa_file_relative = FAA_REL / faa_file.relative_to(
            ANNOTATION_ROOT.parent
        )
        dest_file.symlink_to(faa_file_relative)
        logger.info("Created symlink: %s", faa_file.name)
        try:
            assert dest_file.resolve() == faa_file.resolve()
        except FileNotFoundError:
            logger.error(
                "Symlink %s does not resolve to %s", dest_file, faa_file
            )
            continue
        except AssertionError:
            logger.error(
                "Symlink %s does not match target %s", dest_file, faa_file
            )
            continue
    except Exception as e:
        logger.error(
            "Failed to create symlink for file %s: %s", faa_file.name, e
        )


busco_output_dir = BUSCO_OUT / f"BUSCO_{DIR_FAA.name}"
# Run BUSCO on the folder
if busco_output_dir.exists():
    logger.warning(
        "BUSCO output directory %s already exists. Skipping.", busco_output_dir
    )
else:
    cmd = withActivateEnvCmd(
        busco_cmd, condaEnv=BUSCO_ENV, condaExe=CONDA_EXE, shell=SHELL
    )
    logger.info("Running BUSCO command: %s", cmd)
    busco_run = run(
        cmd, text=True, check=False, capture_output=True, shell=True
    )
    if busco_run.returncode != 0:
        logger.error(
            "BUSCO run failed with return code %d", busco_run.returncode
        )
        logger.error("STDOUT: %s", busco_run.stdout)
        logger.error("STDERR: %s", busco_run.stderr)
    else:
        logger.info("BUSCO run completed successfully.")


# Remove BUSCO temp files and collect results
busco_subdirs = [
    d for d in busco_output_dir.glob("*") if d.is_dir() and d.name != "logs"
]
busco_json_dir = busco_output_dir / "json_files"
busco_json_dir.mkdir(exist_ok=True)
for subdir in busco_subdirs:
    for f in subdir.glob("*"):
        if f.is_dir():
            logger.info("Removing directory: %s", f)
            run(
                f"rm -rf {f}",
                shell=True,
                check=True,
            )
        else:
            # Move file to the BUSCO_OUT directory
            if f.suffix == ".json":
                try:
                    f.rename(
                        busco_json_dir
                        / f.name.removeprefix(
                            "short_summary.specific.paenibacillus_odb12."
                        )
                    )  # Do not remove the "short_summary.specific.paenibacillus_odb12." prefix, will be needed for plotting
                except Exception as e:
                    logger.error("Failed to move JSON file %s: %s", f, e)
            elif f.suffix == ".txt":
                try:
                    f.rename(
                        busco_output_dir
                        / f.name.replace(
                            "short_summary.specific.paenibacillus_odb12.", ""
                        )
                    )
                except Exception as e:
                    logger.error(
                        "Failed to move %s: %s",
                        f.relative_to(ANNOTATION_ROOT.parents[1]),
                        e,
                    )
    # remove the subdirectory after moving files
    try:
        subdir.rmdir()
    except Exception as e:
        logger.error("Failed to remove subdirectory %s: %s", subdir, e)
        continue
    logger.info("Removed subdirectory: %s", subdir)

# Plot BUSCO results
figures = busco_json_dir.glob("busco_figure*.png")
figures_final = busco_output_dir.glob("busco_figure*.png")
if figures:
    logger.info("BUSCO figure already exists: %s", figures)
elif figures_final:
    logger.info("BUSCO figure already exists: %s", figures_final)
else:
    busco_plot_cmd = f"busco --plot {busco_json_dir}"
    busco_plot = run(
        withActivateEnvCmd(
            busco_plot_cmd, condaEnv=BUSCO_ENV, condaExe=CONDA_EXE, shell=SHELL
        ),
        shell=True,
        check=False,
        capture_output=True,
        text=True,
    )

    if busco_plot.returncode != 0:
        logger.error("BUSCO plot command failed: %s", busco_plot.stderr.strip())
        logger.error("STDOUT: %s", busco_plot.stdout.strip())
        logger.error("STDERR: %s", busco_plot.stderr.strip())
    else:
        logger.info("BUSCO plot command completed successfully.")
if figures:
    logger.info("Move figures to the output directory")
    for figure_path in figures:
        figure_path.rename(busco_output_dir / figure_path.name)

# Move everything to the BUSCO_OUT directory
for f in busco_output_dir.glob("*"):
    try:
        f.rename(BUSCO_OUT / f.name)
        logger.info("Moved file %s to BUSCO_OUT", f.name)
    except Exception as e:
        logger.error("Failed to move file %s: %s", f.name, e)
try:
    busco_output_dir.rmdir()
    logger.info("Removed BUSCO output directory: %s", busco_output_dir)
except Exception as e:
    logger.error(
        "Failed to remove BUSCO output directory %s: %s", busco_output_dir, e
    )
