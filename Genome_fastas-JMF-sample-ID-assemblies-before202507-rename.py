from pathlib import Path

import pandas as pd

seq_strain_table = pd.read_excel(
    "./JMF-2310-15_Leiden_Auburn_HES_ANT_17-6-25.xlsx",
    sheet_name="Paenibacillus @ JMF Sequenicng",
    index_col=0,
    usecols=[0, 1],
)

file_rename_dict = {}
exception_lines = []

# Remove existing symlinks
for f in Path("Genome_fastas").glob("*"):
    if f.is_symlink():
        f.unlink()
for pf, row in seq_strain_table.iterrows():
    st = row["User sample ID"].strip()
    files = list(
        Path("Genome_fastas/JMF-sample-ID-assemblies-before202507/").glob(
            f"{pf}*.fa.gz"
        )
    )
    if len(files) == 1:
        target = Path("JMF-sample-ID-assemblies-before202507") / files[0].name
        symlink_name = f"Paenibacillus_sp_{st}.fa.gz"
        i = 1
        symlink = Path("Genome_fastas") / symlink_name
        while symlink.exists():
            exception_lines.append("\t".join([st, symlink_name]) + "\n")
            symlink_name = f"Paenibacillus_sp_{st}_{i}.fa.gz"
            symlink = Path("Genome_fastas") / symlink_name
            exception_lines.append("\t".join([st, symlink_name]) + "\n")
            i += 1
        symlink = Path("Genome_fastas") / symlink_name
        symlink.symlink_to(target)
        file_rename_dict[target.name] = symlink_name
    else:
        exception_lines.append("\t".join([st] + [f.name for f in files]) + "\n")

exception_lines = sorted(list(set(exception_lines)))
with open(
    "Genome_fastas/JMF-sample-ID-assemblies-before202507/exceptions-find-strain.tsv",
    "w",
    encoding="utf-8",
) as exception_file_handle:
    exception_file_handle.writelines(exception_lines)

pd.DataFrame.from_dict(file_rename_dict, orient="index").to_csv(
    "Genome_fastas/JMF-sample-ID-assemblies-before202507/file_rename_list.tsv",
    sep="\t",
)

# Exception handling

Path("Genome_fastas/Paenibacillus_sp_JJ-340.fa.gz").unlink()
Path("Genome_fastas/Paenibacillus_sp_JJ-340_1.fa.gz").rename(
    "Genome_fastas/Paenibacillus_sp_JJ-340.fa.gz"
)
Path("Genome_fastas/Paenibacillus_sp_JJ-299.fa.gz").rename(
    "Genome_fastas/Paenibacillus_sp_JJ-299_0037B.fa.gz"
)
Path("Genome_fastas/Paenibacillus_sp_JJ-299_1.fa.gz").rename(
    "Genome_fastas/Paenibacillus_sp_JJ-299_0063B.fa.gz"
)
Path("Genome_fastas/Paenibacillus_sp_JJ-160b-b1.fa.gz").symlink_to(
    "Genome_fastas/JMF-sample-ID-assemblies-before202507/JMF-2310-15-0096B-ONT.flye.medaka1x.man.bin1.fa.gz"
)
Path("Genome_fastas/Paenibacillus_sp_JJ-160b-b2.fa.gz").symlink_to(
    "Genome_fastas/JMF-sample-ID-assemblies-before202507/JMF-2310-15-0096B-ONT.flye.medaka1x.man.bin2.fa.gz"
)
Path("Genome_fastas/Paenibacillus_sp_JJ-90A-54-b1.fa.gz").symlink_to(
    "Genome_fastas/JMF-sample-ID-assemblies-before202507/JMF-2310-15-0075B-ONT.flye.medaka1x.man.bin1.fa.gz"
)
Path("Genome_fastas/Paenibacillus_sp_JJ-90A-54-b2.fa.gz").symlink_to(
    "Genome_fastas/JMF-sample-ID-assemblies-before202507/JMF-2310-15-0075B-ONT.flye.medaka1x.man.bin2.fa.gz"
)
