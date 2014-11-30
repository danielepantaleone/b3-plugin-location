Location Plugin for BigBrotherBot [![BigBrotherBot](http://i.imgur.com/7sljo4G.png)][B3]
=================================

Description
-----------

A [BigBrotherBot][B3] plugin which adds geolocation capabilities.

Download
--------

Latest version available [here](https://github.com/danielepantaleone/b3-plugin-location/archive/master.zip).

Installation
------------

* copy the `extplugins/location` directory into `b3/extplugins`
* copy the `plugin_location.ini` file in `b3/extplugins/conf`
* add to the `plugins` section of your `b3.xml` config file:

  ```xml
  <plugin name="location" config="@b3/extplugins/conf/plugin_location.ini" />
  ```

In-game user guide
------------------

* **!locate &lt;client&gt;** `display geolocation info of the specified client`
* **!distance &lt;client&gt;** `display the world distance between you and the given client`
* **!isp &lt;client&gt;** `display the isp the specified client is using`


Changelog
---------
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
