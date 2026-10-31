"""Compile the readable semantic source into the installed Python resource."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sync():
    target = ROOT / 'src/lab_kernel/kernel'
    target.mkdir(parents=True, exist_ok=True)
    for name in ('AGENTS.md', 'BOOT.md', 'KERNEL.md', 'CONCEPTS.md', 'COMPETENCES.md'):
        (target / name).write_bytes((ROOT / name).read_bytes())


if __name__ == '__main__':
    sync()
