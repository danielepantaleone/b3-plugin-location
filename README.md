Location Plugin for BigBrotherBot [![BigBrotherBot](http://i.imgur.com/7sljo4G.png)][B3]
=================================

Description
-----------
A [BigBrotherBot][B3] plugin which introduces some new commands useful to display clients geolocation information. The 
plugin can also be enabled to display a geowelcome message when a new player connects to the server.

Download
--------
Latest version available [here](https://github.com/danielepantaleone/b3-plugin-location/archive/master.zip).

Installation
------------
Drop the `location` directory into `b3/extplugins`.  
Load the plugin in your `b3.ini` or `b3.xml` configuration file:
```xml
<plugin>
    <plugin name="location" config="@b3/extplugins/location/conf/plugin_location.ini" />
</plugin>
```
```ini
[plugins]
location: @b3/extplugins/location/conf/plugin_location.ini
```

Commands Reference
------------------
* **!locate &lt;client&gt;** `display geolocation information of the specified client`
* **!distance &lt;client&gt;** `display the world distance between you and the given client`
* **!isp &lt;client&gt;** `display the isp the given client is using to connect to the internet`


Changelog
---------
### 2.0 - 2015/03/13 - Fenix
- rewrite the plugin from scratch and make it subplugin of the [Geolocation Plugin](https://github.com/danielepantaleone/b3-plugin-geolocation)

### 1.15 - 2015/01/27 - Fenix
- changed plugin to support multiple geolocation api
- moved plugin configuration folder inside plugin directory
- added new api support http://www.telize.com/

### 1.14 - 2014/09/12 - Fenix
- make sure to remove/replace unprintable characters from location information

### 1.13 - 2014/08/27 - Courgette
- handle EVT_CLIENT_CONNECT events in a thread to help unclogging the B3 event queue

### 1.12 - 2014/08/27 - Courgette
- set up a 5 seconds timeout when querying ip-api.com

Support
-------

If you have found a bug or have a suggestion for this plugin, please report it on the [B3 forums][Support].


[B3]: http://www.bigbrotherbot.net/ "BigBrotherBot (B3)"
[Support]: http://forum.bigbrotherbot.net/plugins-by-fenix/location-plugin "Support topic on the B3 forums"

[![Build Status](https://travis-ci.org/danielepantaleone/b3-plugin-location.svg?branch=master)](https://travis-ci.org/danielepantaleone/b3-plugin-location)
[![Code Health](https://landscape.io/github/danielepantaleone/b3-plugin-location/master/landscape.svg?style=flat)](https://landscape.io/github/danielepantaleone/b3-plugin-location/master)