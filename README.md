# aws-cost-guard

Beginner-friendly **read-only** AWS cost risk scanner.  
It helps prevent surprise AWS bills by spotting common cost risks.

## What it checks
- **EC2** instances (pending/running/stopping/stopped)
- **EBS** volumes that are **available** (often forgotten)
- **Elastic IPs** that are **unassociated** (unused)
- **NAT Gateways** (can be expensive)

## Why this exists
When learning AWS, it’s easy to forget resources and get billed while sleeping.
This tool provides a quick “am I safe?” checklist from the command line.

## Safety (Important)
- ✅ **Read-only**: this tool does **NOT** create/update/delete any AWS resources.
- ✅ You can run it anytime to confirm cost risks.
- ✅ No AWS keys are stored by this tool (it uses your AWS CLI credentials).

## Prerequisites
- Python 3.10+
- AWS CLI configured (profile or environment variables)

## Install (local)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .


## Compliance / Privacy / Ethics
- This repository is provided as a sample/portfolio.
- Do not process personal/confidential data without proper authorization and consent.
- Review docs/DATA_HANDLING.md and docs/ETHICS.md before any real-world use.
