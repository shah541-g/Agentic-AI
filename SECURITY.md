# Security Policy

## Supported Versions

We actively maintain and provide security patches, dependency updates, and guidance for the following releases and development tracks:

| Version / Milestone Track | Supported          | Status |
| ------------------------- | ------------------ | ------ |
| `main` (Latest / Active)  | :white_check_mark: | Fully supported with active security fixes |
| `v1.x`                    | :white_check_mark: | Critical vulnerabilities and dependency updates |
| `< 1.0` (Archived Labs)   | :x:                | Deprecated / End-of-Life |

---

## Sensitive Scenarios & AI Safety Considerations

Because this repository contains agentic workflows, autonomous tool-calling scripts, and LLM integrations, please pay special attention to:

1. **Credentials & Secrets Exposure:**
   - Never commit `.env` files, API keys (e.g., OpenAI, Anthropic, Google Gemini, Azure, LangSmith), or private access tokens.
   - If an API key or token has been inadvertently exposed in a commit or pull request, treat it as immediately compromised.

2. **Tool Execution & Sandboxing:**
   - Workflows that execute shell commands, run dynamic Python code, or query databases must execute with proper boundaries and sanitized inputs.
   - Any report detailing prompt injection leading to unauthorized remote code execution (RCE) or arbitrary file read/write is treated as high priority.

3. **Data Privacy:**
   - Any leakage of sensitive personal data or proprietary prompt context through logging, tracing, or vector store dumps.

---

## Reporting a Vulnerability

We take the security of our code, dependencies, and agent tooling seriously. If you discover a security vulnerability or credential leak, please report it privately rather than opening a public issue.

### How to Report

- **Preferred:** Use [GitHub Private Vulnerability Reporting](https://github.com/YOUR_GITHUB_USERNAME/Agentic-AI/security/advisories/new) via the repository's **Security** tab.
- **Alternative:** Email the maintainer directly at **your-security-email@domain.com** with the subject line `[SECURITY] Agentic-AI Vulnerability Report`.

### What to Include in Your Report

To help us triage and resolve the issue quickly, please provide:
- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions, Proof of Concept (PoC) script, or minimum reproducible example.
- The environment details (OS, Python version, dependencies/packages involved).
- Any proposed remediation, patch, or mitigation steps (if available).

### Response Timeline

| Phase | Expected Timeframe |
| ----- | ------------------ |
| **Initial Acknowledgment** | Within **48 hours** |
| **Triage & Severity Assessment** | Within **3–5 business days** |
| **Patch Release & Advisory** | Critical: within **7 days** · Low/Moderate: next scheduled release |

### Policy on Disclosure

- **Coordinated Disclosure:** We kindly request that you give us adequate time to investigate and release a fix before disclosing any details publicly.
- **Credit:** We are happy to publicly acknowledge and credit your contribution in our release notes and security advisories once the fix is deployed.
