## [1.0.4](https://github.com/Problematy/goodmap-frontend/compare/1.0.3...1.0.4) (2025-12-31)


### Bug Fixes

* added repository to package.json ([81d299e](https://github.com/Problematy/goodmap-frontend/commit/81d299e116fb64bf7ecff94c84a8706d26b10a7e))

## [1.0.3](https://github.com/Problematy/goodmap-frontend/compare/1.0.2...1.0.3) (2025-12-31)


### Bug Fixes

* split release to use two steps to semantic release ([#129](https://github.com/Problematy/goodmap-frontend/issues/129)) ([c5447d7](https://github.com/Problematy/goodmap-frontend/commit/c5447d79ab39513ba4be8c7300704fb241dff871))

## [1.0.2](https://github.com/Problematy/goodmap-frontend/compare/1.0.1...1.0.2) (2025-12-30)


### Bug Fixes

* added registry-url back ([#128](https://github.com/Problematy/goodmap-frontend/issues/128)) ([9e9cb56](https://github.com/Problematy/goodmap-frontend/commit/9e9cb5651cc72e1b3735a88de6cbcc13d3cd8791))

## [1.0.1](https://github.com/Problematy/goodmap-frontend/compare/v1.0.0...1.0.1) (2025-12-30)


### Bug Fixes

* tests are called before release ([#127](https://github.com/Problematy/goodmap-frontend/issues/127)) ([77e053a](https://github.com/Problematy/goodmap-frontend/commit/77e053a9dc2c37bc976866197b1d17b596b3597d))

# 1.0.0 (2025-12-30)


### Bug Fixes

* bypass branch protection with github app ([73ab987](https://github.com/Problematy/goodmap-frontend/commit/73ab9879f7e1d7b031ba8d7b6823d1c3d1f88deb))
* Fixed handling of invalid, missing or zero geolocation accuracy so the app uses a consistent numeric value and avoids errors ([847ccd3](https://github.com/Problematy/goodmap-frontend/commit/847ccd335d3f7ac74377578bc72a96072f107a61))
* fixed version numbers ([bdd2975](https://github.com/Problematy/goodmap-frontend/commit/bdd29756e9815830cde4e49fc4bd379229e544a9))
* marker popup one-line value ([#67](https://github.com/Problematy/goodmap-frontend/issues/67)) ([148efed](https://github.com/Problematy/goodmap-frontend/commit/148efed30289dd7b465f72000b96a4d394c36bf1))
* suggest button uses dynamic fields ([#120](https://github.com/Problematy/goodmap-frontend/issues/120)) ([ee8259d](https://github.com/Problematy/goodmap-frontend/commit/ee8259de561c15e73cf4be9e67d91ae66b7ccbc4))
* table fill empty rows ([#101](https://github.com/Problematy/goodmap-frontend/issues/101)) ([cec71e9](https://github.com/Problematy/goodmap-frontend/commit/cec71e979a22372a77dd240e4e61f14efa8406fd))
* update dependencies and node version ([#124](https://github.com/Problematy/goodmap-frontend/issues/124)) ([9527865](https://github.com/Problematy/goodmap-frontend/commit/952786594cf3f0dab44f8a8643cb5b6313d2036b))


### Features

* add proper aria-labels for filter ([#56](https://github.com/Problematy/goodmap-frontend/issues/56)) ([1d58d59](https://github.com/Problematy/goodmap-frontend/commit/1d58d59080cb17783dfe5dd862e5d7a70d78d3f8))
* add search bar ([#51](https://github.com/Problematy/goodmap-frontend/issues/51)) ([6d1ffa5](https://github.com/Problematy/goodmap-frontend/commit/6d1ffa541fe701f3fe0d09f576d2168a08f61cf6))
* add text for location target info ([#55](https://github.com/Problematy/goodmap-frontend/issues/55)) ([bb51739](https://github.com/Problematy/goodmap-frontend/commit/bb517390156f1c8d6fe5e3877418440f8af2e76f))
* added icon for points with remarks ([#118](https://github.com/Problematy/goodmap-frontend/issues/118)) ([719dfc2](https://github.com/Problematy/goodmap-frontend/commit/719dfc2e701a69a58bbacbb0f2d2cf0f96011eb9))
* semantic release introduced ([#123](https://github.com/Problematy/goodmap-frontend/issues/123)) ([5fc4190](https://github.com/Problematy/goodmap-frontend/commit/5fc419060e3963fbfbd98b36fa248325813ea0ab))
* Suggesting new points button ([21dae7c](https://github.com/Problematy/goodmap-frontend/commit/21dae7c74ff0aabcc6acee7447634862cef2c59d))

# 0.4.7
- fix: version number fixed

# 0.4.6
- Feature: Suggesting new points button

# 0.4.4
- Fix: fix for zero accuracy

# 0.4.3
- Feature: Added asterisk icon on remarks

# 0.4.1
- Fix: disabled not working loading screen added

# 0.4.0
- Feature: Loading screen added
- Cleanup: removed /data endpoint usage

# 0.3.9
- Feature: Faster map loading
- Feature: Server side clustering

# 0.3.8
- Feature: Added accessibility table

# 0.3.7
- Added translation for navigate me button

# 0.3.6
- Added UA translations

# 0.3.5
- Fix: change uuid to lowercase as in requirements
- Fix: other option works on other languages than English

# 0.3.4
- Fix: Fit details in Dialog box on mobile

# 0.3.3
- Fix: lazy loading
- Feature: infobox for mobiles

# 0.3.2
- fix: marker popup one-line value

# 0.3.1
- Feature: displaying CTA
- Fix: Map centering on user location all the time
- Fix: reporting issue is now translated

# 0.3.0
- Aligned with goodmap 0.4.0 API
- Added text for location target info
- Added proper aria-labels for filter
- Added search bar
- Fixed pin formatting
- Rendering submitButton only when problemType is selected

# 0.2.3
- Fix: Disabled the navigate me button on desktop (it was not working)

# 0.2.2
- Fix: No more typo in reporting issues
- Fix: Navigate me button have pin in third party maps

# 0.2.1
- Fix: Locate Me button works
- Feature: Navigate to point button
- Feature: Report issue with a point
