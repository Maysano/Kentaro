"""Include learner-facing Kentaro files that live outside the Python package.

The wheel carries the complete skill directories recursively.  A skill may add
examples, checklists, or other supporting files without requiring a separate
packaging edit.
"""
from pathlib import Path

from setuptools import setup


ROOT = Path(__file__).parent
ROOT_DOCUMENTS = [ROOT / "README.md", ROOT / "RELEASE_NOTES.md"]
DOCS = sorted((ROOT / "docs").glob("*.md"))
SKILLS = ROOT / ".agents" / "skills"

data_files = [
    ("share/kentaro", [path.relative_to(ROOT).as_posix() for path in ROOT_DOCUMENTS]),
    ("share/kentaro/docs", [path.relative_to(ROOT).as_posix() for path in DOCS]),
]
for skill in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
    files = sorted(path for path in skill.rglob("*") if path.is_file())
    if files:
        data_files.append((f"share/kentaro/skills/{skill.name}", [path.relative_to(ROOT).as_posix() for path in files]))

setup(data_files=data_files)
