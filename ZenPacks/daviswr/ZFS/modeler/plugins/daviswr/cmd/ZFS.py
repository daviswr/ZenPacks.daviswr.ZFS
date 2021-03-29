# pylint: disable=line-too-long, invalid-name
""" Models ZFS datasets via SSH """

import re
import time

from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap


class ZFS(CommandPlugin):
    """ Models ZFS datasets via SSH """
    requiredProperties = (
        'zZFSDatasetIgnoreNames',
        'zZFSDatasetIgnoreTypes',
        'zZPoolIgnoreNames',
        # Required so they'll be available to the DeviceProxy
        # during TALES evaluation
        'zZFSExecPrefix',
        'zZFSBinaryPath',
        )

    deviceProperties = CommandPlugin.deviceProperties + requiredProperties

    # Note that we're using TALES in the command. Normally that's not
    # possible. Check out the monkeypatch of CollectorClient.getCommands
    # in this ZenPack's __init__.py to see what makes it possible.
    commands = [
        '$$ZENOTHING',
        '${here/zZFSExecPrefix} ${here/zZFSBinaryPath} get -pH all',
        ]
    command = ';'.join(commands)

    def process(self, device, results, log):
        """ Generates RelationshipMaps from Command output """
        log.info(
            'Modeler %s processing data for device %s',
            self.name(),
            device.id
            )
        maps = list()

        pools = dict()

        get_regex = r'^(?P<ds>\S+)\t(?P<key>\S+)\t(?P<value>\S+)\t\S+$'

        for line in results.splitlines():
            get_match = re.match(get_regex, line)

            if get_match:
                ds = get_match.group('ds')
                pool = ds.split('/')[0]
                key = get_match.group('key')
                value = get_match.group('value')
                if pool not in pools:
                    pools[pool] = dict()
                if ds not in pools[pool]:
                    pools[pool][ds] = dict()
                if value.endswith('%') or re.match(r'^\d+\.\d{2}x$', value):
                    value = value[:-1]
                elif value == '-':
                    value = None
                elif key == 'type':
                    pools[pool][ds]['zDsType'] = value
                    continue
                pools[pool][ds][key] = value

        booleans = [
            'atime',
            'defer_destroy',
            'mounted',
            'nbmand',
            'overlay',
            'relatime',
            'setuid',
            'utf8only',
            'vscan',
            'zoned',
            ]

        floats = [
            'compressratio',
            'refcompressratio',
            ]

        ints = [
            'available',
            'copies',
            'filesystem_count',
            'filesystem_limit',
            'logicalreferenced',
            'logicalused',
            'quota',
            'recordsize',
            'referenced',
            'refquota',
            'refreservation',
            'reservation',
            'snapshot_count',
            'snapshot_limit',
            'used',
            'usedbychildren',
            'usedbydataset',
            'usedbyrefreservation',
            'usedbysnapshots',
            'userrefs',
            'volblocksize',
            'volsize',
            'written',
            ]

        times = [
            'creation',
            ]

        prefixes = {
            'filesystem': 'fs',
            'volume': 'vol',
            'snapshot': 'snap'
            }

        suffixes = {
            'filesystem': '',
            'volume': 'Vol',
            'snapshot': 'Snap'
            }

        time_format = '%Y-%m-%d %H:%M:%S'

        rm = RelationshipMap(
            relname='zfsdatasets',
            modname='ZenPacks.daviswr.ZFS.ZFSDataset'
            )

        ignore_names_regex = getattr(device, 'zZFSDatasetIgnoreNames', '')
        if ignore_names_regex:
            log.info('zZFSDatasetIgnoreNames set to %s', ignore_names_regex)
        ignore_types = getattr(device, 'zZFSDatasetIgnoreTypes', list())
        if ignore_types:
            log.info('zZFSDatasetIgnoreTypes set to %s', str(ignore_types))
        ignore_pools_regex = getattr(device, 'zZPoolIgnoreNames', '')
        if ignore_pools_regex:
            log.info('zZPoolIgnoreNames set to %s', ignore_pools_regex)

        # Dataset components
        for pool in pools:
            if ignore_pools_regex and re.match(ignore_pools_regex, pool):
                log.debug('Skipping pool %s due to zZPoolIgnoreNames', pool)
                continue

            rm = RelationshipMap(
                compname='zpools/pool_{0}'.format(pool),
                relname='zfsDatasets',
                modname='ZenPacks.daviswr.ZFS.ZFSDataset'
                )

            datasets = pools[pool]
            for ds in datasets:
                if ignore_names_regex and re.match(ignore_names_regex, ds):
                    log.debug(
                        'Skipping dataset %s due to zZFSDatasetIgnoreNames',
                        ds
                        )
                    continue
                elif (ignore_types
                        and datasets[ds].get('zDsType', '') in ignore_types):
                    log.debug(
                        'Skipping dataset %s due to zZFSDatasetIgnoreTypes',
                        ds
                        )
                    continue

                comp = dict()
                for key in datasets[ds]:
                    if key in booleans:
                        comp[key] = (True if datasets[ds][key] in ['on', 'yes']
                                     else False)
                    elif key in floats:
                        comp[key] = float(datasets[ds][key])
                    elif key in ints:
                        comp[key] = int(datasets[ds][key])
                    elif key in times:
                        comp[key] = time.strftime(
                            time_format,
                            time.localtime(int(datasets[ds][key]))
                            )
                    elif 'encryption' == key and 'on' == datasets[ds][key]:
                        # https://docs.oracle.com/cd/E53394_01/html/E54801/gkkih.html  # noqa
                        # The default encryption algorithm is aes-128-ccm when
                        # a file system's encryption value is on.
                        comp[key] = 'aes-128-ccm'
                    else:
                        comp[key] = datasets[ds][key]
                prefix = prefixes.get(comp.get('zDsType'), '')
                suffix = suffixes.get(comp.get('zDsType'), 'Dataset')
                # Pool name should already be part of the dataset name,
                # making it unique
                comp['id'] = self.prepId('{0}_{1}'.format(prefix, ds))
                comp['title'] = ds
                log.debug('Found ZFS %s: %s', comp.get('type', ''), comp['id'])
                mod = 'ZenPacks.daviswr.ZFS.ZFS{0}'.format(suffix)
                rm.append(ObjectMap(
                    modname=mod,
                    data=comp
                    ))
            maps.append(rm)

        log.debug(
            'ZFS RelMap:\n%s',
            str(maps)
            )

        return maps
