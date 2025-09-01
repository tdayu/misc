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
python arxiv_summary/arXiv-summary.py $start_date -e $end_date \
 -y arxiv_summary/options/BandQ.yaml \
 -j BandQ_summary.json \
 -l BandQ_summary \ 
 -t
```

## Explanation of Options
- The `-t` option truncates a long author list. This is meant for papers from collaboration (e.g. LHCb) that has an author list of 1000+ members. When used, only LHCb Collaboration (or first author in the list) is rendered.
- `-y`: YAML to configure the arXiv query.
- `-j`: Output JSON file containing the result of the arXiv query.
- `-l`: Output LaTeX file and the name of the rendered PDF. Note: omit any file format extension for this argument.
