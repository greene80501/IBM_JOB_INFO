# IBM_JOB_INFO

This repo is just IBM early-career jobs data visualization stuff.

I scraped IBM Careers job data into CSV/derived datasets and generated a large set of maps, charts, tables, and NLP visualizations.

Important note: scraping this at scale will very likely violate IBM Careers website Terms of Service. I did it anyway for data analysis/visualization experiments.

## Main Files

- `ibm_jobs.csv`: raw-ish jobs dataset used as input
- `ibm_50_visualizations.py`: script that generates 50 visualization outputs
- `ibm_jobs_50_outputs/`: output folder with charts, maps, tables, dashboard files, and manifest
- `ibm_jobs_current/`: earlier analytics output set
- `old/`: older scripts and intermediate files

## Run

```bash
python ibm_50_visualizations.py --csv ibm_jobs.csv --output-dir ibm_jobs_50_outputs
```

## Output Index

See:

- `ibm_jobs_50_outputs/manifest_50_outputs.csv`

This lists all 50 requested visualization artifacts and where they are stored.
