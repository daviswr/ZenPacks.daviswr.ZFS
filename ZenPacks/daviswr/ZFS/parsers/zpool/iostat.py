# pylint:disable=invalid-name,no-init,no-self-use,too-few-public-methods
""" Parses `zpool iostat` output """

import re

from Products.ZenRRD.CommandParser import CommandParser
from Products.ZenUtils.Utils import prepId


# pylint:disable=line-too-long,too-many-locals
class iostat(CommandParser):
    """ Parses `zpool iostat` output """

    def processResults(self, cmd, result):
        """
        Example output:
                                                         capacity     operations    bandwidth  # noqa
        pool                                          alloc   free   read  write   read  write  # noqa
        --------------------------------------------  -----  -----  -----  -----  -----  -----  # noqa
        pool0                                         11.9T  2.63T      0    165      0   632K  # noqa
          raidz2                                      11.9T  2.63T      0    165      0   632K  # noqa
            ata-WDC_WD40EFRX-68N32N0_WD-WCC7K3HVNHY9      -      -      0     59      0   508K  # noqa
            ata-WDC_WD40EFRX-68N32N0_WD-WCC7K3KCRH5F      -      -      0     48      0   512K  # noqa
            ata-WDC_WD40EFRX-68N32N0_WD-WCC7K7PHLJ15      -      -      0     46      0   524K  # noqa
            ata-WDC_WD40EFRX-68N32N0_WD-WCC7K7ZD5X63      -      -      0     53      0   512K  # noqa
        pool1                                         5.58T  1.67T  1.26K      0   160M      0  # noqa
          raidz2                                      5.58T  1.67T  1.26K      0   160M      0  # noqa
        ...
        """
        iostat_regex = r'^\s*(?P<device>\S+)\s+\S+\s+\S+\s+(?P<op_read>\d+\.?\d?\d?)(?P<op_read_unit>\w)?\s+(?P<op_write>\d+\.?\d?\d?)(?P<op_write_unit>\w)?\s+(?P<bw_read>\d+\.?\d?\d?)(?P<bw_read_unit>\w)?\s+(?P<bw_write>\d+\.?\d?\d?)(?P<bw_write_unit>\w)?$'  # noqa

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

        components = dict()
        offsets = dict()
        last_pool = ''

        for line in cmd.result.output.splitlines():
            match = re.match(iostat_regex, line)
            if match:
                device = match.group('device')
                # Line indented, this is a device, not a pool
                if line.startswith(' '):
                    if (device.startswith('raid')
                            or device.startswith('mirror')):
                        if device not in offsets:
                            offsets[device] = 0
                        suffix = '-{0}'.format(offsets[device])
                        device_name = (device if device.endswith(suffix)
                                       else '{0}{1}'.format(device, suffix)
                                       )
                        offsets[device] += 1
                    else:
                        device_name = device
                    comp_id = prepId('{0}_{1}'.format(
                        last_pool,
                        device_name.replace('-', '_')
                        ))
                # Line has no indent, this is a pool
                else:
                    last_pool = device
                    comp_id = prepId('pool_{0}'.format(device))
                    for offset in offsets:
                        offsets[offset] = 0

                stats = dict()
                for measure in measures:
                    value = float(match.group(measure))
                    unit = match.group('{0}_unit'.format(measure))
                    name = measure.replace('_', '-')
                    stats[name] = int(value * multi.get(unit, 1))

                components[comp_id] = stats

        for point in cmd.points:
            if point.component in components:
                values = components[point.component]
                if point.id in values:
                    result.values.append((point, values[point.id]))
