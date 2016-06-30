import re

from Products.DataCollector.plugins.CollectorPlugin \
    import CommandPlugin
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class ZPool(CommandPlugin):
    command = 'sudo /sbin/zpool get -pH all;' \
        'sudo /sbin/zpool iostat -vg;' \
        'sudo /sbin/zpool iostat -v'

    def process(self, device, results, log):
        log.info(
            "Modeler %s processing data for device %s",
            self.name(), device.id)
        maps = list()

        pools = dict()
        vdevs = dict()
        vdev_idx = dict()
        root_guids = list()
        root_names = list()
        vdev_guids = list()
        vdev_names = list()
        last_pool = None
        last_root = None
        get_regex = r'^(?P<pool>\S+)\s+(?P<key>\S+)\s+(?P<value>\S+)\s+\S+$'
        iostat_regex = r'(?P<dev>\S+)\s+(?:\d\S+|\-)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+'
        for line in results.splitlines():
            get_match = re.match(get_regex, line)
            pool_match = re.match(r'^' + iostat_regex, line)
            root_vdev_match = re.match(r'^\s{2}' + iostat_regex, line)
            vdev_match = re.match(r'^\s{4}' + iostat_regex, line)

            if get_match:
                pool = get_match.group(pool)
                key = get_match.group(key)
                value = get_match.group(value)
                if not pools.has_key(pool):
                    pools.update({pool: dict()})
                # Clean up percentages and ratios
                if value.endswith('%') \
                    or re.match(r'^\d+\.\d{2}x$')
                    value = value[:-1]
                pools[pool].update({key: value})

            elif pool_match:
                pool = pool_match.group(dev)
                last_pool = pool
                if not vdev_idx.has_key(pool):
                    vdev_idx[pool] = dict()

            # Put the vDev names & GUIDs into lists
            # and store the index in the vdev_idx dict
            # so we can sort through them later.
            # An OrderedDict might be a *lot* better for this
            elif root_vdev_match:
                root_vdev = root_vdev_match.group(dev)
                if re.match(r'[a-zA-z]', root_vdev):
                    # mirror, raid, etc
                    if not root_names.__contains__(root_vdev):
                        root_names.append(root_vdev)
                    idx = len(root_names) - 1
                    last_root = idx
                    if vdev_idx.has_key(last_pool) \
                        and not vdev_idx[last_pool].has_key(idx):
                        vdev_idx[last_pool][idx] = list()
                else:
                    # GUID
                    if not root_guids.__contains__(root_vdev):
                        root_guids.append(root_vdev)

            elif vdev_match:
                vdev = vdev_match.group('dev')
                if re.match(r'[a-zA-z]', vdev):
                    # device name
                    if not vdev_names.__contains__(vdev):
                        vdev_names.append(vdev)
                    idx = len(vdev_names) - 1
                    if vdev_idx.has_key(last_pool) \
                        and vdev_idx[last_pool].has_key(last_root) \
                        and not vdev_idx[last_pool][last_root].__contains__(idx):
                        vdev_idx[last_pool][last_root].append(idx)
                else:
                    # GUID
                    if not vdev_guids.__contains__(vdev):
                        vdev_guids.append(vdev)

        # Bring vDev GUIDs and names together, using the indexes
        for pool in vdev_idx:
            vdevs[pool] = dict()
            for root in vdev_idx[pool]:
                rguid = root_guids[root]
                rname = root_names[root]
                vdevs[pool][rguid] = dict()
                vdevs[pool][rguid]['name'] = rname
                vdevs[pool][rguid]['vdevs'] = dict()
                for dev in vdev_idx[pool][root]:
                    dguid = vdev_guids[dev]
                    dname = vdev_names[dev]
                    vdevs[pool][rguid]['vdevs'][dguid] = dname