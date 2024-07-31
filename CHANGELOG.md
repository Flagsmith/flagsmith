# Changelog

## [2.133.1](https://github.com/Flagsmith/flagsmith/compare/v2.133.0...v2.133.1) (2024-07-30)


### Bug Fixes

* add logic to handle subscriptions in trial ([#4404](https://github.com/Flagsmith/flagsmith/issues/4404)) ([c10e012](https://github.com/Flagsmith/flagsmith/commit/c10e012bf2a22d7d88d140177b37c3ef5f93a0ad))
* **build:** Use a pre-created user for the frontend image ([#4394](https://github.com/Flagsmith/flagsmith/issues/4394)) ([45ce495](https://github.com/Flagsmith/flagsmith/commit/45ce4952cf64bd47baf8462e5b850c6993eb9b93))
* casting issue in FE logic for `delete` attribute ([#4398](https://github.com/Flagsmith/flagsmith/issues/4398)) ([cbe0a0c](https://github.com/Flagsmith/flagsmith/commit/cbe0a0c8c25347f90766c1236c08898f8545a7e9))
* **models/featureevaluationraw:** Add index on crated_at ([#4405](https://github.com/Flagsmith/flagsmith/issues/4405)) ([1f90900](https://github.com/Flagsmith/flagsmith/commit/1f90900505a7001fe24626c569bcf9cefd4c1be5))

## [2.133.0](https://github.com/Flagsmith/flagsmith/compare/v2.132.0...v2.133.0) (2024-07-25)


### Features

* Send users notification when api flags have been blocked ([#4338](https://github.com/Flagsmith/flagsmith/issues/4338)) ([114d0c3](https://github.com/Flagsmith/flagsmith/commit/114d0c30c791926bc1ca87c461e08f86c6d535ee))

## [2.132.0](https://github.com/Flagsmith/flagsmith/compare/v2.131.0...v2.132.0) (2024-07-25)


### Features

* Improve versioned change requests to handle multiple open CRs for single feature ([#4245](https://github.com/Flagsmith/flagsmith/issues/4245)) ([f1cc8d8](https://github.com/Flagsmith/flagsmith/commit/f1cc8d8409106d5a8feb6dd36cf8e3e4a8c40f0f))
* Return transient traits explicitly ([#4375](https://github.com/Flagsmith/flagsmith/issues/4375)) ([79b3ae7](https://github.com/Flagsmith/flagsmith/commit/79b3ae7d8fa14658623cd15cfbf4f177256728ff))
* versioned change request change sets ([#4301](https://github.com/Flagsmith/flagsmith/issues/4301)) ([6f1f212](https://github.com/Flagsmith/flagsmith/commit/6f1f212ebbaf4cde927c33fb1a17d0ab1cbf06c2))


### Bug Fixes

* add logic to set segment to lowest priority if not set ([#4381](https://github.com/Flagsmith/flagsmith/issues/4381)) ([a78b284](https://github.com/Flagsmith/flagsmith/commit/a78b284bee634347544acb9b02225d998ad1ef8c))
* Cannot use an API Key to add users to a group ([#4362](https://github.com/Flagsmith/flagsmith/issues/4362)) ([0390075](https://github.com/Flagsmith/flagsmith/commit/03900751daa5bfe40fdf70415a2d81594413b597))
* feature segments created with priority 0 are sent to bottom ([#4383](https://github.com/Flagsmith/flagsmith/issues/4383)) ([3f745c5](https://github.com/Flagsmith/flagsmith/commit/3f745c5621ea931d4dba1d24e81a5fc4317f243b))
* Organisation/Project dropdown not reset after closing ([#4365](https://github.com/Flagsmith/flagsmith/issues/4365)) ([1af5d48](https://github.com/Flagsmith/flagsmith/commit/1af5d489e6db4b662ae1e21a4442ccc3a70f3189))
* users with `CREATE_FEATURE` permission cannot assign feature users / groups ([#4371](https://github.com/Flagsmith/flagsmith/issues/4371)) ([d0f3704](https://github.com/Flagsmith/flagsmith/commit/d0f370413ff3e6ea219cb6d21384ad7ceb4e079c))

## [2.131.0](https://github.com/Flagsmith/flagsmith/compare/v2.130.0...v2.131.0) (2024-07-22)


### Features

* **pg-usage-data:** Add cache to batch tracking data ([#4308](https://github.com/Flagsmith/flagsmith/issues/4308)) ([117f72a](https://github.com/Flagsmith/flagsmith/commit/117f72abb7ce74d75b05a8c5338245c926a39193))
* Wolfi-based Docker images ([#4276](https://github.com/Flagsmith/flagsmith/issues/4276)) ([2e461c8](https://github.com/Flagsmith/flagsmith/commit/2e461c851f8f0069c2d44ef2d6a9b31a489dd6c6))


### Bug Fixes

* **build:** Incorrect package used for GPG ([#4355](https://github.com/Flagsmith/flagsmith/issues/4355)) ([aa2fd70](https://github.com/Flagsmith/flagsmith/commit/aa2fd70e0800e2df388930b239d8b7b677c5fa70))
* **build:** Missing gpg-agent for the SaaS build ([#4356](https://github.com/Flagsmith/flagsmith/issues/4356)) ([c655c73](https://github.com/Flagsmith/flagsmith/commit/c655c73f6d07cf79ae2ab45b2368f78221c47c45))
* Non-admin project Role request to /projects/ID/features/ID Causes Crash ([#4289](https://github.com/Flagsmith/flagsmith/issues/4289)) ([bce6530](https://github.com/Flagsmith/flagsmith/commit/bce65306fab071517bf59fbaec18dc24c50fc1df))
* Styling alert for API usage banner ([#4360](https://github.com/Flagsmith/flagsmith/issues/4360)) ([61cfdbf](https://github.com/Flagsmith/flagsmith/commit/61cfdbf47087e4efc52f75da4cfa6a2d1a9d60a7))
* Update of organisations during flags and admin access ([#4344](https://github.com/Flagsmith/flagsmith/issues/4344)) ([7a9edca](https://github.com/Flagsmith/flagsmith/commit/7a9edca2c6d8cd9de33f8a9bff74689cc5c4ec60))

## [2.130.0](https://github.com/Flagsmith/flagsmith/compare/v2.129.0...v2.130.0) (2024-07-18)


### Features

* Support transient identities and traits ([#4325](https://github.com/Flagsmith/flagsmith/issues/4325)) ([27f6539](https://github.com/Flagsmith/flagsmith/commit/27f6539e7393d35f129f3d5af45d039f4d2843b2))


### Bug Fixes

* Non-admin users cannot link a feature to a GH Issue/PR ([#4336](https://github.com/Flagsmith/flagsmith/issues/4336)) ([56e6390](https://github.com/Flagsmith/flagsmith/commit/56e6390ce6622dcc7d6be3127342a22a6053842a))
* The organisation setting page is broken locally ([#4330](https://github.com/Flagsmith/flagsmith/issues/4330)) ([1cd8e0f](https://github.com/Flagsmith/flagsmith/commit/1cd8e0f503240e38e553bc555b4aedd8686d0097))

## [2.129.0](https://github.com/Flagsmith/flagsmith/compare/v2.128.0...v2.129.0) (2024-07-12)


### Features

* **docker:** Update entrypoint ([#4262](https://github.com/Flagsmith/flagsmith/issues/4262)) ([759e745](https://github.com/Flagsmith/flagsmith/commit/759e745098d2e7cb582c0097c18c042e32533012))
* Open payment modal if a plan was preselected, add annual plans ([#4110](https://github.com/Flagsmith/flagsmith/issues/4110)) ([103a94f](https://github.com/Flagsmith/flagsmith/commit/103a94fe45c6e9ec677dd2aa14ab2009f5f0b44b))


### Bug Fixes

* annual plan ids and refreshing ([#4323](https://github.com/Flagsmith/flagsmith/issues/4323)) ([f5a7eed](https://github.com/Flagsmith/flagsmith/commit/f5a7eed20a24f5ef0c642e48030ed74b168dd41f))
* **build:** Avoid E2E rate limiting by swithing to Postgres image hosted on GHCR ([#4328](https://github.com/Flagsmith/flagsmith/issues/4328)) ([249db14](https://github.com/Flagsmith/flagsmith/commit/249db141a9e3679d28cacbe40e35b67d82d245c3))
* **e2e:** Pass `GITHUB_ACTION_URL` to Docker E2E test runs ([#4322](https://github.com/Flagsmith/flagsmith/issues/4322)) ([f8babe8](https://github.com/Flagsmith/flagsmith/commit/f8babe892a3a066b3dcb80d47fe994e78d4e8ef0))
* Fix "Create Project" button in the project selector not opening the project creation modal ([#4294](https://github.com/Flagsmith/flagsmith/issues/4294)) ([1f9aecc](https://github.com/Flagsmith/flagsmith/commit/1f9aeccff49ab5da37006924b5df1a0f307106d2))
* frontend fails to load when announcement flag isn't set ([#4329](https://github.com/Flagsmith/flagsmith/issues/4329)) ([c047233](https://github.com/Flagsmith/flagsmith/commit/c04723373e4a5bfe236beae9a4c827fa819f6509))
* Prevent "Create Segment" button from disappearing when deleting the last segment ([#4314](https://github.com/Flagsmith/flagsmith/issues/4314)) ([cd121e8](https://github.com/Flagsmith/flagsmith/commit/cd121e8e01bce3ac036587d9741773cbd145b3e3))

## [2.128.0](https://github.com/Flagsmith/flagsmith/compare/v2.127.1...v2.128.0) (2024-07-10)


### Features

* Selected options ([#4311](https://github.com/Flagsmith/flagsmith/issues/4311)) ([d32a320](https://github.com/Flagsmith/flagsmith/commit/d32a3203036fa6fde820c1867862ff909c269b52))


### Bug Fixes

* **get_permitted_projects:** get rid of distinct ([#4320](https://github.com/Flagsmith/flagsmith/issues/4320)) ([e7252cb](https://github.com/Flagsmith/flagsmith/commit/e7252cb056645ff6982772759ca8551cd1855811))
* version diff overflow ([#4313](https://github.com/Flagsmith/flagsmith/issues/4313)) ([2525636](https://github.com/Flagsmith/flagsmith/commit/25256367e706b611ed6e6c399b0b2fb8c672710c))

## [2.127.1](https://github.com/Flagsmith/flagsmith/compare/v2.127.0...v2.127.1) (2024-07-09)


### Bug Fixes

* **segments:** add migration to set version on existing segments ([#4315](https://github.com/Flagsmith/flagsmith/issues/4315)) ([288a47e](https://github.com/Flagsmith/flagsmith/commit/288a47efc6bec12374a05a48191380b645bb99b3))

## [2.127.0](https://github.com/Flagsmith/flagsmith/compare/v2.126.0...v2.127.0) (2024-07-09)


### Features

* Add timestamps to segments models ([#4236](https://github.com/Flagsmith/flagsmith/issues/4236)) ([a5b2421](https://github.com/Flagsmith/flagsmith/commit/a5b24210419e6f33935b4f06d8627bcac4a039bb))
* Announcement feature flag per page ([#4218](https://github.com/Flagsmith/flagsmith/issues/4218)) ([3bfad05](https://github.com/Flagsmith/flagsmith/commit/3bfad055a203f65af84b158daabddc2e3a776556))
* Announcement per page accept an id list on the params key ([#4280](https://github.com/Flagsmith/flagsmith/issues/4280)) ([e2685e9](https://github.com/Flagsmith/flagsmith/commit/e2685e91abcdc78457dc0ecf56f134de877cb609))
* Announcement per page FF accept params ([#4275](https://github.com/Flagsmith/flagsmith/issues/4275)) ([078bf1e](https://github.com/Flagsmith/flagsmith/commit/078bf1e1a8002b9c5142c866804c89df006ffaef))
* **build:** Debian Bookworm base images ([#4263](https://github.com/Flagsmith/flagsmith/issues/4263)) ([0230b9a](https://github.com/Flagsmith/flagsmith/commit/0230b9a479cd8e513e883ae19cd694da088bbc59))
* **build:** Docker build improvements ([#4272](https://github.com/Flagsmith/flagsmith/issues/4272)) ([627370f](https://github.com/Flagsmith/flagsmith/commit/627370f3fb7b92f911db7eba15720e96878b3cd4))
* Create versioning for segments ([#4138](https://github.com/Flagsmith/flagsmith/issues/4138)) ([bc9b340](https://github.com/Flagsmith/flagsmith/commit/bc9b340b2a44c46e93326e9602c48dda55e8a6f8))
* Group versions by date ([#4246](https://github.com/Flagsmith/flagsmith/issues/4246)) ([540d320](https://github.com/Flagsmith/flagsmith/commit/540d320d4fafa686f8d61aed734bafb1c4e82f20))
* Update API usage notifications thresholds ([#4255](https://github.com/Flagsmith/flagsmith/issues/4255)) ([5162687](https://github.com/Flagsmith/flagsmith/commit/516268775ee0581a791fb4fd6244126792f579ba))


### Bug Fixes

* **build:** Avoid Docker Hub pull throttling by using public ECR registry ([#4292](https://github.com/Flagsmith/flagsmith/issues/4292)) ([30bed4e](https://github.com/Flagsmith/flagsmith/commit/30bed4efc3aff4e947d2d3aeb8589481730dbbfb))
* Set early return when influxdb range is empty ([#4274](https://github.com/Flagsmith/flagsmith/issues/4274)) ([007351c](https://github.com/Flagsmith/flagsmith/commit/007351c2338e85cacc051102780778e457f1568a))

## [2.126.0](https://github.com/Flagsmith/flagsmith/compare/v2.125.0...v2.126.0) (2024-06-26)


### Features

* **api usage:** Extra Flagsmith checks for API overage charges ([#4251](https://github.com/Flagsmith/flagsmith/issues/4251)) ([ca2b13b](https://github.com/Flagsmith/flagsmith/commit/ca2b13b06c747d026104de7f012d067905e35a88))


### Bug Fixes

* Hide Sensitive Data switch ([#4199](https://github.com/Flagsmith/flagsmith/issues/4199)) ([ff29f21](https://github.com/Flagsmith/flagsmith/commit/ff29f2184d5b5c372001cfdfb5cd9076a2f4625d))

## [2.125.0](https://github.com/Flagsmith/flagsmith/compare/v2.124.2...v2.125.0) (2024-06-26)


### Features

* **api-usage:** add `subscription.plan` trait to `flagsmith.get_identity_flags` ([#4247](https://github.com/Flagsmith/flagsmith/issues/4247)) ([182ea04](https://github.com/Flagsmith/flagsmith/commit/182ea04c7f776606c931f34c4fad32849f667d2c))


### Bug Fixes

* **ci:** Authenticate Trivy correctly for ephemeral build ([#4227](https://github.com/Flagsmith/flagsmith/issues/4227)) ([b9a6f92](https://github.com/Flagsmith/flagsmith/commit/b9a6f92ec099cac58f16c989d44b86bead443a81))
* **ci:** Enable Docker builds and E2E for external PRs ([#4224](https://github.com/Flagsmith/flagsmith/issues/4224)) ([fe7cc53](https://github.com/Flagsmith/flagsmith/commit/fe7cc53b5b4242db6af5ee818dd1e7c42a8d44ab))
* **ci:** Use correct `ENV` value for production ([#4237](https://github.com/Flagsmith/flagsmith/issues/4237)) ([81753ba](https://github.com/Flagsmith/flagsmith/commit/81753bae01c6665bd4a50349107d709991eabfc4))


### Infrastructure (Flagsmith SaaS Only)

* add production environment variables for FoF and API usage alerting ([#4248](https://github.com/Flagsmith/flagsmith/issues/4248)) ([af61d52](https://github.com/Flagsmith/flagsmith/commit/af61d52bb0da1ba95a45f5ea877fc01abc20d262))

## [2.124.2](https://github.com/Flagsmith/flagsmith/compare/v2.124.1...v2.124.2) (2024-06-25)


### Bug Fixes

* **ci:** `packages:read` permission lacking for Docker publish jobs ([#4223](https://github.com/Flagsmith/flagsmith/issues/4223)) ([a037f9f](https://github.com/Flagsmith/flagsmith/commit/a037f9faaea5dd9b610ca61b5ed43d170f93b0fb))

## [2.124.1](https://github.com/Flagsmith/flagsmith/compare/v2.124.0...v2.124.1) (2024-06-25)


### Bug Fixes

* **ci:** Secrets unavailable to Docker publish jobs ([#4220](https://github.com/Flagsmith/flagsmith/issues/4220)) ([30ba49d](https://github.com/Flagsmith/flagsmith/commit/30ba49dea45f1f54f3f805a7dc14b36ed49c9acf))
* versioning webhooks and update test to correctly test end to end ([#4221](https://github.com/Flagsmith/flagsmith/issues/4221)) ([47eb149](https://github.com/Flagsmith/flagsmith/commit/47eb149ffa6840a2f36f2378737b8aa0ce4b2199))

## [2.124.0](https://github.com/Flagsmith/flagsmith/compare/v2.123.1...v2.124.0) (2024-06-24)


### Features

* Add confirmations when removing features, segments and environments ([#4210](https://github.com/Flagsmith/flagsmith/issues/4210)) ([cdc3410](https://github.com/Flagsmith/flagsmith/commit/cdc3410ccb6941e22ab1c3529ebc7d0330e4eb22))
* Add logic to API usage notification templates ([#4206](https://github.com/Flagsmith/flagsmith/issues/4206)) ([6afa63d](https://github.com/Flagsmith/flagsmith/commit/6afa63d7e2e5e452854944c5034cd2195cf7cffa))
* Add UI for SAML attribute mapping ([#4184](https://github.com/Flagsmith/flagsmith/issues/4184)) ([318fb85](https://github.com/Flagsmith/flagsmith/commit/318fb85e471a96b10274c4f502cfac7971169acf))
* Grafana integration ([#4144](https://github.com/Flagsmith/flagsmith/issues/4144)) ([5c25c41](https://github.com/Flagsmith/flagsmith/commit/5c25c41e01ba68b18887759f2a5650caa6a9f39d))
* **versioning:** add logic to create version in single endpoint ([#3991](https://github.com/Flagsmith/flagsmith/issues/3991)) ([57f8d68](https://github.com/Flagsmith/flagsmith/commit/57f8d68449577228a6f32cd317c4693cf5282824))


### Bug Fixes

* **ci:** Docker build CodeQL permission ([#4217](https://github.com/Flagsmith/flagsmith/issues/4217)) ([7554d15](https://github.com/Flagsmith/flagsmith/commit/7554d159aa46338381d392237e662d43286d9cdd))
* **ci:** Secrets unavailable for deploy jobs ([#4215](https://github.com/Flagsmith/flagsmith/issues/4215)) ([d56ad08](https://github.com/Flagsmith/flagsmith/commit/d56ad08d332d10ee440170afec64bd1efecc5282))
* Include free plans for api use notifications ([#4204](https://github.com/Flagsmith/flagsmith/issues/4204)) ([e1f3a7b](https://github.com/Flagsmith/flagsmith/commit/e1f3a7b92344b909f3547024589086685e7c04fa))
* login redirect ([#4192](https://github.com/Flagsmith/flagsmith/issues/4192)) ([b0bc87a](https://github.com/Flagsmith/flagsmith/commit/b0bc87acbe8c0187eaaa6e01880c64712eea1dba))
* Metadata UI issues ([#4069](https://github.com/Flagsmith/flagsmith/issues/4069)) ([36c8bb3](https://github.com/Flagsmith/flagsmith/commit/36c8bb3c401ed153dcc0e866e0edab49746a4ff9))
* oauth user case sensitivity ([#4207](https://github.com/Flagsmith/flagsmith/issues/4207)) ([af955bf](https://github.com/Flagsmith/flagsmith/commit/af955bf7ef3b35965b5675d957fe56a8383c7d5b))
* Preserve selected environment ([#4190](https://github.com/Flagsmith/flagsmith/issues/4190)) ([6bf9858](https://github.com/Flagsmith/flagsmith/commit/6bf9858ce23400445a3ace960acf78123141cdf0))

## [2.123.1](https://github.com/Flagsmith/flagsmith/compare/v2.123.0...v2.123.1) (2024-06-19)


### Bug Fixes

* not serializable arguments when calling environment feature version webhooks ([#4187](https://github.com/Flagsmith/flagsmith/issues/4187)) ([319708c](https://github.com/Flagsmith/flagsmith/commit/319708c1f2ac8ae5f4e8c1208e9cceab0f939552))
* scarf image formatting ([#4178](https://github.com/Flagsmith/flagsmith/issues/4178)) ([710ed87](https://github.com/Flagsmith/flagsmith/commit/710ed878e3d20f8170544894c4db5c1176e2d149))
* Stale connections after task processor errors ([#4179](https://github.com/Flagsmith/flagsmith/issues/4179)) ([17782bd](https://github.com/Flagsmith/flagsmith/commit/17782bdc39ba010e3e823bf2b7f89f20b61d3234))

## [2.123.0](https://github.com/Flagsmith/flagsmith/compare/v2.122.0...v2.123.0) (2024-06-18)


### Features

* Add alert message in the FE when exceeded the API usage ([#4027](https://github.com/Flagsmith/flagsmith/issues/4027)) ([da46dab](https://github.com/Flagsmith/flagsmith/commit/da46dab0f82dfa38d68c0108ee6fdbfb2c3a344f))


### Bug Fixes

* code highlighting ([#4181](https://github.com/Flagsmith/flagsmith/issues/4181)) ([e6d1f62](https://github.com/Flagsmith/flagsmith/commit/e6d1f620d73ae506767be2daeeb8fcbd1ccea4a1))

## [2.122.0](https://github.com/Flagsmith/flagsmith/compare/v2.121.0...v2.122.0) (2024-06-18)


### Features

* add scarf pixel to docs ([#4169](https://github.com/Flagsmith/flagsmith/issues/4169)) ([ca071dc](https://github.com/Flagsmith/flagsmith/commit/ca071dc1b7d86c6aae87fc097f97871d0c6f43a7))
* Add UI for configuring SAML in Flagsmith ([#4055](https://github.com/Flagsmith/flagsmith/issues/4055)) ([d2c2aba](https://github.com/Flagsmith/flagsmith/commit/d2c2aba01b16683b045aa50b21cf8718bc2aca12))


### Bug Fixes

* **dev:** add management command to manually send API usage to influx ([#4159](https://github.com/Flagsmith/flagsmith/issues/4159)) ([77eeaa7](https://github.com/Flagsmith/flagsmith/commit/77eeaa7576e3f89db0710cb0eff6b209a86e5c20))
* **postgres-analytics/usage:** fix project_id filter ([#4171](https://github.com/Flagsmith/flagsmith/issues/4171)) ([5dafecf](https://github.com/Flagsmith/flagsmith/commit/5dafecf0d5ca612c2cc0caabfdd2c69e1bb71e5b))
* various fixes for API usage alerting / billing ([#4158](https://github.com/Flagsmith/flagsmith/issues/4158)) ([9a6e335](https://github.com/Flagsmith/flagsmith/commit/9a6e33514d183763073c0854b2787cc6708ecd85))

## [2.121.0](https://github.com/Flagsmith/flagsmith/compare/v2.120.0...v2.121.0) (2024-06-13)


### Features

* **analytics:** Command to populate arbitrary periods of analytics data ([#4155](https://github.com/Flagsmith/flagsmith/issues/4155)) ([20fb43e](https://github.com/Flagsmith/flagsmith/commit/20fb43ee2c032ba3ebc02ac838ce5596e0953538))
* Keep segment modal open on create / edit, add segment name to modal ([#4109](https://github.com/Flagsmith/flagsmith/issues/4109)) ([1daedc2](https://github.com/Flagsmith/flagsmith/commit/1daedc22ea5dc4800f625804e99b924dbdfb6338))
* Show new version warning in change requests ([#4153](https://github.com/Flagsmith/flagsmith/issues/4153)) ([69f6ae6](https://github.com/Flagsmith/flagsmith/commit/69f6ae6827fee07e173429b25f3f49e357f4d6d7))


### Bug Fixes

* cascade delete versions when corresponding change request is deleted ([#4152](https://github.com/Flagsmith/flagsmith/issues/4152)) ([baf8ddb](https://github.com/Flagsmith/flagsmith/commit/baf8ddb92b78241d3b0d41e421eeee662f6a6782))
* Edge V2-enabled environments are not rebuilt on feature version publish ([#4132](https://github.com/Flagsmith/flagsmith/issues/4132)) ([7e0c9fd](https://github.com/Flagsmith/flagsmith/commit/7e0c9fdf7cf36930b2bd7ebb153df06650bdb879))
* feature state value conversion ([#3946](https://github.com/Flagsmith/flagsmith/issues/3946)) ([d4f948d](https://github.com/Flagsmith/flagsmith/commit/d4f948d44da6b295d10f585caad30561ac6fe8af))
* **migrate_analytics:** fix migrate_to_pg command ([#4139](https://github.com/Flagsmith/flagsmith/issues/4139)) ([c0f373a](https://github.com/Flagsmith/flagsmith/commit/c0f373aae3681c6cfc35dfc0f4bb010d1096227a))

## [2.120.0](https://github.com/Flagsmith/flagsmith/compare/v2.119.1...v2.120.0) (2024-06-11)


### Features

* Add default rule for segments ([#4095](https://github.com/Flagsmith/flagsmith/issues/4095)) ([c3bf3bf](https://github.com/Flagsmith/flagsmith/commit/c3bf3bf2b25639ac46ed9008f9dfad359940cf9d))


### Bug Fixes

* **deps:** Migrate MFA code to our codebase and bump djangorestframework ([#3988](https://github.com/Flagsmith/flagsmith/issues/3988)) ([e217df7](https://github.com/Flagsmith/flagsmith/commit/e217df7cf3779d3934d8a0a2836d0a3e4484266b))
* Identity overrides tab ([#4134](https://github.com/Flagsmith/flagsmith/issues/4134)) ([1a51fd3](https://github.com/Flagsmith/flagsmith/commit/1a51fd3346e8ff27ffccd8b6878b88cc81df9f4e))

## [2.119.1](https://github.com/Flagsmith/flagsmith/compare/v2.119.0...v2.119.1) (2024-06-06)


### Bug Fixes

* use python3.11 as base image ([#4121](https://github.com/Flagsmith/flagsmith/issues/4121)) ([418e026](https://github.com/Flagsmith/flagsmith/commit/418e026796863ba361c8750c8da6f2abd5e1b283))


### Infrastructure (Flagsmith SaaS Only)

* run influxdb feature evaluation in thread ([#4125](https://github.com/Flagsmith/flagsmith/issues/4125)) ([b135b38](https://github.com/Flagsmith/flagsmith/commit/b135b38703be391ec68a841a8d9d11635742cf89))
* task processor settings tweaks ([#4126](https://github.com/Flagsmith/flagsmith/issues/4126)) ([ea96db9](https://github.com/Flagsmith/flagsmith/commit/ea96db9f70e90476fb2e829715571d063ca615b8))

## [2.119.0](https://github.com/Flagsmith/flagsmith/compare/v2.118.1...v2.119.0) (2024-06-06)


### Features

* Improve API key UX ([#4102](https://github.com/Flagsmith/flagsmith/issues/4102)) ([1600ed7](https://github.com/Flagsmith/flagsmith/commit/1600ed7633827051b92bf94e83b01bc493473da9))


### Bug Fixes

* Add autocomplete for login ([#4103](https://github.com/Flagsmith/flagsmith/issues/4103)) ([5ffdd51](https://github.com/Flagsmith/flagsmith/commit/5ffdd51d61b2840b927eca0c6ca26dd8c06e7382))
* announcement width ([#4122](https://github.com/Flagsmith/flagsmith/issues/4122)) ([f6ac4e5](https://github.com/Flagsmith/flagsmith/commit/f6ac4e52b9c3c0457aef3e096d82dbef5c64a53c))
* delete environment refreshing list ([#4107](https://github.com/Flagsmith/flagsmith/issues/4107)) ([902b3cd](https://github.com/Flagsmith/flagsmith/commit/902b3cdbd26fc6c4c7dd53e9d0094773365a5b8f))
* environment click sizes ([#4104](https://github.com/Flagsmith/flagsmith/issues/4104)) ([9d1622f](https://github.com/Flagsmith/flagsmith/commit/9d1622f7e6445b1b88ad5a369ea6174746458910))
* Environment creating state ([#4060](https://github.com/Flagsmith/flagsmith/issues/4060)) ([652af8f](https://github.com/Flagsmith/flagsmith/commit/652af8f9f2f87e65eb06187c17a7979075f0a57a))
* Flag update scheduling ([#4115](https://github.com/Flagsmith/flagsmith/issues/4115)) ([e90d248](https://github.com/Flagsmith/flagsmith/commit/e90d248de1026200c6134f32b7b104e62ddd69ae))
* Limit feature paging to 50 ([#4120](https://github.com/Flagsmith/flagsmith/issues/4120)) ([c14c3a8](https://github.com/Flagsmith/flagsmith/commit/c14c3a86995e0b44ee080322dda41633d101e56e))
* Protect inputs from autofill ([#3980](https://github.com/Flagsmith/flagsmith/issues/3980)) ([dad3041](https://github.com/Flagsmith/flagsmith/commit/dad304101e073fd7767b8623751f52e4d806a330))
* Reload integrations on create ([#4106](https://github.com/Flagsmith/flagsmith/issues/4106)) ([5155018](https://github.com/Flagsmith/flagsmith/commit/5155018a38d717f167c9e9794067a4013da66c3a))
* save empty segment overrides request ([#4112](https://github.com/Flagsmith/flagsmith/issues/4112)) ([6dbcb4a](https://github.com/Flagsmith/flagsmith/commit/6dbcb4aadace2dccb5c32adfbe3f145ac894982d))
* show audit logs url ([#4123](https://github.com/Flagsmith/flagsmith/issues/4123)) ([bc256ee](https://github.com/Flagsmith/flagsmith/commit/bc256ee6f1788d00a31ad9ee566a895e4484c9f9))
* **versioning:** scheduled changes incorrectly considered live ([#4119](https://github.com/Flagsmith/flagsmith/issues/4119)) ([6856e64](https://github.com/Flagsmith/flagsmith/commit/6856e64ae1028336801fc1c6acd3fd5da8bff8db))
* **versioning:** send live from when creating versions for change requests ([#4116](https://github.com/Flagsmith/flagsmith/issues/4116)) ([765b12a](https://github.com/Flagsmith/flagsmith/commit/765b12a8c049ec65956707c0ab5792376d5dee47))
* **versioning:** use version live from ([#4118](https://github.com/Flagsmith/flagsmith/issues/4118)) ([0345aff](https://github.com/Flagsmith/flagsmith/commit/0345aff4146596f29ff294941fe0ee27ad6db735))


### Infrastructure (Flagsmith SaaS Only)

* reduce Sentry sampling rate ([#4098](https://github.com/Flagsmith/flagsmith/issues/4098)) ([da3f186](https://github.com/Flagsmith/flagsmith/commit/da3f1863a5c0c90b99bf30a8991b9617a037e8ea))

## [2.118.1](https://github.com/Flagsmith/flagsmith/compare/v2.118.0...v2.118.1) (2024-06-03)


### Bug Fixes

* **audit:** audit and history UI tweaks ([#4092](https://github.com/Flagsmith/flagsmith/issues/4092)) ([e65dc34](https://github.com/Flagsmith/flagsmith/commit/e65dc345850c4c656b55bea9337571994a706ba7))
* facilitate FE display of environment version from audit log ([#4077](https://github.com/Flagsmith/flagsmith/issues/4077)) ([be9b7ce](https://github.com/Flagsmith/flagsmith/commit/be9b7ce1f11a343b1c1d2566d851f11e909cebbc))
* select propagation ([#4085](https://github.com/Flagsmith/flagsmith/issues/4085)) ([0e16068](https://github.com/Flagsmith/flagsmith/commit/0e160684e37d5640d4d2be94036765d2d7d5af5d))
* **sentry-FLAGSMITH-API-4FY:** resolve metadata segment n+1 ([#4030](https://github.com/Flagsmith/flagsmith/issues/4030)) ([a22f86c](https://github.com/Flagsmith/flagsmith/commit/a22f86c6a5555960be8227fecf6afb7f8b2d2011))
* **versioning:** ensure get_previous_version returns previous version, not latest version ([#4083](https://github.com/Flagsmith/flagsmith/issues/4083)) ([22d371b](https://github.com/Flagsmith/flagsmith/commit/22d371bd60650abce4c692e1b3032bbd5c1b8e7f))
* **versioning:** ensure that audit log record is created when committing versions via CR ([#4091](https://github.com/Flagsmith/flagsmith/issues/4091)) ([8246dca](https://github.com/Flagsmith/flagsmith/commit/8246dca4f468e851ee5bf0544ca0e4ba0409712e))
* **versioning:** prevent FeatureSegment from writing audit log on delete when v2 versioning enabled ([#4088](https://github.com/Flagsmith/flagsmith/issues/4088)) ([60c0748](https://github.com/Flagsmith/flagsmith/commit/60c07480b298e8a32321e631fe0ec178cdc5f017))

## [2.118.0](https://github.com/Flagsmith/flagsmith/compare/v2.117.1...v2.118.0) (2024-05-31)


### Features

* add audit log when environment feature version is published ([#4064](https://github.com/Flagsmith/flagsmith/issues/4064)) ([88cfc76](https://github.com/Flagsmith/flagsmith/commit/88cfc762f201967f5a4a2b362eecae444b1a2b19))


### Bug Fixes

* don't create audit log for FeatureStateValue when not published ([#4065](https://github.com/Flagsmith/flagsmith/issues/4065)) ([8b73b5c](https://github.com/Flagsmith/flagsmith/commit/8b73b5c5bb4336d5fe5947e3fe3004736c942ae2))
* versioned remove segment override ([#4063](https://github.com/Flagsmith/flagsmith/issues/4063)) ([e4cd25a](https://github.com/Flagsmith/flagsmith/commit/e4cd25ae9d79c66447377bb087061193a6264eff))

## [2.117.1](https://github.com/Flagsmith/flagsmith/compare/v2.117.0...v2.117.1) (2024-05-30)


### Bug Fixes

* Validate feature values before saving ([#4043](https://github.com/Flagsmith/flagsmith/issues/4043)) ([fef9f8f](https://github.com/Flagsmith/flagsmith/commit/fef9f8fdcc3c7153bdc6752cfbfa5df2cffe3b62))

## [2.117.0](https://github.com/Flagsmith/flagsmith/compare/v2.116.3...v2.117.0) (2024-05-30)


### Features

* Add api usage metrics for different periods ([#3870](https://github.com/Flagsmith/flagsmith/issues/3870)) ([50cc369](https://github.com/Flagsmith/flagsmith/commit/50cc369d26d7ec5c418faadcd1079c1e027a6f0e))
* Add endpoint to fetch GitHub repository contributors ([#4013](https://github.com/Flagsmith/flagsmith/issues/4013)) ([6f321d4](https://github.com/Flagsmith/flagsmith/commit/6f321d45898d2c9b7159388df6b850dd873ee68d))
* Add grace period to api usage billing ([#4038](https://github.com/Flagsmith/flagsmith/issues/4038)) ([3b61f83](https://github.com/Flagsmith/flagsmith/commit/3b61f831d44ed6a7d31374fc8fd42017339fed84))
* **analytics:** Add command to migrate analytics data to pg ([#3981](https://github.com/Flagsmith/flagsmith/issues/3981)) ([848db5a](https://github.com/Flagsmith/flagsmith/commit/848db5adc540023f5911826ae10f9d43032cad02))
* Implement be search and lazy loading for GitHub resources ([#3987](https://github.com/Flagsmith/flagsmith/issues/3987)) ([c896c50](https://github.com/Flagsmith/flagsmith/commit/c896c507a6ead8075b3c77d3aa834c057c0cc909))
* Improvements in the GitHub integration BE ([#3962](https://github.com/Flagsmith/flagsmith/issues/3962)) ([59ddfba](https://github.com/Flagsmith/flagsmith/commit/59ddfba70103d021dab1e6ad5726d21f7c3802eb))


### Bug Fixes

* Add support for versioning v2 on GitHub resource linking ([#4015](https://github.com/Flagsmith/flagsmith/issues/4015)) ([edb4a75](https://github.com/Flagsmith/flagsmith/commit/edb4a7591bfb11cedb01a63a3fe23d2d4f2c63c8))
* GitHub repos unique constraint and delete ([#4037](https://github.com/Flagsmith/flagsmith/issues/4037)) ([7454e4a](https://github.com/Flagsmith/flagsmith/commit/7454e4ae7f4df36ff0fb605b6149c8542c5428d6))
* **sentry-FLAGSMITH-API-4FZ:** fix PATCH for segments ([#4029](https://github.com/Flagsmith/flagsmith/issues/4029)) ([3c43bb8](https://github.com/Flagsmith/flagsmith/commit/3c43bb8113c21558583271e13a7a11264a5c4955))
* Set api usage billing to 100k ([#3996](https://github.com/Flagsmith/flagsmith/issues/3996)) ([d86f8e7](https://github.com/Flagsmith/flagsmith/commit/d86f8e7857f882aaa4dfae22760d6e9b3e594246))
* Set billing starts at to reasonable default for API usage notifications ([#4054](https://github.com/Flagsmith/flagsmith/issues/4054)) ([515b34c](https://github.com/Flagsmith/flagsmith/commit/515b34c404b2070f28b128a29eba0bdda8f7a71b))
* Set billing term starts at 30 days for null values ([#4053](https://github.com/Flagsmith/flagsmith/issues/4053)) ([84c0835](https://github.com/Flagsmith/flagsmith/commit/84c0835d710a57cc940b17e4ad22def8307419be))
* Setting `LOG_FORMAT: json` does not write stack traces to logs ([#4040](https://github.com/Flagsmith/flagsmith/issues/4040)) ([9e2ffd2](https://github.com/Flagsmith/flagsmith/commit/9e2ffd2e3b1cf52f3f5773fc312a429413481224))
* Switch function argument to date start ([#4052](https://github.com/Flagsmith/flagsmith/issues/4052)) ([d8f48a7](https://github.com/Flagsmith/flagsmith/commit/d8f48a7ea74e7b2668880513ca63045209ca4d80))


### Infrastructure (Flagsmith SaaS Only)

* add influx token secret ([#4048](https://github.com/Flagsmith/flagsmith/issues/4048)) ([1963e03](https://github.com/Flagsmith/flagsmith/commit/1963e03c23545ff91bcd5bbc185baa6b309fdd5e))
* remove duplicate secret definition ([#4049](https://github.com/Flagsmith/flagsmith/issues/4049)) ([adc6429](https://github.com/Flagsmith/flagsmith/commit/adc6429b0c6426ac9b1ef83339f58fee08fb70a4))
* Setup InfluxDB on staging for analytics ([#4042](https://github.com/Flagsmith/flagsmith/issues/4042)) ([d9d503a](https://github.com/Flagsmith/flagsmith/commit/d9d503a8aa5c31cb7359946c07b192d70a4f930c))

## [2.116.3](https://github.com/Flagsmith/flagsmith/compare/v2.116.2...v2.116.3) (2024-05-22)


### Bug Fixes

* **versioning:** webhooks not triggered when new version published ([#3953](https://github.com/Flagsmith/flagsmith/issues/3953)) ([fb2191b](https://github.com/Flagsmith/flagsmith/commit/fb2191b34fef9b6d45d7eda17e22b77d826d4a19))

## [2.116.2](https://github.com/Flagsmith/flagsmith/compare/v2.116.1...v2.116.2) (2024-05-22)


### Bug Fixes

* **versioning:** segment overrides limit ([#4007](https://github.com/Flagsmith/flagsmith/issues/4007)) ([918b731](https://github.com/Flagsmith/flagsmith/commit/918b73148e180d91e794ea8b840310b61ffe6300))

## [2.116.1](https://github.com/Flagsmith/flagsmith/compare/v2.116.0...v2.116.1) (2024-05-21)


### Bug Fixes

* **versioning:** fix cloning environments using v2 versioning ([#3999](https://github.com/Flagsmith/flagsmith/issues/3999)) ([eef02fb](https://github.com/Flagsmith/flagsmith/commit/eef02fb75de85a75b169561b9055b533f3c71bfb))

## [2.116.0](https://github.com/Flagsmith/flagsmith/compare/v2.115.0...v2.116.0) (2024-05-20)


### Features

* Add API usage billing ([#3729](https://github.com/Flagsmith/flagsmith/issues/3729)) ([03cdee3](https://github.com/Flagsmith/flagsmith/commit/03cdee3beea9cfecf6ca119fcaeac9530345368c))
* Add global domain auth methods ([#3949](https://github.com/Flagsmith/flagsmith/issues/3949)) ([796564a](https://github.com/Flagsmith/flagsmith/commit/796564a7894939d83abc7657c8cb62f072b7ebec))
* Add metadata fields to core entities (FE) ([#3212](https://github.com/Flagsmith/flagsmith/issues/3212)) ([c5bd7a2](https://github.com/Flagsmith/flagsmith/commit/c5bd7a230e5f44b633ef04948b5ee15073fe8a09))
* Edge V2 migration opt-in, capacity budget for migration ([#3881](https://github.com/Flagsmith/flagsmith/issues/3881)) ([bca4165](https://github.com/Flagsmith/flagsmith/commit/bca4165002a45967b34ee93716dbac3442cf2570))
* Identity overrides in environment document ([#3766](https://github.com/Flagsmith/flagsmith/issues/3766)) ([e8d1337](https://github.com/Flagsmith/flagsmith/commit/e8d133726c5b724057175bfc7d945e12a733f9d1))


### Bug Fixes

* change environment in settings page ([#3956](https://github.com/Flagsmith/flagsmith/issues/3956)) ([0d30180](https://github.com/Flagsmith/flagsmith/commit/0d30180d7e7d1a4128fbf60d0db469d6c9088e86))
* change environment in settings page ([#3977](https://github.com/Flagsmith/flagsmith/issues/3977)) ([db12f17](https://github.com/Flagsmith/flagsmith/commit/db12f1728b6698bfaea96a8d93923ef189d9e6f4))
* Improve the UI/UX for clone identities ([#3934](https://github.com/Flagsmith/flagsmith/issues/3934)) ([48ac76c](https://github.com/Flagsmith/flagsmith/commit/48ac76c22654155aee36c0805705333d28b82f3d))
* Improve the UI/UX for GitHub integrations ([#3907](https://github.com/Flagsmith/flagsmith/issues/3907)) ([f624223](https://github.com/Flagsmith/flagsmith/commit/f624223afcf77fa709150c2195e94991d3488d50))
* segment overrides stale feature state value while creating GitHub comment ([#3961](https://github.com/Flagsmith/flagsmith/issues/3961)) ([e9246bc](https://github.com/Flagsmith/flagsmith/commit/e9246bc02cb856ab9e4dcf42f727a6e1c40437d0))
* **versioning:** ensure that future scheduled changes are migrated to versioning v2 ([#3958](https://github.com/Flagsmith/flagsmith/issues/3958)) ([c5aa610](https://github.com/Flagsmith/flagsmith/commit/c5aa6102f176884ef608795cfda2f2a0e481c255))
* **versioning:** handle Master API Keys when publishing a version ([#3959](https://github.com/Flagsmith/flagsmith/issues/3959)) ([98a5114](https://github.com/Flagsmith/flagsmith/commit/98a51148b5536a61226afe9281900a3c4cbc8263))
* **versioning:** multiple versioned segment overrides added to environment document ([#3974](https://github.com/Flagsmith/flagsmith/issues/3974)) ([aa5cc95](https://github.com/Flagsmith/flagsmith/commit/aa5cc95f19eccf3d404a8f0694c2e5c303422c46))

## [2.115.0](https://github.com/Flagsmith/flagsmith/compare/v2.114.1...v2.115.0) (2024-05-15)


### Features

* Add metadata fields to core entities (API) ([#3315](https://github.com/Flagsmith/flagsmith/issues/3315)) ([06eb8a4](https://github.com/Flagsmith/flagsmith/commit/06eb8a4754bf8afbff29974eb6e075953ca0352d))


### Bug Fixes

* add trailing slash to update group logic ([#3943](https://github.com/Flagsmith/flagsmith/issues/3943)) ([95b14d1](https://github.com/Flagsmith/flagsmith/commit/95b14d121d0a8d2419746ac5112b6ca78670f5d9))
* changed the error message from custom_auth serializer ([#3924](https://github.com/Flagsmith/flagsmith/issues/3924)) ([185bd6a](https://github.com/Flagsmith/flagsmith/commit/185bd6a441af53fefec2426a891df0a1d140af58))
* Create GitHub comment as table ([#3948](https://github.com/Flagsmith/flagsmith/issues/3948)) ([bf67b1d](https://github.com/Flagsmith/flagsmith/commit/bf67b1dc0ad3a34c38f8aabb8a5cfaf5f65863de))
* Organisation ID is an object calling useHasPermission at organisation level ([#3950](https://github.com/Flagsmith/flagsmith/issues/3950)) ([1372917](https://github.com/Flagsmith/flagsmith/commit/13729173d0587c322272f603f1957908874f9375))
* organisation id parsing ([#3954](https://github.com/Flagsmith/flagsmith/issues/3954)) ([aae116b](https://github.com/Flagsmith/flagsmith/commit/aae116bc6fd83837e6ead8bc681155c25149dcdc))
* Scroll to top on path change ([#3926](https://github.com/Flagsmith/flagsmith/issues/3926)) ([1a2e793](https://github.com/Flagsmith/flagsmith/commit/1a2e793e9bb47922ad0c688c445a54d5ff2677db))
* segment override link ([#3945](https://github.com/Flagsmith/flagsmith/issues/3945)) ([fc0cceb](https://github.com/Flagsmith/flagsmith/commit/fc0cceb40b881891878678c1c61cc0cc1148d090))
* Validate and handle URL params ([#3932](https://github.com/Flagsmith/flagsmith/issues/3932)) ([7e1617f](https://github.com/Flagsmith/flagsmith/commit/7e1617f5bd4e754dbc7d17db957f4315c53c3fba))
* **versioning:** prevent task from deleting all unrelated feature states / feature segments ([#3955](https://github.com/Flagsmith/flagsmith/issues/3955)) ([0ed5148](https://github.com/Flagsmith/flagsmith/commit/0ed5148183e21a74ad93aa9e0af47a08941cfed6))

## [2.114.1](https://github.com/Flagsmith/flagsmith/compare/v2.114.0...v2.114.1) (2024-05-14)


### Bug Fixes

* Add multivariate values when cloning identities ([#3894](https://github.com/Flagsmith/flagsmith/issues/3894)) ([92e3e9f](https://github.com/Flagsmith/flagsmith/commit/92e3e9f55c25855cd0d1b7b7333184ab54385846))
* Organisation id not numeric in organisation settings ([#3929](https://github.com/Flagsmith/flagsmith/issues/3929)) ([9e3746b](https://github.com/Flagsmith/flagsmith/commit/9e3746bd7dce9a8d2eac6bf616a73f2dd1f5b54e))
* **versioning:** fix exception getting feature states for edge identity post v2 versioning migration ([#3916](https://github.com/Flagsmith/flagsmith/issues/3916)) ([132ef77](https://github.com/Flagsmith/flagsmith/commit/132ef77ee0d50c618c23431e3ea1b60aec3e5bf4))
* **versioning:** handle mapping of environment to engine post v2 versioning migration ([#3913](https://github.com/Flagsmith/flagsmith/issues/3913)) ([75acd12](https://github.com/Flagsmith/flagsmith/commit/75acd12c632a9fe8b4a5af5a48a33d18a406e9d4))

## [2.114.0](https://github.com/Flagsmith/flagsmith/compare/v2.113.0...v2.114.0) (2024-05-10)


### Features

* add endpoint to revert v2 versioning ([#3897](https://github.com/Flagsmith/flagsmith/issues/3897)) ([da9e051](https://github.com/Flagsmith/flagsmith/commit/da9e051e72a1d50532fbf688d693980880f395c1))
* Implement GitHub Webhook ([#3906](https://github.com/Flagsmith/flagsmith/issues/3906)) ([9303267](https://github.com/Flagsmith/flagsmith/commit/9303267a078ecfb6788df51a8b3ff5fb83f67e8d))


### Bug Fixes

* Disable segment override diffs for non versioned environments ([#3914](https://github.com/Flagsmith/flagsmith/issues/3914)) ([e5b4313](https://github.com/Flagsmith/flagsmith/commit/e5b4313231bb3f882e2f61512933d9bb127c1a4d))
* Move call to GitHub integration tasks out from trigger_feature_state_change_webhooks ([#3905](https://github.com/Flagsmith/flagsmith/issues/3905)) ([dec9afa](https://github.com/Flagsmith/flagsmith/commit/dec9afab22019297e18ef6efb01c3398abeb9746))

## [2.113.0](https://github.com/Flagsmith/flagsmith/compare/v2.112.0...v2.113.0) (2024-05-09)


### Features

* Block access after seven days notice of API overage ([#3714](https://github.com/Flagsmith/flagsmith/issues/3714)) ([e2cb7eb](https://github.com/Flagsmith/flagsmith/commit/e2cb7eb003513a218e60c9d926988a8adaa0d565))
* versioned segment override change request ([#3790](https://github.com/Flagsmith/flagsmith/issues/3790)) ([cf320b7](https://github.com/Flagsmith/flagsmith/commit/cf320b7d030db0819ba784146da7e42220b154cf))


### Bug Fixes

* codehelp docs links ([#3900](https://github.com/Flagsmith/flagsmith/issues/3900)) ([5f7d3cd](https://github.com/Flagsmith/flagsmith/commit/5f7d3cd6a604c439ba586614065c8da605dc06f1))
* **docker:** Run Task Processor entrypoint with PID 1 ([#3889](https://github.com/Flagsmith/flagsmith/issues/3889)) ([79f4ef7](https://github.com/Flagsmith/flagsmith/commit/79f4ef7bbec47dcc1e315b3db7ae625b1bb91e38))
* Ensure flags are set in code example ([#3901](https://github.com/Flagsmith/flagsmith/issues/3901)) ([fa46ba7](https://github.com/Flagsmith/flagsmith/commit/fa46ba75aa050af6c05a2fe3925c2fed873687b8))
* send all users on paid subscriptions to hubspot ([#3902](https://github.com/Flagsmith/flagsmith/issues/3902)) ([0c79870](https://github.com/Flagsmith/flagsmith/commit/0c798702a313e86d62c1c4e9c7af019969eae117))

## [2.112.0](https://github.com/Flagsmith/flagsmith/compare/v2.111.1...v2.112.0) (2024-05-07)


### Features

* Clone identities (FE) ([#3725](https://github.com/Flagsmith/flagsmith/issues/3725)) ([084d775](https://github.com/Flagsmith/flagsmith/commit/084d7756864e72ef020554380e175238c39d5b3b))
* sort by Overage in sales dashboard ([#3858](https://github.com/Flagsmith/flagsmith/issues/3858)) ([2417f57](https://github.com/Flagsmith/flagsmith/commit/2417f57a037a2a6444fa2604d38dc49ffbff234c))


### Bug Fixes

* Change some texts in the cloning Identities flow ([#3862](https://github.com/Flagsmith/flagsmith/issues/3862)) ([57313ca](https://github.com/Flagsmith/flagsmith/commit/57313ca6802321688b7c735d8284f540188c4d9f))
* For Hubspot make the switch to unique org id ([#3863](https://github.com/Flagsmith/flagsmith/issues/3863)) ([54c2603](https://github.com/Flagsmith/flagsmith/commit/54c2603bbe7bef1bf3e520c6b6ae78c9c16b9458))
* Organisation can't have a new Github integration when had a prior one deleted ([#3874](https://github.com/Flagsmith/flagsmith/issues/3874)) ([53e728a](https://github.com/Flagsmith/flagsmith/commit/53e728a588cd193c8ea352d1b99ce7157d6cf2ef))
* typo ([#3861](https://github.com/Flagsmith/flagsmith/issues/3861)) ([29ae2e9](https://github.com/Flagsmith/flagsmith/commit/29ae2e995f794519cc6f5bb2fa22ebb5ba078650))
* update secrets location for GITHUB_PEM ([#3868](https://github.com/Flagsmith/flagsmith/issues/3868)) ([6e8d7b7](https://github.com/Flagsmith/flagsmith/commit/6e8d7b768871fa57f871b24c92b10f55ec43233a))
* use ENABLE_FLAGSMITH_REALTIME environment var ([#3867](https://github.com/Flagsmith/flagsmith/issues/3867)) ([41a8aa3](https://github.com/Flagsmith/flagsmith/commit/41a8aa3dd133424adef69b3f1b4ac0ae0df0bba8))
* **versioning:** feature segments updated with version ([#3880](https://github.com/Flagsmith/flagsmith/issues/3880)) ([08d4046](https://github.com/Flagsmith/flagsmith/commit/08d4046d05bfb278851b4a6bb0b3a7956a3f018d))
* **versioning:** prevent deleted segment overrides returning ([#3850](https://github.com/Flagsmith/flagsmith/issues/3850)) ([41981d4](https://github.com/Flagsmith/flagsmith/commit/41981d432b8adbb515d0bda2de3bdeb290a9276e))

## [2.111.1](https://github.com/Flagsmith/flagsmith/compare/v2.111.0...v2.111.1) (2024-04-30)


### Bug Fixes

* edit group ([#3856](https://github.com/Flagsmith/flagsmith/issues/3856)) ([b25e6f8](https://github.com/Flagsmith/flagsmith/commit/b25e6f8ad1256b5556cfc7623064a6fd42b299fb))

## [2.111.0](https://github.com/Flagsmith/flagsmith/compare/v2.110.2...v2.111.0) (2024-04-30)


### Features

* Capability for Pydantic-based OpenAPI response schemas ([#3795](https://github.com/Flagsmith/flagsmith/issues/3795)) ([609deaa](https://github.com/Flagsmith/flagsmith/commit/609deaa999c86bc05e1875c58f91c7c34532f3c5))
* **permissions:** manage permissions from a single location ([#3730](https://github.com/Flagsmith/flagsmith/issues/3730)) ([fc34a53](https://github.com/Flagsmith/flagsmith/commit/fc34a53e92ba6c1870ab9539bfa21b6af08964cc))


### Bug Fixes

* Add GitHub app URL to env var ([#3847](https://github.com/Flagsmith/flagsmith/issues/3847)) ([210dbf7](https://github.com/Flagsmith/flagsmith/commit/210dbf7543dfddcbc36422eec0be958d6e8d6589))
* Filter versioned features ([#3756](https://github.com/Flagsmith/flagsmith/issues/3756)) ([686e1ab](https://github.com/Flagsmith/flagsmith/commit/686e1ab81aae938a4a85680a6ed581d90b7ff11d))
* Get current api usage InfluxDB query ([#3846](https://github.com/Flagsmith/flagsmith/issues/3846)) ([905c9fb](https://github.com/Flagsmith/flagsmith/commit/905c9fb36a67171464f03fd9565f02db74708974))
* **hubspot:** create hubspot company with domain ([#3844](https://github.com/Flagsmith/flagsmith/issues/3844)) ([d4c9173](https://github.com/Flagsmith/flagsmith/commit/d4c9173c6c371546f581f2c81572fa2c7395dd17))
* **sentry-FLAGSMITH-API-4BN:** update permission method ([#3851](https://github.com/Flagsmith/flagsmith/issues/3851)) ([b4e058a](https://github.com/Flagsmith/flagsmith/commit/b4e058a47c807455aefcd846f7a7f48de8c4a320))
* useHasPermission import ([#3853](https://github.com/Flagsmith/flagsmith/issues/3853)) ([e156609](https://github.com/Flagsmith/flagsmith/commit/e156609570782fa9edbdf52e9e01e627e9bf8ffc))
* user delete social auth ([#3693](https://github.com/Flagsmith/flagsmith/issues/3693)) ([3372207](https://github.com/Flagsmith/flagsmith/commit/3372207a8db623a6a07ac5df0902f24b8c0b1e4a))

## [2.110.2](https://github.com/Flagsmith/flagsmith/compare/v2.110.1...v2.110.2) (2024-04-25)


### Bug Fixes

* **saas:** fix account number in secrets references ([#3842](https://github.com/Flagsmith/flagsmith/issues/3842)) ([0f6d333](https://github.com/Flagsmith/flagsmith/commit/0f6d3339b3f0e0854acb473aeffd5c97e8d37a7d))

## [2.110.1](https://github.com/Flagsmith/flagsmith/compare/v2.110.0...v2.110.1) (2024-04-25)


### Bug Fixes

* **saas:** add correct GITHUB env vars to all locations ([#3840](https://github.com/Flagsmith/flagsmith/issues/3840)) ([12242c4](https://github.com/Flagsmith/flagsmith/commit/12242c453729f9b3250a81b2637db9609c56d854))

## [2.110.0](https://github.com/Flagsmith/flagsmith/compare/v2.109.0...v2.110.0) (2024-04-25)


### Features

* Add GitHub Integration ([#3298](https://github.com/Flagsmith/flagsmith/issues/3298)) ([9aa72bd](https://github.com/Flagsmith/flagsmith/commit/9aa72bdd144e89badc24607f68207b2b4a5a84de))
* Add Pytest CI mode to optimise migrations ([#3815](https://github.com/Flagsmith/flagsmith/issues/3815)) ([25afe3b](https://github.com/Flagsmith/flagsmith/commit/25afe3b2e468687cdf3abede46da85a211f2e4d4))
* Clone identity flag states ([#3773](https://github.com/Flagsmith/flagsmith/issues/3773)) ([01794b9](https://github.com/Flagsmith/flagsmith/commit/01794b9c669208659a3936baf327742c200f47fe))


### Bug Fixes

* Delete feature external resources when GitHub integration was deleted ([#3836](https://github.com/Flagsmith/flagsmith/issues/3836)) ([576cc83](https://github.com/Flagsmith/flagsmith/commit/576cc83936bbd155ac576a2e2498e38f1bd1b827))

## [2.109.0](https://github.com/Flagsmith/flagsmith/compare/v2.108.1...v2.109.0) (2024-04-23)


### Features

* Ability to customise default environments for new project ([#3655](https://github.com/Flagsmith/flagsmith/issues/3655)) ([cfb5748](https://github.com/Flagsmith/flagsmith/commit/cfb57484597274506f44c86ec4f089b1fe4c0f14))
* Report database errors when waiting for database in entrypoint ([#3823](https://github.com/Flagsmith/flagsmith/issues/3823)) ([a66c262](https://github.com/Flagsmith/flagsmith/commit/a66c262bf169ed887418338efc735eee79884e87))
* Show organisation name in header ([#3808](https://github.com/Flagsmith/flagsmith/issues/3808)) ([10b14fd](https://github.com/Flagsmith/flagsmith/commit/10b14fd6a73462305087832ed750752b3157be80))
* Show organisation name in HTML title ([#3814](https://github.com/Flagsmith/flagsmith/issues/3814)) ([ccfe3c3](https://github.com/Flagsmith/flagsmith/commit/ccfe3c3ddea9cd7123e4576428c6a79c15ae5f5a))
* stale flags (FE) ([#3606](https://github.com/Flagsmith/flagsmith/issues/3606)) ([424b754](https://github.com/Flagsmith/flagsmith/commit/424b754cbdfdb079c76de7c890848884402b6ed2))


### Bug Fixes

* archived persistence ([#3802](https://github.com/Flagsmith/flagsmith/issues/3802)) ([40363dc](https://github.com/Flagsmith/flagsmith/commit/40363dc8171520bee32227056c0496f283647b52))
* broken link in New Segment modal ([#3820](https://github.com/Flagsmith/flagsmith/issues/3820)) ([97c5db7](https://github.com/Flagsmith/flagsmith/commit/97c5db7f9649077b230c19e67b2b4243d3478319))
* master api key org api access ([#3817](https://github.com/Flagsmith/flagsmith/issues/3817)) ([cae2eac](https://github.com/Flagsmith/flagsmith/commit/cae2eacf2325cc3d6c4b6b590e3046fe0513844d))
* Set error value from validation exception properly for feature seralizer ([#3809](https://github.com/Flagsmith/flagsmith/issues/3809)) ([18d8214](https://github.com/Flagsmith/flagsmith/commit/18d8214c760ee02a0b05ccc647868bbabc044a25))

## [2.108.1](https://github.com/Flagsmith/flagsmith/compare/v2.108.0...v2.108.1) (2024-04-18)


### Bug Fixes

* prevent unauthorised remove-users access ([#3791](https://github.com/Flagsmith/flagsmith/issues/3791)) ([05353a5](https://github.com/Flagsmith/flagsmith/commit/05353a5fbe661d504abdede8875f450c4cc8dce5))

## [2.108.0](https://github.com/Flagsmith/flagsmith/compare/v2.107.4...v2.108.0) (2024-04-17)


### Features

* Swagger schema for environment document ([#3789](https://github.com/Flagsmith/flagsmith/issues/3789)) ([dd89326](https://github.com/Flagsmith/flagsmith/commit/dd893262cff97a1b301a346737c106afc58bc146))


### Bug Fixes

* edge API not updated when versioned change request committed ([#3760](https://github.com/Flagsmith/flagsmith/issues/3760)) ([a7ee657](https://github.com/Flagsmith/flagsmith/commit/a7ee6578b5923c9f85527a022f88b1aaa0fe5a04))
* handle InfluxDBError when writing data ([#3788](https://github.com/Flagsmith/flagsmith/issues/3788)) ([1eaa823](https://github.com/Flagsmith/flagsmith/commit/1eaa823d3b7a2167ba424c83838bb72a4b2ec7ad))
* odd behaviour seen when using REPLICA_DATABASE_URLS ([#3771](https://github.com/Flagsmith/flagsmith/issues/3771)) ([ec9e8ab](https://github.com/Flagsmith/flagsmith/commit/ec9e8ab30d224042e1bc07c00355f7b3e1b3977a))

## [2.107.4](https://github.com/Flagsmith/flagsmith/compare/v2.107.3...v2.107.4) (2024-04-17)


### Bug Fixes

* Add Flagsmith signature header when testing webhook. ([#3666](https://github.com/Flagsmith/flagsmith/issues/3666)) ([c950875](https://github.com/Flagsmith/flagsmith/commit/c95087516e17cc610eea80d733cf11ddf8b74d80))
* correct JS code snippets syntax ([#3770](https://github.com/Flagsmith/flagsmith/issues/3770)) ([e2155d2](https://github.com/Flagsmith/flagsmith/commit/e2155d2cecdd67c37bc5b8e98c5b354923abac67))
* Enable faster feature loading ([#3550](https://github.com/Flagsmith/flagsmith/issues/3550)) ([157a9aa](https://github.com/Flagsmith/flagsmith/commit/157a9aab645e6853ecf9f98b8b453a1a9c95f0d6))
* tests using `has_calls` instead of `assert_has_calls` ([#3775](https://github.com/Flagsmith/flagsmith/issues/3775)) ([b019a35](https://github.com/Flagsmith/flagsmith/commit/b019a35df425e439c2ff36239bf6540c61ffe993))

## [2.107.3](https://github.com/Flagsmith/flagsmith/compare/v2.107.2...v2.107.3) (2024-04-10)


### Infrastructure (Flagsmith SaaS Only)

* cache environment segments in production ([#3745](https://github.com/Flagsmith/flagsmith/issues/3745)) ([f2302ee](https://github.com/Flagsmith/flagsmith/commit/f2302ee34d9b80f0de43b460b1f6cd2f712ba3e6))

## [2.107.2](https://github.com/Flagsmith/flagsmith/compare/v2.107.1...v2.107.2) (2024-04-09)


### Bug Fixes

* Revert "feat: Support multiple OR'd search terms in sales-dashboard" ([#3739](https://github.com/Flagsmith/flagsmith/issues/3739)) ([7dd0c82](https://github.com/Flagsmith/flagsmith/commit/7dd0c8296859717f9723047605dac9ed44ae77b0))

## [2.107.1](https://github.com/Flagsmith/flagsmith/compare/v2.107.0...v2.107.1) (2024-04-09)


### Bug Fixes

* segment override assignment ([#3734](https://github.com/Flagsmith/flagsmith/issues/3734)) ([a859902](https://github.com/Flagsmith/flagsmith/commit/a859902c21d564ddfbb5c2c433eeefab34deedb3))
* **task-processor:** catch all exceptions ([#3737](https://github.com/Flagsmith/flagsmith/issues/3737)) ([84ab486](https://github.com/Flagsmith/flagsmith/commit/84ab4867bb25c4db7c75826b3b74fdb687d86eb1))

## [2.107.0](https://github.com/Flagsmith/flagsmith/compare/v2.106.0...v2.107.0) (2024-04-09)


### Features

* add is_live filter to versions endpoint ([#3688](https://github.com/Flagsmith/flagsmith/issues/3688)) ([af0cc9c](https://github.com/Flagsmith/flagsmith/commit/af0cc9c3105759e95a35283bab2776aeab5ce65c))
* Support multiple OR'd search terms in sales-dashboard ([#3715](https://github.com/Flagsmith/flagsmith/issues/3715)) ([d5f76ff](https://github.com/Flagsmith/flagsmith/commit/d5f76ff88ef8a4356d6b653df8cf7c34d4d1c078))


### Bug Fixes

* Adjust permissions logic for view / manage groups ([#3679](https://github.com/Flagsmith/flagsmith/issues/3679)) ([5ba3083](https://github.com/Flagsmith/flagsmith/commit/5ba3083f88ddd8965d65225105d515cfd1ab9bd0))
* allow deletion of scheduled change requests ([#3713](https://github.com/Flagsmith/flagsmith/issues/3713)) ([cd1f79c](https://github.com/Flagsmith/flagsmith/commit/cd1f79c55a5a794cbf1064b10e4643707ba1f74d))
* async feature versioning test ([#3717](https://github.com/Flagsmith/flagsmith/issues/3717)) ([8ad7f04](https://github.com/Flagsmith/flagsmith/commit/8ad7f04aefca6fd519a4f2c99cf0c66540843838))
* convert CharFields to TextFields for FeatureImport / FeatureExport models ([#3720](https://github.com/Flagsmith/flagsmith/issues/3720)) ([6bebcef](https://github.com/Flagsmith/flagsmith/commit/6bebceff1cdf7bbfbcf9b22db6ca551a46ae1435))
* Create API usage notification butter bar ([#3698](https://github.com/Flagsmith/flagsmith/issues/3698)) ([d99fb24](https://github.com/Flagsmith/flagsmith/commit/d99fb24b820231e24a1a5635b717fcf5af3f679a))
* database Compose warnings and set a project name ([#3701](https://github.com/Flagsmith/flagsmith/issues/3701)) ([93ace86](https://github.com/Flagsmith/flagsmith/commit/93ace8615b30b8c7cee916be0ab73abd431dfb4f))
* ensure api/static directory is created by Git ([#3702](https://github.com/Flagsmith/flagsmith/issues/3702)) ([eca05ca](https://github.com/Flagsmith/flagsmith/commit/eca05cad2581032cac1320e422767ccd9500eeef))
* Incorrect environment variable interpolation in Makefile ([#3709](https://github.com/Flagsmith/flagsmith/issues/3709)) ([79a85bd](https://github.com/Flagsmith/flagsmith/commit/79a85bda45660c76043d17c0d06abb3f8b622954))
* organisation store imports ([#3721](https://github.com/Flagsmith/flagsmith/issues/3721)) ([2df29c4](https://github.com/Flagsmith/flagsmith/commit/2df29c4cb486e6c13b8753a462b65cc9e4d683b9))
* Remove CSRF parameter from sales-dashboard search form ([#3716](https://github.com/Flagsmith/flagsmith/issues/3716)) ([1e75ae9](https://github.com/Flagsmith/flagsmith/commit/1e75ae9b573063684c5935fd01ac1945bc869a93))

## [2.106.0](https://github.com/Flagsmith/flagsmith/compare/v2.105.1...v2.106.0) (2024-04-02)


### Features

* Add Hubspot lead tracking for Hubspot data ([#3647](https://github.com/Flagsmith/flagsmith/issues/3647)) ([ee1c396](https://github.com/Flagsmith/flagsmith/commit/ee1c396c7b22a1d751e5408a9e78450c22480fa8))
* Enabled state filter (Frontend) ([#3542](https://github.com/Flagsmith/flagsmith/issues/3542)) ([741320e](https://github.com/Flagsmith/flagsmith/commit/741320edc22046eed4248d8fb53bcfd6d230366a))


### Bug Fixes

* API usage alerting in production ([#3507](https://github.com/Flagsmith/flagsmith/issues/3507)) ([ce38ab7](https://github.com/Flagsmith/flagsmith/commit/ce38ab787e743ec20ce071ac8515bd8f39eb8358))
* Avoid using a Gunicorn config file ([#3699](https://github.com/Flagsmith/flagsmith/issues/3699)) ([647c52a](https://github.com/Flagsmith/flagsmith/commit/647c52aba4add765061fcb29eb073c6d68ee9115))
* broken CSS on Integrations page in non-Chromium browsers ([#3705](https://github.com/Flagsmith/flagsmith/issues/3705)) ([0fe8646](https://github.com/Flagsmith/flagsmith/commit/0fe8646e6a6ff9c016a5665c6cb8b1766ba4eec3))

## [2.105.1](https://github.com/Flagsmith/flagsmith/compare/v2.105.0...v2.105.1) (2024-03-28)


### Bug Fixes

* rollback json access logging ([#3694](https://github.com/Flagsmith/flagsmith/issues/3694)) ([6f66e0f](https://github.com/Flagsmith/flagsmith/commit/6f66e0ff3d295e11e9ba699b92be2f53309d8459))

## [2.105.0](https://github.com/Flagsmith/flagsmith/compare/v2.104.1...v2.105.0) (2024-03-27)


### Features

* Add domain to Hubspot company ([#3648](https://github.com/Flagsmith/flagsmith/issues/3648)) ([87d2d52](https://github.com/Flagsmith/flagsmith/commit/87d2d52b21f161352b9880aaae210853ceb9e321))
* Add org id to hubspot company ([#3680](https://github.com/Flagsmith/flagsmith/issues/3680)) ([9952424](https://github.com/Flagsmith/flagsmith/commit/99524247399079f6d28491e6d66d3776f3abaf51))
* Add subscription to Hubspot tracker ([#3676](https://github.com/Flagsmith/flagsmith/issues/3676)) ([44ed1bf](https://github.com/Flagsmith/flagsmith/commit/44ed1bfabebace7929d0b83f9a6d1508896d08e2))
* JSON logging for Gunicorn ([#3672](https://github.com/Flagsmith/flagsmith/issues/3672)) ([3ce1754](https://github.com/Flagsmith/flagsmith/commit/3ce1754d9c45200ef4e4f464953d079d478f5dac))
* Summary of group permissions in the Project settings page ([#3629](https://github.com/Flagsmith/flagsmith/issues/3629)) ([da12c93](https://github.com/Flagsmith/flagsmith/commit/da12c932c4b5a72084a0025c0c9bd8ef7daa1625))


### Bug Fixes

* Avoid loading Django settings in Gunicorn ([#3685](https://github.com/Flagsmith/flagsmith/issues/3685)) ([7c65445](https://github.com/Flagsmith/flagsmith/commit/7c654457c7eb673df61ee33295c55edff3cea172))
* prevent tasks dying from temporary loss of db connection ([#3674](https://github.com/Flagsmith/flagsmith/issues/3674)) ([b872a6c](https://github.com/Flagsmith/flagsmith/commit/b872a6ca568b0541ca46c2f38135739d214b2f10))
* Use dotenv in frontend/bin/env.js ([#3668](https://github.com/Flagsmith/flagsmith/issues/3668)) ([8c25cd6](https://github.com/Flagsmith/flagsmith/commit/8c25cd6199973cb60a70608737e3bd83631f06e9))

## [2.104.1](https://github.com/Flagsmith/flagsmith/compare/v2.104.0...v2.104.1) (2024-03-26)


### Bug Fixes

* Create group should auto focus on the name input ([#3632](https://github.com/Flagsmith/flagsmith/issues/3632)) ([ddb0b7f](https://github.com/Flagsmith/flagsmith/commit/ddb0b7f35b5e414d8a2f6d01dc88f642b0514f92))
* No pagination when querying `environments_v2` ([#3661](https://github.com/Flagsmith/flagsmith/issues/3661)) ([7e19f4f](https://github.com/Flagsmith/flagsmith/commit/7e19f4ff2b2f3941e55360936b816879af4d06b6))

## [2.104.0](https://github.com/Flagsmith/flagsmith/compare/v2.103.4...v2.104.0) (2024-03-20)


### Features

* Add state feature filter ([#3541](https://github.com/Flagsmith/flagsmith/issues/3541)) ([2ffe8e9](https://github.com/Flagsmith/flagsmith/commit/2ffe8e9adf9006d4fe1d2a5efc3c5af94bde300a))
* Filter features by owners and group owners ([#3579](https://github.com/Flagsmith/flagsmith/issues/3579)) ([79ad523](https://github.com/Flagsmith/flagsmith/commit/79ad5236e5277db4a42b53f0780640baa6499d27))
* **tags:** prevent system tag modifications ([#3605](https://github.com/Flagsmith/flagsmith/issues/3605)) ([974dfc5](https://github.com/Flagsmith/flagsmith/commit/974dfc57537003626ba10cdab98f394dbdf69ab7))


### Bug Fixes

* Add stale_flags_limit_days to Project serializer ([#3607](https://github.com/Flagsmith/flagsmith/issues/3607)) ([99e0148](https://github.com/Flagsmith/flagsmith/commit/99e0148df93eac328f3f3779813db78f78c7f7e5))
* **change-requests:** prevent incorrect scheduled changes warning ([#3593](https://github.com/Flagsmith/flagsmith/issues/3593)) ([165088b](https://github.com/Flagsmith/flagsmith/commit/165088b893910d1cfe451fc8ff5289af5fd8c3a1))
* Freeze time for tests to ensure dependability ([#3627](https://github.com/Flagsmith/flagsmith/issues/3627)) ([2f647f2](https://github.com/Flagsmith/flagsmith/commit/2f647f250d299128e2d9432bbfc28f15d3637be0))
* remove feature modal ([#3608](https://github.com/Flagsmith/flagsmith/issues/3608)) ([9d737ad](https://github.com/Flagsmith/flagsmith/commit/9d737ad456dbf07596cb0dd7b796a7e3175c1ab8))
* startup plan does not allow correct permissions ([#3602](https://github.com/Flagsmith/flagsmith/issues/3602)) ([9642e2f](https://github.com/Flagsmith/flagsmith/commit/9642e2f3f23f00c586820b6b21a26280dd9689f2))

## [2.103.4](https://github.com/Flagsmith/flagsmith/compare/v2.103.3...v2.103.4) (2024-03-11)


### Bug Fixes

* don't create feature export before launch darkly import ([#3510](https://github.com/Flagsmith/flagsmith/issues/3510)) ([afadf5a](https://github.com/Flagsmith/flagsmith/commit/afadf5afa26eae667cdcedbce268185614b7a85d))

## [2.103.3](https://github.com/Flagsmith/flagsmith/compare/v2.103.2...v2.103.3) (2024-03-11)


### Bug Fixes

* **audit:** add segment deleted audit log ([#3585](https://github.com/Flagsmith/flagsmith/issues/3585)) ([e2b8a92](https://github.com/Flagsmith/flagsmith/commit/e2b8a9287269133f3a19fd0a51fc8bb53a63551b))
* poetry audit ([#3592](https://github.com/Flagsmith/flagsmith/issues/3592)) ([c2155b2](https://github.com/Flagsmith/flagsmith/commit/c2155b2c2e76e44b5fee09a66f4de6e52aa93fe9))
* remove duplicate tos ([#3589](https://github.com/Flagsmith/flagsmith/issues/3589)) ([0f2506e](https://github.com/Flagsmith/flagsmith/commit/0f2506e7dc85948e0aa690cd6e8b35073f4df763))

## [2.103.2](https://github.com/Flagsmith/flagsmith/compare/v2.103.1...v2.103.2) (2024-03-08)


### Bug Fixes

* **audit:** create audit log for deleted conditions in a segment ([#3577](https://github.com/Flagsmith/flagsmith/issues/3577)) ([1330b4a](https://github.com/Flagsmith/flagsmith/commit/1330b4a5d8c68c8840814c867fb4105374e2e089))
* **audit:** use correct endpoint for retrieve ([#3578](https://github.com/Flagsmith/flagsmith/issues/3578)) ([5f98b1b](https://github.com/Flagsmith/flagsmith/commit/5f98b1ba0746acfeeb1b430ab892890ed4de34a3))
* clear schedule date ([#3558](https://github.com/Flagsmith/flagsmith/issues/3558)) ([fa9c68f](https://github.com/Flagsmith/flagsmith/commit/fa9c68f7717d68382803da472e132125655d05a4))
* enable hubspot for staging ([#3545](https://github.com/Flagsmith/flagsmith/issues/3545)) ([2460c81](https://github.com/Flagsmith/flagsmith/commit/2460c8151ee81174d73934817691f4bd0ce54569))
* prevent cascade deletes from users deleting change requests ([#3580](https://github.com/Flagsmith/flagsmith/issues/3580)) ([b961790](https://github.com/Flagsmith/flagsmith/commit/b9617904e45b167a50908f1df5c7494f6ec42859))
* Project settings with no environments ([#3572](https://github.com/Flagsmith/flagsmith/issues/3572)) ([becfff1](https://github.com/Flagsmith/flagsmith/commit/becfff19c11a9720b583d20645c637dcdf64308c))
* Refresh filter after tagging ([#3575](https://github.com/Flagsmith/flagsmith/issues/3575)) ([62f8f69](https://github.com/Flagsmith/flagsmith/commit/62f8f69aa198cf03aaada3e736ff7f6f14f1f776))
* **revert:** disable hubspot for staging ([#3576](https://github.com/Flagsmith/flagsmith/issues/3576)) ([c647fbd](https://github.com/Flagsmith/flagsmith/commit/c647fbdcccd3a14cd2940668d70c9e32e99a3095))

## [2.103.1](https://github.com/Flagsmith/flagsmith/compare/v2.103.0...v2.103.1) (2024-03-05)


### Bug Fixes

* Dasherize conversion event types path ([#3516](https://github.com/Flagsmith/flagsmith/issues/3516)) ([994eb55](https://github.com/Flagsmith/flagsmith/commit/994eb556123b0c04495f00d16369c12943927fa6))
* **fs-delete/webhook:** use fs instance instead of historical ([#3475](https://github.com/Flagsmith/flagsmith/issues/3475)) ([90e10cf](https://github.com/Flagsmith/flagsmith/commit/90e10cf656dba13c2a137e2c5630b325b8290776))

## [2.103.0](https://github.com/Flagsmith/flagsmith/compare/v2.102.0...v2.103.0) (2024-03-01)


### Features

* Add has expired column in the api keys table ([#3433](https://github.com/Flagsmith/flagsmith/issues/3433)) ([3f83130](https://github.com/Flagsmith/flagsmith/commit/3f83130fb00e09878228483131187df9d61e117f))
* Track leads to Hubspot ([#3473](https://github.com/Flagsmith/flagsmith/issues/3473)) ([02c59d2](https://github.com/Flagsmith/flagsmith/commit/02c59d25c7a440d0fc0a09a689ea62202c4e1c43))


### Bug Fixes

* Add padding to the announcement ([#3474](https://github.com/Flagsmith/flagsmith/issues/3474)) ([e5f29a1](https://github.com/Flagsmith/flagsmith/commit/e5f29a11b068c1a2537df66dd72fb47f95852209))
* Add trailing / to delete api key endpoint ([#3506](https://github.com/Flagsmith/flagsmith/issues/3506)) ([0d655a0](https://github.com/Flagsmith/flagsmith/commit/0d655a0a0399c02032f4c2369c09c0d7b616944f))
* N+1 on segment overrides for environment-document endpoint ([#3512](https://github.com/Flagsmith/flagsmith/issues/3512)) ([4e92f34](https://github.com/Flagsmith/flagsmith/commit/4e92f348c2e9863e19bd72f8bca1499d9a42786d))
* toggle flag ([#3480](https://github.com/Flagsmith/flagsmith/issues/3480)) ([87cfcd9](https://github.com/Flagsmith/flagsmith/commit/87cfcd9baee2a28dee53842e6fea79bc5dea9fd3))

## [2.102.0](https://github.com/Flagsmith/flagsmith/compare/v2.101.0...v2.102.0) (2024-02-27)


### Features

* add option to disable secure cookies and configure `samesite` ([#3441](https://github.com/Flagsmith/flagsmith/issues/3441)) ([7ec5491](https://github.com/Flagsmith/flagsmith/commit/7ec54911d617f113dae5a735a9b2007ddc7405e7))

## [2.101.0](https://github.com/Flagsmith/flagsmith/compare/v2.100.1...v2.101.0) (2024-02-26)


### Features

* add fields necessary for stale flags ([#3263](https://github.com/Flagsmith/flagsmith/issues/3263)) ([aa1d6bb](https://github.com/Flagsmith/flagsmith/commit/aa1d6bb9f06dd4071ccab098f2be9cfba678e012))
* Add role API key (BE) ([#3346](https://github.com/Flagsmith/flagsmith/issues/3346)) ([c60a145](https://github.com/Flagsmith/flagsmith/commit/c60a14518331f2f3c3f975ce517bb556bdaa6d0c))
* Add role api keys in UI ([#3042](https://github.com/Flagsmith/flagsmith/issues/3042)) ([b746d09](https://github.com/Flagsmith/flagsmith/commit/b746d098e58d9915ee975f7c8b75d750d126e9b9))
* **api-keys:** add `has_expired` to MasterAPIKey response ([#3432](https://github.com/Flagsmith/flagsmith/issues/3432)) ([0a28ee0](https://github.com/Flagsmith/flagsmith/commit/0a28ee02578f48affc099d084f4af87015a527ed))
* Create api usage function ([#3340](https://github.com/Flagsmith/flagsmith/issues/3340)) ([16a2468](https://github.com/Flagsmith/flagsmith/commit/16a24685449ea33906c5b225929c1ad08717ca70))
* **datadog:** add source type name to datadog ([#3342](https://github.com/Flagsmith/flagsmith/issues/3342)) ([a89410c](https://github.com/Flagsmith/flagsmith/commit/a89410c2ac315350c7a6dc0c4b9993ed90b1ed8c))
* GitHub star ([#3451](https://github.com/Flagsmith/flagsmith/issues/3451)) ([b3414b3](https://github.com/Flagsmith/flagsmith/commit/b3414b3ab0561c266c969b0d37f0dd3c6e2a4516))
* Import export environment flags ([#3161](https://github.com/Flagsmith/flagsmith/issues/3161)) ([7b8c8dc](https://github.com/Flagsmith/flagsmith/commit/7b8c8dc753af1d6073e203a745a79b7969536a8c))
* Issue 166 json formatted logs ([#3376](https://github.com/Flagsmith/flagsmith/issues/3376)) ([c666d29](https://github.com/Flagsmith/flagsmith/commit/c666d2961b62634aa51e7c2d9ccb2ed3b4060bec))
* project usage limits ([#3313](https://github.com/Flagsmith/flagsmith/issues/3313)) ([87501f5](https://github.com/Flagsmith/flagsmith/commit/87501f5273aaaef843e97bf26ad063b2e07cfcbb))
* **segments:** add query param to exclude / include feature specific ([#3430](https://github.com/Flagsmith/flagsmith/issues/3430)) ([aa22aad](https://github.com/Flagsmith/flagsmith/commit/aa22aad2138feb100942feddcccf8a27bf4ac61b))
* versioned feature states ([#2688](https://github.com/Flagsmith/flagsmith/issues/2688)) ([c02562e](https://github.com/Flagsmith/flagsmith/commit/c02562ec94f5e590d87e1e5ab30e2e2111620965))


### Bug Fixes

* Add create segment error handling ([#3413](https://github.com/Flagsmith/flagsmith/issues/3413)) ([932c62d](https://github.com/Flagsmith/flagsmith/commit/932c62d2b65503e5f707e5f4e1084546919166c8))
* **analytics:** move feature_name index into its own migration file ([#3427](https://github.com/Flagsmith/flagsmith/issues/3427)) ([39b7300](https://github.com/Flagsmith/flagsmith/commit/39b730098371a80b7b4c5266ba400ed19955a9b5))
* audit paging ([#3421](https://github.com/Flagsmith/flagsmith/issues/3421)) ([32f3b0a](https://github.com/Flagsmith/flagsmith/commit/32f3b0a9ccccbb3bb8b91ba854ffa9f5f5cb9ea0))
* **db:** Fix read replica strategy ([#3426](https://github.com/Flagsmith/flagsmith/issues/3426)) ([d63a289](https://github.com/Flagsmith/flagsmith/commit/d63a2896e53edbe34edd8d5c88e13c6aba982789))
* Docs - Bring the code examples in-line with the latest SDK ([#3456](https://github.com/Flagsmith/flagsmith/issues/3456)) ([1270b18](https://github.com/Flagsmith/flagsmith/commit/1270b18a2340962cba46eb3047340a3f74930267))
* Get permissions by using environment instead of project scope ([#3444](https://github.com/Flagsmith/flagsmith/issues/3444)) ([1b427f2](https://github.com/Flagsmith/flagsmith/commit/1b427f29d3981d6cf9938ea41fd33eb29bad3843))
* Limit segment rules and conditions ([#3397](https://github.com/Flagsmith/flagsmith/issues/3397)) ([c89e96e](https://github.com/Flagsmith/flagsmith/commit/c89e96ec70e67a69817897e692c47397a3a9b00c))
* **migrations:** Fix tags migrations ([#3419](https://github.com/Flagsmith/flagsmith/issues/3419)) ([f1ebdf5](https://github.com/Flagsmith/flagsmith/commit/f1ebdf56b1c81ff9abc8601a31259a351a1350f1))
* org switcher ([#3453](https://github.com/Flagsmith/flagsmith/issues/3453)) ([3bc1bd8](https://github.com/Flagsmith/flagsmith/commit/3bc1bd819f5e1f68a3984a4d6100ec786b8d3e5b))
* **segments:** use API query param for feature-specific filter ([#3431](https://github.com/Flagsmith/flagsmith/issues/3431)) ([86cc3da](https://github.com/Flagsmith/flagsmith/commit/86cc3dabd8804f2d38ba8fc47913f30d1aeb943a))
* toggle mv flags ([#3450](https://github.com/Flagsmith/flagsmith/issues/3450)) ([4214657](https://github.com/Flagsmith/flagsmith/commit/42146573f5083950769be6948e50c58f5ea12fdc))
* Versioning test - always login regardless of skip test ([#3424](https://github.com/Flagsmith/flagsmith/issues/3424)) ([a04aafb](https://github.com/Flagsmith/flagsmith/commit/a04aafbef0a366ab6b1990092f24e48ec8511b24))

## [2.100.1](https://github.com/Flagsmith/flagsmith/compare/v2.100.0...v2.100.1) (2024-02-13)


### Bug Fixes

* **infra:** use correct version number for flagsmith workflows ([#3408](https://github.com/Flagsmith/flagsmith/issues/3408)) ([7adaeb1](https://github.com/Flagsmith/flagsmith/commit/7adaeb123c9ee2e9dfe62d35266db590ec38ab5d))

## [2.100.0](https://github.com/Flagsmith/flagsmith/compare/v2.99.0...v2.100.0) (2024-02-12)


### Features

* Add support for replicas and cross region replicas ([#3300](https://github.com/Flagsmith/flagsmith/issues/3300)) ([bda59f5](https://github.com/Flagsmith/flagsmith/commit/bda59f5982270545c27e600b77e5d06f6229ab93))
* **api-usage:** add environment variable to prevent API usage tracking. ([#3386](https://github.com/Flagsmith/flagsmith/issues/3386)) ([5fa0a1a](https://github.com/Flagsmith/flagsmith/commit/5fa0a1a4694a9c869bdec3604271bcd5ecbc43b4))
* Create split testing for multivariate ([#3235](https://github.com/Flagsmith/flagsmith/issues/3235)) ([ad3ce0e](https://github.com/Flagsmith/flagsmith/commit/ad3ce0e962c85c97fdce1641f3e842ab1c2cfb03))
* try importing rules from LD flags ([#3233](https://github.com/Flagsmith/flagsmith/issues/3233)) ([42634ec](https://github.com/Flagsmith/flagsmith/commit/42634ece4724b869f21e13fc4818e93406c5e0d5))


### Bug Fixes

* Avoid errors when missing subscription information cache id ([#3380](https://github.com/Flagsmith/flagsmith/issues/3380)) ([d9a835f](https://github.com/Flagsmith/flagsmith/commit/d9a835f525ffb3976eabc99dd3210a3804b59744))
* delete project ([#3393](https://github.com/Flagsmith/flagsmith/issues/3393)) ([be544e2](https://github.com/Flagsmith/flagsmith/commit/be544e2351044ebf08eabe67b2ca1315d2fe86ae))
* **redis_cache:** extend DefaultClient class to add support  for RedisClusterException ([#3392](https://github.com/Flagsmith/flagsmith/issues/3392)) ([0949963](https://github.com/Flagsmith/flagsmith/commit/0949963a804e4d9aa69120d48181c220f9bdd375))
* **redis-cluster:** add lower socket timeout ([#3401](https://github.com/Flagsmith/flagsmith/issues/3401)) ([37b89b3](https://github.com/Flagsmith/flagsmith/commit/37b89b311d77d570c822ca2800f3719e26826ea1))
* regex tester ([#3395](https://github.com/Flagsmith/flagsmith/issues/3395)) ([64650c6](https://github.com/Flagsmith/flagsmith/commit/64650c630542338c5c41929eeecd40fe443f18de))
* regular expression validation UI ([#3394](https://github.com/Flagsmith/flagsmith/issues/3394)) ([5f13624](https://github.com/Flagsmith/flagsmith/commit/5f13624136c52e74b9dcb9712ad720e8ac11644e))

## [2.99.0](https://github.com/Flagsmith/flagsmith/compare/v2.98.0...v2.99.0) (2024-02-05)


### Features

* Add audit log detail page ([#3356](https://github.com/Flagsmith/flagsmith/issues/3356)) ([e8bc7d3](https://github.com/Flagsmith/flagsmith/commit/e8bc7d3116e9b2ba153044e5539ee5872af13028))


### Bug Fixes

* **revert:** "feat(rate-limit): enable rate limit in production ([#3362](https://github.com/Flagsmith/flagsmith/issues/3362))" ([#3381](https://github.com/Flagsmith/flagsmith/issues/3381)) ([ea3bc3c](https://github.com/Flagsmith/flagsmith/commit/ea3bc3cfd9e451f7ddba0ae493e8531e86b039f6))

## [2.98.0](https://github.com/Flagsmith/flagsmith/compare/v2.97.1...v2.98.0) (2024-02-05)


### Features

* **rate-limit:** enable rate limit in production ([#3362](https://github.com/Flagsmith/flagsmith/issues/3362)) ([f9545f7](https://github.com/Flagsmith/flagsmith/commit/f9545f702079587cde0a6cd24558fee3baf49433))
* **task-processor:** add Task Processor inputs as env vars ([#3355](https://github.com/Flagsmith/flagsmith/issues/3355)) ([789898c](https://github.com/Flagsmith/flagsmith/commit/789898c47a3fa726bbd1c99d7d7700ae1eb4f3ef))


### Bug Fixes

* **audit:** add details for override creation ([#3359](https://github.com/Flagsmith/flagsmith/issues/3359)) ([a888f29](https://github.com/Flagsmith/flagsmith/commit/a888f291eafd3b113233cf30b19594a37f8fb13a))
* Long `DELETE` project call ([#3360](https://github.com/Flagsmith/flagsmith/issues/3360)) ([aca0fc5](https://github.com/Flagsmith/flagsmith/commit/aca0fc54f5902d4c9ba5630aa8af35b66b7c0799))
* **webhooks:** prevent unnecessary organisation webhook tasks ([#3365](https://github.com/Flagsmith/flagsmith/issues/3365)) ([ec32ce7](https://github.com/Flagsmith/flagsmith/commit/ec32ce7dfc86ccb350f2a9e1af8c3f85f6c154b7))

## [2.97.1](https://github.com/Flagsmith/flagsmith/compare/v2.97.0...v2.97.1) (2024-02-02)


### Bug Fixes

* **audit:** handle case where AuditLog doesn't have a history record ([#3357](https://github.com/Flagsmith/flagsmith/issues/3357)) ([6501829](https://github.com/Flagsmith/flagsmith/commit/65018291c96730c7ef045ccc79defaa5e84e09db))
* **feature-service/get_edge_override:** handle deleted features ([#3368](https://github.com/Flagsmith/flagsmith/issues/3368)) ([1eae11c](https://github.com/Flagsmith/flagsmith/commit/1eae11c93076cfb4d6a226de385166953fcea2b6))

## [2.97.0](https://github.com/Flagsmith/flagsmith/compare/v2.96.0...v2.97.0) (2024-01-31)


### Features

* **rate-limit/redis:** Use redis to store throttling data for admin endpoints ([#2863](https://github.com/Flagsmith/flagsmith/issues/2863)) ([61537ce](https://github.com/Flagsmith/flagsmith/commit/61537ce790dc3b2119b7cc8ee15b9ddc5530c2c9))
* send telemetry heartbeat post migrations are applied ([#3351](https://github.com/Flagsmith/flagsmith/issues/3351)) ([31af594](https://github.com/Flagsmith/flagsmith/commit/31af59418a6995fd7e6813f07e8eaea5747e13ab))


### Bug Fixes

* **2079/deadlock:** avoid deadlock by updating env individually ([#3339](https://github.com/Flagsmith/flagsmith/issues/3339)) ([85443a2](https://github.com/Flagsmith/flagsmith/commit/85443a23c4d81cd41045604f605c14d541ceae3d))
* **staging/infra/redis:** use correct connection factory ([#3353](https://github.com/Flagsmith/flagsmith/issues/3353)) ([4a5f5e6](https://github.com/Flagsmith/flagsmith/commit/4a5f5e6af28ff755e1f82617d605be26a2e2ba42))
* **webhook/logging:** log response code only if response is not none ([#3354](https://github.com/Flagsmith/flagsmith/issues/3354)) ([ea42a34](https://github.com/Flagsmith/flagsmith/commit/ea42a34bd320a077ebc225ac999f4cac875b8df0))

## [2.96.0](https://github.com/Flagsmith/flagsmith/compare/v2.95.0...v2.96.0) (2024-01-29)


### Features

* make segment condition value dynamic ([#3245](https://github.com/Flagsmith/flagsmith/issues/3245)) ([dea63df](https://github.com/Flagsmith/flagsmith/commit/dea63df8a1fb26c09caf2087d241bc27890035ff))
* redesign organisation layout ([#3257](https://github.com/Flagsmith/flagsmith/issues/3257)) ([61d0585](https://github.com/Flagsmith/flagsmith/commit/61d0585eea358b0e8a32aa0a1d80e85dc40d4a6b))
* **sse/tracking:** Add project and org name to the influx event ([#3337](https://github.com/Flagsmith/flagsmith/issues/3337)) ([351232f](https://github.com/Flagsmith/flagsmith/commit/351232fc82a88cd12483f701ba832d1ae3725dd5))


### Bug Fixes

* display of usage chart ([#3331](https://github.com/Flagsmith/flagsmith/issues/3331)) ([21cf0b8](https://github.com/Flagsmith/flagsmith/commit/21cf0b8e159190df516635253b88df3b8b33e0d8))
* projects list navigation ([#3328](https://github.com/Flagsmith/flagsmith/issues/3328)) ([92d6076](https://github.com/Flagsmith/flagsmith/commit/92d6076df295aeda17576625482280758b84636d))
* segment paging ([#3332](https://github.com/Flagsmith/flagsmith/issues/3332)) ([8050aed](https://github.com/Flagsmith/flagsmith/commit/8050aed9448203245e6585bd5962a5538502c48a))
* tweak sdk copy ([#3341](https://github.com/Flagsmith/flagsmith/issues/3341)) ([13617c5](https://github.com/Flagsmith/flagsmith/commit/13617c5c37c5b05b244c0a25436f1c5c9aa7c21f))

## [2.95.0](https://github.com/Flagsmith/flagsmith/compare/v2.94.0...v2.95.0) (2024-01-23)


### Features

* Add endpoints for feature imports ([#3255](https://github.com/Flagsmith/flagsmith/issues/3255)) ([a2eeaf4](https://github.com/Flagsmith/flagsmith/commit/a2eeaf402b50609d5986c0897f819b275d58c926))


### Bug Fixes

* allow editing scheduled changes ([#3227](https://github.com/Flagsmith/flagsmith/issues/3227)) ([90ee8c7](https://github.com/Flagsmith/flagsmith/commit/90ee8c76ebfd9aa554334dbf9a9b588191f4d0e0))
* Handle feature import processing during import ([#3305](https://github.com/Flagsmith/flagsmith/issues/3305)) ([28459c5](https://github.com/Flagsmith/flagsmith/commit/28459c502405de2a208f86f66f573a4a4d60d45e))
* Incorrect tag filtering when results have no features ([#3309](https://github.com/Flagsmith/flagsmith/issues/3309)) ([cca86c3](https://github.com/Flagsmith/flagsmith/commit/cca86c391cfd167f3a968128ef6b4b568628dfdb))
* **sse/stream_access_logs:** handle invalid log ([#3307](https://github.com/Flagsmith/flagsmith/issues/3307)) ([0ef4764](https://github.com/Flagsmith/flagsmith/commit/0ef476466fd8688053b68c3cb03f39b945056e87))
* variation percentage calculation ([#3268](https://github.com/Flagsmith/flagsmith/issues/3268)) ([ec272ba](https://github.com/Flagsmith/flagsmith/commit/ec272ba29f08f58c5a30bdc6e6da7a03233b8513))

## [2.94.0](https://github.com/Flagsmith/flagsmith/compare/v2.93.0...v2.94.0) (2024-01-16)


### Features

* pure BSD3 license ([#3294](https://github.com/Flagsmith/flagsmith/issues/3294)) ([1a1f265](https://github.com/Flagsmith/flagsmith/commit/1a1f2654a5fcfab4c35386c8f74f8ca4caa5a2e8))


### Bug Fixes

* Paging spacer logic ([#3275](https://github.com/Flagsmith/flagsmith/issues/3275)) ([00ac34e](https://github.com/Flagsmith/flagsmith/commit/00ac34ee76b91fe789f60590f92531c9c9c1a7f6))
* Reading role permissions generates 500 errors ([#3009](https://github.com/Flagsmith/flagsmith/issues/3009)) ([de5cf9d](https://github.com/Flagsmith/flagsmith/commit/de5cf9db8a97414241e84b5b51853bb77f9e878c))
* Reset password error handling ([#3271](https://github.com/Flagsmith/flagsmith/issues/3271)) ([a54352f](https://github.com/Flagsmith/flagsmith/commit/a54352fe8efb0488fab1c41019df7a5ce305454c))
* Tidy up ld import ([#3276](https://github.com/Flagsmith/flagsmith/issues/3276)) ([3ee8e6a](https://github.com/Flagsmith/flagsmith/commit/3ee8e6a8be8f2260660997c857d369b55800b476))
* **webhooks:** prevent raise on give up ([#3295](https://github.com/Flagsmith/flagsmith/issues/3295)) ([581a8c9](https://github.com/Flagsmith/flagsmith/commit/581a8c9c31666aadfd64d6b656f6836d71631e3f))

## [2.93.0](https://github.com/Flagsmith/flagsmith/compare/v2.92.0...v2.93.0) (2024-01-11)


### Features

* **audit:** add change details to AuditLog ([#3218](https://github.com/Flagsmith/flagsmith/issues/3218)) ([c665063](https://github.com/Flagsmith/flagsmith/commit/c665063fd22b7cf740eb5b27981c8633a577c470))
* Call webhooks async and add backoff to webhooks ([#2932](https://github.com/Flagsmith/flagsmith/issues/2932)) ([445c698](https://github.com/Flagsmith/flagsmith/commit/445c69837b43e341d6ad48a1a9fd7d12af47a115))
* **dynamo_documents:** propagate delete to dynamo  ([#3220](https://github.com/Flagsmith/flagsmith/issues/3220)) ([b7ecd75](https://github.com/Flagsmith/flagsmith/commit/b7ecd75810d0d98221b775a7f87ba1e73b98647a))
* implement feature actions dropdown ([#3253](https://github.com/Flagsmith/flagsmith/issues/3253)) ([972f1a3](https://github.com/Flagsmith/flagsmith/commit/972f1a364e4774f7a4ce722fe88b4bbee6bb9a11))
* **tags/view:** Add api to get tag by uuid ([#3229](https://github.com/Flagsmith/flagsmith/issues/3229)) ([6500451](https://github.com/Flagsmith/flagsmith/commit/6500451a93c317df6fe57740abc5f5b70853bfa5))


### Bug Fixes

* Adjust segment not rule ([#3267](https://github.com/Flagsmith/flagsmith/issues/3267)) ([6edc932](https://github.com/Flagsmith/flagsmith/commit/6edc9324ffc02aedcf768aeaf5268cbca458d7ee))
* **infra/staging:** Add INFLUXDB_BUCKET to task def ([#3199](https://github.com/Flagsmith/flagsmith/issues/3199)) ([445dc2b](https://github.com/Flagsmith/flagsmith/commit/445dc2b852617953fefd7dd6b40c5f1eee480450))
* OR button hiding and empty condtions ([#3269](https://github.com/Flagsmith/flagsmith/issues/3269)) ([0e28b6c](https://github.com/Flagsmith/flagsmith/commit/0e28b6cc98f5a4c03c95d662058cef896e1f8132))
* **versioning:** endpoints should return latest versions ([#3209](https://github.com/Flagsmith/flagsmith/issues/3209)) ([5e16e56](https://github.com/Flagsmith/flagsmith/commit/5e16e56c34e66787dc8d25512e58d1dbe869a4c4))
* **webhooks:** default task processor to use processor and prevent webhook retries in non-processor environments ([#3273](https://github.com/Flagsmith/flagsmith/issues/3273)) ([4d002fc](https://github.com/Flagsmith/flagsmith/commit/4d002fc84f563b559fceb67c2d03ace822d18499))

## [2.92.0](https://github.com/Flagsmith/flagsmith/compare/v2.91.0...v2.92.0) (2024-01-02)


### Features

* Add new url for role master api keys ([#3215](https://github.com/Flagsmith/flagsmith/issues/3215)) ([924149c](https://github.com/Flagsmith/flagsmith/commit/924149cdb711c510d2eb94c3d03f492977fac335))
* prepopulate control value on segment overrides ([#3208](https://github.com/Flagsmith/flagsmith/issues/3208)) ([68a1c6c](https://github.com/Flagsmith/flagsmith/commit/68a1c6c27eac83b90a9161864b47a9c19d6115f8))
* **tasks-processor:** Add recurring task to clean up old recurring task runs ([#3151](https://github.com/Flagsmith/flagsmith/issues/3151)) ([9f83f27](https://github.com/Flagsmith/flagsmith/commit/9f83f27481d31147173f772728c3e31116ba4548))


### Bug Fixes

* `env` variable instructions on locally-api.md ([#3223](https://github.com/Flagsmith/flagsmith/issues/3223)) ([4f2fa90](https://github.com/Flagsmith/flagsmith/commit/4f2fa90da424f326d2b8e3758c41439554cc829f))
* erroneous booleans in feature tooltip ([#3219](https://github.com/Flagsmith/flagsmith/issues/3219)) ([3758d33](https://github.com/Flagsmith/flagsmith/commit/3758d335a4c959e7da4f2caa0545711f90535969))

## [2.91.0](https://github.com/Flagsmith/flagsmith/compare/v2.90.0...v2.91.0) (2023-12-21)


### Features

* Add new url for roles master api keys ([#3154](https://github.com/Flagsmith/flagsmith/issues/3154)) ([d770399](https://github.com/Flagsmith/flagsmith/commit/d7703994f700f078f1a569be1f0fb64923b19193))
* add new url from role groups ([#3178](https://github.com/Flagsmith/flagsmith/issues/3178)) ([eebc541](https://github.com/Flagsmith/flagsmith/commit/eebc541e89daedfba4c98716d88c3ff5d4943032))
* Revert Add new url for roles master api keys ([#3154](https://github.com/Flagsmith/flagsmith/issues/3154)) ([#3214](https://github.com/Flagsmith/flagsmith/issues/3214)) ([22b8d9c](https://github.com/Flagsmith/flagsmith/commit/22b8d9cc2b8e51f622ea18520987351b2dda27a1))


### Bug Fixes

* **admin/task-processor:** handle no task run ([#3196](https://github.com/Flagsmith/flagsmith/issues/3196)) ([eab1f6d](https://github.com/Flagsmith/flagsmith/commit/eab1f6db74a9b0ba728e081bcc6ce83001553b15))
* **subscriptions:** ensure that manually added subscriptions work correctly in all deployments ([#3182](https://github.com/Flagsmith/flagsmith/issues/3182)) ([ae94267](https://github.com/Flagsmith/flagsmith/commit/ae94267bd11b346baa1466bf3d3c2ce38b2935dc))
* **task-processor:** implement grace period for deleting old recurring task ([#3169](https://github.com/Flagsmith/flagsmith/issues/3169)) ([00f0552](https://github.com/Flagsmith/flagsmith/commit/00f055297b55f3dfdceb8bd35ec22e1d50bfadfd))

## [2.90.0](https://github.com/Flagsmith/flagsmith/compare/v2.89.0...v2.90.0) (2023-12-20)


### Features

* **task-processor:** Add recurring task to clean password reset ([#3153](https://github.com/Flagsmith/flagsmith/issues/3153)) ([6898253](https://github.com/Flagsmith/flagsmith/commit/6898253d10e2347b9a309e81e0766761ce560e83))


### Bug Fixes

* **sse/tracking:** Use INFLUXDB_BUCKET for storing data ([#3197](https://github.com/Flagsmith/flagsmith/issues/3197)) ([fbd14fe](https://github.com/Flagsmith/flagsmith/commit/fbd14feed3aa2e3ffc861ce304e973f06614f91a))
* **task-processor/task-definition:** set RUN_BY_PROCESSOR ([#3195](https://github.com/Flagsmith/flagsmith/issues/3195)) ([f478def](https://github.com/Flagsmith/flagsmith/commit/f478def5af554752c0824d3fb7110d0052ad7406))
* **ui:** SAML should not be in Scale-up ([#3189](https://github.com/Flagsmith/flagsmith/issues/3189)) ([e6822bd](https://github.com/Flagsmith/flagsmith/commit/e6822bda01443c7fc05b5070ea90f490f0b4f6be))

## [2.89.0](https://github.com/Flagsmith/flagsmith/compare/v2.88.0...v2.89.0) (2023-12-19)


### Features

* Count v2 identity overrides for feature state list view ([#3164](https://github.com/Flagsmith/flagsmith/issues/3164)) ([65be52b](https://github.com/Flagsmith/flagsmith/commit/65be52b72835ba36075b499fdac59a1ace61b6ec))
* Create flagsmith on flagsmith feature export task ([#3149](https://github.com/Flagsmith/flagsmith/issues/3149)) ([e74ba0f](https://github.com/Flagsmith/flagsmith/commit/e74ba0f13ec17a3c949a9b3d1f68c2e15419d04e))
* Organisation reverts to free plan ([#3096](https://github.com/Flagsmith/flagsmith/issues/3096)) ([e5efdc8](https://github.com/Flagsmith/flagsmith/commit/e5efdc861cb6f88ac60dc503a596683f8a5ec0f1))
* **postgres/analytics:** Add task to clean-up old data ([#3170](https://github.com/Flagsmith/flagsmith/issues/3170)) ([8c8ce1f](https://github.com/Flagsmith/flagsmith/commit/8c8ce1f60478de197b95fc148abcaed680f2c5e5))
* Write migrated environments to v2 ([#3147](https://github.com/Flagsmith/flagsmith/issues/3147)) ([5914860](https://github.com/Flagsmith/flagsmith/commit/59148603b1566ef630d0b78118a540a210fb1624))


### Bug Fixes

* Add missing f-string from app_analytics models ([#3155](https://github.com/Flagsmith/flagsmith/issues/3155)) ([58d6589](https://github.com/Flagsmith/flagsmith/commit/58d6589889647a71fe22dacc4d960225996eee20))
* change request rendering issue when author no longer belongs to organisation ([#3087](https://github.com/Flagsmith/flagsmith/issues/3087)) ([8087fe2](https://github.com/Flagsmith/flagsmith/commit/8087fe2b65cd2ec2c945ea6d7d88332645f335ee))
* **Dockerfile:** setup gnupg correctly for nobody ([#3167](https://github.com/Flagsmith/flagsmith/issues/3167)) ([4759876](https://github.com/Flagsmith/flagsmith/commit/47598768d672dd1623abb822753317ddcc6c570c))
* Fine tune feature import export ([#3163](https://github.com/Flagsmith/flagsmith/issues/3163)) ([79e67ee](https://github.com/Flagsmith/flagsmith/commit/79e67ee40b06071093c580ab96649e2d5873407f))
* hide identity overrides badge or edge projects ([#3156](https://github.com/Flagsmith/flagsmith/issues/3156)) ([6a44b3d](https://github.com/Flagsmith/flagsmith/commit/6a44b3dd90cc9ff549dd99752618decd8d3cac9c))

## [2.88.0](https://github.com/Flagsmith/flagsmith/compare/v2.87.0...v2.88.0) (2023-12-13)


### Features

* Add a task for writing (edge) identity overrides ([#3127](https://github.com/Flagsmith/flagsmith/issues/3127)) ([2a9cd7c](https://github.com/Flagsmith/flagsmith/commit/2a9cd7cace471c2876f455436a9c5b0dd5cb4d45))
* add attribute to store identity overrides storage type ([#3109](https://github.com/Flagsmith/flagsmith/issues/3109)) ([c31322b](https://github.com/Flagsmith/flagsmith/commit/c31322bd4ed661d8ef23130cdcc0f4ad57a94153))
* Add dunning banner ([#3114](https://github.com/Flagsmith/flagsmith/issues/3114)) ([ad26100](https://github.com/Flagsmith/flagsmith/commit/ad261009de88ad12f831173dd192557278b4a7a9))
* add endpoint to list (edge) identity overrides for a feature ([#3116](https://github.com/Flagsmith/flagsmith/issues/3116)) ([098ab94](https://github.com/Flagsmith/flagsmith/commit/098ab94b17b5e7787252ec557dd3727e5bdd4342))
* Add new url for role users ([#3120](https://github.com/Flagsmith/flagsmith/issues/3120)) ([0604ec1](https://github.com/Flagsmith/flagsmith/commit/0604ec1467295887f608af379f081e4bf7ce04fc))
* Add Payment component in the blocked page ([#3068](https://github.com/Flagsmith/flagsmith/issues/3068)) ([3f100d2](https://github.com/Flagsmith/flagsmith/commit/3f100d20bee2d35342c9f8bc4294d0f68b84b3c9))
* explicitly set audit log created date ([#3083](https://github.com/Flagsmith/flagsmith/issues/3083)) ([e470ddb](https://github.com/Flagsmith/flagsmith/commit/e470ddb2f2fb7f4bf0fe4fe2afbe4744afff5ee3))
* Flag group owners ([#3112](https://github.com/Flagsmith/flagsmith/issues/3112)) ([b0a00d0](https://github.com/Flagsmith/flagsmith/commit/b0a00d0175460828038cb68656ea70d2a5fb3f0e))
* Import / export of features across environments and orgs ([#3026](https://github.com/Flagsmith/flagsmith/issues/3026)) ([c4bdc0f](https://github.com/Flagsmith/flagsmith/commit/c4bdc0fee57d2bb833e3b0f46dfb4b33f2c4acf8))
* Migrate given project's (edge) identities to environments v2 ([#3138](https://github.com/Flagsmith/flagsmith/issues/3138)) ([574a08e](https://github.com/Flagsmith/flagsmith/commit/574a08e274b1ee8de56faa765b3bb9a4ec464473))
* Set feature export response on initial API request ([#3126](https://github.com/Flagsmith/flagsmith/issues/3126)) ([89b7c8c](https://github.com/Flagsmith/flagsmith/commit/89b7c8c152a0e60c0816b56edc9339de645175f3))
* **sse:** track usage  ([#3050](https://github.com/Flagsmith/flagsmith/issues/3050)) ([9502e55](https://github.com/Flagsmith/flagsmith/commit/9502e55ea9c9fc67bfb4255e8485bff1ac018d2a))


### Bug Fixes

* **api-deploy/action.yml:** Write the PGP key correctly  ([#3099](https://github.com/Flagsmith/flagsmith/issues/3099)) ([c1c45cb](https://github.com/Flagsmith/flagsmith/commit/c1c45cbe1a8acc6feaa5182cc0f908626e0e51e6))
* bump rbac to fix import issue ([#3128](https://github.com/Flagsmith/flagsmith/issues/3128)) ([ba33582](https://github.com/Flagsmith/flagsmith/commit/ba33582863fe4d2e7cbe320ff8bd92a68ae6e8e5))
* do not show identity overrides tab until release ([#3134](https://github.com/Flagsmith/flagsmith/issues/3134)) ([b1fb768](https://github.com/Flagsmith/flagsmith/commit/b1fb768b29b7b9e9ef8dffa12e1a29613b08fc5c))
* **Dockerfile:** Use correct secret ID for pgp_key ([#3141](https://github.com/Flagsmith/flagsmith/issues/3141)) ([44ee410](https://github.com/Flagsmith/flagsmith/commit/44ee410b56ee3250bee27878bf3b4e79a885569a))
* Environments metadata n+1 for project admin ([#3101](https://github.com/Flagsmith/flagsmith/issues/3101)) ([093fa3a](https://github.com/Flagsmith/flagsmith/commit/093fa3a42f0f2c0d8e00c8a7ac9e4ef306f93831))
* hide additional actions on identity overrides tab in Edge ([#3135](https://github.com/Flagsmith/flagsmith/issues/3135)) ([5e0093e](https://github.com/Flagsmith/flagsmith/commit/5e0093ebebc9b4e2e3521353508dbe109c5087ec))
* Husky install ([#3137](https://github.com/Flagsmith/flagsmith/issues/3137)) ([921b210](https://github.com/Flagsmith/flagsmith/commit/921b2100b92581bf98cb1a28757fdac34a1f537b))
* Manage members layout is broken ([#3058](https://github.com/Flagsmith/flagsmith/issues/3058)) ([d129397](https://github.com/Flagsmith/flagsmith/commit/d129397a8ff91bcde022c3516582318bd2be6b94))
* re-add identity overrides for core projects ([#3139](https://github.com/Flagsmith/flagsmith/issues/3139)) ([8a5c20f](https://github.com/Flagsmith/flagsmith/commit/8a5c20f71038614e16e6b2e29c08931d82bf4c92))
* show falsy values in identity overrides ([#3144](https://github.com/Flagsmith/flagsmith/issues/3144)) ([68cfd15](https://github.com/Flagsmith/flagsmith/commit/68cfd156211e30e82aa16fb31cfc9864510037b6))
* Show scheduled change request ([#3118](https://github.com/Flagsmith/flagsmith/issues/3118)) ([efddf13](https://github.com/Flagsmith/flagsmith/commit/efddf13b5ed66818979eea60d63c3bcba64f7f94))
* **sse_recurring_task:** reload sse/tasks ([#3108](https://github.com/Flagsmith/flagsmith/issues/3108)) ([4e8e321](https://github.com/Flagsmith/flagsmith/commit/4e8e32156f527af72f4a9f806ca3b72a994e9dbf))
* **tests/NoCredentialsError:** use aws_credentials fixture ([#3131](https://github.com/Flagsmith/flagsmith/issues/3131)) ([7883e28](https://github.com/Flagsmith/flagsmith/commit/7883e283d403f8a518ac592e60642322968cb251))
* Unable to delete multiple segment overrides at once ([#3100](https://github.com/Flagsmith/flagsmith/issues/3100)) ([9e6e0ca](https://github.com/Flagsmith/flagsmith/commit/9e6e0ca91f750350b3dda4c98ac644436de9c51a))

## [2.87.0](https://github.com/Flagsmith/flagsmith/compare/v2.86.0...v2.87.0) (2023-12-05)


### Features

* add new endpoint to list summary objects of permission groups ([#3064](https://github.com/Flagsmith/flagsmith/issues/3064)) ([2880ef5](https://github.com/Flagsmith/flagsmith/commit/2880ef55cdf7eadfc50ef71217f57d20d7e83fff))


### Bug Fixes

* Add group owners to missing endpoint ([#3080](https://github.com/Flagsmith/flagsmith/issues/3080)) ([8fe2ea7](https://github.com/Flagsmith/flagsmith/commit/8fe2ea7a1ca9c069a0608c91d73660920414af22))
* Move environments and features to test area ([#3081](https://github.com/Flagsmith/flagsmith/issues/3081)) ([05a3b37](https://github.com/Flagsmith/flagsmith/commit/05a3b37319cbad8ba0ccae38c76b9db4e503b966))
* **postgres/feature-analytics:** use feature filter ([#3091](https://github.com/Flagsmith/flagsmith/issues/3091)) ([c0fc231](https://github.com/Flagsmith/flagsmith/commit/c0fc231a2c4d2c1b41e07aebd5721bd8a477a691))
* Reading role permissions generates 500 error backend ([#3079](https://github.com/Flagsmith/flagsmith/issues/3079)) ([cee607a](https://github.com/Flagsmith/flagsmith/commit/cee607a7ef19c0d0eed91ecf01ee44476214f440))
* Refactor existing Chargebee webhooks for subscriptions ([#3047](https://github.com/Flagsmith/flagsmith/issues/3047)) ([c89c56a](https://github.com/Flagsmith/flagsmith/commit/c89c56aaa694976e80e7b47d90b28921b0fdfece))
* remove pagination from group summaries ([#3090](https://github.com/Flagsmith/flagsmith/issues/3090)) ([1065ad0](https://github.com/Flagsmith/flagsmith/commit/1065ad0258c36e76cca6a106d4888ffdc329d54e))
* resolve outstanding N+1 issues ([#3066](https://github.com/Flagsmith/flagsmith/issues/3066)) ([661c42f](https://github.com/Flagsmith/flagsmith/commit/661c42f52c2c525d57a2c52954440b5444fd7fbf))
* revert "fix: Reading role permissions generates 500 error backend" ([#3093](https://github.com/Flagsmith/flagsmith/issues/3093)) ([e57a01c](https://github.com/Flagsmith/flagsmith/commit/e57a01cf54ce07a18b757b4c5e9707c247c89639))

## [2.86.0](https://github.com/Flagsmith/flagsmith/compare/v2.85.0...v2.86.0) (2023-11-30)


### Features

* **auth:** integrate ldap ([#3031](https://github.com/Flagsmith/flagsmith/issues/3031)) ([65f78f7](https://github.com/Flagsmith/flagsmith/commit/65f78f79c78fb272de1052ff1a2e6c830af50318))


### Bug Fixes

* only run index queries for Postgres DBs ([#3055](https://github.com/Flagsmith/flagsmith/issues/3055)) ([7664ea2](https://github.com/Flagsmith/flagsmith/commit/7664ea2073fcaed35f13a7ce6f4234d7b52fef2a))

## [2.85.0](https://github.com/Flagsmith/flagsmith/compare/v2.84.2...v2.85.0) (2023-11-28)


### Features

* Rebuild chargebee caches ([#3028](https://github.com/Flagsmith/flagsmith/issues/3028)) ([aed15c3](https://github.com/Flagsmith/flagsmith/commit/aed15c351d19813667de04245e9cb41560c15651))


### Bug Fixes

* Move projects and integrations to tests ([#3044](https://github.com/Flagsmith/flagsmith/issues/3044)) ([0dc4e14](https://github.com/Flagsmith/flagsmith/commit/0dc4e14aa10fa4f0401c2cac200e91a390700e28))
* Rely on Flagsmith Engine for segment evaluation, avoid N+1 queries ([#3038](https://github.com/Flagsmith/flagsmith/issues/3038)) ([616c6be](https://github.com/Flagsmith/flagsmith/commit/616c6be03a0b8c9dd742415c2fd2cde8cd08c95d))
* Safely parse announcement Flag ([#3052](https://github.com/Flagsmith/flagsmith/issues/3052)) ([6994f6b](https://github.com/Flagsmith/flagsmith/commit/6994f6bfb08eed104133fc13967ef68cac19b58b))

## [2.84.2](https://github.com/Flagsmith/flagsmith/compare/v2.84.1...v2.84.2) (2023-11-27)


### Bug Fixes

* Move organisation tests to proper location ([#3041](https://github.com/Flagsmith/flagsmith/issues/3041)) ([34c6d07](https://github.com/Flagsmith/flagsmith/commit/34c6d072adae2558c7fee4c58a61570a817fe23d))
* resolve environment N+1 caused by feature versioning v2 ([#3040](https://github.com/Flagsmith/flagsmith/issues/3040)) ([5392480](https://github.com/Flagsmith/flagsmith/commit/5392480c3e35fd689347a80714901d4f70116367))

## [2.84.1](https://github.com/Flagsmith/flagsmith/compare/v2.84.0...v2.84.1) (2023-11-27)


### Bug Fixes

* Revert to Core API segment evaluation ([#3036](https://github.com/Flagsmith/flagsmith/issues/3036)) ([e5058ae](https://github.com/Flagsmith/flagsmith/commit/e5058ae01cca1ceb783c38d2eb29c83f07a86a8c))

## [2.84.0](https://github.com/Flagsmith/flagsmith/compare/v2.83.0...v2.84.0) (2023-11-27)


### Features

* Feature Versioning V2 ([#2382](https://github.com/Flagsmith/flagsmith/issues/2382)) ([bcfb10e](https://github.com/Flagsmith/flagsmith/commit/bcfb10ece60d4c9ce751ceef8681a1d264d69291))
* Rely on Flagsmith Engine for segment evaluation ([#2865](https://github.com/Flagsmith/flagsmith/issues/2865)) ([322eb08](https://github.com/Flagsmith/flagsmith/commit/322eb08167a8cec4b052dabddd34b10e346dca9a))
* **ui:** hide API keys from integrations list ([#3019](https://github.com/Flagsmith/flagsmith/issues/3019)) ([b02a524](https://github.com/Flagsmith/flagsmith/commit/b02a524ad5932e1cb0ef447e3bb8aa754e966118))


### Bug Fixes

* WIP Move groups of tests to proper location ([#3027](https://github.com/Flagsmith/flagsmith/issues/3027)) ([1592919](https://github.com/Flagsmith/flagsmith/commit/159291919541b2c20e8302339b6a2e04722ce191))

## [2.83.0](https://github.com/Flagsmith/flagsmith/compare/v2.82.0...v2.83.0) (2023-11-21)


### Features

* introduce dunning billing status ([#2976](https://github.com/Flagsmith/flagsmith/issues/2976)) ([975c7b0](https://github.com/Flagsmith/flagsmith/commit/975c7b0d6438cd973ccd62b590436e4c2568b9d4))


### Bug Fixes

* **api:** validate before creating projects based on current subscription ([#2869](https://github.com/Flagsmith/flagsmith/issues/2869)) ([f32159e](https://github.com/Flagsmith/flagsmith/commit/f32159e3fd821c6dc7bfbd50a0c3d22374f1b558))
* **edge-identity-view:** reduce max page size to 100 ([#2937](https://github.com/Flagsmith/flagsmith/issues/2937)) ([6c4807f](https://github.com/Flagsmith/flagsmith/commit/6c4807f0b2dd2ee770d2d712b2955a9fd71c37a0))
* Move and merge features tests into proper location ([#3002](https://github.com/Flagsmith/flagsmith/issues/3002)) ([5f3482c](https://github.com/Flagsmith/flagsmith/commit/5f3482c8c376c6dd283ab4aff36dedb67825facc))

## [2.82.0](https://github.com/Flagsmith/flagsmith/compare/v2.81.1...v2.82.0) (2023-11-20)


### Features

* Add permission for manage segments overrides ([#2919](https://github.com/Flagsmith/flagsmith/issues/2919)) ([716f6a9](https://github.com/Flagsmith/flagsmith/commit/716f6a960a8843503e6af622eaea30a3924e9eb3))
* Add seats to next invoice ([#2977](https://github.com/Flagsmith/flagsmith/issues/2977)) ([e4325a8](https://github.com/Flagsmith/flagsmith/commit/e4325a872265d0c60415bac6545c8d040d31d00f))
* Remove all but first admin when subscription has reached cancellation date ([#2965](https://github.com/Flagsmith/flagsmith/issues/2965)) ([6976f81](https://github.com/Flagsmith/flagsmith/commit/6976f81c910d5d8de4f194fc27e799b72778b9f6))


### Bug Fixes

* add LDAP to installed apps ([#2993](https://github.com/Flagsmith/flagsmith/issues/2993)) ([9f9237e](https://github.com/Flagsmith/flagsmith/commit/9f9237ec8d9e017401316ded027989139e707bf2))
* ensure SimpleFeatureStateViewSet uses correct permissions for segment overrides ([#2990](https://github.com/Flagsmith/flagsmith/issues/2990)) ([00c6444](https://github.com/Flagsmith/flagsmith/commit/00c6444cc4abffb6bdd50e47f5f1e560667f8b85))
* Excessive 404s on subscription metadata ([#2985](https://github.com/Flagsmith/flagsmith/issues/2985)) ([627a6fa](https://github.com/Flagsmith/flagsmith/commit/627a6fa0b3d3609ac6e12aae7f9b71220f2567af))
* Failure to import LD project other than `default` ([#2979](https://github.com/Flagsmith/flagsmith/issues/2979)) ([e0d6e8a](https://github.com/Flagsmith/flagsmith/commit/e0d6e8acd9ef28d685fca724cef435bbefdbee3d))
* Logic in segment overrides readonly with the manage_segment_overrides permission ([#2973](https://github.com/Flagsmith/flagsmith/issues/2973)) ([37879b2](https://github.com/Flagsmith/flagsmith/commit/37879b2046cd7bcd1293ffa81c2bfcaff93798d3))
* Move tests to unit  ([#2987](https://github.com/Flagsmith/flagsmith/issues/2987)) ([43caad8](https://github.com/Flagsmith/flagsmith/commit/43caad803b4d04144099e9cdfb4554a1ef19cb14))
* opening the flag panel shifts the main table slightly ([#2994](https://github.com/Flagsmith/flagsmith/issues/2994)) ([85d980c](https://github.com/Flagsmith/flagsmith/commit/85d980c6cb817867848f4676744e4324df8f3f49))
* Pagination icons disappeared ([#2982](https://github.com/Flagsmith/flagsmith/issues/2982)) ([0d2b979](https://github.com/Flagsmith/flagsmith/commit/0d2b979354390e945bcd003e174c424ac7482f2e))
* Update docstring to not include change requests ([#2995](https://github.com/Flagsmith/flagsmith/issues/2995)) ([e3ac7ef](https://github.com/Flagsmith/flagsmith/commit/e3ac7ef063d81f4264b3a03552dd67925e31382b))
* Update endpoint getEnvironment RTK response ([#2968](https://github.com/Flagsmith/flagsmith/issues/2968)) ([3993823](https://github.com/Flagsmith/flagsmith/commit/39938239a6f58a0266c9a32f35ee6c5ae7c15c5c))

## [2.81.1](https://github.com/Flagsmith/flagsmith/compare/v2.81.0...v2.81.1) (2023-11-14)


### Bug Fixes

* try self-hosted runner for the private cloud image ([#2969](https://github.com/Flagsmith/flagsmith/issues/2969)) ([99180cd](https://github.com/Flagsmith/flagsmith/commit/99180cdbf3cc3362efbb80eb83d131d066ae0f5f))

## [2.81.0](https://github.com/Flagsmith/flagsmith/compare/v2.80.0...v2.81.0) (2023-11-14)


### Features

* add foundation for LDAP in core repository ([#2923](https://github.com/Flagsmith/flagsmith/issues/2923)) ([65351e2](https://github.com/Flagsmith/flagsmith/commit/65351e205e268e49b01567ab7ed06fbaa1107643))
* Add manage segment overrides permission in UI ([#2936](https://github.com/Flagsmith/flagsmith/issues/2936)) ([88c43cd](https://github.com/Flagsmith/flagsmith/commit/88c43cda72cb747735254de44ae0ed78bc954808))
* Allow organisation admins to mandate 2fa for their organisation ([#2877](https://github.com/Flagsmith/flagsmith/issues/2877)) ([1d006fb](https://github.com/Flagsmith/flagsmith/commit/1d006fbc1515e16582210554b562d4aec2b382d5))
* trial management in sales dashboard ([#2805](https://github.com/Flagsmith/flagsmith/issues/2805)) ([a056713](https://github.com/Flagsmith/flagsmith/commit/a056713c31b11302b9445a57929b6a4ee9e4d109))


### Bug Fixes

* Audit Log records don't get created with threaded task processing ([#2958](https://github.com/Flagsmith/flagsmith/issues/2958)) ([716b228](https://github.com/Flagsmith/flagsmith/commit/716b2281c1d15277cfd9f48843970fc3c785719d))
* Fix evironment metadata N+1 for environments list ([#2947](https://github.com/Flagsmith/flagsmith/issues/2947)) ([7e1c779](https://github.com/Flagsmith/flagsmith/commit/7e1c77911af7c9cdbbdb6f9b1dff6c7c95becc52))
* Handle payment errors during user flow ([#2951](https://github.com/Flagsmith/flagsmith/issues/2951)) ([b18e4a6](https://github.com/Flagsmith/flagsmith/commit/b18e4a6d6588e80be4575de1891d51f10040ebef))
* Move organisation tests ([#2964](https://github.com/Flagsmith/flagsmith/issues/2964)) ([01d14d2](https://github.com/Flagsmith/flagsmith/commit/01d14d2ce23c787bbcea417fefb97b85a56b6413))
* sales dashboard subscription metadata shows wrong data after starting trial ([#2962](https://github.com/Flagsmith/flagsmith/issues/2962)) ([9a49f7d](https://github.com/Flagsmith/flagsmith/commit/9a49f7dcac5c01741cc5625314215edb04f1a3ea))

## [2.80.0](https://github.com/Flagsmith/flagsmith/compare/v2.79.0...v2.80.0) (2023-11-13)


### Features

* add copy button to server keys ([#2943](https://github.com/Flagsmith/flagsmith/issues/2943)) ([b78842b](https://github.com/Flagsmith/flagsmith/commit/b78842b6041cff8edc8c8091f79b47953568a63d))
* Add or remove user and groups from roles ([#2791](https://github.com/Flagsmith/flagsmith/issues/2791)) ([c2d0c11](https://github.com/Flagsmith/flagsmith/commit/c2d0c1142f5beb18c90c14e35c3eb329aafc26b4))
* **boto3/dynamo:** use tcp_keepalive ([#2926](https://github.com/Flagsmith/flagsmith/issues/2926)) ([eee1c0a](https://github.com/Flagsmith/flagsmith/commit/eee1c0a647331dd49ebd81fbc9cc0e1b53ce6c72))


### Bug Fixes

* Check that feature owners are able to view the project of a feature ([#2931](https://github.com/Flagsmith/flagsmith/issues/2931)) ([a0eefdd](https://github.com/Flagsmith/flagsmith/commit/a0eefdd3223cb0e684eb4aed36f21b9ea4f9d370))
* Close icon missing in roles modal ([#2946](https://github.com/Flagsmith/flagsmith/issues/2946)) ([4960f7e](https://github.com/Flagsmith/flagsmith/commit/4960f7e51f63b6483a5751dc435a67e20bcb6499))
* creating change requests in private cloud UI ([#2953](https://github.com/Flagsmith/flagsmith/issues/2953)) ([8eedf55](https://github.com/Flagsmith/flagsmith/commit/8eedf55ab34a9eedeea9c11e1dd9ac7b8e0ffa61))
* **deps:** CVE dependency updates (PVE-2023-61661, PVE-2023-61657, PV… ([#2939](https://github.com/Flagsmith/flagsmith/issues/2939)) ([ac26fc9](https://github.com/Flagsmith/flagsmith/commit/ac26fc97fb9aa461357973a25ab52741ccbfc7d9))
* Infinite loop 404 after leaving the organisation ([#2957](https://github.com/Flagsmith/flagsmith/issues/2957)) ([7b7f986](https://github.com/Flagsmith/flagsmith/commit/7b7f9860e63806552353f092d3d61a9d23f8c0af))
* prevent sentry errors for on premise subscriptions ([#2948](https://github.com/Flagsmith/flagsmith/issues/2948)) ([6f830e2](https://github.com/Flagsmith/flagsmith/commit/6f830e2b2124dd50d2cd078e156d028c5b9f9ae9))
* Rebuild environments when stop serving flags changed ([#2944](https://github.com/Flagsmith/flagsmith/issues/2944)) ([7d16197](https://github.com/Flagsmith/flagsmith/commit/7d161972e9a9e7ffbffbff905ae0053d86bd35f9))

## [2.79.0](https://github.com/Flagsmith/flagsmith/compare/v2.78.0...v2.79.0) (2023-11-07)


### Features

* add group owners to features ([#2908](https://github.com/Flagsmith/flagsmith/issues/2908)) ([493f0e5](https://github.com/Flagsmith/flagsmith/commit/493f0e5a09bb92dab38e13419e7b5c320e9779dd))
* Create staff fixture ([#2928](https://github.com/Flagsmith/flagsmith/issues/2928)) ([a09436d](https://github.com/Flagsmith/flagsmith/commit/a09436ddde7fd7c68a8e75b1dd311d5ac804f397))


### Bug Fixes

* Tighten ACL for user routes ([#2929](https://github.com/Flagsmith/flagsmith/issues/2929)) ([3732e67](https://github.com/Flagsmith/flagsmith/commit/3732e67f2dc1c0010ad5d4796960af2ddedf90c9))

## [2.78.0](https://github.com/Flagsmith/flagsmith/compare/v2.77.0...v2.78.0) (2023-11-01)


### Features

* **task-processor:** Add priority support  ([#2847](https://github.com/Flagsmith/flagsmith/issues/2847)) ([6830ef6](https://github.com/Flagsmith/flagsmith/commit/6830ef666c7f9931a4d4edfeef9e58e7d2768dcc))


### Bug Fixes

* Revert "ci: Run only API tests affected by changes in PRs and Upgrade GHA runners" ([#2910](https://github.com/Flagsmith/flagsmith/issues/2910)) ([6a730c7](https://github.com/Flagsmith/flagsmith/commit/6a730c7ae87b06df13af82b4c51dd113343c6333))
* **task/priority:** change field to SmallIntegerField ([#2914](https://github.com/Flagsmith/flagsmith/issues/2914)) ([6e6a48b](https://github.com/Flagsmith/flagsmith/commit/6e6a48be303197ebc90d096b44c4b75d7a22c778))

## [2.77.0](https://github.com/Flagsmith/flagsmith/compare/v2.76.0...v2.77.0) (2023-10-30)


### Features

* Click Segment Overrides icon doesnt open the segment override tab ([#2887](https://github.com/Flagsmith/flagsmith/issues/2887)) ([96f3b22](https://github.com/Flagsmith/flagsmith/commit/96f3b22f3d21d81074643df90878dba2ace51580))
* **permissions/tags:** Add tags support  ([#2685](https://github.com/Flagsmith/flagsmith/issues/2685)) ([78e559c](https://github.com/Flagsmith/flagsmith/commit/78e559c320011bcc6ec9339cb2614a9751244156))


### Bug Fixes

* Handle null tooltip data ([#2892](https://github.com/Flagsmith/flagsmith/issues/2892)) ([a1190ae](https://github.com/Flagsmith/flagsmith/commit/a1190ae90a31496e9e368a1dbdc232a1dd4daf1a))

## [2.76.0](https://github.com/Flagsmith/flagsmith/compare/v2.75.0...v2.76.0) (2023-10-24)


### Features

* **rate-limit:** allow user to pass default throttle classes ([#2878](https://github.com/Flagsmith/flagsmith/issues/2878)) ([dc4b02c](https://github.com/Flagsmith/flagsmith/commit/dc4b02c7c3a67c34f16146c686786ffb09367ecf))

## [2.75.0](https://github.com/Flagsmith/flagsmith/compare/v2.74.0...v2.75.0) (2023-10-23)


### Features

* partial imports, off values as control value ([#2864](https://github.com/Flagsmith/flagsmith/issues/2864)) ([93df958](https://github.com/Flagsmith/flagsmith/commit/93df958b8fc67d17c6cfc298184bfef0f83847b4))
* update change request layout ([#2848](https://github.com/Flagsmith/flagsmith/issues/2848)) ([eaffffe](https://github.com/Flagsmith/flagsmith/commit/eaffffe0d0313eaadbf25980ea42afeb1e753ffd))


### Bug Fixes

* Cannot see the assigned users in the changes request section ([#2868](https://github.com/Flagsmith/flagsmith/issues/2868)) ([59abf20](https://github.com/Flagsmith/flagsmith/commit/59abf20f59b92c5f47d7ddfc698c81eb695e3bb4))
* rate limit admin endpoints ([#2703](https://github.com/Flagsmith/flagsmith/issues/2703)) ([b0ef013](https://github.com/Flagsmith/flagsmith/commit/b0ef0134cf40703de225ffa3ad4363fee4f8f997))

## [2.74.0](https://github.com/Flagsmith/flagsmith/compare/v2.73.1...v2.74.0) (2023-10-18)


### Features

* Launchdarkly importer ([#2530](https://github.com/Flagsmith/flagsmith/issues/2530)) ([4f7464b](https://github.com/Flagsmith/flagsmith/commit/4f7464b24aba4f0cf0fb79379dbde1275f50f71a))
* LaunchDarkly importer UI ([#2837](https://github.com/Flagsmith/flagsmith/issues/2837)) ([a78eeaf](https://github.com/Flagsmith/flagsmith/commit/a78eeaf4cae8b84ef3b45f5edd761dc46da966ba))


### Bug Fixes

* enable audit for import events ([#2849](https://github.com/Flagsmith/flagsmith/issues/2849)) ([7964e49](https://github.com/Flagsmith/flagsmith/commit/7964e4999cbea031422aa610282cbacc303d8177))
* incorrect default_percentage_allocation on import, binary flags imported as multivariate ([#2841](https://github.com/Flagsmith/flagsmith/issues/2841)) ([619c3f5](https://github.com/Flagsmith/flagsmith/commit/619c3f52a821d8eaace2035c5e34b51b16040deb))
* Logged out of Flagsmith when testing Webhook ([#2842](https://github.com/Flagsmith/flagsmith/issues/2842)) ([cfbf7f1](https://github.com/Flagsmith/flagsmith/commit/cfbf7f192e699c9318c97a05266e31ff7d680e3d))

## [2.73.1](https://github.com/Flagsmith/flagsmith/compare/v2.73.0...v2.73.1) (2023-10-05)


### Bug Fixes

* **tasks:** Create a different task to update environment document  ([#2807](https://github.com/Flagsmith/flagsmith/issues/2807)) ([ab21983](https://github.com/Flagsmith/flagsmith/commit/ab21983e8736d4244df2cd37c235d8ce4795e948))

## [2.73.0](https://github.com/Flagsmith/flagsmith/compare/v2.72.1...v2.73.0) (2023-10-05)


### Features

* **tasks/queue-size:** Implement queue_size ([#2826](https://github.com/Flagsmith/flagsmith/issues/2826)) ([94fff2c](https://github.com/Flagsmith/flagsmith/commit/94fff2c53bc80ada60c18bf5bfd91c700d363d61))


### Bug Fixes

* Project Dropdown selector is not sorted alphabetically ([#2812](https://github.com/Flagsmith/flagsmith/issues/2812)) ([7123cf6](https://github.com/Flagsmith/flagsmith/commit/7123cf67df7169576eaeb609f1d67b48097310bf))
* Shows "Identities" nav element as disabled for users without relevant permission ([#2813](https://github.com/Flagsmith/flagsmith/issues/2813)) ([3ec2f6b](https://github.com/Flagsmith/flagsmith/commit/3ec2f6b4d10019c757f336f23048342aab835d13))

## [2.72.1](https://github.com/Flagsmith/flagsmith/compare/v2.72.0...v2.72.1) (2023-09-28)


### Bug Fixes

* Last Influx data updated at never updates ([#2802](https://github.com/Flagsmith/flagsmith/issues/2802)) ([929afeb](https://github.com/Flagsmith/flagsmith/commit/929afeb49466bf0be893a2f5033c0fff8a6f8a1a))
* Payment modal ([#2792](https://github.com/Flagsmith/flagsmith/issues/2792)) ([c231749](https://github.com/Flagsmith/flagsmith/commit/c231749272d52d7b1a987aa2fdd82855e05f6d07))
* Price is missing in dark mode ([#2799](https://github.com/Flagsmith/flagsmith/issues/2799)) ([31c9884](https://github.com/Flagsmith/flagsmith/commit/31c9884b9cd3a518b14cf8b796c934c4303738a9))
* **seat-upgrades:** Allow auto seat upgrades for new scaleup plan ([#2809](https://github.com/Flagsmith/flagsmith/issues/2809)) ([1cada3c](https://github.com/Flagsmith/flagsmith/commit/1cada3ced81e9b9b4a4257a49ec0a9da9e305f1c))
* Toast messages look wrong ([#2800](https://github.com/Flagsmith/flagsmith/issues/2800)) ([f003732](https://github.com/Flagsmith/flagsmith/commit/f003732d89d4e2ad01a222083dcd68760faa6950))

## [2.72.0](https://github.com/Flagsmith/flagsmith/compare/v2.71.0...v2.72.0) (2023-09-19)


### Features

* Add a pill for server side only flags ([#2780](https://github.com/Flagsmith/flagsmith/issues/2780)) ([2b70c68](https://github.com/Flagsmith/flagsmith/commit/2b70c68d548a1f9a5ae30372506e503611d7c707))
* display warning and prevent creation on limit ([#2526](https://github.com/Flagsmith/flagsmith/issues/2526)) ([000be2b](https://github.com/Flagsmith/flagsmith/commit/000be2b0c071d6ef839da5d0febcc85b58e47ab7))
* Realtime updates, defaultFlags, cacheControl and timeout config for Android ([#2757](https://github.com/Flagsmith/flagsmith/issues/2757)) ([54de331](https://github.com/Flagsmith/flagsmith/commit/54de331af199a898e7850eeac30aeb9ac41a4d58))


### Bug Fixes

* Environment webhook update button not working ([#2788](https://github.com/Flagsmith/flagsmith/issues/2788)) ([5f92a00](https://github.com/Flagsmith/flagsmith/commit/5f92a0067034ae1ee95d3b3bb8c360eddd8996bb))
* Feature id in mv-option request is undefined ([#2751](https://github.com/Flagsmith/flagsmith/issues/2751)) ([3c3b1d7](https://github.com/Flagsmith/flagsmith/commit/3c3b1d7af2e4b62f75979b8c8c2ea931f8736cbd))
* fix segments display crashing ([#2770](https://github.com/Flagsmith/flagsmith/issues/2770)) ([#2789](https://github.com/Flagsmith/flagsmith/issues/2789)) ([bb080d2](https://github.com/Flagsmith/flagsmith/commit/bb080d2e11ecb6197406b483c58e694f66c95194))
* Send JSON response instead of plain text ([#2739](https://github.com/Flagsmith/flagsmith/issues/2739)) ([cad0cbf](https://github.com/Flagsmith/flagsmith/commit/cad0cbfb08fd34c2732ff5fefc2f5a5752cb60cf))

## [2.71.0](https://github.com/Flagsmith/flagsmith/compare/v2.70.2...v2.71.0) (2023-09-11)


### Features

* Add feature description like the old UI ([#2733](https://github.com/Flagsmith/flagsmith/issues/2733)) ([33e7c17](https://github.com/Flagsmith/flagsmith/commit/33e7c17b3f7b1cb7964c2f00ae8001faf251945e))
* **task-processor:** validate arguments passed to task processor functions ([#2747](https://github.com/Flagsmith/flagsmith/issues/2747)) ([d947474](https://github.com/Flagsmith/flagsmith/commit/d947474696a3a213ff196ffc5ac3bf802dbd8062))


### Bug Fixes

* allow registration via invite link if ALLOW_REGISTRATION_WITHOUT_INVITE is False ([#2731](https://github.com/Flagsmith/flagsmith/issues/2731)) ([73705d5](https://github.com/Flagsmith/flagsmith/commit/73705d57068ef63eb5c36b104dc25b68fa14dcfd))
* Deleting a project causes multiple UI issues ([#2749](https://github.com/Flagsmith/flagsmith/issues/2749)) ([8cd144b](https://github.com/Flagsmith/flagsmith/commit/8cd144b66069fbc0bdc934d67d44f9d4fd5d6d16))
* **featurestate-permissions:** Add misc extra checks ([#2712](https://github.com/Flagsmith/flagsmith/issues/2712)) ([ecb7fd2](https://github.com/Flagsmith/flagsmith/commit/ecb7fd2c0e352058609b07ac049d90ca9d2a36e5))
* UI issue when there were more than 100 features ([#2711](https://github.com/Flagsmith/flagsmith/issues/2711)) ([c1a62ce](https://github.com/Flagsmith/flagsmith/commit/c1a62ce47c57a30bdeeee2adb023e36bbf9ff579))
* update ecs staging docker ([#2759](https://github.com/Flagsmith/flagsmith/issues/2759)) ([34f9a5b](https://github.com/Flagsmith/flagsmith/commit/34f9a5b8b0b02dce76cf7d7488e76e2ce78ed279))
* Update Webhook button not working ([#2753](https://github.com/Flagsmith/flagsmith/issues/2753)) ([8566fe0](https://github.com/Flagsmith/flagsmith/commit/8566fe02c39a7ddd958f42ffcb59320948b72e38))
* Webhook doesnt show the environment selected ([#2748](https://github.com/Flagsmith/flagsmith/issues/2748)) ([79b6030](https://github.com/Flagsmith/flagsmith/commit/79b60307ea279a6a6ddc0324b9cf436e5a62ae23))

## [2.70.2](https://github.com/Flagsmith/flagsmith/compare/v2.70.1...v2.70.2) (2023-09-05)


### Bug Fixes

* **chargebee:** ensure multiple addons are counted to subscription limits ([#2741](https://github.com/Flagsmith/flagsmith/issues/2741)) ([2ac23a8](https://github.com/Flagsmith/flagsmith/commit/2ac23a8d4cc966dc66ab8d31da7c536aec355bd1))
* **migrations:** remove features/0060 set environment not null ([#2738](https://github.com/Flagsmith/flagsmith/issues/2738)) ([3aed121](https://github.com/Flagsmith/flagsmith/commit/3aed12170ce72bfd8ebca5a74153ca0b7dcec40c))

## [2.70.1](https://github.com/Flagsmith/flagsmith/compare/v2.70.0...v2.70.1) (2023-09-05)


### Bug Fixes

* remove migration health check ([#2736](https://github.com/Flagsmith/flagsmith/issues/2736)) ([e5483cb](https://github.com/Flagsmith/flagsmith/commit/e5483cbdcd6a79b278d41775e18a2722bd177a9d))

## [2.70.0](https://github.com/Flagsmith/flagsmith/compare/v2.69.1...v2.70.0) (2023-09-05)


### Features

* integrate flagsmith client into API layer ([#2447](https://github.com/Flagsmith/flagsmith/issues/2447)) ([e71efbb](https://github.com/Flagsmith/flagsmith/commit/e71efbb19d7e81b4601f5e50968a1ea362b6e32d))


### Bug Fixes

* **model/featurestate:** make environment not null ([#2708](https://github.com/Flagsmith/flagsmith/issues/2708)) ([55a9ef7](https://github.com/Flagsmith/flagsmith/commit/55a9ef7bcfc62b9752a7407fbfe545b2df6bb72c))

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
