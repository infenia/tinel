# Branch Protection Configuration

This document outlines the recommended branch protection rules for the Tinel repository to ensure code quality and security.

## Main Branch Protection Rules

Configure the following settings for the `main` branch in GitHub repository settings:

### General Settings
- **Restrict pushes that create files to the repository**: ✅ Enabled
- **Restrict pushes to matching branches**: ✅ Enabled

### Branch Protection Rules for `main`

#### Protect matching branches
- **Require a pull request before merging**: ✅ Enabled
  - **Require approvals**: ✅ Enabled (minimum 2 reviewers)
  - **Dismiss stale reviews when new commits are pushed**: ✅ Enabled
  - **Require review from code owners**: ✅ Enabled
  - **Restrict reviews to users with write access**: ✅ Enabled
  - **Allow specified actors to bypass required pull requests**: ❌ Disabled

#### Status Checks
- **Require status checks to pass before merging**: ✅ Enabled
- **Require branches to be up to date before merging**: ✅ Enabled

**Required Status Checks:**
- `Quality Gates (Python 3.11)`
- `Quality Gates (Python 3.12)`
- `Quality Gates (Python 3.13)`
- `Build & Security Scan`
- `Integration & E2E Tests (integration)`
- `Integration & E2E Tests (performance)`
- `Integration & E2E Tests (security)`
- `Documentation Build & Validation`
- `Dependency Security Analysis`
- `Secret & Credential Detection`
- `Static Security Analysis`
- `Container Security Scanning`
- `Security Compliance & Reporting`

#### Additional Restrictions
- **Restrict pushes to matching branches**: ✅ Enabled
- **Allow force pushes**: ❌ Disabled
- **Allow deletions**: ❌ Disabled
- **Do not allow bypassing the above settings**: ✅ Enabled

## Develop Branch Protection Rules

Configure similar rules for the `develop` branch with slightly relaxed settings:

#### Protect matching branches
- **Require a pull request before merging**: ✅ Enabled
  - **Require approvals**: ✅ Enabled (minimum 1 reviewer)
  - **Dismiss stale reviews when new commits are pushed**: ✅ Enabled
  - **Require review from code owners**: ✅ Enabled

#### Status Checks
- **Require status checks to pass before merging**: ✅ Enabled
- **Required Status Checks:**
  - `Quality Gates (3.12)` (at minimum)
  - `Code Quality Analysis`
  - `Test Coverage Analysis`

## Repository-Level Security Settings

### General Security Settings
- **Enable vulnerability alerts**: ✅ Enabled
- **Enable Dependabot security updates**: ✅ Enabled
- **Enable Dependabot version updates**: ✅ Enabled (configured via `.github/dependabot.yml`)

### Actions Settings
- **Allow actions and reusable workflows**: Select "Allow actions from GitHub, and select third-party actions"
- **Allow actions created by GitHub**: ✅ Enabled
- **Allow actions by Marketplace verified creators**: ✅ Enabled
- **Allow specified actions and reusable workflows**: Configure allowlist if needed

### Secrets and Variables
Configure the following repository secrets:
- `CODECOV_TOKEN`: Token for Codecov integration
- `GITLEAKS_LICENSE`: License for GitLeaks (if applicable)

## Code Owners Configuration

Create a `.github/CODEOWNERS` file with the following content:

```
# Global code owners
* @infenia/tinel-maintainers

# Security-sensitive files
/.github/ @infenia/tinel-security-team
/SECURITY.md @infenia/tinel-security-team
/.github/workflows/security.yml @infenia/tinel-security-team

# Core system components
/tinel/interfaces.py @infenia/tinel-core-team
/tinel/system.py @infenia/tinel-core-team

# Hardware analysis modules
/tinel/hardware/ @infenia/tinel-hardware-team

# CI/CD and build configuration
/.github/workflows/ @infenia/tinel-devops-team
/noxfile.py @infenia/tinel-devops-team
/pyproject.toml @infenia/tinel-devops-team
```

## Environment Protection Rules

For production deployments, configure environment protection rules:

### Production Environment
- **Required reviewers**: Minimum 2 from `@infenia/tinel-maintainers`
- **Wait timer**: 10 minutes
- **Deployment branches**: Only `main` branch

### Staging Environment  
- **Required reviewers**: Minimum 1 from `@infenia/tinel-maintainers`
- **Deployment branches**: `main` and `develop` branches

## Enforcement Guidelines

### Pull Request Requirements
1. All PRs must pass the complete CI/CD pipeline
2. Security scans must pass without high-severity issues
3. Code coverage must maintain 100% threshold
4. All linting and formatting checks must pass
5. Type checking must pass without errors

### Review Requirements
1. At least 2 approving reviews for `main` branch
2. At least 1 approving review for `develop` branch
3. Security-sensitive changes require review from security team
4. Core component changes require review from core team

### Automated Enforcement
- Dependabot PRs can be auto-merged if all checks pass
- Security vulnerability PRs are created automatically
- Failed security scans block merging
- Coverage drops below threshold block merging

## Setup Instructions

To apply these settings:

1. Go to repository Settings → Branches
2. Click "Add rule" for each branch (`main`, `develop`)
3. Configure settings as outlined above
4. Go to Settings → Actions → General to configure Actions permissions
5. Go to Settings → Code security and analysis to enable security features
6. Create the required secrets in Settings → Secrets and variables → Actions
7. Create `.github/CODEOWNERS` file with appropriate team assignments

## Monitoring and Maintenance

- Review branch protection effectiveness monthly
- Update status check requirements when workflows change
- Monitor security scan results and adjust thresholds as needed
- Review and update team assignments in CODEOWNERS quarterly