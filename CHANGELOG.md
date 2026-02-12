# CHANGELOG

<!-- version list -->

## v1.6.1 (2026-02-12)

### Bug Fixes

- Update platzky dependency ([#333](https://github.com/Problematy/goodmap/pull/333),
  [`1714928`](https://github.com/Problematy/goodmap/commit/17149289e77c276db76eee5d1bf208f1e3a064bc))

### Chores

- More docs introduced ([#332](https://github.com/Problematy/goodmap/pull/332),
  [`6696298`](https://github.com/Problematy/goodmap/commit/6696298c0f705bebc78fe2ac8daaa1da6a3c2ee0))


## v1.6.0 (2026-02-04)

### Features

- Add configurable reported issue types ([#331](https://github.com/Problematy/goodmap/pull/331),
  [`28e1f85`](https://github.com/Problematy/goodmap/commit/28e1f85e964af4e00251f21106d0438266b64502))


## v1.5.0 (2026-02-03)

### Chores

- **ci**: Bump actions/download-artifact from 4 to 7
  ([#329](https://github.com/Problematy/goodmap/pull/329),
  [`44652a6`](https://github.com/Problematy/goodmap/commit/44652a6a3a315554f3f3e4bd3b42c3ad6af1b677))

- **ci**: Bump actions/upload-artifact from 4 to 6
  ([#328](https://github.com/Problematy/goodmap/pull/328),
  [`cdf0b96`](https://github.com/Problematy/goodmap/commit/cdf0b9685604566a70809792e95a1e85c4b73d03))

- **deps)(deps**: Bump gunicorn from 23.0.0 to 24.1.1
  ([#326](https://github.com/Problematy/goodmap/pull/326),
  [`3834b67`](https://github.com/Problematy/goodmap/commit/3834b67dd07aa488b8d8fc418788061b467b7832))

- **deps)(deps**: Bump the minor-and-patch group with 7 updates
  ([#325](https://github.com/Problematy/goodmap/pull/325),
  [`630e567`](https://github.com/Problematy/goodmap/commit/630e5673b28c26dfc975c8defc6c70653c4b6a7a))

- **deps)(deps-dev**: Bump black from 24.10.0 to 26.1.0
  ([#327](https://github.com/Problematy/goodmap/pull/327),
  [`553dfa7`](https://github.com/Problematy/goodmap/commit/553dfa7d0f45f42925f8cbe713b98577fb0e3338))

### Features

- Refactor feature flags from dict-based ([#330](https://github.com/Problematy/goodmap/pull/330),
  [`5deb7ef`](https://github.com/Problematy/goodmap/commit/5deb7efa6c87103fe748cee3c0ddec59f8a8e98c))


## v1.4.0 (2026-01-24)

### Features

- Implement photo uploads with file validation
  ([#324](https://github.com/Problematy/goodmap/pull/324),
  [`63c8fe7`](https://github.com/Problematy/goodmap/commit/63c8fe751768c610a36a131890d646df6d904cca))


## v1.3.1 (2026-01-20)

### Bug Fixes

- Categories-full endpoint now provides helpers
  ([`0b548fc`](https://github.com/Problematy/goodmap/commit/0b548fcb3b9fbcb8a9283188f5d5288b76b96925))


## v1.3.0 (2026-01-20)

### Chores

- Removed submodules from checkout (#123) ([#321](https://github.com/Problematy/goodmap/pull/321),
  [`2e77b1d`](https://github.com/Problematy/goodmap/commit/2e77b1d19b20512cd4865df8d2d63b23efeccacc))

### Features

- Add /categories-full endpoint for combined category data
  ([`564b97a`](https://github.com/Problematy/goodmap/commit/564b97ad95495a6bd46b9b4354a722ce9562632f))

### Refactoring

- Admin api extraction ([#317](https://github.com/Problematy/goodmap/pull/317),
  [`2098e09`](https://github.com/Problematy/goodmap/commit/2098e09253c4073720f318ada14d6b2efdbce56d))


## v1.2.0 (2026-01-14)

### Chores

- Add docstrings to core data processing and validation functions
  ([#306](https://github.com/Problematy/goodmap/pull/306),
  [`27968e7`](https://github.com/Problematy/goodmap/commit/27968e7d8dc1643b8a5c3da151e364a7033ddca1))

- Added more docs ([#301](https://github.com/Problematy/goodmap/pull/301),
  [`21409d2`](https://github.com/Problematy/goodmap/commit/21409d2efceda1dbb0810169f4df2cfbcde038b9))

- Removed extra permissions ([#307](https://github.com/Problematy/goodmap/pull/307),
  [`0c8af05`](https://github.com/Problematy/goodmap/commit/0c8af05b062c2ca5ed70d25d08910d82cae0781f))

- **ci**: Bump actions/cache from 4 to 5 ([#305](https://github.com/Problematy/goodmap/pull/305),
  [`f42cc11`](https://github.com/Problematy/goodmap/commit/f42cc113cf2f76529f4b6e3b09886fe07b432a2f))

- **ci**: Bump actions/checkout from 4 to 6 ([#304](https://github.com/Problematy/goodmap/pull/304),
  [`3a274c6`](https://github.com/Problematy/goodmap/commit/3a274c6b82cc2183feaedbd544a255c3235da7bf))

- **ci**: Bump actions/setup-python from 5 to 6
  ([#303](https://github.com/Problematy/goodmap/pull/303),
  [`a1cffa1`](https://github.com/Problematy/goodmap/commit/a1cffa12cb2070bc5e8e7696328458b3640ba5e6))

- **deps)(deps-dev**: Bump coverage from 6.5.0 to 7.13.1
  ([#302](https://github.com/Problematy/goodmap/pull/302),
  [`d07c981`](https://github.com/Problematy/goodmap/commit/d07c981ac2cd05a9912a45f2b3c664e27499986c))

### Features

- Better model handling when suggesting new point and migrate API from RESTX to Spectree
  ([#309](https://github.com/Problematy/goodmap/pull/309),
  [`612054c`](https://github.com/Problematy/goodmap/commit/612054c24a52b97d498f31e9f40b0f1a0229041a))


## v1.1.14 (2025-12-31)

### Bug Fixes

- **ci**: Move changelog_file to default_templates per deprecation warning
  ([`b948817`](https://github.com/problematy/goodmap/commit/b948817b5aa2f57002c877e4193e6e8ac539f02c))


## v1.1.13 (2025-12-31)

### Bug Fixes

- **ci**: Explicitly enable CHANGELOG.md generation in semantic-release config"
  ([#298](https://github.com/problematy/goodmap/pull/298),
  [`5d6449c`](https://github.com/problematy/goodmap/commit/5d6449c1ce777d6e2041007e667bbaf3325711f9))


## v1.1.12 (2025-12-31)

### Bug Fixes

- Debug added ([#297](https://github.com/problematy/goodmap/pull/297),
  [`4ac8756`](https://github.com/problematy/goodmap/commit/4ac8756836c75cd56da87ea5f083a6334fe8d8d5))


## v1.1.11 (2025-12-31)

### Bug Fixes

- Semantic release fix ([#296](https://github.com/problematy/goodmap/pull/296),
  [`761cb8f`](https://github.com/problematy/goodmap/commit/761cb8f4e381392821ae37a73c877e212062cf91))


## v1.1.10 (2025-12-31)

### Bug Fixes

- Remove tests job from release workflow and update tests workflow trigger
  ([#295](https://github.com/problematy/goodmap/pull/295),
  [`f9a2939`](https://github.com/problematy/goodmap/commit/f9a29390568cce60969065c8b91e2b492388be62))

### Chores

- **ci**: Bump python-semantic-release/publish-action from 10.4.1 to 10.5.3
  ([#287](https://github.com/problematy/goodmap/pull/287),
  [`c5e1a8c`](https://github.com/problematy/goodmap/commit/c5e1a8cfda1eb46ad1fcade820e0664b56501354))

- **deps)(deps-dev**: Bump coveralls from 3.3.1 to 4.0.2
  ([#291](https://github.com/problematy/goodmap/pull/291),
  [`4658654`](https://github.com/problematy/goodmap/commit/46586544c37e53d33ab54ee81d9a53571706704f))


## v1.1.9 (2025-12-31)

### Bug Fixes

- Changelog in release fixed ([#294](https://github.com/problematy/goodmap/pull/294),
  [`24b3e21`](https://github.com/problematy/goodmap/commit/24b3e2147376869dc301eca3bfd037946bf7c3f6))

- Fix csrf protection usage ([#283](https://github.com/problematy/goodmap/pull/283),
  [`5ebc9e6`](https://github.com/problematy/goodmap/commit/5ebc9e65723bfbc2d4c23108a9f7a88eb1d9664e))

- Write permission for pull-request added ([#289](https://github.com/problematy/goodmap/pull/289),
  [`4da664d`](https://github.com/problematy/goodmap/commit/4da664db56cb39da5a1c002b5cb7f7ee2478246a))

### Chores

- **ci**: Bump alstr/todo-to-issue-action from 4 to 5
  ([#288](https://github.com/problematy/goodmap/pull/288),
  [`dc85d7e`](https://github.com/problematy/goodmap/commit/dc85d7edfe10b4c574d898eba37c76a6810a2609))

- **ci**: Bump python-semantic-release/python-semantic-release from 10.4.1 to 10.5.3
  ([#286](https://github.com/problematy/goodmap/pull/286),
  [`6b55e4c`](https://github.com/problematy/goodmap/commit/6b55e4c49b5b7f855ed1e49a6b6361b73ae4e717))


## v1.1.8 (2025-12-30)

### Bug Fixes

- Fixed version of create-github-app-token ([#284](https://github.com/problematy/goodmap/pull/284),
  [`1976990`](https://github.com/problematy/goodmap/commit/1976990461bb14192cbab458a83d7a86e50944e6))

### Chores

- **release**: 1.1.8
  ([`13eb5ec`](https://github.com/problematy/goodmap/commit/13eb5ec1b9c2386acebe0e7ae0d3d96077e6ea11))


## v1.1.7 (2025-12-30)

### Bug Fixes

- Uuid sanitization and better errors handling
  ([#278](https://github.com/problematy/goodmap/pull/278),
  [`2340894`](https://github.com/problematy/goodmap/commit/23408946b4d763fa9b529f6f1fbc87a7898f6188))

### Chores

- **release**: 1.1.7
  ([`07e7bcc`](https://github.com/problematy/goodmap/commit/07e7bccac263683417a33c120c68654af44c52c3))


## v1.1.6 (2025-11-15)

### Bug Fixes

- Changed dependency to custom pysupercluster-problematy version
  ([#276](https://github.com/problematy/goodmap/pull/276),
  [`cbb72bc`](https://github.com/problematy/goodmap/commit/cbb72bca9e619b8dec55935696c8c8465ef1fb56))

### Chores

- **release**: 1.1.6
  ([`783f855`](https://github.com/problematy/goodmap/commit/783f855e7f01edef6fa57dc552ecb1bd586536bf))


## v1.1.5 (2025-11-15)

### Bug Fixes

- Fix problem with permissions ([#273](https://github.com/problematy/goodmap/pull/273),
  [`233c2ab`](https://github.com/problematy/goodmap/commit/233c2ab92de3bd818e163f992ee4095d6aa5fea9))

- Updated e2e dependency ([#274](https://github.com/problematy/goodmap/pull/274),
  [`fcd69fd`](https://github.com/problematy/goodmap/commit/fcd69fdd25dd6778ede16f2a772378ea8a900aee))

- Updated pipeline to fix semantic release ([#272](https://github.com/problematy/goodmap/pull/272),
  [`b390204`](https://github.com/problematy/goodmap/commit/b390204d0c32971b613721c6853f50e702fca88d))

### Chores

- New way of running e2e tests ([#271](https://github.com/problematy/goodmap/pull/271),
  [`3489e07`](https://github.com/problematy/goodmap/commit/3489e07f78a0181d46308e84a88131059d54f59f))

- **release**: 1.1.5
  ([`f5355b0`](https://github.com/problematy/goodmap/commit/f5355b02e5e34ee104734c464b746ed8b2fce040))


## v1.1.4 (2025-10-16)

### Bug Fixes

- Remark is no longer shown where it should not be shown
  ([`b980159`](https://github.com/problematy/goodmap/commit/b9801597d2f918d8bab1c44c8c55d3ba8422daca))

### Chores

- **release**: 1.1.4
  ([`8b2a882`](https://github.com/problematy/goodmap/commit/8b2a882f1abb305c315deaa6244f31d603397c0a))


## v1.1.3 (2025-10-15)

### Bug Fixes

- Faster google_jsond_db ([#265](https://github.com/problematy/goodmap/pull/265),
  [`7216d55`](https://github.com/problematy/goodmap/commit/7216d55836be6d018f58769c2925ca9a3acc3787))

### Chores

- **release**: 1.1.3
  ([`0702b37`](https://github.com/problematy/goodmap/commit/0702b37edaedb408f539baa261540a3902235d40))


## v1.1.2 (2025-10-15)

### Bug Fixes

- Add get_visible_data and get_meta_data methods to resolve #177
  ([#264](https://github.com/problematy/goodmap/pull/264),
  [`4788517`](https://github.com/problematy/goodmap/commit/4788517ec67a633bfd0ea8bda4e9052bd4c2fc74))

### Chores

- Added docs ([#263](https://github.com/problematy/goodmap/pull/263),
  [`bdd9d4b`](https://github.com/problematy/goodmap/commit/bdd9d4b4d9d3ca6b87b564fbd0c7b09a988d0f05))

- **release**: 1.1.2
  ([`db1e946`](https://github.com/problematy/goodmap/commit/db1e94604ae50cf01ac96d3c03de0d5f716aa58d))


## v1.1.1 (2025-10-13)

### Bug Fixes

- Fix locations reports on google_json db ([#262](https://github.com/problematy/goodmap/pull/262),
  [`cb2b23f`](https://github.com/problematy/goodmap/commit/cb2b23f3334326e01cd5675ce6217ebb2f49a04d))

### Chores

- **release**: 1.1.1
  ([`e71f357`](https://github.com/problematy/goodmap/commit/e71f357a088e5c7cc6a3ec87360d655d4c0885ca))


## v1.1.0 (2025-10-13)

### Chores

- **release**: 1.1.0
  ([`743d2bd`](https://github.com/problematy/goodmap/commit/743d2bd1270ce0db6c0c8282701beb076b65dd03))

### Features

- New way of setting up frontend version ([#261](https://github.com/problematy/goodmap/pull/261),
  [`e4a32e4`](https://github.com/problematy/goodmap/commit/e4a32e4f81bdfb89b4870fdaa8128a92e8d0a0ff))


## v1.0.4 (2025-10-03)

### Bug Fixes

- Updated dependencies (/health/readines|liveness checks added
  ([#260](https://github.com/problematy/goodmap/pull/260),
  [`3b1b49a`](https://github.com/problematy/goodmap/commit/3b1b49a3d686fa3aba802247968d7e0e75326b14))

### Chores

- **release**: 1.0.4
  ([`b08abd8`](https://github.com/problematy/goodmap/commit/b08abd867cb660170ec939a6ba12e30d304fc4f0))


## v1.0.3 (2025-10-01)

### Bug Fixes

- Sonarqube error removed ([#259](https://github.com/problematy/goodmap/pull/259),
  [`a8c09e3`](https://github.com/problematy/goodmap/commit/a8c09e3f9eeb7e3bc00092996a62292a731d4af4))

### Chores

- **release**: 1.0.3
  ([`8032e2e`](https://github.com/problematy/goodmap/commit/8032e2e62aca866a68a36502594ef5acddb6352f))


## v1.0.2 (2025-10-01)

### Bug Fixes

- Pipeline fix now ([#254](https://github.com/problematy/goodmap/pull/254),
  [`209e1d5`](https://github.com/problematy/goodmap/commit/209e1d5c508b3fbd22419ace719a18bcdb576da5))

### Chores

- Changed release command to build
  ([`bd257e4`](https://github.com/problematy/goodmap/commit/bd257e4bc0b79ff0e6acc1160f0fd5b6b079280d))

- Fix building on release ([#258](https://github.com/problematy/goodmap/pull/258),
  [`fb41de5`](https://github.com/problematy/goodmap/commit/fb41de56e32f0006c56f71256c158bd63970941d))

- Fix pipeline ([#257](https://github.com/problematy/goodmap/pull/257),
  [`ed82807`](https://github.com/problematy/goodmap/commit/ed828074007ce6362ebc5b206c9248bf46aa03cf))

- Fixed badge in readme.md ([#251](https://github.com/problematy/goodmap/pull/251),
  [`f24d3f5`](https://github.com/problematy/goodmap/commit/f24d3f575a0af67c0bc8d8c9a362036d066102c6))

- Fixed sha ([#255](https://github.com/problematy/goodmap/pull/255),
  [`9df94f8`](https://github.com/problematy/goodmap/commit/9df94f8b2e22fc24e04c06021b0c3a704ccce7dc))

- Install dependencies in release ([#256](https://github.com/problematy/goodmap/pull/256),
  [`273f1ce`](https://github.com/problematy/goodmap/commit/273f1ce33e368dce1855f1d5252cbe6799833cfa))

- Pipeline fix ([#252](https://github.com/problematy/goodmap/pull/252),
  [`183d051`](https://github.com/problematy/goodmap/commit/183d051749a83e32408658918dc3d18e8eb11022))

- **release**: 1.0.2
  ([`1512017`](https://github.com/problematy/goodmap/commit/15120172102d3d25b2fe5586c8b2f3167188297c))


## v1.0.1 (2025-10-01)

### Bug Fixes

- Added missing permision ([#250](https://github.com/problematy/goodmap/pull/250),
  [`05fccf5`](https://github.com/problematy/goodmap/commit/05fccf5601c1dc58de41e3763283e19456d29501))

### Chores

- **release**: 1.0.1
  ([`b303df1`](https://github.com/problematy/goodmap/commit/b303df181bf79be573e87ec0d8f3b61fbb4d78fb))


## v1.0.0 (2025-10-01)

### Bug Fixes

- Fix pipeline ([#249](https://github.com/problematy/goodmap/pull/249),
  [`9f45fc7`](https://github.com/problematy/goodmap/commit/9f45fc7fc2f155014ab321f811cebb27277af8ec))

- Fix pipeline ([#243](https://github.com/problematy/goodmap/pull/243),
  [`2519cf2`](https://github.com/problematy/goodmap/commit/2519cf2bbb1166ef24b8eb65da7efe02c0a5941f))

- Pipeline fix ([#246](https://github.com/problematy/goodmap/pull/246),
  [`d2f5408`](https://github.com/problematy/goodmap/commit/d2f540851823e95ddb3b88217b6dc249754c6743))

- Submodule is cloned now ([#247](https://github.com/problematy/goodmap/pull/247),
  [`b083139`](https://github.com/problematy/goodmap/commit/b083139c758f32d818f1f8c8af94c55c279448e3))

- Updated version of platzky ([#248](https://github.com/problematy/goodmap/pull/248),
  [`18b77a7`](https://github.com/problematy/goodmap/commit/18b77a7169c4ac9d6c524c83e1f6df2d1bf28e4e))

### Chores

- **release**: 1.0.0
  ([`91aa712`](https://github.com/problematy/goodmap/commit/91aa71292174498a89bdbbb153db6618938a54d0))

### Features

- Introduced mongodb backend ([#240](https://github.com/problematy/goodmap/pull/240),
  [`5d95515`](https://github.com/problematy/goodmap/commit/5d95515be5c6c196176135a954863560a0cc0616))


## v0.5.3 (2025-08-19)


## v0.5.2 (2025-07-07)


## v0.5.1 (2025-07-07)

### Build System

- Add github logs for stress test ([#236](https://github.com/problematy/goodmap/pull/236),
  [`a9dd425`](https://github.com/problematy/goodmap/commit/a9dd4258aad44b35c848864537212b38fae139eb))

### Features

- Add remark field ([#222](https://github.com/problematy/goodmap/pull/222),
  [`34edc10`](https://github.com/problematy/goodmap/commit/34edc107c11f5c2b4f34d1c1ba0c947e2b0d186c))


## v0.5.0 (2025-03-16)


## v0.4.4 (2025-01-28)


## v0.4.3 (2024-12-12)


## v0.4.2 (2024-12-05)


## v0.4.1 (2024-11-19)


## v0.4.0 (2024-10-16)


## v0.3.1 (2024-09-02)


## v0.3.0 (2024-08-24)


## v0.2.3 (2023-12-22)


## v0.2.2 (2023-12-21)


## v0.2.1 (2023-12-12)


## v0.2.0 (2023-08-21)


## v0.1.12 (2023-08-04)


## v0.1.11 (2023-07-24)


## v0.1.10 (2023-06-27)


## v0.1.9 (2023-06-17)

### Bug Fixes

- App not displaying data if visible data is null #53
  ([`864f26e`](https://github.com/problematy/goodmap/commit/864f26ee8be507a57b8a82951562324b5ba43cda))


## v0.1.8 (2023-05-30)


## v0.1.7 (2022-10-27)


## v0.1.6 (2022-10-05)


## v0.1.5 (2022-10-05)


## v0.1.4 (2022-09-12)

- Initial Release
