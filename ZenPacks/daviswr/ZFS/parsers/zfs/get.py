""" Parses `zfs get` output """

import re

from Products.ZenRRD.CommandParser import CommandParser


class get(CommandParser):
    """ Parses `zfs get` output """

    def processResults(self, cmd, result):
        """
        Example output
        pool0/home	used	299133114880	-
        """
        get_regex = r'^(?P<ds>\S+)\t(?P<key>\S+)\t(?P<value>\S+)\t\S+$'

        ds = dict()
        for line in cmd.result.output.splitlines():
            get_match = re.match(get_regex, line)

            if get_match:
                key = get_match.group('key')
                value = get_match.group('value')
                if value.endswith('%') or re.match(r'^\d+\.\d{2}x$', value):
                    value = value[:-1]
                elif '-' == value:
                    value = None
                ds[key] = value

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

        values = dict()
        for measure in datapoints:
            if measure in ds:
                values[measure] = int(ds[measure])

        for point in cmd.points:
            if point.id in values:
                result.values.append((point, values[point.id]))
