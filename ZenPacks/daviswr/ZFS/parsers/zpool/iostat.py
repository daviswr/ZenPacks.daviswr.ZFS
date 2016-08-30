import re

from Products.ZenRRD.CommandParser \
    import CommandParser
from Products.ZenUtils.Utils \
    import prepId

class iostat(CommandParser):
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

    def processResults(self, cmd, result):
        components = dict()
        pools = dict()
        iostat_regex = r'^(?P<pool>\S+)\s+\S+\s+\S+\s+(?P<op_read>\d+)\s+(?P<op_write>\d+)\s+(?P<bw_read>\S+)(?P<bw_read_unit>\w)\s+(?P<bw_write>\S+)(?P<bw_write_unit>\w)$'

        for line in cmd.result.output.splitlines():
            match = re.match(iostat_regex, line)
            if match:
                pool = match.group('pool')
                stats = self.process_iostat(match)
                pools[pool] = stats

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

    def process_iostat(self, match):
        stats = dict()

        stats['op-read'] = int(match.group('op_read'))
        stats['op-write'] = int(match.group('op_write'))

        bw_read = float(match.group('bw_read'))
        bw_read_unit = match.group('bw_read_unit')
        stats['bw-read'] = bw_read * self.multi.get(bw_read_unit, 1)

        bw_write = float(match.group('bw_write'))
        bw_write_unit = match.group('bw_write_unit')
        stats['bw-write'] = bw_write * self.multi.get(bw_write_unit, 1)

        return stats
