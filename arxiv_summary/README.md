# ArXiv Summary

Python script to generate a summary of ArXiv entries added or updated within a certain time window.

Requires:
- pylatex
- latexmk
- lualatex (to handle unicode math symbols)

Usage:
```sh
start_date="2025-07-22"
end_date="2025-07-29"
python arxiv_summary/arXiv-summary.py $start_date -e $end_date -y arxiv_summary/options/BandQ.yaml -j BandQ_summary.json -l BandQ_summary
```
