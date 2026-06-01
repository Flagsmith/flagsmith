---
title: CVES and Vulnerabilities
sidebar_position: 132
sidebar_label: CVES and Vulnerabilities
---

## CVEs and Vulnerability Reports

We actively scan for vulnerabilities across our supply chain and take remediation seriously. If your security scanner
has flagged a CVE against a Flagsmith image or dependency, this section will help you interpret the results and
determine whether it needs to be raised with us.

For details on reporting security issues, see our
[Security Policy](https://github.com/Flagsmith/flagsmith/security/policy).

### How We Scan

We run continuous, automated vulnerability scanning:

-   **[Trivy](https://github.com/Flagsmith/flagsmith/blob/main/.github/workflows/platform-docker-trivy-scan.yml)** scans
    our Docker images every 3 hours, with results fed into GitHub's security tab via SARIF reporting.
-   **[Renovate](https://github.com/Flagsmith/flagsmith/blob/main/renovate.json)** monitors Python, Node.js,
    and documentation dependencies in security-only mode — it raises PRs only for known vulnerabilities, not routine
    version bumps.
-   **Docker Scout** provides additional image-level security analysis.

Our Docker images use [Chainguard Wolfi](https://www.flagsmith.com/blog/we-made-docker-images-more-secure-with-oss) as
the base OS, which significantly reduces the attack surface compared to traditional base images.

### Interpreting Scan Results

Not every CVE that a scanner reports represents a real risk to your Flagsmith deployment. Here's what to consider before
raising it with us.

#### Lockfile and documentation dependencies are not runtime dependencies

Our repository lockfile includes dependencies for documentation tooling, development utilities, and build-time packages
that are **not present in the runtime Docker image**. Scanners that analyse the source repository (rather than the
deployed image) may flag these, but they are not exploitable in a running Flagsmith instance.

#### A CVE in a dependency does not mean it's exploitable

A CVE in a transitive dependency doesn't automatically mean Flagsmith is affected. We assess actual exploitability —
whether the vulnerable code path is reachable in Flagsmith's context — not just the presence of a flagged package. Many
CVEs require specific conditions or call patterns that don't apply to how Flagsmith uses the dependency.

#### Check whether it's already fixed

Before reporting a CVE to us, please check whether it exists in the
[latest Flagsmith release](https://github.com/Flagsmith/flagsmith/releases). Our scanning runs continuously, so newer
versions will typically have fewer outstanding CVEs. If you're running an older version, the issue may already be
resolved.

#### Don't let a reported CVE block an upgrade

If you're hesitating to upgrade because the target version has a reported CVE, compare it to what you're currently
running. Older versions are typically affected by the same vulnerabilities — plus additional ones that have since been
patched. Staying on an older version is usually the riskier choice.

If you've reviewed the above and believe a CVE is genuinely exploitable in a deployed Flagsmith instance, please report
it to [support@flagsmith.com](mailto:support@flagsmith.com) with the CVE identifier, the affected Flagsmith version, and
any context on the suspected impact.
