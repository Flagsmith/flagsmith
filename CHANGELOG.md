# Changelog

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
