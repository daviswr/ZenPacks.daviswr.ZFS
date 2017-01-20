# Change Log

## [Unreleased]

## [0.7.5] - 2017-01-19
### Added
 * Basic pool and vdev health check
   * Changes to `sudoers` config on monitored system(s) may be requried
 * Model a pool's spare devices

### Changed
 * Cache, log, and spare devices are now their own component types rather than Root vDevs

## [0.7.4] - 2016-10-08
### Changed
 * Tweaks to component detail display order, grid column widths, etc

### Fixed
 * ZPool modeler redundantly processing Relationship Maps

## [0.7.3] - 2016-09-18
### Added
 * ZPool capacity thresholds configurable via zProperties:
   * zZPoolThresholdWarning
   * zZPoolThresholdError
   * zZPoolThresholdCritical

### Changed
 * `zfs get` datasource runs once per modeled dataset, rather than collecting all performance data for all datasets in one run 
   * Changes to `sudoers` config on monitored system(s) may be requried
 * Logging severity lowered to debug when components are ignored by modelers


## [0.7.2] - 2016-09-14
### Added
 * Modelers ignore components based on zProperties:
   * zZFSDatasetIgnoreNames
   * zZFSDatasetIgnoreTypes
   * zZPoolIgnoreNames


## [0.7.1] - 2016-09-13
### Fixed
 * Cache device enumeration in ZPool modeler


## 0.7.0 - 2016-09-11
 * Alpha release


[Unreleased]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.5...HEAD
[0.7.5]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.4...0.7.5
[0.7.4]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.3...0.7.4
[0.7.3]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.2...0.7.3
[0.7.2]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.1...0.7.2 
[0.7.1]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.0...0.7.1
