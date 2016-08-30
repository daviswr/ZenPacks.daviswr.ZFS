import re
import time

from Products.DataCollector.plugins.CollectorPlugin \
    import CommandPlugin
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class ZFS(CommandPlugin):
    command = '/usr/bin/sudo /sbin/zfs get -pH all'

    def process(self, device, results, log):
        log.info(
            "Modeler %s processing data for device %s",
            self.name(), device.id)
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
                if value.endswith('%') \
                    or re.match(r'^\d+\.\d{2}x$', value):
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

        # Dataset components
        for pool in pools:
            rm = RelationshipMap(
                compname='zpools/pool_{}'.format(pool),
                relname='zfsDatasets',
                modname='ZenPacks.daviswr.ZFS.ZFSDataset'
                )
            datasets = pools[pool]
            for ds in datasets:
                comp = dict()
                for key in datasets[ds]:
                    if key in booleans:
                        comp[key] = True if ('on' == datasets[ds][key] or 'yes' == datasets[ds][key]) else False
                    elif key in floats:
                        comp[key] = float(datasets[ds][key])
                    elif key in ints:
                        comp[key] = int(datasets[ds][key])
                    elif key in times:
                        comp[key] = time.strftime(
                            time_format,
                            time.localtime(int(datasets[ds][key]))
                            )
                    else:
                        comp[key] = datasets[ds][key]
                prefix = prefixes.get(comp.get('zDsType'), '')
                suffix = suffixes.get(comp.get('zDsType'), 'Dataset')
                # Pool name should already be part of the dataset name,
                # making it unique
                comp['id'] = self.prepId('{0}_{1}'.format(prefix, ds))
                comp['title'] = ds
                log.debug('Found ZFS %s: %s', comp.get('type', ''), comp['id'])
                mod = 'ZenPacks.daviswr.ZFS.ZFS{}'.format(suffix)
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
