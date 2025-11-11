---
title: Release Notes
sidebar_position: 3
---

We follow the [SemVer](https://semver.org/) version naming strategy.

Please follow our [GitHub Releases](https://github.com/Flagsmith/flagsmith/releases) page for detailed change logs.

:::important

This page provides an overview of recent releases. For the most up-to-date and detailed information, please refer to our [GitHub Releases](https://github.com/Flagsmith/flagsmith/releases) and [Changelog](https://github.com/Flagsmith/flagsmith/blob/main/CHANGELOG.md) pages.

:::

## Recent Releases

### v2.184.0 (18 June 2025)

**Features:**
- Add `make` shortcut to run both API and worker
- Add wait for trigger to release pipelines
- Frontend report environment metrics
- Integrate with Sentry feature flag Change Tracking
- Release Pipelines UI

**Bug Fixes:**
- Deduplicate metrics live features states
- Fix Sentry Change Tracking response handling
- Handle (ignore) unrecognised analytics data
- Handle bad input before checking permission
- Use query from workflow list change request

### v2.183.0 (10 June 2025)

**Features:**
- Report environment metrics API

**Bug Fixes:**
- Disable e2e tests in draft PRs
- Silence warning when receiving analytics for unknown flags

### v2.182.0 (4 June 2025)

**Features:**
- Track welcome page tasks and integrations

**Bug Fixes:**
- Fix Launch Darkly importer rate limit handling

### v2.181.0 (4 June 2025)

**Features:**
- Welcome page

**Bug Fixes:**
- Adjust Flagsmith client URL
- Fix identities endpoint not respecting deleted segment overrides
- Fix Launch Darkly importer rate limit responses

### v2.180.0 (3 June 2025)

**Features:**
- Launch Darkly importer: Support large segments import and other improvements

**Bug Fixes:**
- Hide billing periods if subscription has no periods
- Hide dropdown caret if no text content
- Improve audit logs when postponing scheduled Change Requests
- Raise 404 if org does not have billing periods
- Update prevent signups and invitation documentation

## Release Schedule

We typically release new versions every 1-2 weeks. Major releases are planned quarterly and include significant new features or breaking changes.

### Release Types

- **Patch releases** (e.g., 2.184.1): Bug fixes and minor improvements
- **Minor releases** (e.g., 2.185.0): New features and improvements
- **Major releases** (e.g., 3.0.0): Breaking changes and major new features

## Breaking Changes

When we introduce breaking changes, we'll:

1. Announce them in advance through our blog and GitHub issues
2. Provide migration guides
3. Maintain backward compatibility where possible
4. Give plenty of notice before removing deprecated features

## Release Process

1. **Development**: Features are developed in feature branches
2. **Testing**: All changes go through automated and manual testing
3. **Review**: Code is reviewed by the team
4. **Release**: Releases are tagged and published to GitHub
5. **Documentation**: Release notes are updated and documentation is revised

## Getting Notified

- **GitHub**: Watch the [Flagsmith repository](https://github.com/Flagsmith/flagsmith) for release notifications
- **Discord**: Join our [Discord community](https://discord.gg/hFhxNtXzgm) for announcements
- **Blog**: Follow our [blog](https://flagsmith.com/blog/) for major release announcements
- **Email**: Sign up for our newsletter for important updates

## Previous Releases

For a complete history of all releases, please see our [GitHub Releases page](https://github.com/Flagsmith/flagsmith/releases) or the [full changelog](https://github.com/Flagsmith/flagsmith/blob/main/CHANGELOG.md).

### Notable Past Releases

- **v2.48** (14 March 2023): Feature name validation, user improvements
- **v2.47** (6 March 2023): Upgrade to Python 3.11
- **v2.46** (3 March 2023): Add ability to store usage data in Postgres
- **v2.45** (2 March 2023): Real-time flags, scheduled change requests
- **v2.44** (1 March 2023): Bug fixes for multivariate flag values

## Support

If you encounter issues with a specific release:

1. Check the [GitHub issues](https://github.com/Flagsmith/flagsmith/issues) for known problems
2. Search our [Discord community](https://discord.gg/hFhxNtXzgm) for solutions
3. Open a new issue if the problem hasn't been reported
4. Consider downgrading to a previous stable release if needed

We're committed to maintaining stable releases and providing timely bug fixes. Thank you for using Flagsmith! 🚀
