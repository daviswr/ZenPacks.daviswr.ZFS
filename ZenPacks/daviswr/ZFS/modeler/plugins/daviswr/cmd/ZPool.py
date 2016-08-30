import re

from Products.DataCollector.plugins.CollectorPlugin \
    import CommandPlugin
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class ZPool(CommandPlugin):
    command = '/usr/bin/sudo /sbin/zpool get -pH all;' \
        '/usr/bin/sudo /sbin/zdb -L;' \
        '/usr/bin/sudo /sbin/zpool status -v'

    def process(self, device, results, log):
        log.info(
            "Modeler %s processing data for device %s",
            self.name(), device.id)
        maps = list()

        pools = dict()
        last_parent = None
        last_pool = None
        last_root = None
        last_tree = None
        last_type = None
        last_vdev = None
        zpool_status = False

        get_regex = r'^(?P<pool>\S+)\t(?P<key>\S+)\t(?P<value>\S+)\t\S+$'
        zdb_header_regex = r'(?P<key>\S+)\:$'
        zdb_kv_regex = r'\ {4}\s*(?P<key>\S+)\:\s?(?P<value>\S+)'
        status_pool_regex = r'^\s+pool: (?P<dev>\S+)$'
        status_logs_regex = r'^\s+logs$'
        status_cache_regex = r'^\s+cache$'
        status_dev_regex = r'(?P<dev>\S+)\s+\S+(?:\s+\d+){3}$'

        for line in results.splitlines():
            get_match = re.match(get_regex, line)
            zdb_pool_match = re.match(r'^' + zdb_header_regex, line)
            zdb_tree_match = re.match(r'^    ' + zdb_header_regex, line)
            zdb_root_match = re.match(r'^        ' + zdb_header_regex, line)
            zdb_vdev_match = re.match(r'^            ' + zdb_header_regex, line)
            zdb_kv_match = re.match(zdb_kv_regex, line)
            status_pool_match = re.match(status_pool_regex, line) \
                or re.match(r'^\t' + status_dev_regex, line)
            status_logs_match = re.match(status_logs_regex, line)
            status_cache_match = re.match(status_cache_regex, line)
            status_root_match = re.match(r'^\t  ' + status_dev_regex, line)
            status_child_match = re.match(r'^\t    ' + status_dev_regex, line)

            if get_match:
                pool = get_match.group('pool')
                key = get_match.group('key')
                value = get_match.group('value')
                if pool not in pools:
                    pools[pool] = dict()
                if value.endswith('%') \
                    or re.match(r'^\d+\.\d{2}x$', value):
                    value = value[:-1]
                elif value == '-':
                    value = None
                pools[pool][key] = value

            elif zdb_pool_match:
                if not zpool_status:
                    pool = zdb_pool_match.group('key')
                    if pool not in pools:
                        pools[pool] = dict()
                    last_pool = pools[pool]
                    last_pool['type'] = 'pool'
                    last_parent = last_pool

            elif zdb_tree_match:
                key = zdb_tree_match.group('key')
                if key.find('tree') > -1:
                    last_pool[key] = dict()
                    last_tree = last_pool[key]
                    last_parent = last_tree

            elif zdb_root_match:
                key = zdb_root_match.group('key')
                last_tree[key] = dict()
                last_root = last_tree[key]
                last_parent = last_root

            elif zdb_vdev_match:
                key = zdb_vdev_match.group('key')
                last_root[key] = dict()
                last_vdev = last_root[key]
                last_parent = last_vdev

            elif zdb_kv_match:
                key = zdb_kv_match.group('key')
                value = zdb_kv_match.group('value').replace("'", "")
                # Attributes right under vdev_tree are pool-wide
                # and should already be in `zpool get` output
                if 'vdev_tree' in last_pool \
                    and last_pool['vdev_tree'] == last_parent:
                    continue
                # ZenModeler does not like these in the RelMap
                elif key in ['hostid', 'hostname']:
                    continue
                elif key == 'name':
                    last_parent['title'] = value
                    continue
                elif key == 'pool_guid':
                    last_parent['guid'] = value
                    continue
                last_parent[key] = value
                # disk type
                if key == 'path':
                    last_parent['title'] = value.split('/')[-1]
                # mirror type
                elif key == 'id' \
                    and 'type' in last_parent:
                    last_parent['title'] = '{0}-{1}'.format(
                        last_parent['type'],
                        value
                        )
                # raidz type
                elif key == 'nparity' \
                    and 'id' in last_parent \
                    and 'type' in last_parent:
                    last_parent['type'] += value
                    last_parent['title'] = '{0}-{1}'.format(
                        last_parent['type'],
                        last_parent['id']
                        )

            # 'zpool status' is only to find cache devices
            # since they're strangely absent from zdb
            elif status_pool_match:
                zpool_status = True
                pool = status_pool_match.group('dev')
                if pool not in pools:
                    pools[pool] = dict()
                if 'vdev_tree' not in pools[pool]:
                    pools[pool]['vdev_tree'] = dict()
                last_pool = pools[pool]
                last_pool['type'] = 'pool'
                last_type = last_pool['type']
                last_tree = pools[pool]['vdev_tree']
                last_parent = last_tree

            elif status_logs_match:
                last_type = 'logs'

            elif status_cache_match:
                last_type = 'cache'

            # Emulate structure in zdb output for log devices
            # Each device is a root vdev,
            # rather than a child vdev in a logs/cache root
            elif status_root_match:
                if 'cache' == last_type:
                    dev = status_child_match.group('dev')
                    key = 'cache_{}'.format(dev)
                    if key not in last_tree:
                        last_tree[key] = dict()
                    last_root = last_tree[key]
                    last_root['title'] = dev
                    last_root['is_cache'] = '1'
                    last_root['is_log'] = '0'

            elif status_child_match:
                last_type = 'child'
                
        booleans = [
            'autoexpand',
            'autoreplace',
            'delegation',
            'listsnapshots',
            'readonly',
            ]

        ints = [
            'allocated',
            'ashift',
            'asize',
            'capacity',
            'create_txg',
            'dedupditto',
            'free',
            'freeing',
            'leaked',
            'metaslab_array',
            'metaslab_shift',
            'size',
            'txg',
            'DTL',
            ]

        floats = [
            'dedupratio',
            'fragmentation',
            ]

        pool_rm = RelationshipMap(
            relname='zpools',
            modname='ZenPacks.daviswr.ZFS.ZPool'
            )

        root_rm_list = list()
        child_rm_list = list()

        # Pool components
        for pool in pools:
            comp = dict()
            for key in pools[pool]:
                if key in booleans:
                    comp[key] = True if ('on' == pools[pool][key]) else False
                elif key in ints:
                    comp[key] = int(pools[pool][key])
                elif key in floats:
                    comp[key] = float(pools[pool][key])
                elif not key == 'vdev_tree' \
                    and not key == 'name':
                    comp[key] = pools[pool][key]
            # Can't use the GUID since it's not available in iostat
            comp['id'] = self.prepId('pool_{}'.format(pool))
            log.debug('Found ZPool: %s', comp['id'])
            pool_rm.append(ObjectMap(
                modname='ZenPacks.daviswr.ZFS.ZPool',
                data=comp
                ))
            # Root vDev components
            roots = pools[pool].get('vdev_tree', None)
            if roots is not None:
                log.debug('ZPool %s has children', comp['id'])
                root_rm = RelationshipMap(
                    compname='zpools/pool_{}'.format(pool),
                    relname='zrootVDevs',
                    modname='ZenPacks.daviswr.ZFS.ZRootVDev'
                    )
                for key in roots.keys():
                    if not key.startswith('children') \
                        and not key.startswith('cache_'):
                        del roots[key]
                for root in roots:
                    comp = dict()
                    children = list()
                    for key in roots[root]:
                        if key in ['is_cache', 'is_log', 'whole_disk']:
                            comp[key] = True if ('1' == roots[root][key]) else False
                        elif key in ints:
                            comp[key] = int(roots[root][key])
                        elif key == 'type':
                            comp['VDevType'] = roots[root][key]
                        elif key.startswith('children[') \
                            or key.startswith('cache_'):
                            children.append(roots[root][key])
                        elif not key == 'name':
                            comp[key] = roots[root][key]
                    id_str = '{0}_{1}'.format(
                        pool,
                        comp.get('title', '').replace('-', '_')
                        )
                    comp['id'] = self.prepId(id_str)
                    log.debug('Found Root vDev: %s', comp['id'])
                    root_rm.append(ObjectMap(
                        modname='ZenPacks.daviswr.ZFS.ZRootVDev',
                        data=comp
                        ))
                    root_rm_list.append(root_rm)
                    # Store Dev components
                    if len(children) > 0:
                        log.debug('Root vDev %s has children', comp['id'])
                        child_rm = RelationshipMap(
                            compname='zpools/pool_{0}/zrootVDevs/{1}'.format(pool, id_str),
                            relname='zstoreDevs',
                            modname='ZenPacks.daviswr.ZFS.ZStoreDev'
                            )
                        for child in children:
                            comp = dict()
                            for key in child:
                                if key in ['is_cache', 'is_log', 'whole_disk']:
                                    comp[key] = True if ('1' == child[key]) else False
                                elif key in ints:
                                    comp[key] = int(child[key])
                                elif key == 'type':
                                    comp['VDevType'] = child[key]
                                elif not key == 'name':
                                    comp[key] = child[key]
                            id_str = '{0}_{1}'.format(
                                pool,
                                comp.get('title', '').replace('-', '_')
                                )
                            comp['id'] = self.prepId(id_str)
                            log.debug('Found child vDev: %s', comp['id'])
                            child_rm.append(ObjectMap(
                                modname='ZenPacks.daviswr.ZFS.ZStoreDev',
                                data=comp
                                ))
                            child_rm_list.append(child_rm)

        maps.append(pool_rm)
        for rm in root_rm_list:
            maps.append(rm)
        for rm in child_rm_list:
            maps.append(rm)

        log.debug(
            'ZPool RelMap:\n%s',
            str(maps)
            )

        return maps
