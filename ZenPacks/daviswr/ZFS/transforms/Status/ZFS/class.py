from zenoss.protocols.protobufs.zep_pb2 import (
    SEVERITY_CLEAR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_ERROR,
    SEVERITY_CRITICAL
    )

if evt.eventKey == 'zpool-status|zpool-status_health|Health':
    current = int(float(evt.current))

    # Match values in the zool.iostat.status parser
    health_map = {
        1: 'ONLINE',
        2: 'AVAIL',
        3: 'INUSE',
        4: 'DEGRADED',
        5: 'FAULTED',
        6: 'OFFLINE',
        7: 'UNAVAIL',
        8: 'REMOVED',
        9: 'SUSPENDED',
        }

    health = health_map.get(current, 'UNKNOWN')
    if component and component.id and component.title:
        if component.id.startswith('pool_'):
            comp_name = 'Pool {0}'.format(component.title)
        elif (hasattr(component, 'pool')
                and (component.title.startswith('mirror')
                     or component.title.startswith('raid'))):
            comp_name = '{0} {1}'.format(component.pool, component.title)
        else:
            comp_name = component.title
    else:
        comp_name = 'State'
    evt.summary = '{0} is {1}'.format(comp_name, health)

    # https://docs.oracle.com/cd/E19253-01/819-5461/gamno/index.html
    # https://docs.oracle.com/cd/E19253-01/819-5461/gcvcw/index.html
    severities = {
        # The device or virtual device is in normal working order
        'ONLINE': SEVERITY_CLEAR,
        # Available hot spare
        'AVAIL': SEVERITY_CLEAR,
        # Hot spare that is currently in use
        'INUSE': SEVERITY_INFO,
        # The virtual device has experienced a failure but can still function
        'DEGRADED': SEVERITY_ERROR,
        # The device or virtual device is completely inaccessible
        'FAULTED': SEVERITY_CRITICAL,
        # The device has been explicitly taken offline by the administrator
        'OFFLINE': SEVERITY_ERROR,
        # The device or virtual device cannot be opened
        'UNAVAIL': SEVERITY_CRITICAL,
        # The device was physically removed while the system was running
        'REMOVED': SEVERITY_CRITICAL,
        'SUSPENDED': SEVERITY_CRITICAL,
        }

    evt.severity = severities.get(health, SEVERITY_ERROR)
    evt.eventClass = '/Status'

    if component:
        if hasattr(component, 'health'):
            @transact
            def updateDb():
                component.health = health
            updateDb()

elif evt.eventKey.startswith('zpool-get|zpool-get_capacity'):
    current = int(float(evt.current))
    pool_name = component.title if component and component.title \
        else evt.component
    evt.summary = 'Pool {0} {1}% allocated'.format(pool_name, current)
    evt.eventClass = '/Storage'
