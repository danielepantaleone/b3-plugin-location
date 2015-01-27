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

__author__ = 'Fenix'
__version__ = '1.15'

import b3
import b3.plugin
import b3.events
import math
import unicodedata as ud

from ConfigParser import NoOptionError
from threading import Thread
from .requests.exceptions import RequestException
from . import requests

try:
    # import the getCmd function
    import b3.functions.getCmd as getCmd
except ImportError:
    # keep backward compatibility
    def getCmd(instance, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(instance, cmd):
            func = getattr(instance, cmd)
            return func
        return None


class Locator(object):

    _timeout = 5

    @classmethod
    def getLocationData(cls, client):
        """
        Retrieve location data
        :param client: The client geolocalize
        :raise RequestException: When we are not able to retrieve location information
        :return: A dict with location information
        """
        raise NotImplementedError

    @classmethod
    def normalize(cls, data):
        """
        Normalize returned data
        :param data: A dict with location data
        :return: A dict with location data normalized (printable in game chat/console)
        """
        # do not use dict comprehension syntax for python 2.6 compatibility
        return dict((k, ud.normalize('NFKD', unicode(v)).encode('ascii','ignore').strip()) for (k, v) in data.items())


class IpApiLocator(Locator):

    _url = 'http://ip-api.com/json/%s'

    @classmethod
    def getLocationData(cls, client):
        """
        Retrieve location data
        :param client: The client geolocalize
        :raise RequestException: When we are not able to retrieve location information
        :raise AttributeError: When returned data doesn't contain necessary information
        :return: A dict with location information
        """
        data = requests.get(cls._url % client.ip, timeout=cls._timeout).json()

        if data['status'] == 'fail':
            raise RequestException('invalid data returned by the api: %r' % data)

        if 'country' not in data:
            raise AttributeError('could not establish in which country is ip %s' % client.ip)

        return cls.normalize(data)


class TelizeLocator(Locator):

    _url = 'http://www.telize.com/geoip/%s'

    @classmethod
    def getLocationData(cls, client):
        """
        Retrieve location data
        :param client: The client geolocalize
        :raise RequestException: When we are not able to retrieve location information
        :raise AttributeError: When returned data doesn't contain necessary information
        :return: A dict with location information
        """
        data = requests.get(cls._url % client.ip, timeout=cls._timeout).json()

        if 'code' in data and int(data['code']) == 401:
            raise RequestException('input string is not a valid ip address: %s' % client.ip)

        if 'country' not in data:
            raise AttributeError('could not establish in which country is ip %s' % client.ip)

        return cls.normalize(data)


class LocationPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None

    _locators = frozenset([IpApiLocator, TelizeLocator])

    _settings = {
        'announce': True,
        'verbose': True
    }

    ####################################################################################################################
    ##                                                                                                                ##
    ##   STARTUP                                                                                                      ##
    ##                                                                                                                ##
    ####################################################################################################################

    def __init__(self, console, config=None):
        """
        Build the plugin object.
        """
        b3.plugin.Plugin.__init__(self, console, config)

        # get the admin plugin
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            self.critical('could not start without admin plugin')
            raise SystemExit(220)

        self._default_messages = {
            'connect': "^7$client ^3from ^7$country ^3connected",
            'connect_city': "^7$client ^3from ^7$city ^3(^7$country^3) connected",
            'locate': "^7$client ^3is connected from ^7$country",
            'locate_city': "^7$client ^3is connected from ^7$city ^3(^7$country^3)",
            'locate_failed': "^7Could not locate ^1$client",
            'distance': "^7$client ^3is ^7$distance ^3km away from you",
            'distance_self': "^7Sorry, I'm not that smart...meh!",
            'distance_failed': "^7Could not compute distance with ^1$client",
            'isp': "^7$client ^3is using ^7$isp ^3as isp",
            'isp_failed': "^7Could not retrieve ^1$client ^7isp",
        }

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        try:
            self._settings['announce'] = self.config.getboolean('settings', 'announce')
            self.debug('loaded announce setting: %s' % self._settings['announce'])
        except NoOptionError:
            self.warning('could not find settings/announce in config file, using default: %s' % self._settings['announce'])
        except ValueError, e:
            self.error('could not load settings/announce config value: %s' % e)
            self.debug('using default value (%s) for settings/announce' % self._settings['announce'])

        try:
            self._settings['verbose'] = self.config.getboolean('settings', 'verbose')
            self.debug('loaded verbose setting: %s' % self._settings['verbose'])
        except NoOptionError:
            self.warning('could not find settings/verbose in config file, using default: %s' % self._settings['verbose'])
        except ValueError, e:
            self.error('could not load settings/verbose config value: %s' % e)
            self.debug('using default value (%s) for settings/verbose' % self._settings['verbose'])

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

                func = getCmd(self, cmd)
                if func: 
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        try:
            # register the events needed using the new event dispatch system
            self.registerEvent(self.console.getEventID('EVT_CLIENT_CONNECT'), self.onConnect)
        except TypeError:
            # keep backwards compatibility
            self.registerEvent(self.console.getEventID('EVT_CLIENT_CONNECT'))

        # notice plugin started
        self.debug('plugin started')

    def onEnable(self):
        """
        Executed when the plugin is enabled.
        """
        def _threaded_get_location_data(client):

            for c in self._locators:

                try:
                    self.debug('retrieving location data for %s: %s' % (client.name, c._url % client.ip))
                    data = c.getLocationData(client)
                    self.debug("retrieved location data for %s: %r" % (client.name, data))
                    client.setvar(self, 'location', data)
                    return
                except Exception, e:
                    self.warning('could not retrieve location data for %s using %s: %s' % (client.name, c._url % client.ip, e))

        for cl in self.console.clients.getList():
            if not cl.isvar(self, 'location'):
                t = Thread(target=_threaded_get_location_data, args=(cl, ))
                t.daemon = True  # won't prevent B3 from exiting
                t.start()

    ####################################################################################################################
    ##                                                                                                                ##
    ##   EVENTS                                                                                                       ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onEvent(self, event):
        """
        Old event dispatch system
        """
        if event.type == self.console.getEventID('EVT_CLIENT_CONNECT'):
            self.onConnect(event)

    def onConnect(self, event):
        """
        Handle EVT_CLIENT_CONNECT
        """
        def _threaded_on_connect(client):

            data = None

            for c in self._locators:

                try:
                    self.debug('retrieving location data for %s: %s' % (client.name, c._url % client.ip))
                    data = c.getLocationData(client)
                    self.debug("retrieved location data for %s: %r" % (client.name, data))
                    break # stop iterating if we collect valid data
                except Exception, e:
                    self.warning('could not retrieve location data for %s using %s: %s' % (client.name, c._url % client.ip, e))
                    data = None

            if data:
                client.setvar(self, 'location', data)
                if self._settings['announce'] and self.console.upTime() > 300:
                    if self._settings['verbose'] and 'city' in data:
                        message = self.getMessage('connect_city', {'client': client.name, 'city': data['city'], 'country': data['country']})
                    else:
                        message = self.getMessage('connect', {'client': client.name, 'country': data['country']})
                    self.console.say(message)

        if not event.client.isvar(self, 'location'):
            # handling the event in a thread so B3 can pass that event to other plugins right away
            t = Thread(target=_threaded_on_connect, args=(event.client, ))
            t.daemon = True  # won't prevent B3 from exiting
            t.start()

    ####################################################################################################################
    ##                                                                                                                ##
    ##   FUNCTIONS                                                                                                    ##
    ##                                                                                                                ##
    ####################################################################################################################

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
        """
        <client> - display geolocation info of the specified client
        """
        if not data: 
            client.message('^7missing data, try ^3!^7help locate')
            return
        
        cl = self._adminPlugin.findClientPrompt(data, client)
        if not cl:
            return

        if not cl.isvar(self, 'location'):
            cmd.sayLoudOrPM(client, self.getMessage('locate_failed', {'client': cl.name}))
            return 

        l = cl.var(self, 'location').value

        if self._settings['verbose'] and 'city' in l:
            msg = self.getMessage('locate_city', {'client': cl.name, 'city': l['city'], 'country': l['country']})
        else:
            msg = self.getMessage('locate', {'client': cl.name, 'country': l['country']})

        cmd.sayLoudOrPM(client, msg)

    def cmd_distance(self, data, client, cmd=None):
        """
        <client> - display the world distance between you and the given client
        """
        if not data: 
            client.message('^7missing data, try ^3!^7help distance')
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
        else:
            cmd.sayLoudOrPM(client, self.getMessage('distance', {'client': cl.name, 'distance': distance}))

    def cmd_isp(self, data, client, cmd=None):
        """
        <client> - display the isp the specified client is using
        """
        if not data:
            client.message('^7missing data, try ^3!^7help isp')
            return

        cl = self._adminPlugin.findClientPrompt(data, client)
        if not cl:
            return

        if not cl.isvar(self, 'location'):
            cmd.sayLoudOrPM(client, self.getMessage('isp_failed', {'client': cl.name}))
        else:
            l = cl.var(self, 'location').value
            cmd.sayLoudOrPM(client, self.getMessage('isp', {'client': cl.name, 'isp': l['isp']}))