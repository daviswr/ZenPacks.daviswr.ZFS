""" Parses `zpool get` output """

import re

from Products.ZenRRD.CommandParser import CommandParser
from Products.ZenUtils.Utils import prepId


class get(CommandParser):
    """ Parses `zpool get` output """

    def processResults(self, cmd, result):
        """"
        Example output
        pool0	size	399431958528	-
        """
        get_regex = r'^(?P<pool>\S+)\t(?P<key>\S+)\t(?P<value>\S+)\t\S+$'

        pools = dict()
        for line in cmd.result.output.splitlines():
            get_match = re.match(get_regex, line)

            if get_match:
                pool = get_match.group('pool')
                key = get_match.group('key')
                value = get_match.group('value')
                if pool not in pools:
                    pools[pool] = dict()
                if value.endswith('%') or re.match(r'^\d+\.\d{2}x$', value):
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

        components = dict()
        for pool in pools:
            comp_id = prepId('pool_{0}'.format(pool))
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
