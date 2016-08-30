import re

from Products.ZenRRD.CommandParser \
    import CommandParser
from Products.ZenUtils.Utils \
    import prepId

class get(CommandParser):

    def processResults(self, cmd, result):
        components = dict()

        pools = dict()

        get_regex = r'^(?P<pool>\S+)\t(?P<key>\S+)\t(?P<value>\S+)\t\S+$'

        for line in cmd.result.output.splitlines():
            get_match = re.match(get_regex, line)

            if get_match:
                pool = get_match.group('pool')
                key = get_match.group('key')
                value = get_match.group('value')
                if not pools.has_key(pool):
                    pools[pool] = dict()
                if value.endswith('%') \
                    or re.match(r'^\d+\.\d{2}x$', value):
                    value = value[:-1]
                elif value == '-':
                    value = None
                pools[pool][key] = value

        datapoints = [
            'allocated',
            'capacity',
            'free',
            ]

        floats = [
            'dedupratio',
            'fragmentation',
            ]

        datapoints += floats

        for pool in pools:
            comp_id = prepId('pool_{}'.format(pool))
            if comp_id not in components:
                components[comp_id] = dict()
            for measure in datapoints:
                if measure in pools[pool]:
                    if measure in floats:
                        value = float(pools[pool].get(measure))
                    else:
                        value = int(pools[pool].get(measure))
                    components[comp_id][measure] = value

        for point in cmd.points:
            if point.component in components:
                values = components[point.component]
                if point.id in values:
                    result.values.append((point, values[point.id]))
