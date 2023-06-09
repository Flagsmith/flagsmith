# Releases

We have a fairly standard tagging strategy:

- Git tags created from the `main` branch trigger Docker image builds tagged `latest`.
- Git tags e.g. `2.7.1` will trigger Docker image builds tagged:
  - `2.7.1`
  - `2.7`

Please look out our [Github Releases](https://github.com/Flagsmith/flagsmith/releases) page for detailed change logs.

## v2.48

Released **14 March 2023**

- Feature name validation
- Show 'last logged in' on users area
- Hide disabled Flags per Environment
- Rename Users > Identities in the nav for consistency
- Various bug fixes

## v2.47

Released **6 March 2023**

- Upgrade to Python 3.11

## v2.46

Released **3 March 2023**

- Add ability to store usage data in Postgres

## v2.45

Released **2 March 2023**

- Real time flags
- Scheduled Change requests split out from regular Change Requests
- Generic meta-data to entity models - backend implemented

## v2.44

Released **1 March 2023**

- Bug fixes for multivariate flag values
- Permission tweaks
- Bug fixes soft-delete edge cases

## v2.43

Released **20 February 2023**

- Improve caching
- Security patches

## v2.42

Released **20 February 2023**

- Big Audit Log refactor
- Datadog Dashboard Widget
- Add soft delete to core model entities

## v2.41

Released **4 January 2023**

- Add ability to validate feature names using regex
- Add View identities permission
- Fix security issue creating unauthorised Terraform API keys

## v2.40

Released **20 December 2022**

- Add 'Manage user groups' permission
- Add setting to allow upper case characters to be used in feature names
- Display traits with a float value correctly in UI

## v2.39

Released **6 December 2022**

- Add option to add DB read replicas
- Add description field to segment condition
- Expire user cookies after 30 days of inactivity

## v2.38

Released **29 November 2022**

- Fix missing invite users button

## v2.37

Released **22 November 2022**

- Add segment support for Terraform integration
- Add ability to rotate personal API tokens
- Performance optimisations for retrieving segments for an identity
- UI improvements for settings

## v2.36

Released **11 November 2022**

- Add read only view for features
- Performance optimisations for updating identity traits
- Prevent invite links creation in the API
- Make master API keys read only

## v2.35

Released **8 November 2022**

- Add option to hide invite links
- Add SAML group sync (SaaS / Private cloud only)
- Multivariate feature management fixes
- Add more tag colours

## v2.34

Released **25 October 2022**

- Add functionality to include a permission group when inviting users via email
- Performance optimisations for update-traits endpoint
- Remove user traits panel from dashboard
- Add ability to invalidate / regenerate invite links
- Performance optimisations for listing segments
- Performance optimisations for /traits/bulk endpoint
- Add expiring cache options for flags and identities endpoints

## v2.33

Released **20 October 2022**

- Add functionality to support adding users to a default user group on joining an organisation
- Add new index to identites to improve dashboard performance
- IS_SET and IS_NOT_SET segment operators
- Add statsd metrics

## v2.32

Released **6 October 2022**

- Mixpanel integration payload fix
- Add fix for testing webhooks in UI when webhook has basic authentication
- Add MV options support for Terraform

## v2.31

Released **29 September 2022**

- Permissions fix for identity feature states view
- Percentage split operator fix for 0 value
- Added modulo operator for segment engine
- create / approve change request permissions

## v2.30

Released **13 September 2022**

- Add support for managing project features in Terraform
- Feature specific segments
- Add audit log records for Change Requests
- Add setting to prevent flag defaults being set in all environments when creating a feature

## v2.29

Released **8 August 2022**

- Async processor core engine
- Allow Segment overrides when viewing associated Features for a Segment
- Allow users with CREATE_FEATURE permission to manage multivariate options

## v2.28

Released **8 July 2022**

- Import/Export data improvements
- Export organisation to AWS S3
- Show associated Segments in Features
- Add management command to import organisation
- Add manage Segments permissions
- Show Segment Identity Sampling
- Prevent null feature type
- (Enterprise only) Add LDAP username/password
- (Enterprise only) LDAP permission group syncing fixes

## v2.27

Released **1 July 2022**

- Add ability to export and import data for an organisation
- Allow Environments to prevent clients from setting Traits

## v2.26

Released **22 June 2022**

- Bug Fixes

## v2.25

Released **17 June 2022**

- Filter tags
- Added user-managed "Beta Features"
- Prevent users on free plans from setting minimum_change_request_approvals

## v2.24

Released **1 June 2022**

- Segments overrides can now take Multi-Variate percentages
- RBAC updates
- Allow custom headers in CORS restrictions

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

- Server-side SDK keys Frontend developed
- Improved Segment Rules evaluation
- Multiple Dependency Updates

## v2.17

Released **8 February 2022**

- Webhook Analytics Integration
- Audit Log Search is now Server-side
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
