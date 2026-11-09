# Release consistency audit

## Source reconciliation

The academic report supplied the problem definition, algorithm descriptions, experimental protocol, and interpretation. The saved notebook and its exports supplied the numerical results. The report and notebook agree on the retained graph, benchmark pairs, resource-measurement method, sample settings, and conclusions.

| Check | Evidence |
| --- | --- |
| Main results | All 50 report rows match the original notebook exports for both algorithms' costs, selections, and maximum frontiers. The nine archived CSV projections checked against saved notebook tables also match. Per-pair displayed values match at their display precision. |
| Graph and route checks | The saved graph counts agree with the report. The two archived 50-route exports match the original machine-readable notebook export. Independent BFS verified all 50 UCS shortest-hop costs in the fresh run. |
| Depth follow-up | All six report depth rows match the notebook output. The 63 detailed records aggregate to the recorded means. The fresh run reproduced all 63 pair identities, routes, and stable measurements, including the three depth-eight pairs. |
| Timing and memory | The report summary, reduction table, and six stage times match the recorded outputs. The archived values remain byte-identical. The fresh runner retains the warm-up, five timed searches, and separate tracing run. |
| Expansion order | The report's first-pair table matches the saved notebook. The fresh run reproduced the full sequences and their 28 shared selections. |
| Figures | Eleven PNGs were extracted directly from the saved notebook. Ten are byte-identical to images in the academic report. |
| Deterministic rerun | Seven output tables and ten graph metrics match the archived values after excluding runtime and traced-allocation fields. |

The archive preserves the original degree histogram. Its final bin includes degree 30 while its title says “1–29 shown.” The package's fresh histogram uses integer-centered bins for degrees 1–30 and labels that range. This presentation correction leaves the underlying graph and search experiments intact.

## Scope of the public release

The academic DOCX contains identifying information and is kept outside this release. The cleaned notebook uses the package for executable code and reads the original data snapshot for its recorded comparison. The repository documents the methodology from the report and excludes student and instructor details. No poster accompanied the source files.

The dataset remains available through the official Stanford source. The archive includes a download workflow, source hashes, derived experimental CSVs, and plots. The included MIT license is the proposed license for project-owned code and documentation. The project contributors should confirm that choice before public release.

## Verification scope

The package was installed and tested locally with Python 3.12. The full CLI benchmark used the cached official edge list. The downloader and corrupt-archive handling have dataset-free tests. The notebook ran in a fresh in-process Jupyter kernel because the execution environment blocks the separate kernel's socket transport. The GitHub Actions workflow is configured for future pushes and pull requests.

[Test results](../results/verification/tests.txt) · [CLI reproduction check](../results/verification/deterministic_check.json) · [Notebook check](../results/verification/notebook_check.json) · [Recorded provenance](../results/recorded/provenance.json)
