# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Tinel seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: <arun@infenia.com>

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

## Preferred Languages

We prefer all communications to be in English.

## Policy

- We will respond to your report within 48 hours with our evaluation of the report and an expected resolution date.
- If you have followed the instructions above, we will not take any legal action against you in regard to the report.
- We will handle your report with strict confidentiality, and not pass on your personal details to third parties without your permission.
- We will keep you informed of the progress towards resolving the problem.
- In the public information concerning the problem reported, we will give your name as the discoverer of the problem (unless you desire otherwise).

## Security Considerations

### System Access

This MCP server requires access to system information through:

- Reading from `/proc` and `/sys` filesystems
- Executing system utilities (`lscpu`, `lspci`, `lsusb`, etc.)
- Potentially requiring `sudo` access for some hardware information

### Data Exposure

The server exposes detailed hardware information that could potentially be used for:

- System fingerprinting
- Identifying specific hardware vulnerabilities
- Understanding system architecture for targeted attacks

### Mitigation

- Run the server with minimal required privileges
- Consider filtering sensitive hardware information in production environments
- Monitor access to the MCP server endpoints
- Regularly update system utilities used by the server
