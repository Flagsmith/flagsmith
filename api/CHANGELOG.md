# Changelog

## 0.1.0 (2023-08-09)


### Features

* add descriptive event title to dynatrace integration ([#2424](https://github.com/dabeeeenster/flagsmith/issues/2424)) ([f1dba53](https://github.com/dabeeeenster/flagsmith/commit/f1dba5376b4bf1d2e9115f08998c8170678a8a80))
* Adjust AWS payment settings ([#2400](https://github.com/dabeeeenster/flagsmith/issues/2400)) ([de4618d](https://github.com/dabeeeenster/flagsmith/commit/de4618d02fbdffd774e7a34047590921c4c5bf4f))
* Bake enterprise version info into private cloud image ([#2420](https://github.com/dabeeeenster/flagsmith/issues/2420)) ([acebf93](https://github.com/dabeeeenster/flagsmith/commit/acebf939d80503d1b1fd964135646d06c7d0cb04))
* **integrations:** add support for Amplitude base url ([#2534](https://github.com/dabeeeenster/flagsmith/issues/2534)) ([5d52564](https://github.com/dabeeeenster/flagsmith/commit/5d5256483dd99d05ceaf4cb08ea66191b1cbc852))
* **limits:** Add limits to features, segments and segment overrides ([#2480](https://github.com/dabeeeenster/flagsmith/issues/2480)) ([d150c7f](https://github.com/dabeeeenster/flagsmith/commit/d150c7f6c4b5e2336518b4dfba7895c61c2737a1))
* Migrate to poetry ([#2214](https://github.com/dabeeeenster/flagsmith/issues/2214)) ([0754071](https://github.com/dabeeeenster/flagsmith/commit/0754071edebaca400c0fb2db1169de0495a2c33b))
* **tests:** test coverage ([#2482](https://github.com/dabeeeenster/flagsmith/issues/2482)) ([1389c6e](https://github.com/dabeeeenster/flagsmith/commit/1389c6eb8e39920fcc962c73c71fa096b902c260))


### Bug Fixes

* (sales dashboard) correct api call overage data  ([#2434](https://github.com/dabeeeenster/flagsmith/issues/2434)) ([c55e675](https://github.com/dabeeeenster/flagsmith/commit/c55e675b023567b38e9750a3a5cc6b0a1859c209))
* allow creating integration configurations where deleted versions exist ([#2531](https://github.com/dabeeeenster/flagsmith/issues/2531)) ([3430829](https://github.com/dabeeeenster/flagsmith/commit/34308293a2b3a5dfa8f4b764e847e6cd297279ed))
* change request audit logs ([#2527](https://github.com/dabeeeenster/flagsmith/issues/2527)) ([d7c459e](https://github.com/dabeeeenster/flagsmith/commit/d7c459ed4f43b57d61259692a1efb5363a4f4d41))
* ensure recurring tasks are unlocked after being picked up (but not executed) ([#2508](https://github.com/dabeeeenster/flagsmith/issues/2508)) ([24c21ea](https://github.com/dabeeeenster/flagsmith/commit/24c21ead348f5c3dc190468309459611336c4856))
* ensure that migrate command exits with non zero error code ([#2578](https://github.com/dabeeeenster/flagsmith/issues/2578)) ([6c96ccf](https://github.com/dabeeeenster/flagsmith/commit/6c96ccfbb70e559b3b525e683563217f85fd406d))
* environment webhooks shows current date, not created date ([#2555](https://github.com/dabeeeenster/flagsmith/issues/2555)) ([94fb957](https://github.com/dabeeeenster/flagsmith/commit/94fb957e2beafaa2e303e63d0e9fc954e37daf85))
* rendering recurring task admin times out ([#2514](https://github.com/dabeeeenster/flagsmith/issues/2514)) ([cb95a92](https://github.com/dabeeeenster/flagsmith/commit/cb95a925cc8907a8f37f76f48a840261c467372d))
* revert EDGE_API_URL removal and reduce timeout further to 0.1s ([#2467](https://github.com/dabeeeenster/flagsmith/issues/2467)) ([fc81925](https://github.com/dabeeeenster/flagsmith/commit/fc819257bbe41d15f208376ed451045b26015a41))
* **roles/org-permission:** Add missing viewset ([#2495](https://github.com/dabeeeenster/flagsmith/issues/2495)) ([2b56c7c](https://github.com/dabeeeenster/flagsmith/commit/2b56c7cc52631686f8b28e9cdb03c7203ec6abdb))
* **SwaggerGenerationError:** Remove filterset_field ([#2539](https://github.com/dabeeeenster/flagsmith/issues/2539)) ([6dba7bd](https://github.com/dabeeeenster/flagsmith/commit/6dba7bdd0563a4916d9185555512d21e6d77643c))
* **tests:** support any webhook order ([#2524](https://github.com/dabeeeenster/flagsmith/issues/2524)) ([da2b4a7](https://github.com/dabeeeenster/flagsmith/commit/da2b4a7128a7b40605eed04774a703839777a841))
* **webhooks:** fix skipping webhooks calls on timeouts ([#2501](https://github.com/dabeeeenster/flagsmith/issues/2501)) ([583e248](https://github.com/dabeeeenster/flagsmith/commit/583e248cda58341b02ceeb5b75945550963a6dba))
