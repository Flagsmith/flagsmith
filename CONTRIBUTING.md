# Contributing Guide

We're always looking to improve this project, and we welcome your participation! Flagsmith accepts contributions via GitHub pull requests (PRs). This guide is intended to help ensure the success of your contribution.

## Create an issue

Before opening a PR, we encourage you to [create an issue](https://github.com/Flagsmith/flagsmith/issues/new/choose) describing your problem or feature request.

We don't leave PRs unattended, but it will be easier for us to prioritise a review of your PR when there is a relevant issue at hand.

You can submit a PR directly for problems such as spelling mistakes or other things where it's clear what the problem is.

If you decide to create an issue, be sure to search for an existing one first.

## Find an issue

If you are prepared to contribute but are uncertain as to how, consider narrowing your search with issue filters. For instance:
- [is:issue state:open type:Bug no:assignee](https://github.com/Flagsmith/flagsmith/issues?q=is%3Aissue%20state%3Aopen%20type%3ABug%20no%3Aassignee) includes all current bugs.
- [is:issue state:open label:"good first issue" no:assignee](https://github.com/Flagsmith/flagsmith/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22good%20first%20issue%22%20no%3Aassignee) lists issues we think are good for newcomers.

## Submit a PR

1. The target branch should always be set to `main`, unless otherwise asked in the respective issue.
1. An approved PR is eventually merged into `main`. Documentation changes will get deployed immediately afterwards. Your frontend changes will get deployed to SaaS, and you can expect both backend and frontend changes to be included in the next release.

To learn how we write PR titles and descriptions, structure reviews, and address feedback, see [PR_COLLABORATION.md](https://github.com/Flagsmith/AGENTS.md/blob/main/PR_COLLABORATION.md). It's the guide our team and review agents follow, and we encourage you to follow it as well.

## Setup local development

The development tooling is intended for use with Linux or macOS, and [GNU Make](https://www.gnu.org/software/make/). Consider using Windows Subsystem for Linux (WSL) to develop on Windows.

To install Git hooks, run `make install-hooks`.

Each component provides its own Makefile in its respective subdirectory, and documents its usage and dependencies in a `README.md` file.
