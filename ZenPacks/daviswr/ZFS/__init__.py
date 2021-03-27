import re
import sys
from ZenPacks.zenoss.ZenPackLib import zenpacklib

# https://www.skills-1st.co.uk/papers/jane/zpdevguide/ZenPack_DevGuide_V1.0.1_publish1_20161013.pdf  # noqa
# https://github.com/cluther/ZenPacks.example.EvaluatedCommandModeler
from Products.ZenUtils.Utils import monkeypatch
from Products.ZenUtils.ZenTales import talesEvalStr

CFG = zenpacklib.load_yaml()
schema = CFG.zenpack_module.schema

# SshClient does a relative import of CollectorClient from
#    /opt/zenoss/Products/DataCollector/CollectorClient.py.
# The standard CollectorClient class has an __init__ like:
#    def __init__(self, hostname, ip, port, plugins=None, options=None,
#                 device=None, datacollector=None, alog=None):
# Note the first 3 paramters are mandatory ( args[0] to args[2] ), plugins
#  is the first optional at args[3]. device may be args[5]
#
# Normally one cannot pass TALES expressions to a command. This code
# does a monkeypatch to the relative CollectorClient module already in
# sys.modules to check for ${ syntax and performs a TALES evaluation.
if 'CollectorClient' in sys.modules:
    CollectorClient = sys.modules['CollectorClient']

    @monkeypatch(CollectorClient.CollectorClient)
    def __init__(self, *args, **kwargs):
        # original is injected into locals by the monkeypatch decorator.
        original(self, *args, **kwargs)

        # Reset cmdmap and _commands.
        self.cmdmap = {}
        self._commands = []

        # Get plugins from args or kwargs.
        plugins = kwargs.get('plugins')
        if plugins is None:
            if len(args) > 3:
                plugins = args[3]
            else:
                plugins = []

        # Get device from args or kwargs.
        device = kwargs.get('device')
        if device is None:
            if len(args) > 5:
                device = args[5]
            else:
                device = None

        # Do TALES evaluation of each plugin's command.
        for plugin in plugins:
            if re.search(r'\$\{\S+\/\S+\}', plugin.command):
                try:
                    command = talesEvalStr(plugin.command, device)
                except Exception:
                    CollectorClient.log.exception(
                        '%s - command TALES evaluation failed, proceeding',
                        device.id)

                    command = plugin.command
            else:
                command = plugin.command

            self.cmdmap[command] = plugin
            self._commands.append(command)
