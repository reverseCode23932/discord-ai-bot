"""Remove Cursor co-author line from git commit messages (stdin -> stdout)."""
import sys

msg = sys.stdin.read()
lines = [line for line in msg.splitlines() if "Co-authored-by: Cursor" not in line]
out = "\n".join(lines).strip()
if out:
    print(out + "\n")
