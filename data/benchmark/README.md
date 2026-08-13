# Pakistan Legal & Policy Corpus Directory

This directory stores the official, authoritative Pakistan legal and policy PDF instruments used in **Benchmark Mode** and for generating evaluation metrics.

## File Requirements & Mapping

To guarantee reproducibility of the evaluation harness, files must be named exactly as shown below:

| Document ID | Official Title | Category | Filename | Source URL |
|---|---|---|---|---|
| `constitution` | Constitution of the Islamic Republic of Pakistan | Constitutional | `constitution.pdf` | [NA Link](https://na.gov.pk/uploads/documents/1333524740_370.pdf) |
| `ppc` | Pakistan Penal Code, 1860 | Criminal Law | `pakistan_penal_code.pdf` | [Law Ministry](https://pakistancode.gov.pk) |
| `crpc` | Code of Criminal Procedure, 1898 | Criminal Procedure | `code_of_criminal_procedure.pdf` | [Law Ministry](https://pakistancode.gov.pk) |
| `cpc` | Code of Civil Procedure, 1908 | Civil Procedure | `code_of_civil_procedure.pdf` | [Law Ministry](https://pakistancode.gov.pk) |
| `elections_act` | Elections Act, 2017 | Election Law | `elections_act_2017.pdf` | [NA Link](https://na.gov.pk/uploads/documents/1507727142_915.pdf) |
| `peca` | Prevention of Electronic Crimes Act, 2016 | Cyber Law | `prevention_of_electronic_crimes_act.pdf` | [NA Link](https://na.gov.pk/uploads/documents/1472635250_246.pdf) |
| `rai_act` | Right of Access to Information Act, 2017 | Administrative Law | `right_of_access_to_information_act.pdf` | [NA Link](https://na.gov.pk/uploads/documents/1508233377_122.pdf) |
| `civil_servants_act` | Civil Servants Act, 1973 | Service Law | `civil_servants_act_1973.pdf` | [NA Link](http://na.gov.pk/uploads/documents/1498115655_160.pdf) |

## Fetching the Files

Run the utility script to fetch files from their official sources:
```bash
python scripts/download_benchmark.py
```

If any link is blocked, restricted, or down, download the official PDF directly from the source URL above and rename it to the specified **Filename** before placing it in this folder.
