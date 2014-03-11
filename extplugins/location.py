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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

__author__ = 'Fenix'
__version__ = '1.7'

import b3
import b3.plugin
import b3.events
import json
import math

from urllib2 import urlopen
from urllib2 import URLError
from ConfigParser import NoOptionError


class LocationPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None

    _announce = True
    _verbose = True

    ####################################################################################################################
    ##                                                                                                                ##
    ##   STARTUP                                                                                                      ##
    ##                                                                                                                ##
    ####################################################################################################################

    def __init__(self, console, config=None):
        """
        Build the plugin object
        """
        b3.plugin.Plugin.__init__(self, console, config)

        # get the admin plugin
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            self.critical('could not start without admin plugin')
            raise SystemExit(220)

        self._default_messages = dict(
            connect='''^7$client ^3from ^7$country ^3connected''',
            connect_city='''^7$client ^3from ^7$city ^3(^7$country^3) connected''',
            locate='''^7$client ^3is connected from ^7$country''',
            locate_city='''^7$client ^3is connected from ^7$city ^3(^7$country^3)''',
            locate_failed='''^7Could not locate ^1$client''',
            distance='''^7$client ^3is ^7$distance ^3km away from you''',
            distance_self='''^7Sorry, I'm not that smart...meh!''',
            distance_failed='''^7Could not compute distance with ^1$client''',
        )

    def onLoadConfig(self):
        """\
        Load plugin configuration
        """
        try:
            self._announce = self.config.getboolean('settings', 'announce')
            self.debug('loaded announce setting: %s' % self._verbose)
        except NoOptionError:
            self.warning('could not find settings/announce in config file, using default: %s' % self._announce)
        except ValueError, e:
            self.error('could not load settings/announce config value: %s' % e)
            self.debug('using default value (%s) for settings/announce' % self._announce)

        try:
            self._verbose = self.config.getboolean('settings', 'verbose')
            self.debug('loaded verbose setting: %s' % self._verbose)
        except NoOptionError:
            self.warning('could not find settings/verbose in config file, using default: %s' % self._verbose)
        except ValueError, e:
            self.error('could not load settings/verbose config value: %s' % e)
            self.debug('using default value (%s) for settings/verbose' % self._verbose)

    def onStartup(self):
        """
        Initialize plugin settings
        """
        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2: 
                    cmd, alias = sp

                func = self.getCmd(cmd)
                if func: 
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)
        
        # register the events needed
        self.registerEvent(self.console.getEventID('EVT_CLIENT_CONNECT'), self.onConnect)

        # notice plugin started
        self.debug('plugin started')

    def onEnable(self):
        """\
        Executed when the plugin is enabled
        """
        for c in self.console.clients.getList():
            if not c.isvar(self, 'location'):
                loc = self.getLocationData(c)
                if loc:
                    c.setvar(self, 'location', loc)

    ####################################################################################################################
    ##                                                                                                                ##
    ##   EVENTS                                                                                                       ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onConnect(self, event):
        """
        Handle EVT_CLIENT_CONNECT
        """
        client = event.client
        # if we already have location data
        # for this client, don't bother
        if client.isvar(self, 'location'):
            return

        # retrieve geolocation data
        loc = self.getLocationData(client)

        if not loc:
            # if we didn't manage to retrieve
            # geolocation info just exit here
            return

        # store data in the client object so we do
        # not have to query the API on every request
        client.setvar(self, 'location', loc)

        # if we have to announce and we got a valid response
        # from the API, print location info in the game chat
        if self._announce and self.console.upTime() > 300:

            if self._verbose and 'city' in loc:
                # if we got a proper city and we are supposed to display a verbose message
                message = self.getMessage('connect_city', {'client': client.name,
                                                           'city': loc['city'],
                                                           'country': loc['country']})
            else:
                # just display basic geolocation info
                message = self.getMessage('connect', {'client': client.name, 'country': loc['country']})

            self.console.say(message)

    ####################################################################################################################
    ##                                                                                                                ##
    ##   FUNCTIONS                                                                                                    ##
    ##                                                                                                                ##
    ####################################################################################################################

    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
        return None    

    def getLocationData(self, client):
        """
        Retrieve location data from the API
        """
        try:
            # will retrieve necessary data from the API and perform some checks on it
            self.debug("contacting http://ip-api.com to retrieve location data for %s..." % client.name)
            data = json.load(urlopen('http://ip-api.com/json/%s' % client.ip))
        except URLError, e:
            self.warning("could not connect to http://ip-api.com: %s" % e)
            return None
            
        if data['status'] == 'fail':
            self.debug('could not retrieve valid geolocation info using ip %s: %s' % (client.ip, data['message']))
            return None
        
        if 'country' not in data:
            self.debug('could not establish in which country is ip %s' % client.ip)
            return None

        self.debug("retrieved location data for %s: %r" % (client.name, data))
        return data

    def getLocationDistance(self, cl1, cl2):
        """
        Return the distance between 2 clients (in Km)
        """
        if not cl1.isvar(self, 'location'):
            self.debug('could not compute distance: %s has no location data' % cl1.name)
            return False
        
        if not cl2.isvar(self, 'location'):
            self.debug('could not compute distance: %s has no location data' % cl2.name)
            return False

        loc1 = cl1.var(self, 'location').value
        loc2 = cl2.var(self, 'location').value
        
        if not 'lat' in loc1 or not 'lon' in loc1:
            self.debug('could not compute distance: %s does not have enough location parameters: %r' % (cl1.name, loc1))
            return False
           
        if not 'lat' in loc2 or not 'lon' in loc2:
            self.debug('could not compute distance: %s does not have enough location parameters: %r' % (cl2.name, loc2))
            return False
        
        # print some verbose logging just for testing purpose
        self.verbose('computing distance between %s and %s' % (cl1.name, cl2.name))
        
        lat1 = float(loc1['lat'])
        lat2 = float(loc2['lat'])
        lon1 = float(loc1['lon'])
        lon2 = float(loc2['lon'])
        
        ###
        # Haversine formula
        ###
        
        radius = 6371  # Earth radius in Km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        
        b = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return round(abs(radius * b), 2)

    ####################################################################################################################
    ##                                                                                                                ##
    ##   COMMANDS                                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    def cmd_locate(self, data, client, cmd=None):
        """\
        <client> - Display geolocation info of the specified client
        """
        if not data: 
            client.message('^7Invalid data, try ^3!^7help locate')
            return
        
        cl = self._adminPlugin.findClientPrompt(data, client)
        if not cl:
            return

        if not cl.isvar(self, 'location'):
            cmd.sayLoudOrPM(client, self.getMessage('locate_failed', {'client': cl.name}))
            return 
        
        # get the client location data
        loc = cl.var(self, 'location').value

        if self._verbose and 'city' in loc:
            # if we got a proper city and we are supposed to display a verbose message
            msg = self.getMessage('locate_city', {'client': cl.name, 'city': loc['city'], 'country': loc['country']})
        else:
            # just display basic geolocation info
            msg = self.getMessage('locate', {'client': cl.name, 'country': loc['country']})

        cmd.sayLoudOrPM(client, msg)

    def cmd_distance(self, data, client, cmd=None):
        """\
        <client> - Display the world distance between you and the given client
        """
        if not data: 
            client.message('^7Invalid data, try ^3!^7help distance')
            return
        
        cl = self._adminPlugin.findClientPrompt(data, client)
        if not cl:
            return
        
        if cl == client:
            cmd.sayLoudOrPM(client, self.getMessage('distance_self'))
            return
        
        # compute the distance between the given clients
        # this will return false in case we have data inconsistency
        distance = self.getLocationDistance(client, cl)
        if not distance:
            cmd.sayLoudOrPM(client, self.getMessage('distance_failed', {'client': cl.name}))
            return

        cmd.sayLoudOrPM(client, self.getMessage('distance', {'client': cl.name, 'distance': distance}))