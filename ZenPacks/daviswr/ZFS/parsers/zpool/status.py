# pylint: disable=C0301
""" Parses `zpool status` output """

import re

from Products.ZenEvents import Event
from Products.ZenRRD.CommandParser import CommandParser


class status(CommandParser):
    """ Parses `zpool status` output """

    def processResults(self, cmd, result):
        """
        Example unhealthy output:
          pool: zpool3
         state: DEGRADED
        status: One or more devices has been removed by the administrator.
            Sufficient replicas exist for the pool to continue functioning in a
            degraded state.
        action: Online the device using 'zpool online' or replace the device with      # noqa
            'zpool replace'.
          scan: resilvered 856G in 22h23m with 0 errors on Thu Jul  7 17:26:46 2016    # noqa
        config:

            NAME                                           STATE     READ WRITE CKSUM  # noqa
            zpool3                                         DEGRADED 0     0     0      # noqa
              raidz2-0                                     DEGRADED 0     0     0      # noqa
                ata-ST2000LM007-1R8174_WCC08SPQ            REMOVED 0     0     0       # noqa
                ata-ST2000LM003_HN-M201RAD_S362J9CH186029  ONLINE 0     0     0
                ata-ST2000LM003_HN-M201RAD_S34RJ9AG212597  ONLINE 0     0     0
                ata-ST2000LM003_HN-M201RAD_S34RJ9AG212657  ONLINE 0     0     0
            logs
              ata-ACSC2M064S25_986012880052                ONLINE 0     0     0

        errors: No known data errors
        """
        device_re = r'(?P<dev>\S+)\s+(?P<health>\S+)\s+(?P<read>\d+)\s+(?P<write>\d+)\s+(?P<cksum>\d+)'  # noqa
        device_error_re = device_re + r'\s+(?P<msg>\w.+)$'

        # Convert pool state to number for monitoring template
        # An event transform will make this human-readable again
        health_map = {
            'ONLINE': 1,
            'AVAIL': 2,  # Spare
            'INUSE': 3,  # Spare
            'DEGRADED': 4,
            'FAULTED': 5,
            'OFFLINE': 6,
            'UNAVAIL': 7,
            'REMOVED': 8,
            'SUSPENDED': 9,
            }

        measures = [
            'read',
            'write',
            'cksum'
            ]

        scrub_map = {
            'complete': 1,
            'scrub': 2,
            'resilver': 3,
            }

        values = dict()
        events = {'device': None, 'errors': None, 'status': None}

        comp_health = None
        pool_health = None

        for line in cmd.result.output.splitlines():
            line = line.strip()
            match = re.search(device_re, line)

            if match:
                health = match.group('health').upper()
                comp_health = health_map.get(health, 100)
                for measure in measures:
                    metric = int(match.group(measure))
                    values['error-{0}'.format(measure)] = metric
                err_match = re.search(device_error_re, line)
                if err_match:
                    events['device'] = err_match.group('msg')

            elif 'scan:' in line or 'scrub:' in line:
                line = line.replace('scrub: ', '')
                if ('completed' in line
                        or 'repaired' in line
                        or 'resilvered' in line):
                    values['scrub'] = scrub_map.get('complete', 100)
                elif 'scrub' in line:
                    values['scrub'] = scrub_map.get('scrub', 100)
                elif 'resilver' in line:
                    values['scrub'] = scrub_map.get('resilver', 100)
                else:
                    values['scrub'] = scrub_map.get('complete', 100)

            elif 'state:' in line:
                pool_health = health_map.get(line.split(':')[1].strip(), 100)

            elif 'status:' in line:
                message = line.split(':', 1)[1].strip()
                events['status'] = (message[:-3] if message.endswith(' or')
                                    else message)

            elif 'errors:' in line:
                message = line.split(':')[-1].strip()
                events['errors'] = (None if message == 'No known data errors'
                                    else message)

        if comp_health and pool_health:
            # If both available, use the worse value
            values['health'] = (comp_health if comp_health >= pool_health
                                else pool_health)
        elif comp_health:
            values['health'] = comp_health
        elif pool_health:
            values['health'] = pool_health

        if events['device'] or events['errors'] or events['status']:
            for message in events.values():
                if message:
                    result.events.append({
                        'device': cmd.deviceConfig.device,
                        'component': cmd.component,
                        'severity': Event.Error,
                        'eventKey': 'zpool-status',
                        'eventClass': '/Storage',
                        'summary': message,
                        })
        else:
            result.events.append({
                'device': cmd.deviceConfig.device,
                'component': cmd.component,
                'severity': Event.Clear,
                'eventKey': 'zpool-status',
                'eventClass': '/Storage',
                'summary': 'No known data errors',
                })

        for point in cmd.points:
            if point.id in values:
                result.values.append((point, values[point.id]))
