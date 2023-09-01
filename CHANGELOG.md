# Changelog

## [2.69.1](https://github.com/Flagsmith/flagsmith/compare/v2.69.0...v2.69.1) (2023-09-01)


### Bug Fixes

* Announcement desing ([#2721](https://github.com/Flagsmith/flagsmith/issues/2721)) ([45844d2](https://github.com/Flagsmith/flagsmith/commit/45844d2105534a6fe7819f4817de59816ca486dd))
* Button to go to the link doesnt close the announcement ([#2724](https://github.com/Flagsmith/flagsmith/issues/2724)) ([b7c92df](https://github.com/Flagsmith/flagsmith/commit/b7c92df09f02bdcbeab7a7b0b9c5f1491b1d5dff))
* make `OrganisationSubscriptionInformationCache.allowed_projects` nullable ([#2716](https://github.com/Flagsmith/flagsmith/issues/2716)) ([1b37c99](https://github.com/Flagsmith/flagsmith/commit/1b37c99d93471def56a5042afb78e15cc2d7727e))
* prevent error when addons is null ([#2722](https://github.com/Flagsmith/flagsmith/issues/2722)) ([003d782](https://github.com/Flagsmith/flagsmith/commit/003d7824acf5d3242d79664dde7ff51f9b2a1ac6))

## [2.69.0](https://github.com/Flagsmith/flagsmith/compare/v2.68.0...v2.69.0) (2023-08-31)


### Features

* Home page announcement ([#2710](https://github.com/Flagsmith/flagsmith/issues/2710)) ([9de235b](https://github.com/Flagsmith/flagsmith/commit/9de235b6cc68f6b467c7ccc7db3317b069c6dbd6))
* **master-api-key/roles:** Add roles to master api key ([#2436](https://github.com/Flagsmith/flagsmith/issues/2436)) ([a46295b](https://github.com/Flagsmith/flagsmith/commit/a46295b885ecaf2a40a2f626a46c3a46a323f833))
* Use get-metadata-subscription to get max_api_calls ([#2279](https://github.com/Flagsmith/flagsmith/issues/2279)) ([42049fc](https://github.com/Flagsmith/flagsmith/commit/42049fcca8372dc32b4dab0fb350b9d8dc15ab34))


### Bug Fixes

* ensure feature segments are cloned correctly ([#2706](https://github.com/Flagsmith/flagsmith/issues/2706)) ([414e62f](https://github.com/Flagsmith/flagsmith/commit/414e62f6821efb9bf85dfc72a1f76625c6e96b20))
* **env-clone/permission:** allow clone using CREATE_ENVIRONMENT ([#2675](https://github.com/Flagsmith/flagsmith/issues/2675)) ([edc3afc](https://github.com/Flagsmith/flagsmith/commit/edc3afcb84b624aedbc9af56861cc1eb0f60dcf3))
* environment document totals ([#2671](https://github.com/Flagsmith/flagsmith/issues/2671)) ([33c9bf2](https://github.com/Flagsmith/flagsmith/commit/33c9bf22dce4ff50e0e01a9c1351b31aee41411d))
* settings page margin ([#2707](https://github.com/Flagsmith/flagsmith/issues/2707)) ([ef0ca42](https://github.com/Flagsmith/flagsmith/commit/ef0ca42bad1c58d4ab7730bbf021c4ace3357315))

## [2.68.0](https://github.com/Flagsmith/flagsmith/compare/v2.67.0...v2.68.0) (2023-08-22)


### Features

* admin action to delete all segments for project ([#2646](https://github.com/Flagsmith/flagsmith/issues/2646)) ([4df1b80](https://github.com/Flagsmith/flagsmith/commit/4df1b8037796b1304ce2dc4353c51bc7a67b1178))
* re-add totals and limits ([#2631](https://github.com/Flagsmith/flagsmith/issues/2631)) ([7a6a2c8](https://github.com/Flagsmith/flagsmith/commit/7a6a2c8f929bc079526a852494e3cfb87f796fb3))


### Bug Fixes

* **frontend:** Disabled loading indicator when getting featuers so screen doesn't flicker ([#2598](https://github.com/Flagsmith/flagsmith/issues/2598)) ([830e899](https://github.com/Flagsmith/flagsmith/commit/830e8991e7526a0e05cbbcef22110189d4a8ba55))
* **password-reset:** rate limit password reset emails ([#2619](https://github.com/Flagsmith/flagsmith/issues/2619)) ([db98743](https://github.com/Flagsmith/flagsmith/commit/db98743d426c0ded932d5a624cf8bd00cf2c6a86))
* total api calls handling ([#2583](https://github.com/Flagsmith/flagsmith/issues/2583)) ([ff0da20](https://github.com/Flagsmith/flagsmith/commit/ff0da20c57c4d37829e6d32e60db35886529fc86))
* **user-create:** duplicate email error message ([#2642](https://github.com/Flagsmith/flagsmith/issues/2642)) ([7b65a8d](https://github.com/Flagsmith/flagsmith/commit/7b65a8d7d7b0a2d6b938170a67ba6cabc32d00df))

## [2.67.0](https://github.com/Flagsmith/flagsmith/compare/v2.66.2...v2.67.0) (2023-08-15)


### Features

* Compare identities ([#2616](https://github.com/Flagsmith/flagsmith/issues/2616)) ([aafce13](https://github.com/Flagsmith/flagsmith/commit/aafce134fd2d078fe244e6ed983e2f05cfff820b))


### Bug Fixes

* update POETRY_OPTS in private cloud build ([#2624](https://github.com/Flagsmith/flagsmith/issues/2624)) ([d76f84c](https://github.com/Flagsmith/flagsmith/commit/d76f84c202641011443831f5edd912bec01cd64f))

## [2.66.2](https://github.com/Flagsmith/flagsmith/compare/v2.66.1...v2.66.2) (2023-08-10)


### Bug Fixes

* revert totals attributes ([#2625](https://github.com/Flagsmith/flagsmith/issues/2625)) ([3905527](https://github.com/Flagsmith/flagsmith/commit/39055275d18023702b9906991ad418cb2857088f))

## [2.66.1](https://github.com/Flagsmith/flagsmith/compare/v2.66.0...v2.66.1) (2023-08-10)


### Bug Fixes

* issue retrieving project with master api key ([#2623](https://github.com/Flagsmith/flagsmith/issues/2623)) ([1514bf7](https://github.com/Flagsmith/flagsmith/commit/1514bf735d670de67b847873061797608387f039))
* update auth controller vars in private cloud image build ([#2620](https://github.com/Flagsmith/flagsmith/issues/2620)) ([863c863](https://github.com/Flagsmith/flagsmith/commit/863c863ef6b595c24f8cf1de95a851f9de6b2f0a))

## [2.66.0](https://github.com/Flagsmith/flagsmith/compare/v2.65.0...v2.66.0) (2023-08-10)


### Features

* add limits and totals to API responses ([#2615](https://github.com/Flagsmith/flagsmith/issues/2615)) ([321d435](https://github.com/Flagsmith/flagsmith/commit/321d43537a049bd8b8efecad1619e7b32aa0bf33))
* Migrate to poetry ([#2214](https://github.com/Flagsmith/flagsmith/issues/2214)) ([0754071](https://github.com/Flagsmith/flagsmith/commit/0754071edebaca400c0fb2db1169de0495a2c33b))


### Bug Fixes

* Associated segment overrides ([#2582](https://github.com/Flagsmith/flagsmith/issues/2582)) ([707d394](https://github.com/Flagsmith/flagsmith/commit/707d3949a93e2041b3b25ee71a3f1693a311772f))
* metadata validation causes AttributeError for patch requests ([#2614](https://github.com/Flagsmith/flagsmith/issues/2614)) ([5e13707](https://github.com/Flagsmith/flagsmith/commit/5e13707b911a53924496a2e57e72b436b4dec510))
* variation value overflow ([#2612](https://github.com/Flagsmith/flagsmith/issues/2612)) ([863161b](https://github.com/Flagsmith/flagsmith/commit/863161b60b31db9defb751da852d9835e20f6746))

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
