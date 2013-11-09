#
# Location Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Fenix <fenix@urbanterror.info)
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

__author__ = 'Fenix - http://www.urbanterror.info'
__version__ = '1.2'

import b3
import b3.plugin
import b3.events
import urllib2
import json
import math


class LocationPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None
    _announce = True
      
    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        self.verbose('Loading configuration file...')
        
        try:
            self._announce = self.config.getboolean('settings', 'announce')
            self.debug('loaded announce setting: %r' % self._announce)
        except Exception, e:
            self.error('could not load announce setting: %s' % e)
            self.debug('using default value for announce: %r' % self._announce)

    def onStartup(self):
        """
        Initialize plugin settings
        """
        # get the admin plugin
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:    
            self.error('Could not find admin plugin')
            return False
        
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
        self.registerEvent(b3.events.EVT_CLIENT_CONNECT)

    # ######################################################################################### #
    # ##################################### HANDLE EVENTS ##################################### #        
    # ######################################################################################### #    

    def onEvent(self, event):
        """
        Handle intercepted events
        """
        if event.type == b3.events.EVT_CLIENT_CONNECT:
            self.onConnect(event.client)

    # ######################################################################################### #
    # ####################################### FUNCTIONS ####################################### #        
    # ######################################################################################### # 

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
            data = json.load(urllib2.urlopen('http://ip-api.com/json/%s' % client.ip))
        
        except urllib2.URLError, e:
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

        location1 = cl1.var(self, 'location').value
        location2 = cl2.var(self, 'location').value
        
        if not 'lat' in location1 or not 'lon' in location1:
            self.debug('could not compute distance: %s has no enough location parameters: %r' % (cl1.name, location1))
            return False
           
        if not 'lat' in location2 or not 'lon' in location2:
            self.debug('could not compute distance: %s has no enough location parameters: %r' % (cl2.name, location2))
            return False
        
        # print some verbose logging just for testing purpose
        self.verbose('computing distance between %s and %s' % (cl1.name, cl2.name))
        
        lat1 = float(location1['lat'])
        lat2 = float(location2['lat'])
        lon1 = float(location1['lon'])
        lon2 = float(location2['lon'])
        
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

    def onConnect(self, client):
        """
        Handle EVT_CLIENT_CONNECT
        """
        # if we already have location data
        # for this client, don't bother
        if client.isvar(self, 'location'):
            return

        loc = self.getLocationData(client)
        
        if not loc:
            
            if self._announce and self.console.upTime() > 300:
                # since we have to announce a connection inform that
                # a guy from an unknown location connected to the server
                self.console.say('^7%s ^3from ^7-- ^3connected' % client.name)
            
            return

        # trim off whitespaces since api sometime
        # returns data without trimming them
        loc['country'] = loc['country'].strip()
        if 'city' in loc:
            loc['city'] = loc['city'].strip()

        # store data in the client object so we do
        # not have to query the API on every request
        client.setvar(self, 'location', loc)
        
        # if we have to announce and we got a valid response
        # from the API, print location info in the game chat        
        if self._announce and self.console.upTime() > 300:

            message = '^7%s ^3from ^7%s ^3connected' % (client.name, loc['country'])
            if 'city' in loc:
                # if we got a city overwrite previously generated message with a more detailed one
                message = '^7%s ^3from ^7%s ^3(^7%s^3) connected' % (client.name, loc['city'], loc['country'])
                
            self.console.say(message)

    # ######################################################################################### #
    # ######################################## COMMANDS ####################################### #        
    # ######################################################################################### # 

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
            cmd.sayLoudOrPM(client, '^7Could not locate ^1%s' % cl.name)
            return 
        
        # get the client location data
        loc = cl.var(self, 'location').value
        
        message = '^7%s ^3is connected from ^7%s' % (cl.name, loc['country'])
        if 'city' in loc:
            # if we got a city overwrite previously generated message with a more detailed one
            message = '^7%s ^3is connected from ^7%s ^3(^7%s^3)' % (cl.name, loc['city'], loc['country'])
        
        cmd.sayLoudOrPM(client, message)
        
        if 'isp' in loc:
            # sisplay also the ISP of the client if we got a valid entry
            cmd.sayLoudOrPM(client, '^3He\'s currently using ^7%s ^3as ISP' % loc['isp'])
    
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
            cmd.sayLoudOrPM(client, '^7Sorry, I\'m not that smart...meh!')
            return
        
        # compute the distance between the given clients
        # this will return false in case we have data inconsistency
        distance = self.getLocationDistance(client, cl)
        if not distance:
            cmd.sayLoudOrPM(client, '^7Could not compute distance with ^1%s' % cl.name)
            return
        
        cmd.sayLoudOrPM(client, '^7%s ^3is ^7%.2f ^3km away from you' % (cl.name, distance))
