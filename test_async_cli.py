"""Quick test: verify async subprocess shell calls work on Windows."""
import asyncio
import json
import os

async def test_cmd(name, cmd):
    env = os.environ.copy()
    env.pop("PAGER", None)

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await proc.communicate()
    out = stdout.decode(errors="replace").strip()
    err = stderr.decode(errors="replace").strip()
    print(f"\n--- {name} ---")
    print(f"RC: {proc.returncode}")
    print(f"STDOUT ({len(out)} chars): {out[:300]}")
    if err:
        print(f"STDERR: {err[:200]}")

async def main():
    await asyncio.gather(
        test_cmd("GCP Auth", "gcloud auth list --filter=status:ACTIVE --format=json"),
        test_cmd("AWS STS", "aws sts get-caller-identity --output json"),
        test_cmd("Azure Accounts", "az account list --output json"),
    )

asyncio.run(main())
