#
# Location Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import math
import json
import time
import logging
import unittest2

from mock import Mock
from mock import patch
from mockito import when
from b3.config import XmlConfigParser
from b3.plugins.admin import AdminPlugin
from b3.update import B3version
from b3 import __version__ as b3_version

from location import LocationPlugin


def patch_location_plugin():

    # patch the getLocationData method so it returns
    # static json data instead of querying the API
    def getLocationData(this, client):
        return json.loads("""{"status":"success","country":"Italy","countryCode":"IT","region":"07",
        "regionName":"Lazio", "city":"Rome","zip":"00100","lat":"41.9","lon":"12.4833","timezone":"Europe\/Rome",
        "isp":"Fastweb","org":"Fastweb", "as":"AS12874 Fastweb SpA","query":"93.40.107.236"}""")

    # patch the getLocationDistance method so it returns
    # a fixed distance between random coordinates
    def getLocationDistance(this, cl1, cl2):

        lat1 = 41.9
        lon1 = 12.4833
        lat2 = 38.0
        lon2 = -97.0

        radius = 6371  # Earth radius in Km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        b = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(abs(radius * b), 2)

    LocationPlugin.getLocationData = getLocationData
    LocationPlugin.getLocationDistance = getLocationDistance


class logging_disabled(object):
    """
    Context manager that temporarily disable logging.

    USAGE:
        with logging_disabled():
            # do stuff
    """
    DISABLED = False

    def __init__(self):
        self.nested = logging_disabled.DISABLED

    def __enter__(self):
        if not self.nested:
            logging.getLogger('output').propagate = False
            logging_disabled.DISABLED = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.nested:
            logging.getLogger('output').propagate = True
            logging_disabled.DISABLED = False


class LocationTestCase(unittest2.TestCase):

    def setUp(self):
        self.sleep_patcher = patch("time.sleep")
        self.sleep_mock = self.sleep_patcher.start()

        # create a FakeConsole parser
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString(r"""<configuration/>""")
        with logging_disabled():
            from b3.fake import FakeConsole
            self.console = FakeConsole(self.parser_conf)

        # load the admin plugin
        if B3version(b3_version) >= B3version("1.10dev"):
            admin_plugin_conf_file = '@b3/conf/plugin_admin.ini'
        else:
            admin_plugin_conf_file = '@b3/conf/plugin_admin.xml'

        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, admin_plugin_conf_file)
            self.adminPlugin._commands = {}
            self.adminPlugin.onStartup()

        # make sure the admin plugin obtained by other plugins is our admin plugin
        when(self.console).getPlugin('admin').thenReturn(self.adminPlugin)

        # patch the location plugin for the automated tests
        patch_location_plugin()

        self.console.screen = Mock()
        self.console.time = time.time
        self.console.upTime = Mock(return_value=3)
        self.console.cron.stop()

    def tearDown(self):
        self.sleep_patcher.stop()