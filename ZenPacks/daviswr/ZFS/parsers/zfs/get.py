import re

from Products.ZenRRD.CommandParser \
    import CommandParser
from Products.ZenUtils.Utils \
    import prepId

class get(CommandParser):

    def processResults(self, cmd, result):
        components = dict()

        pools = dict()

        get_regex = r'^(?P<ds>\S+)\s+(?P<key>\S+)\s+(?P<value>\S+)\s+\S+$'

        for line in cmd.result.output.splitlines():
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

        datapoints = [
            'available',
            'logicalreferenced',
            'logicalused',
            'referenced',
            'used',
            'usedbychildren',
            'usedbydataset',
            'usedbyrefreservation',
            'usedbysnapshots',
            ]

        prefixes = {
            'filesystem': 'fs',
            'volume': 'vol',
            'snapshot': 'snap'
            }

        for pool in pools:
            datasets = pools[pool]
            for ds in datasets:
                prefix = prefixes.get(datasets[ds].get('zDsType'), '')
                comp_id = prepId('{0}_{1}'.format(prefix, ds))
                if comp_id not in components:
                    components[comp_id] = dict()
                for measure in datapoints:
                    if measure in datasets[ds]:
                        components[comp_id][measure] = int(datasets[ds].get(measure))

        for point in cmd.points:
            if point.component in components:
                values = components[point.component]
                if point.id in values:
                    result.values.append((point, values[point.id]))
