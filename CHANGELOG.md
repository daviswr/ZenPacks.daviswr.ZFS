# Change Log

## [Unreleased]

## [0.8.1] - 2024-04-06
### Added
 * Support for minor output formatting changes after OpenZFS 2.0
 * Events generated from ZPool status

### Changed
 * Removed dependency on GNU echo

### Fixed
 * ZPool status line check
 * Event summary generation in zpool status parser
 * zed process regex will not match ffprobe


## [0.8.0] - 2021-02-06
### Added
 * vDev I/O activity graphs
 * Pool health status
 * Error counter graphs
 * Scrub/resilver events
 * Encryption attributes modeled
 * Process monitoring
 * Per-pool configurable utilization thresholds

### Changed
 * ZenPackLib 2.x required
 * Adjusted zpool iostat sampling interval for improve accuracy
 * zdb/zfs/zpool paths determined by modeler
 * Modeler determines if privilege escalation is required

### Removed
 * TALES monkeypatch for zProperties in Command modeler
   * Only used in intermediate/dev versions between Dec. 2020 and Feb. 2022
 * zZpoolThreshold* properties

### Fixed
 * Component-level health checks
 * Pool title populated if not found in zdb


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

[Unreleased]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.8.1...HEAD
[0.8.1]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.8.0...0.8.1
[0.8.0]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.5...0.8.0
[0.7.5]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.4...0.7.5
[0.7.4]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.3...0.7.4
[0.7.3]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.2...0.7.3
[0.7.2]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.1...0.7.2
[0.7.1]: https://github.com/daviswr/ZenPacks.daviswr.ZFS/compare/0.7.0...0.7.1
