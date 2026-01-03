# Data Handling (Privacy / Compliance)

## Purpose
Describe what the software does and what data it processes.

## Data Categories
- Potential personal data (e.g., names, emails, resumes, meeting notes)
- Potential sensitive data (e.g., health, finance) **should not be processed unless explicitly authorized**

## Data Flow (Typical)
1. Input collected from user / workspace tools
2. Processing locally and/or via third-party APIs (LLM, Slack, Notion, Google, etc.)
3. Output stored where (file/db/Notion/Slack) and for how long

## Storage & Retention
- Default: minimize storage
- If storing outputs: define retention period and deletion method

## Third-Party Processors
List external services and what is sent to them. Use least privilege and avoid sending raw PII where possible.

## Security Controls
- Secrets via environment variables (never commit)
- Access control: least privilege
- Logs: do not log raw inputs containing PII

## User Responsibilities
- Obtain required consent/authorization before processing personal or confidential data.
- Comply with applicable laws and platform terms.
