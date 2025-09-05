# E2E Test Video Recording

This document explains how video recording works for failed E2E tests in GitHub Actions.

## Overview

The E2E tests are configured to automatically record videos of **failed tests only** and upload them to both Slack and GitHub Actions artifacts for debugging purposes.

## How it works

1. **TestCafe Configuration**: The `.testcaferc.js` file is configured with:
   - `failedOnly: true` - Only records videos when tests fail
   - Videos are saved to `reports/screen-captures/`
   - Files are named with environment, timestamp, and test index for easy identification

2. **Dual Upload System**: 
   - **Slack**: Videos are uploaded to the team's Slack channel
   - **GitHub Actions**: Videos are also uploaded as artifacts for easy access
   - Both uploads happen automatically

3. **GitHub Actions Artifacts**: 
   - Videos are automatically uploaded as artifacts when tests fail
   - Artifacts are retained for 30 days
   - Different workflows use different artifact names:
     - `e2e-failed-test-videos-{environment}-{run_attempt}` for direct e2e-tests action
     - `e2e-failed-test-videos-docker-{run_attempt}` for Docker-based tests
     - `e2e-failed-test-videos-manual-{run_attempt}` for manual test runs

## Accessing Video Recordings

### GitHub Actions Artifacts
1. Go to the failed GitHub Actions run
2. Scroll down to the "Artifacts" section at the bottom of the run page
3. Download the video artifact(s) to view the recordings of failed tests

### Slack
Videos are automatically posted to the team's Slack channel.

## Benefits

- **Multiple Access Points**: Videos available both in Slack and GitHub Actions
- **Better Accessibility**: Team members can access videos directly from the GitHub Actions run
- **Extended Retention**: 30-day retention in GitHub Actions provides longer access

## Configuration

The video recording behavior is controlled by:
- TestCafe configuration in `.testcaferc.js` - controls video quality, path, and naming
- GitHub Actions workflow files - handle the artifact upload

## Video Settings

- **Format**: MP4
- **Frame rate**: 20 FPS
- **Aspect ratio**: 4:3
- **Recording**: Only when tests fail
- **Retention**: 30 days in GitHub Actions, standard Slack retention for Slack uploads

## Troubleshooting

- If no videos appear in artifacts, check that tests actually failed (videos are only recorded on failure)
- For Docker-based tests, ensure the video extraction step completed successfully
- Check the test logs for any video-related error messages
- Slack uploads work independently of GitHub Actions artifacts
