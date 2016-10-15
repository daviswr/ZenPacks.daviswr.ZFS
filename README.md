# ZenPacks.daviswr.ZFS

ZenPack to model & monitor ZFS pools and datasets

## Requirements

* Solaris or Illumos-based OS, or Linux with [ZFS-on-Linux (ZoL)](http://zfsonlinux.org/)
  * Only tested against Debian 7 with ZoL 0.6.5 so far...
* An account on the ZFS-capable host, which can
  * Log in via SSH with a key
  * Run the `zdb`, `zpool`, and `zfs` commands with certain parameters without password via `sudo`

Example entries in `/etc/sudoers`

```
Cmnd_Alias ZDB = /sbin/zdb -L
Cmnd_Alias ZPOOL = /sbin/zpool get -pH all, /sbin/zpool iostat -y 1 1, /sbin/zpool status -v, /sbin/zpool status -x *
Cmnd_Alias ZFS = /sbin/zfs get -pH all, /sbin/zfs get -pH all *
zenoss ALL=(ALL) NOPASSWD: ZDB, ZPOOL, ZFS
```
## zProperties
* `zZFSDatasetIgnoreNames`
  * Regex of dataset names for the modeler to ignore.
* `zZFSDatasetIgnoreTypes`
  * List of dataset types for the modeler to ignore. Valid types:
    * filesystem
    * snapshot
    * volume
* `zZPoolIgnoreNames`
  * Regex of pool names for the modeler to ignore. 
* `zZPoolThresholdWarning`
  * Capacity percentage for warning threshold. Default 80.
* `zZPoolThresholdError`
  * Capacity percentage for error threshold. Default 85.
* `zZPoolThresholdCritical`
  * Capacity percentage for critical threshold. Default 90.

## Illumos notes
Being a ZoL user, I don't have an Illumos system handy to develop against, so everything uses `sudo` rather than `pfexec` and paths to things are `/sbin` rather than `/usr/sbin`. But support might come in the form of a second set of modelers and monitoring templates.

That said, this ZenPack's still a work in progress; all of the `zdb`, `zpool`, and `zfs` parameters should work on an Illumos system, at least. Some [patient](https://github.com/Crosse) [friends](https://github.com/baileytj3) that use SmartOS have helped me with that.

## Usage
### Modelers
I'm not going to make any assumptions about your device class organization, so it's up to you to configure the `daviswr.cmd.ZPool` and `daviswr.cmd.ZFS` modelers on the appropriate class or device. The ZPool modeler must be in the list of modelers before the ZFS one.

### Zenoss configuration
I've found that reducing `zSshConcurrentSessions` on the device or class from 10 to maybe 5 helps with problems due to overrunning a monitored system's available SSH channels.

### ZPool I/O stats
The `zpool-iostat` datasource **will** miss data since it's only noting what's happened in the last second when it polls. While an actual counter would be nice, that's the only source of pool activity information I can find. Any suggestions would be appreciated.
