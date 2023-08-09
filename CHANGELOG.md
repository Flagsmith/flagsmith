# Changelog

## [2.67.0](https://github.com/dabeeeenster/flagsmith/compare/v2.66.0...v2.67.0) (2023-08-09)


### Features

* test8 ([#12](https://github.com/dabeeeenster/flagsmith/issues/12)) ([cfb4997](https://github.com/dabeeeenster/flagsmith/commit/cfb4997b5d023578e53f3b9d6f8db6fec8756057))
* test9 ([#14](https://github.com/dabeeeenster/flagsmith/issues/14)) ([32a0eb9](https://github.com/dabeeeenster/flagsmith/commit/32a0eb92dccb4fea750d3c28cb17f62d0e873478))

## [2.66.0](https://github.com/dabeeeenster/flagsmith/compare/v2.65.0...v2.66.0) (2023-08-09)


### Features

* add descriptive event title to dynatrace integration ([#2424](https://github.com/dabeeeenster/flagsmith/issues/2424)) ([f1dba53](https://github.com/dabeeeenster/flagsmith/commit/f1dba5376b4bf1d2e9115f08998c8170678a8a80))
* Adjust AWS payment settings ([#2400](https://github.com/dabeeeenster/flagsmith/issues/2400)) ([de4618d](https://github.com/dabeeeenster/flagsmith/commit/de4618d02fbdffd774e7a34047590921c4c5bf4f))
* Bake enterprise version info into private cloud image ([#2420](https://github.com/dabeeeenster/flagsmith/issues/2420)) ([acebf93](https://github.com/dabeeeenster/flagsmith/commit/acebf939d80503d1b1fd964135646d06c7d0cb04))
* **integrations:** add support for Amplitude base url ([#2534](https://github.com/dabeeeenster/flagsmith/issues/2534)) ([5d52564](https://github.com/dabeeeenster/flagsmith/commit/5d5256483dd99d05ceaf4cb08ea66191b1cbc852))
* **limits:** Add limits to features, segments and segment overrides ([#2480](https://github.com/dabeeeenster/flagsmith/issues/2480)) ([d150c7f](https://github.com/dabeeeenster/flagsmith/commit/d150c7f6c4b5e2336518b4dfba7895c61c2737a1))
* Migrate to poetry ([#2214](https://github.com/dabeeeenster/flagsmith/issues/2214)) ([0754071](https://github.com/dabeeeenster/flagsmith/commit/0754071edebaca400c0fb2db1169de0495a2c33b))
* **tests:** test coverage ([#2482](https://github.com/dabeeeenster/flagsmith/issues/2482)) ([1389c6e](https://github.com/dabeeeenster/flagsmith/commit/1389c6eb8e39920fcc962c73c71fa096b902c260))
* Use isEnterprise from endpoint version response to determine permissions ([#2422](https://github.com/dabeeeenster/flagsmith/issues/2422)) ([edf38ac](https://github.com/dabeeeenster/flagsmith/commit/edf38ac8114a7148991ee47b216fa67a5ffd5e95))


### Bug Fixes

* (sales dashboard) correct api call overage data  ([#2434](https://github.com/dabeeeenster/flagsmith/issues/2434)) ([c55e675](https://github.com/dabeeeenster/flagsmith/commit/c55e675b023567b38e9750a3a5cc6b0a1859c209))
* allow creating integration configurations where deleted versions exist ([#2531](https://github.com/dabeeeenster/flagsmith/issues/2531)) ([3430829](https://github.com/dabeeeenster/flagsmith/commit/34308293a2b3a5dfa8f4b764e847e6cd297279ed))
* Allow signups when invited and in PREVENT_SIGNUP mode ([#2448](https://github.com/dabeeeenster/flagsmith/issues/2448)) ([10719eb](https://github.com/dabeeeenster/flagsmith/commit/10719ebb89eccb7bed83e5c43055d98c14724748))
* Associated segment overrides ([#2582](https://github.com/dabeeeenster/flagsmith/issues/2582)) ([707d394](https://github.com/dabeeeenster/flagsmith/commit/707d3949a93e2041b3b25ee71a3f1693a311772f))
* change request audit logs ([#2527](https://github.com/dabeeeenster/flagsmith/issues/2527)) ([d7c459e](https://github.com/dabeeeenster/flagsmith/commit/d7c459ed4f43b57d61259692a1efb5363a4f4d41))
* ensure recurring tasks are unlocked after being picked up (but not executed) ([#2508](https://github.com/dabeeeenster/flagsmith/issues/2508)) ([24c21ea](https://github.com/dabeeeenster/flagsmith/commit/24c21ead348f5c3dc190468309459611336c4856))
* ensure relevant email domains are not sent to Pipedrive ([#2431](https://github.com/dabeeeenster/flagsmith/issues/2431)) ([3a4d8cb](https://github.com/dabeeeenster/flagsmith/commit/3a4d8cbe8889389bbd7aefd9676f8c12cedf3c52))
* ensure that migrate command exits with non zero error code ([#2578](https://github.com/dabeeeenster/flagsmith/issues/2578)) ([6c96ccf](https://github.com/dabeeeenster/flagsmith/commit/6c96ccfbb70e559b3b525e683563217f85fd406d))
* environment webhooks shows current date, not created date ([#2555](https://github.com/dabeeeenster/flagsmith/issues/2555)) ([94fb957](https://github.com/dabeeeenster/flagsmith/commit/94fb957e2beafaa2e303e63d0e9fc954e37daf85))
* Highlight encoding ([#2558](https://github.com/dabeeeenster/flagsmith/issues/2558)) ([717f175](https://github.com/dabeeeenster/flagsmith/commit/717f17579eb08d403439b51b932692eb8a118b90))
* **infra:** reduce number of threads per processor and increase sleep interval ([#2486](https://github.com/dabeeeenster/flagsmith/issues/2486)) ([dd2516b](https://github.com/dabeeeenster/flagsmith/commit/dd2516b222785dbc62003c9d054716f1c7d32e44))
* percentage allocation display ([#2518](https://github.com/dabeeeenster/flagsmith/issues/2518)) ([f8b1d50](https://github.com/dabeeeenster/flagsmith/commit/f8b1d50a62ec08bb1df8b00b9ba1edcc1b91aeb5))
* re-add EDGE_API_URL to api service task definition ([#2475](https://github.com/dabeeeenster/flagsmith/issues/2475)) ([9554864](https://github.com/dabeeeenster/flagsmith/commit/95548642edb40b5ec2fffdb6c1dcdab82a083181))
* rendering recurring task admin times out ([#2514](https://github.com/dabeeeenster/flagsmith/issues/2514)) ([cb95a92](https://github.com/dabeeeenster/flagsmith/commit/cb95a925cc8907a8f37f76f48a840261c467372d))
* revert EDGE_API_URL removal and reduce timeout further to 0.1s ([#2467](https://github.com/dabeeeenster/flagsmith/issues/2467)) ([fc81925](https://github.com/dabeeeenster/flagsmith/commit/fc819257bbe41d15f208376ed451045b26015a41))
* **roles/org-permission:** Add missing viewset ([#2495](https://github.com/dabeeeenster/flagsmith/issues/2495)) ([2b56c7c](https://github.com/dabeeeenster/flagsmith/commit/2b56c7cc52631686f8b28e9cdb03c7203ec6abdb))
* Sanitize HTML tooltips ([#2538](https://github.com/dabeeeenster/flagsmith/issues/2538)) ([f68ea54](https://github.com/dabeeeenster/flagsmith/commit/f68ea5426a0fe704276725b29c5d1b4fad9aeb35))
* **SwaggerGenerationError:** Remove filterset_field ([#2539](https://github.com/dabeeeenster/flagsmith/issues/2539)) ([6dba7bd](https://github.com/dabeeeenster/flagsmith/commit/6dba7bdd0563a4916d9185555512d21e6d77643c))
* **tests:** support any webhook order ([#2524](https://github.com/dabeeeenster/flagsmith/issues/2524)) ([da2b4a7](https://github.com/dabeeeenster/flagsmith/commit/da2b4a7128a7b40605eed04774a703839777a841))
* Update Hyperlink "Learn about Audit Webhooks" URL ([#2504](https://github.com/dabeeeenster/flagsmith/issues/2504)) ([9ec20b5](https://github.com/dabeeeenster/flagsmith/commit/9ec20b5214b95a9bfe481ac42511d1ff8fa1b3ea))
* **webhooks:** fix skipping webhooks calls on timeouts ([#2501](https://github.com/dabeeeenster/flagsmith/issues/2501)) ([583e248](https://github.com/dabeeeenster/flagsmith/commit/583e248cda58341b02ceeb5b75945550963a6dba))


### Infrastructure (Flagsmith SaaS Only)

* **task-processor:** bump cpu and memory ([#2472](https://github.com/dabeeeenster/flagsmith/issues/2472)) ([18b8174](https://github.com/dabeeeenster/flagsmith/commit/18b81744704af1c662b2e9bc9421def66ee56da2))

## [2.65.0](https://github.com/Flagsmith/flagsmith/compare/v2.64.1...v2.65.0) (2023-08-04)


### Features

* Use isEnterprise from endpoint version response to determine permissions ([#2422](https://github.com/Flagsmith/flagsmith/issues/2422)) ([edf38ac](https://github.com/Flagsmith/flagsmith/commit/edf38ac8114a7148991ee47b216fa67a5ffd5e95))


### Bug Fixes

* ensure that migrate command exits with non zero error code ([#2578](https://github.com/Flagsmith/flagsmith/issues/2578)) ([6c96ccf](https://github.com/Flagsmith/flagsmith/commit/6c96ccfbb70e559b3b525e683563217f85fd406d))

## [2.64.1](https://github.com/Flagsmith/flagsmith/compare/v2.64.0...v2.64.1) (2023-08-03)


### Bug Fixes

* environment webhooks shows current date, not created date ([#2555](https://github.com/Flagsmith/flagsmith/issues/2555)) ([94fb957](https://github.com/Flagsmith/flagsmith/commit/94fb957e2beafaa2e303e63d0e9fc954e37daf85))
* Highlight encoding ([#2558](https://github.com/Flagsmith/flagsmith/issues/2558)) ([717f175](https://github.com/Flagsmith/flagsmith/commit/717f17579eb08d403439b51b932692eb8a118b90))
* Sanitize HTML tooltips ([#2538](https://github.com/Flagsmith/flagsmith/issues/2538)) ([f68ea54](https://github.com/Flagsmith/flagsmith/commit/f68ea5426a0fe704276725b29c5d1b4fad9aeb35))

## [2.64.0](https://github.com/Flagsmith/flagsmith/compare/v2.63.3...v2.64.0) (2023-07-31)


### Features

* **integrations:** add support for Amplitude base url ([#2534](https://github.com/Flagsmith/flagsmith/issues/2534)) ([5d52564](https://github.com/Flagsmith/flagsmith/commit/5d5256483dd99d05ceaf4cb08ea66191b1cbc852))

## [2.63.3](https://github.com/Flagsmith/flagsmith/compare/v2.63.2...v2.63.3) (2023-07-28)


### Bug Fixes

* allow creating integration configurations where deleted versions exist ([#2531](https://github.com/Flagsmith/flagsmith/issues/2531)) ([3430829](https://github.com/Flagsmith/flagsmith/commit/34308293a2b3a5dfa8f4b764e847e6cd297279ed))
* change request audit logs ([#2527](https://github.com/Flagsmith/flagsmith/issues/2527)) ([d7c459e](https://github.com/Flagsmith/flagsmith/commit/d7c459ed4f43b57d61259692a1efb5363a4f4d41))
* percentage allocation display ([#2518](https://github.com/Flagsmith/flagsmith/issues/2518)) ([f8b1d50](https://github.com/Flagsmith/flagsmith/commit/f8b1d50a62ec08bb1df8b00b9ba1edcc1b91aeb5))
* **roles/org-permission:** Add missing viewset ([#2495](https://github.com/Flagsmith/flagsmith/issues/2495)) ([2b56c7c](https://github.com/Flagsmith/flagsmith/commit/2b56c7cc52631686f8b28e9cdb03c7203ec6abdb))
* **SwaggerGenerationError:** Remove filterset_field ([#2539](https://github.com/Flagsmith/flagsmith/issues/2539)) ([6dba7bd](https://github.com/Flagsmith/flagsmith/commit/6dba7bdd0563a4916d9185555512d21e6d77643c))
* **tests:** support any webhook order ([#2524](https://github.com/Flagsmith/flagsmith/issues/2524)) ([da2b4a7](https://github.com/Flagsmith/flagsmith/commit/da2b4a7128a7b40605eed04774a703839777a841))

## [2.63.2](https://github.com/Flagsmith/flagsmith/compare/v2.63.1...v2.63.2) (2023-07-25)


### Bug Fixes

* ensure recurring tasks are unlocked after being picked up (but not executed) ([#2508](https://github.com/Flagsmith/flagsmith/issues/2508)) ([24c21ea](https://github.com/Flagsmith/flagsmith/commit/24c21ead348f5c3dc190468309459611336c4856))
* rendering recurring task admin times out ([#2514](https://github.com/Flagsmith/flagsmith/issues/2514)) ([cb95a92](https://github.com/Flagsmith/flagsmith/commit/cb95a925cc8907a8f37f76f48a840261c467372d))
* Update Hyperlink "Learn about Audit Webhooks" URL ([#2504](https://github.com/Flagsmith/flagsmith/issues/2504)) ([9ec20b5](https://github.com/Flagsmith/flagsmith/commit/9ec20b5214b95a9bfe481ac42511d1ff8fa1b3ea))

## [2.63.1](https://github.com/Flagsmith/flagsmith/compare/v2.63.0...v2.63.1) (2023-07-21)


### Bug Fixes

* **webhooks:** fix skipping webhooks calls on timeouts ([#2501](https://github.com/Flagsmith/flagsmith/issues/2501)) ([583e248](https://github.com/Flagsmith/flagsmith/commit/583e248cda58341b02ceeb5b75945550963a6dba))

## [2.63.0](https://github.com/Flagsmith/flagsmith/compare/v2.62.5...v2.63.0) (2023-07-21)


### Features

* **limits:** Add limits to features, segments and segment overrides ([#2480](https://github.com/Flagsmith/flagsmith/issues/2480)) ([d150c7f](https://github.com/Flagsmith/flagsmith/commit/d150c7f6c4b5e2336518b4dfba7895c61c2737a1))
* **tests:** test coverage ([#2482](https://github.com/Flagsmith/flagsmith/issues/2482)) ([1389c6e](https://github.com/Flagsmith/flagsmith/commit/1389c6eb8e39920fcc962c73c71fa096b902c260))

## [2.62.5](https://github.com/Flagsmith/flagsmith/compare/v2.62.4...v2.62.5) (2023-07-20)


### Bug Fixes

* **infra:** reduce number of threads per processor and increase sleep interval ([#2486](https://github.com/Flagsmith/flagsmith/issues/2486)) ([dd2516b](https://github.com/Flagsmith/flagsmith/commit/dd2516b222785dbc62003c9d054716f1c7d32e44))

## [2.62.4](https://github.com/Flagsmith/flagsmith/compare/v2.62.3...v2.62.4) (2023-07-19)


### Bug Fixes

* re-add EDGE_API_URL to api service task definition ([#2475](https://github.com/Flagsmith/flagsmith/issues/2475)) ([9554864](https://github.com/Flagsmith/flagsmith/commit/95548642edb40b5ec2fffdb6c1dcdab82a083181))

## [2.62.0](https://github.com/Flagsmith/flagsmith/compare/v2.61.0...v2.62.0) (2023-07-19)


### Features

* add descriptive event title to dynatrace integration ([#2424](https://github.com/Flagsmith/flagsmith/issues/2424)) ([f1dba53](https://github.com/Flagsmith/flagsmith/commit/f1dba5376b4bf1d2e9115f08998c8170678a8a80))


### Bug Fixes

* Allow signups when invited and in PREVENT_SIGNUP mode ([#2448](https://github.com/Flagsmith/flagsmith/issues/2448)) ([10719eb](https://github.com/Flagsmith/flagsmith/commit/10719ebb89eccb7bed83e5c43055d98c14724748))

## [2.61.0](https://github.com/Flagsmith/flagsmith/compare/v2.60.0...v2.61.0) (2023-07-16)


### Features

* Adjust AWS payment settings ([#2400](https://github.com/Flagsmith/flagsmith/issues/2400)) ([de4618d](https://github.com/Flagsmith/flagsmith/commit/de4618d02fbdffd774e7a34047590921c4c5bf4f))
* Bake enterprise version info into private cloud image ([#2420](https://github.com/Flagsmith/flagsmith/issues/2420)) ([acebf93](https://github.com/Flagsmith/flagsmith/commit/acebf939d80503d1b1fd964135646d06c7d0cb04))


### Bug Fixes

* (sales dashboard) correct api call overage data  ([#2434](https://github.com/Flagsmith/flagsmith/issues/2434)) ([c55e675](https://github.com/Flagsmith/flagsmith/commit/c55e675b023567b38e9750a3a5cc6b0a1859c209))
* ensure relevant email domains are not sent to Pipedrive ([#2431](https://github.com/Flagsmith/flagsmith/issues/2431)) ([3a4d8cb](https://github.com/Flagsmith/flagsmith/commit/3a4d8cbe8889389bbd7aefd9676f8c12cedf3c52))


### Documentation

* new architecture diagram ([#2433](https://github.com/Flagsmith/flagsmith/issues/2433)) ([2169340](https://github.com/Flagsmith/flagsmith/commit/21693404229f6705379be093c5a946f7bdcdda5f))
