# Changelog

## [2.68.0](https://github.com/Flagsmith/flagsmith/compare/v2.67.0...v2.68.0) (2023-08-29)


### Features

* add descriptive event title to dynatrace integration ([#2424](https://github.com/Flagsmith/flagsmith/issues/2424)) ([f1dba53](https://github.com/Flagsmith/flagsmith/commit/f1dba5376b4bf1d2e9115f08998c8170678a8a80))
* add limits and totals to API responses ([#2615](https://github.com/Flagsmith/flagsmith/issues/2615)) ([321d435](https://github.com/Flagsmith/flagsmith/commit/321d43537a049bd8b8efecad1619e7b32aa0bf33))
* Adjust AWS payment settings ([#2400](https://github.com/Flagsmith/flagsmith/issues/2400)) ([de4618d](https://github.com/Flagsmith/flagsmith/commit/de4618d02fbdffd774e7a34047590921c4c5bf4f))
* admin action to delete all segments for project ([#2646](https://github.com/Flagsmith/flagsmith/issues/2646)) ([4df1b80](https://github.com/Flagsmith/flagsmith/commit/4df1b8037796b1304ce2dc4353c51bc7a67b1178))
* Bake enterprise version info into private cloud image ([#2420](https://github.com/Flagsmith/flagsmith/issues/2420)) ([acebf93](https://github.com/Flagsmith/flagsmith/commit/acebf939d80503d1b1fd964135646d06c7d0cb04))
* **integrations:** add support for Amplitude base url ([#2534](https://github.com/Flagsmith/flagsmith/issues/2534)) ([5d52564](https://github.com/Flagsmith/flagsmith/commit/5d5256483dd99d05ceaf4cb08ea66191b1cbc852))
* **limits:** Add limits to features, segments and segment overrides ([#2480](https://github.com/Flagsmith/flagsmith/issues/2480)) ([d150c7f](https://github.com/Flagsmith/flagsmith/commit/d150c7f6c4b5e2336518b4dfba7895c61c2737a1))
* **master-api-key/roles:** Add roles to master api key ([#2436](https://github.com/Flagsmith/flagsmith/issues/2436)) ([a46295b](https://github.com/Flagsmith/flagsmith/commit/a46295b885ecaf2a40a2f626a46c3a46a323f833))
* Migrate to poetry ([#2214](https://github.com/Flagsmith/flagsmith/issues/2214)) ([0754071](https://github.com/Flagsmith/flagsmith/commit/0754071edebaca400c0fb2db1169de0495a2c33b))
* re-add totals and limits ([#2631](https://github.com/Flagsmith/flagsmith/issues/2631)) ([7a6a2c8](https://github.com/Flagsmith/flagsmith/commit/7a6a2c8f929bc079526a852494e3cfb87f796fb3))
* **tests:** test coverage ([#2482](https://github.com/Flagsmith/flagsmith/issues/2482)) ([1389c6e](https://github.com/Flagsmith/flagsmith/commit/1389c6eb8e39920fcc962c73c71fa096b902c260))
* Use get-metadata-subscription to get max_api_calls ([#2279](https://github.com/Flagsmith/flagsmith/issues/2279)) ([42049fc](https://github.com/Flagsmith/flagsmith/commit/42049fcca8372dc32b4dab0fb350b9d8dc15ab34))


### Bug Fixes

* (sales dashboard) correct api call overage data  ([#2434](https://github.com/Flagsmith/flagsmith/issues/2434)) ([c55e675](https://github.com/Flagsmith/flagsmith/commit/c55e675b023567b38e9750a3a5cc6b0a1859c209))
* allow creating integration configurations where deleted versions exist ([#2531](https://github.com/Flagsmith/flagsmith/issues/2531)) ([3430829](https://github.com/Flagsmith/flagsmith/commit/34308293a2b3a5dfa8f4b764e847e6cd297279ed))
* change request audit logs ([#2527](https://github.com/Flagsmith/flagsmith/issues/2527)) ([d7c459e](https://github.com/Flagsmith/flagsmith/commit/d7c459ed4f43b57d61259692a1efb5363a4f4d41))
* ensure recurring tasks are unlocked after being picked up (but not executed) ([#2508](https://github.com/Flagsmith/flagsmith/issues/2508)) ([24c21ea](https://github.com/Flagsmith/flagsmith/commit/24c21ead348f5c3dc190468309459611336c4856))
* ensure that migrate command exits with non zero error code ([#2578](https://github.com/Flagsmith/flagsmith/issues/2578)) ([6c96ccf](https://github.com/Flagsmith/flagsmith/commit/6c96ccfbb70e559b3b525e683563217f85fd406d))
* **env-clone/permission:** allow clone using CREATE_ENVIRONMENT ([#2675](https://github.com/Flagsmith/flagsmith/issues/2675)) ([edc3afc](https://github.com/Flagsmith/flagsmith/commit/edc3afcb84b624aedbc9af56861cc1eb0f60dcf3))
* environment webhooks shows current date, not created date ([#2555](https://github.com/Flagsmith/flagsmith/issues/2555)) ([94fb957](https://github.com/Flagsmith/flagsmith/commit/94fb957e2beafaa2e303e63d0e9fc954e37daf85))
* issue retrieving project with master api key ([#2623](https://github.com/Flagsmith/flagsmith/issues/2623)) ([1514bf7](https://github.com/Flagsmith/flagsmith/commit/1514bf735d670de67b847873061797608387f039))
* metadata validation causes AttributeError for patch requests ([#2614](https://github.com/Flagsmith/flagsmith/issues/2614)) ([5e13707](https://github.com/Flagsmith/flagsmith/commit/5e13707b911a53924496a2e57e72b436b4dec510))
* **password-reset:** rate limit password reset emails ([#2619](https://github.com/Flagsmith/flagsmith/issues/2619)) ([db98743](https://github.com/Flagsmith/flagsmith/commit/db98743d426c0ded932d5a624cf8bd00cf2c6a86))
* rendering recurring task admin times out ([#2514](https://github.com/Flagsmith/flagsmith/issues/2514)) ([cb95a92](https://github.com/Flagsmith/flagsmith/commit/cb95a925cc8907a8f37f76f48a840261c467372d))
* revert EDGE_API_URL removal and reduce timeout further to 0.1s ([#2467](https://github.com/Flagsmith/flagsmith/issues/2467)) ([fc81925](https://github.com/Flagsmith/flagsmith/commit/fc819257bbe41d15f208376ed451045b26015a41))
* revert totals attributes ([#2625](https://github.com/Flagsmith/flagsmith/issues/2625)) ([3905527](https://github.com/Flagsmith/flagsmith/commit/39055275d18023702b9906991ad418cb2857088f))
* **roles/org-permission:** Add missing viewset ([#2495](https://github.com/Flagsmith/flagsmith/issues/2495)) ([2b56c7c](https://github.com/Flagsmith/flagsmith/commit/2b56c7cc52631686f8b28e9cdb03c7203ec6abdb))
* **SwaggerGenerationError:** Remove filterset_field ([#2539](https://github.com/Flagsmith/flagsmith/issues/2539)) ([6dba7bd](https://github.com/Flagsmith/flagsmith/commit/6dba7bdd0563a4916d9185555512d21e6d77643c))
* **tests:** support any webhook order ([#2524](https://github.com/Flagsmith/flagsmith/issues/2524)) ([da2b4a7](https://github.com/Flagsmith/flagsmith/commit/da2b4a7128a7b40605eed04774a703839777a841))
* **user-create:** duplicate email error message ([#2642](https://github.com/Flagsmith/flagsmith/issues/2642)) ([7b65a8d](https://github.com/Flagsmith/flagsmith/commit/7b65a8d7d7b0a2d6b938170a67ba6cabc32d00df))
* **webhooks:** fix skipping webhooks calls on timeouts ([#2501](https://github.com/Flagsmith/flagsmith/issues/2501)) ([583e248](https://github.com/Flagsmith/flagsmith/commit/583e248cda58341b02ceeb5b75945550963a6dba))

## [2.67.0](https://github.com/Flagsmith/flagsmith/compare/v2.66.2...v2.67.0) (2023-08-22)


### Features

* admin action to delete all segments for project ([#2646](https://github.com/Flagsmith/flagsmith/issues/2646)) ([4df1b80](https://github.com/Flagsmith/flagsmith/commit/4df1b8037796b1304ce2dc4353c51bc7a67b1178))
* re-add totals and limits ([#2631](https://github.com/Flagsmith/flagsmith/issues/2631)) ([7a6a2c8](https://github.com/Flagsmith/flagsmith/commit/7a6a2c8f929bc079526a852494e3cfb87f796fb3))


### Bug Fixes

* **password-reset:** rate limit password reset emails ([#2619](https://github.com/Flagsmith/flagsmith/issues/2619)) ([db98743](https://github.com/Flagsmith/flagsmith/commit/db98743d426c0ded932d5a624cf8bd00cf2c6a86))
* **user-create:** duplicate email error message ([#2642](https://github.com/Flagsmith/flagsmith/issues/2642)) ([7b65a8d](https://github.com/Flagsmith/flagsmith/commit/7b65a8d7d7b0a2d6b938170a67ba6cabc32d00df))
