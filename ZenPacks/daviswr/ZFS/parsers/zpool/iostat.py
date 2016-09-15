import re

from Products.ZenRRD.CommandParser \
    import CommandParser
from Products.ZenUtils.Utils \
    import prepId

class iostat(CommandParser):
    def processResults(self, cmd, result):
        """
        Example output
        pool1       5.58T  1.67T  1.26K      0   160M      0
        """
        iostat_regex = r'^(?P<pool>\S+)\s+\S+\s+\S+\s+(?P<op_read>\d+\.?\d?\d?)(?P<op_read_unit>\w)?\s+(?P<op_write>\d+\.?\d?\d?)(?P<op_write_unit>\w)?\s+(?P<bw_read>\d+\.?\d?\d?)(?P<bw_read_unit>\w)?\s+(?P<bw_write>\d+\.?\d?\d?)(?P<bw_write_unit>\w)?$'

        multi = {
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4,
            'P': 1024**5,
            'E': 1024**6,
            'Z': 1024**7,
            'Y': 1024**8,
            }

        measures = [
            'op_read',
            'op_write',
            'bw_read',
            'bw_write',
            ]

        pools = dict()
        for line in cmd.result.output.splitlines():
            match = re.match(iostat_regex, line)
            if match:
                stats = dict()
                for measure in measures:
                    value = float(match.group(measure))
                    unit = match.group('{}_unit'.format(measure))
                    name = measure.replace('_', '-')
                    stats[name] =  value * multi.get(unit, 1)
                pool = match.group('pool')
                pools[pool] = stats

        components = dict()
        for pool in pools:
            comp_id = prepId('pool_{}'.format(pool))
            if comp_id not in components:
                components[comp_id] = dict()
            for measure in pools[pool]:
                value = pools[pool].get(measure)
                components[comp_id][measure] = value

        for point in cmd.points:
            if point.component in components:
                values = components[point.component]
                if point.id in values:
                    result.values.append((point, values[point.id]))
