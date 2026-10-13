# qc-westgard-sentinel-agent

A deterministic analytical quality-control evaluator implementing Westgard multirule interpretation, with a browser-only Levey–Jennings interface, Python CLI, and optional REST endpoint. The repository also retains its earlier generic threshold-based multi-agent demonstrations for compatibility.

## Use the browser application

The static application is in [`web/`](web/). Open it through a local static server:

```bash
python -m http.server 8080 --directory web
```

Visit `http://127.0.0.1:8080/`. Paste a QC CSV, open a local CSV file, or load the included example. Select **Evaluate QC** to inspect the standardized chart and rule events; export JSON or an annotated CSV. There are no external JavaScript, font, or Python runtime dependencies.

The GitHub Pages workflow deploys `web/` from the `master` branch. A live link should only be added after the Pages deployment is enabled and verified.

## Westgard interpretation

The dedicated evaluator processes QC observations *in supplied chronological order*, using the assigned target mean and positive standard deviation for each control material:

| Rule | Interpretation | Action |
| --- | --- | --- |
| `1_2s` | One result beyond ±2 SD | Warning; assess further |
| `1_3s` | One result beyond ±3 SD | Reject |
| `2_2s` | Two sequential results beyond 2 SD on the same side | Reject |
| `R_4s` | One result beyond +2 SD and another below −2 SD **within the same run** | Reject |
| `4_1s` | Four sequential results beyond 1 SD on the same side | Reject |
| `10x` | Ten sequential results on the same side of the mean | Reject |

The evaluator uses the **modern, non-gated interpretation**: `4_1s` and `10x` can trigger without a preceding `1_2s` warning. Sequential checks run within each material across runs. For exactly two consistently recorded control materials per run, `4_1s` also examines two successive complete runs and `10x` five successive complete runs. `2_2s` additionally checks controls within each run. The application does not join separate lots or changed means/SDs: supply them as separate datasets.

Numeric decision limits use strict exceedance: a result exactly at +2 SD is not a `1_2s` warning. An evaluated series is `REJECT` if any rejection rule triggers, `WARNING` for `1_2s` alone, otherwise `ACCEPT`. These terms reflect QC rule interpretation, **not permission to release patient results**. Instrument interlocks, calibration actions, and notifications are not implemented.

References: [Westgard multirule definitions](https://www.westgard.com/westgard-rules.html) and [multirule interpretation across control materials and runs](https://www.westgard.com/lessons/basic-qc-practices/lesson18.html).

## QC CSV input

Fields are required and each `run,level` pair must occur at most once:

```csv
run,level,value,mean,sd
1,Low,100.5,100,5
1,High,100.2,100,5
2,Low,112,100,5
2,High,113,100,5
```

Maximum 10,000 observations. All values must be finite and SD must be greater than zero. Use QC material identifiers only, not patient identifiers.

## Python CLI

Requires Python 3.9 or later.

```bash
python -m pip install -e .
qc-westgard-sentinel-engine qc -i qc_example.csv -o qc_report.json
```

Or run directly:

```bash
python -m qc_westgard_sentinel_agent.cli qc -i qc_example.csv
```

The original `audit`, `batch`, `chat`, and `serve` package commands remain available. The separate legacy top-level `python cli.py` interface also remains for compatibility. **Those legacy commands apply generic demonstration thresholds, not the Westgard multirule evaluator.**

## Optional REST server and local Docker

```bash
python -m pip install -e '.[server]'
python cli.py serve --host 127.0.0.1 --port 8000
```

`POST /api/qc/evaluate` accepts an object containing `measurements`, an array of the five-field QC objects above. The same evaluator powers Python and this endpoint. The original `/api/audit`, `/api/chat`, `/metrics`, `/health`, and `/api/audit/logs` endpoints remain.

For Docker Compose, provide a strong secret at runtime:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

The Docker API port binds to loopback by default. The REST API has no authentication or HTTPS termination: do **not** expose it directly to untrusted networks.

## Privacy and audit integrity

The standalone browser application performs analysis and exports entirely in the browser. It does not transmit, persist, or upload QC data. The backend's legacy task registry and audit chain are **process-memory only**, and the in-memory HMAC signing key defaults to a random ephemeral development key when `AUDIT_SECRET_KEY` is absent. Historical logs are not durable across process restarts.

The legacy PHI guard uses limited pattern matching; it is not comprehensive de-identification or HIPAA certification. Do not submit patient identifiers or regulated clinical data. For any clinical use, verify configured QC procedures against laboratory SOPs and instrument-specific requirements.

## Development and verification

```bash
python -m pip install -e '.[server,dev]'
python -m pytest -q
python -m pip check
node --check web/app.js
node --check web/westgard.js
node --test tests/test_westgard_browser.cjs
```

CI checks Python 3.10, 3.11, and 3.12 and Node.js 22. The frontend targets current Chrome, Firefox, Edge, and Safari, using standard modern browser APIs. The static app requires no Pyodide or server-side Python.

## License

[MIT](LICENSE).
