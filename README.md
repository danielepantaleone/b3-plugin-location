Location Plugin for BigBrotherBot
=================================

## Description

This plugin adds geolocation capability to the Big Brother Bot.<br />
It retrieves geolocation data for every client using http://ip-api.com/ API system.

* *NOTE #1*: since version 1.5 this plugin works only with b3 1.10-dev or higher: http://files.cucurb.net/b3/daily/
* *NOTE #2*: this plugin works differently from the CountryFilter Plugin (by courgette) since it doesn't have filtering capabilities but it provides only geolocation information.

## How to install

### Installing the plugin

* Copy **location.py** into **b3/extplugins**
* Copy **plugin_location.ini** into **b3/extplugins/conf**
* Load the plugin in your **b3.xml** configuration file

## In-game user guide

* **!locate [client]** *Display geolocation info of the specified client*
* **!distance [client]** *Display the world distance between you and the given client*

## Support

For support regarding this very plugin you can find me on IRC on **#urbanterror / #goreclan** @ **Quakenet**<br>
For support regarding Big Brother Bot you may ask for help on the official website: http://www.bigbrotherbot.net
