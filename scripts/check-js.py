"""Check every pre-commit input; node --check accepts only one source file."""
import subprocess
import sys

for filename in sys.argv[1:]:
    result = subprocess.run(['node', '--check', filename])
    if result.returncode:
        raise SystemExit(result.returncode)
