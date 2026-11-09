"""Execute the public notebook in a fresh in-process Jupyter kernel."""

import argparse
import os
from pathlib import Path

import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_TYPES = {"stream", "display_data", "execute_result", "error"}


def execute(notebook) -> int:
    """Run each code cell and capture its standard Jupyter output messages."""
    manager = InProcessKernelManager()
    manager.start_kernel()
    client = manager.client()
    client.start_channels()
    count = 0
    try:
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue
            request = client.execute(cell.source, allow_stdin=False)
            reply = client.get_shell_msg(timeout=30)["content"]
            cell.execution_count = reply["execution_count"]
            cell.outputs = []
            while True:
                message = client.get_iopub_msg(timeout=30)
                if message["parent_header"].get("msg_id") != request:
                    continue
                kind = message["msg_type"]
                if kind in OUTPUT_TYPES:
                    cell.outputs.append(nbformat.v4.output_from_msg(message))
                if kind == "status" and message["content"]["execution_state"] == "idle":
                    break
            if reply["status"] != "ok":
                raise RuntimeError("\n".join(reply.get("traceback", [])) or "Notebook cell failed")
            count += 1
    finally:
        client.stop_channels()
        manager.shutdown_kernel()
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, help="Local SNAP text or gzip file")
    parser.add_argument("--output", type=Path, default=Path("runs/executed_notebook.ipynb"))
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("Choose a new notebook output path")
    if args.dataset is not None:
        os.environ["PATENT_DATASET"] = str(args.dataset.resolve(strict=True))
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.chdir(ROOT)
    notebook = nbformat.read(ROOT / "notebooks/ucs_vs_gbfs.ipynb", as_version=4)
    count = execute(notebook)
    nbformat.validate(notebook)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        nbformat.write(notebook, stream)
    print(f"Executed {count} code cells and saved the notebook to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
