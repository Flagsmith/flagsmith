# Releases

## Docker Image Tags

We have a fairly simple tagging strategy:

- Commits to the `main` branch trigger Docker image builds tagged `latest`.
- Git tags (e.g. `2.7.1`) will trigger Docker image builds tagged:
  - 2.7.1
  - 2.7

Please look out our [Github Releases](https://github.com/Flagsmith/flagsmith/releases) page for detailed updates.

## v2.23

Released **17 May 2022**

- Security Audit Fixes
- Add cache for returning 403 for unknown Environments in header
- Semver and regex validation

## v2.22

Released **25 April 2022**

- Semantic Version Operators
- Permissions Improvements
- UI improvements

## v2.21

Released **12 April 2022**

- Dropped Python 3.6 support
- Change Requests

## v2.20

Released **7 April 2022**

- Dashboard performance improvements
- Segment Identity Sampling

## v2.19

Released **24 March 2022**

- Dashboard performance improvements
- UI tweaks
- ARM Docker images
- Dynatrace Integration

## v2.18

Released **15 February 2022**

- Serverside SDK keys Frontend developed
- Improved Segment Rules evaluation
- Multiple Dependency Updates

## v2.17

Released **8 February 2022**

- Webhook Analytics Integration
- Audit Log Search is now Serverside
- Improvements to Flag Value Text Editor

## v2.16

Released **31 January 2022**

- Segment Override Permissions Upgrade
- Added lots of 1-click installers (fly.io, render, digital ocean)
- Rudderstack Integration
- New SDK tokens in preparation for SDKv2

## v2.15

Released **22 January 2022**

- Added hostnames to InfluxDB
- Better Env Var handling of SSL and `USE_X_FORWARDED_HOST`

## v2.14

Released **4 January 2022**

- Slack Integration
- Additional Permission Options
- E2E tests moved to TestCafe

## v2.13

Released **8 December 2021**

- Protected Flags
- Compare Environments
- Force 2fa

## v2.12

Released **2 December 2021**

- Environment Variable renaming

## v2.11

Released **18 November 2021**

- Improved Docker Compose
- Heap Integration
- Multiple Dependency Updates

## v2.10

Released **2 November 2021**

- Elixir SDK
- Archive Flags
- Specify Flag Owners
- Database performance improvements
- Permission improvements

## v2.9

Released **23 August 2021**

- Archive flags
- Optionally GZIP responses
- Large number of small bug fixes

## v2.8

Released **28 July 2021**

- SAML Integration (Enterprise version only)

## v2.7

Released **5 May 2021**

- [Multivariate Flags](https://flagsmith.com/blog/introducing-multivariate-flags/)
- Various minor bug fixes

## v2.6

Released **9 Apr 2021**

- Combine Feature Flags and Remote Config
- Dark mode
- Formatter for remote config supporting xml, json, toml and yaml
- Fix Segment override incorrect date
- Add sorting to identity feature list
- Enable SDK analytics based on FLAGSMITH_ANALYTICS env var
- Configurable butter-bar
- Show segment descriptions
- New integrations
  - Mixpanel
  - Heap Analytics
  - New Relic

Breaking changes:

- Segment overrides use new API

## v2.5

Released **20 Jan 2021**

- Add invite via link functionality
- More third party integrations

## v2.4

Released **7 Dec 2020**

This release is the first under our new brand, Flagsmith.

The rebrand comes with no breaking changes, mainly just a refactor to urls and wording, however we have built several
new features and bug fixes since our last release:

- If your api is using influx, we now show usage data in a graph format
  ![image](https://user-images.githubusercontent.com/8608314/101258233-16227880-3719-11eb-86c0-738c43d2ec0f.png)
- New look and feel
- Ability to bulk enable / disable all segment overrides and user overrides for a flag
  ![image](https://user-images.githubusercontent.com/8608314/101258463-87aef680-371a-11eb-9e98-35c976612962.png)
- Sensible page size for the users page
- Improved E2E stability
- Integration page, this page is almost fully managed by remote config. It will allow users t enhance Flagsmith with
  your favourite tools. We currently support data dog and will shortly support amplitude.
  ![image](https://user-images.githubusercontent.com/8608314/101258436-6ea64580-371a-11eb-8afe-3626eb36bbbe.png)

The remote config to use this is as follows:

```json
integrations:

["data_dog"]
```

```json
integration_data
{
    "perEnvironment": false,
    "image": "https://xyz",
    "fields": [
      {
        "key": "base_url",
        "label": "Base URL"
      },
      {
        "key": "api_key",
        "label": "API Key"
      }
    ],
    "tags": [
      "logging"
    ],
    "title": "Data dog",
    "description": "Sends events to Data dog for when flags are created, updated and removed. Logs are tagged with the environment they came from e.g. production."
}
```

## v2.3

Released **9 Nov 2020**

We've added a bunch of new features and bug fixes.

- You can now tag flags with user-defined tags. You can use these tags to manage flags and organise them.
- Beta release of both [Data Dog](https://docs.flagsmith.com/integrations/datadog/) and
  [Amplitude](https://docs.flagsmith.com/integrations/amplitude/) integrations.
- You can now set multiple traits in a single call
- For a given feature, show which Identities have it individually overridden
- When viewing an Identity, show the segments and test whether the identity is a member of each segment

## v2.2

Released **12th June 2020**

- Flags that are defined with Segment overrides are now based on an Environment level, as opposed to a Project level. So
  you can now define Segment overrides differently between Environments
- Redesigned the left hand navigation area
- You can now filter the audit log per flag
- You can jump to a flags audit log from the main features page

## v2.1

Released **28th May 2020**

- Google OAuth2 integration
- 2 Factor authentication
- Influx DB integration for API call statistics
- The API can now set multiple traits in a single API request
- Fixed an issue where webhooks could miss data in a certain scenarios
- Mainly CSS design Tweaks

## v2.0

Released **19th December 2019**

- Removed Flagsmith homepage from Front End App
- Added Webhooks

## v1.9

Released **22nd September 2019**

- Added Segments
- Added Auditing Logs
- Better E2E testing
