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

from mockito import when, any as ANY
from b3.config import CfgConfigParser
from textwrap import dedent
from tests import LocationTestCase
from tests import FAKE_LOCATION_DATA
from tests import logging_disabled
from location import LocationPlugin
from location import IpApiLocator
from location import TelizeLocator


class Test_commands(LocationTestCase):

    def setUp(self):
        LocationTestCase.setUp(self)

        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent(r"""
            [settings]
            announce: yes
            verbose: yes

            [messages]
            connect: ^7$client ^3from ^7$country ^3connected
            connect_city: ^7$client ^3from ^7$city ^3(^7$country^3) connected
            locate: ^7$client ^3is connected from ^7$country
            locate_city: ^7$client ^3is connected from ^7$city ^3(^7$country^3)
            locate_failed: ^7Could not locate ^1$client
            distance: ^7$client ^3is ^7$distance ^3km away from you
            distance_self: ^7Sorry, I'm not that smart...meh!
            distance_failed: ^7Could not compute distance with ^1$client
            isp: ^7$client ^3is using ^7$isp ^3as isp
            isp_failed: ^7Could not retrieve ^1$client ^7isp

            [commands]
            locate: user
            distance: user
            isp: mod
        """))

        self.p = LocationPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        when(IpApiLocator).getLocationData(ANY()).thenReturn(FAKE_LOCATION_DATA)
        when(TelizeLocator).getLocationData(ANY()).thenReturn(FAKE_LOCATION_DATA)

        with logging_disabled():
            from b3.fake import FakeClient

        # create 2 fake clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", groupBits=16)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", groupBits=16)

        # connect the clients
        self.mike.connects("1")
        self.bill.connects("2")

    def tearDown(self):
        LocationTestCase.tearDown(self)

    ####################################################################################################################
    ##                                                                                                                ##
    ##  TEST CMD LOCATE                                                                                               ##
    ##                                                                                                                ##
    ####################################################################################################################

    def test_cmd_locate_no_arguments(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!locate")
        # THEN
        self.assertListEqual(['missing data, try !help locate'], self.mike.message_history)

    def test_cmd_locate(self):
        # GIVEN
        self.p._settings['verbose'] = False
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!locate bill")
        # THEN
        self.assertListEqual(['Bill is connected from Italy'], self.mike.message_history)

    def test_cmd_locate_verbose(self):
        # GIVEN
        self.p._settings['verbose'] = True
        # WHEN
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!locate bill")
        # THEN
        self.assertListEqual(['Bill is connected from Rome (Italy)'], self.mike.message_history)

    ####################################################################################################################
    ##                                                                                                                ##
    ##  TEST CMD DISTANCE                                                                                             ##
    ##                                                                                                                ##
    ####################################################################################################################

    def test_cmd_distance_no_arguments(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!distance")
        # THEN
        self.assertListEqual(['missing data, try !help distance'], self.mike.message_history)

    def test_cmd_distance_self(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!distance mike")
        # THEN
        self.assertListEqual(['Sorry, I\'m not that smart...meh!'], self.mike.message_history)

    def test_cmd_distance(self):
        # GIVEN
        when(self.p).getLocationDistance(ANY(), ANY()).thenReturn(8623.52)
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!distance bill")
        # THEN
        self.assertListEqual(['Bill is 8623.52 km away from you'], self.mike.message_history)

    ####################################################################################################################
    ##                                                                                                                ##
    ##  TEST CMD ISP                                                                                                  ##
    ##                                                                                                                ##
    ####################################################################################################################

    def test_cmd_isp_no_arguments(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!isp")
        # THEN
        self.assertListEqual(['missing data, try !help isp'], self.mike.message_history)

    def test_cmd_isp(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!isp bill")
        # THEN
        self.assertListEqual(['Bill is using Fastweb as isp'], self.mike.message_history)