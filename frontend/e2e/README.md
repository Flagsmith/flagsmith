# E2E Test Video Recording

This document explains how to access video recordings of failed E2E tests from GitHub Actions.

## Overview

The E2E tests are configured to automatically record videos of **failed tests only** and upload them as GitHub Actions artifacts.

## How it works

**TestCafe Configuration**: The `.testcaferc.js` file is configured with:
- `failedOnly: true` - Only records videos when tests fail.
- Videos are saved to `reports/screen-captures/`.
- Files are named with environment, timestamp, and test index for easy identification.

**GitHub Actions Artifacts**:
- Videos are automatically uploaded as artifacts when tests fail.
- Artifacts are retained for 30 days.
- Different workflows use different artifact names:
  - `e2e-failed-test-videos-{environment}-{run_attempt}` for direct e2e-tests action
  - `e2e-failed-test-videos-docker-{run_attempt}` for Docker-based tests
  - `e2e-failed-test-videos-manual-{run_attempt}` for manual test runs

## Accessing Video Recordings

1. Go to the failed GitHub Actions run.
2. Scroll down to the "Artifacts" section at the bottom of the run page.
3. Download the video artifact(s) to view the recordings of failed tests.

## Configuration

The video recording behavior is controlled by:
- TestCafe configuration in `.testcaferc.js` - controls video quality, path, and naming
- GitHub Actions workflow files - handle the artifact upload

## Video Settings

- **Format**: MP4
- **Frame rate**: 20 FPS
- **Aspect ratio**: 4:3
- **Recording**: Only when tests fail
- **GitHub Actions Retention**: 30 days

## Troubleshooting

- If no videos appear in artifacts, check that tests actually failed (videos are only recorded on failure).
- For Docker-based tests, ensure the video extraction step completed successfully.
- Check the test logs for any video-related error messages.
