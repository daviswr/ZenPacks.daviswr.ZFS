import re

from Products.DataCollector.plugins.CollectorPlugin \
    import CommandPlugin
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class ZPool(CommandPlugin):
    command = 'sudo /sbin/zpool get -pH all;' \
        'sudo /sbin/zdb -L'

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
        last_vdev = None
        
        get_regex = r'^(?P<pool>\S+)\s+(?P<key>\S+)\s+(?P<value>\S+)\s+\S+$'
        zdb_header_regex = r'(?P<key>\S+)\:$'
        zdb_kv_regex = r'\ {4}\s*(?P<key>\S+)\:\s?(?P<value>\S+)'

        for line in results.splitlines():
            get_match = re.match(get_regex, line)
            zdb_pool_match = re.match(r'^' + zdb_header_regex, line)
            zdb_tree_match = re.match(r'^    ' + zdb_header_regex, line)
            zdb_root_match = re.match(r'^        ' + zdb_header_regex, line)
            zdb_vdev_match = re.match(r'^            ' + zdb_header_regex, line)
            zdb_kv_match = re.match(zdb_kv_regex, line)

            if get_match:
                pool = get_match.group('pool')
                key = get_match.group('key')
                value = get_match.group('value')
                if not pools.has_key(pool):
                    pools.update({pool: dict()})
                if value.endswith('%') \
                    or re.match(r'^\d+\.\d{2}x$', value):
                    value = value[:-1]
                elif value == '-':
                    value = None
                pools[pool].update({key: value})

            elif zdb_pool_match:
                pool = zdb_pool_match.group('key')
                if not pools.has_key(pool):
                    pools.update({pool: dict()})
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
                last_root['parent_guid'] = last_pool['guid']
                last_root['parent_pool'] = last_pool['title']
                last_root['parent_vdev'] = last_pool['title']
                last_parent = last_root

            elif zdb_vdev_match:
                key = zdb_vdev_match.group('key')
                last_root[key] = dict()
                last_vdev = last_root[key]
                last_vdev['parent_guid'] = last_root['guid']
                last_vdev['parent_vdev'] = last_root['title']
                last_vdev['parent_pool'] = last_pool['title']
                last_parent = last_vdev

            elif zdb_kv_match:
                key = zdb_kv_match.group('key')
                value = zdb_kv_match.group('value').replace("'", "")
                # Attributes right under vdev_tree are pool-wide
                # and should already be in `zpool get` output
                if last_pool.has_key('vdev_tree') \
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
				# Path comes after ID & type in ZDB output if vDev is a disk
                if key == 'path':
                    last_parent['title'] = value.split('/')[-1]
                elif key == 'id' \
                    and last_parent.has_key('type'):
                    last_parent['title'] = '{0}-{1}'.format(last_parent['type'], value)

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
                    if not key.startswith('children'):
                        del roots[key]
                for root in roots:
                    comp = dict()
                    children = list()
                    for key in roots[root]:
                        if key in ['is_log', 'whole_disk']:
                            comp[key] = True if ('1' == roots[root][key]) else False
                        elif key in ints:
                            comp[key] = int(roots[root][key])
                        elif key == 'type':
                            comp['vDevType'] = value
                        elif key.startswith('children['):
                            children.append(roots[root][key])
                        elif not key == 'name':
                            comp[key] = roots[root][key]
                    id_str = '{0}_{1}'.format(pool, comp.get('title', '').replace('-', '_'))
                    comp['id']= self.prepId(id_str)
                    log.debug('Found Root vDev: %s', comp['id'])
                    root_rm.append(ObjectMap(
                        modname='ZenPacks.daviswr.ZFS.ZRootVDev',
                        data=comp
                        ))
                    root_rm_list.append(root_rm)
                    # Child vDev components
                    if len(children) > 0:
                        log.debug('Root vDev %s has children', comp['id'])
                        child_rm = RelationshipMap(
                            compname='zpools/pool_{0}/zrootVDevs/{1}'.format(pool, id_str),
                            relname='zchildVDevs',
                            modname='ZenPacks.daviswr.ZFS.ZChildVDev'
                            )
                        for child in children:
                            comp = dict()
                            for key in child:
                                if key in ['is_log', 'whole_disk']:
                                    comp[key] = True if ('1' == child[key]) else False
                                elif key in ints:
                                    comp[key] = int(child[key])
                                elif key == 'type':
                                    comp['vDevType'] = value
                                elif not key == 'name':
                                    comp[key] = child[key]
                            id_str = '{0}_{1}'.format(pool, comp.get('title', '').replace('-', '_')) 
                            comp['id']= self.prepId(id_str)
                            log.debug('Found child vDev: %s', comp['id'])
                            child_rm.append(ObjectMap(
                                modname='ZenPacks.daviswr.ZFS.ZChildVDev',
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
