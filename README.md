# ZenPacks.daviswr.ZFS

ZenPack to model & monitor ZFS pools and datasets

## Requirements

* An OS that supports ZFS (Solaris/Illumos, FreeBSD, Linux with [OpenZFS](https://openzfs.org/))
  * See "Illumos & FreeBSD notes" below for non-Linux hosts
* An account on the ZFS-capable host, which can
  * Log in via SSH with a key
  * Use a bash-compatible shell
  * Run the `zdb`, `zpool`, and `zfs` commands command with certain parameters via privilege escalation without password
    * This may not be required on some hosts, depending on configuration
    * Currently tries to detect `dzdo`, `doas`, `pfexec`, and `sudo`
* [ZenPackLib](https://zenpacks.zenoss.io/zenoss/ZenPackLib/)

Example entries in `/etc/sudoers`

```
Cmnd_Alias ZDB = /sbin/zdb -L
Cmnd_Alias ZPOOL = /sbin/zpool get -pH all, /sbin/zpool iostat -y *, /sbin/zpool status -v, /sbin/zpool status -v *, /sbin/zpool status -x *
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
* ~`zZPoolThresholdWarning`~
  * DEPRECATED: Replaced by per-pool thresholds
* ~`zZPoolThresholdError`~
  * DEPRECATED: Replaced by per-pool thresholds
* ~`zZPoolThresholdCritical`~
  * DEPRECATED: Replaced by per-pool thresholds
* ~`zZFSExecPrefix`~
  * DEPRECATED: Deteremined by modeler
* ~`zZFSBinaryPath`~
  * DEPRECATED: Deteremined by modeler
* ~`zZPoolBinaryPath`~
  * DEPRECATED: Deteremined by modeler
* ~`zZdbBinaryPath`~
  * DEPRECATED: Deteremined by modeler

Deprecated zProperties will be removed before the v1.0 release.

## Illumos & FreeBSD notes
Being an OpenZFS/ZoL user, I'm primarily developing on Linux, but paths to `zdb`, `zfs`, and `zpool` should be automatically determined by the modeler, as well as what, if anything, to use for priviledge escalation (sudo, pfexec, etc).

That said, this ZenPack's a work in progress; all of the `zdb`, `zpool`, and `zfs` parameters should work on an Illumos system, at least. Some [patient](https://github.com/Crosse) [friends](https://github.com/baileytj3) that use SmartOS have helped me with that.

## Usage
### Modelers
I'm not going to make any assumptions about your device class organization, so it's up to you to configure the `daviswr.cmd.ZPool` and `daviswr.cmd.ZFS` modelers on the appropriate class or device. The ZPool modeler must be in the list of modelers before the ZFS one.

### Zenoss configuration
I've found that reducing `zSshConcurrentSessions` on the device or class from 10 to maybe 5 helps with problems due to overrunning a monitored system's available SSH channels.

### ZPool I/O stats
The `zpool-iostat` datasource **will** miss data since it's only noting what's happened in the last second when it polls. While an actual counter would be nice, that's the only source of pool activity information I can find. Any suggestions would be appreciated.

## Special Thanks
* [RageLtMan](https://github.com/sempervictus) - without his testing, feedback, and input this ZenPack would be a mere fraction of what it's become
* [JRansomed](https://github.com/JRansomed)
* [Crosse](https://github.com/Crosse)
* [BaileyTJ](https://github.com/baileytj3)
* [RipleyMJ](https://github.com/ripleymj)
