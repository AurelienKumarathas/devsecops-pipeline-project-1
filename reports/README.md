# Reports — NexusCore Technologies Threat Model

This directory contains the complete threat model for the NexusCore Technologies DevSecOps pipeline project.

## Document Map

| Document | Description | Read This If... |
|----------|-------------|----------------|
| [threat-model-report.md](threat-model-report.md) | Executive summary, architecture overview, vulnerability inventory, and remediation roadmap | Start here |
| [analyses/stride-threats.md](analyses/stride-threats.md) | Full STRIDE threat register — 21 threats across Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege | You want per-threat detail with mitigations |
| [analyses/mitre-mapping.md](analyses/mitre-mapping.md) | MITRE ATT&CK technique mapping — 21 techniques across 12 tactics, each grounded in a specific file and vulnerability | You want adversary-perspective framing |
| [analyses/kill-chain-analysis.md](analyses/kill-chain-analysis.md) | Three end-to-end attack chains with phase-by-phase breakdowns | You want to see how individual vulnerabilities chain into full compromises |

## Methodology

All findings in this threat model are grounded in confirmed vulnerabilities present in the repository. Every threat references the specific file, route, or resource that enables it. No threats are hypothetical or based on assumed infrastructure that does not exist in the codebase.

**Frameworks used:** STRIDE (per component) · MITRE ATT&CK v14 · Unified Kill Chain

## Relationship to the Codebase

```
Main branch  — deliberately vulnerable code — proves each security gate fires correctly
Hardened branch — remediated versions of every file — proves the vulnerabilities can be fixed
This reports/ directory — documents why each vulnerability matters operationally
```

See [REMEDIATION.md](../REMEDIATION.md) at the root for the full findings index with before/after technical detail.
