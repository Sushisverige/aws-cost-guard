# aws-cost-guard

Beginner-friendly **read-only** AWS cost risk scanner.
It helps prevent surprise AWS bills by spotting common cost risks:
- EC2 instances (running/stopped)
- EBS volumes (available)
- Elastic IPs (unused)
- NAT Gateways

## Install (local)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .

