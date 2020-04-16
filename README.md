This tool shows if one or multiple filters that you setup are enabled or disabled. Runs inside OBS custom browser docks or any modern web browser.

![Example image](https://www.lebaston100.de/data/lebcdn/git/obsfiltermonitor/example1.jpg)

### Requirements

- The [obs-websocket plugin](https://github.com/Palakis/obs-websocket/releases) (Version >= 4.7.0)

### Setup obs-websocket

- Download the installer and run it
- Start OBS, open the "Tools" menu and select "websocket server settings"
- Make sure that "Enable Websocket server" is checked, "Server Port" is 4444 and "Enable authentification" is unchecked

### Configuration

All configuration is done inside the monitor.html file by editing it with a normal text editor. You also only need this file to run everything, all the other files (and the icons folder) is just there for project management purposes.

By default it is configured with 4 example filter entrys which result in the image shown on the top of this readme. You can remove or add filters depending on what you need. Make sure there is no "," after the last entry before the "]". Just follow the format that is already there if you don't know how to use Javascript arrays and objects.

The following options are available for the main array beginning in line 10:
- "filtername" (required): This is the name of the filter itself. This name can be changed in obs and is displayed in the left list in the filter dialog.
- "sourceName" (required): This is the name of the source that the filter is on.
- "displayName" (optional): If this property is set, the page will show this custom text instead of the source name followed by the filter name
- "onColor" (optional): This is a custom color (in a css format) that is displayed for the filter symbol in the -on- state

(required) means that this property has to exist for it to work, (optional) means that you can use it, but don't have to have it present.

Other options that you can use/set:
- defaultOffColor (line 25): This is the css color for the -off- state
- defaultOffSymbol (line 27): This is the symbol that is overlayed over the defaultOffColor. Can be:
	- g_x_black (a black X)
	- g_x_white (a white X)
	- g_off_black (black "off" text)
	- g_off_white (white "off" text)
- fallbackOnColor (line 30): This is the css color that is used for the -on- state when no "onColor" is set

If you want to generate the css color codes, search google for "css color picker" and you will get a color picker. Just use the value displayed under "HEX" (please include the "#").


### Setup inside OBS

To create a custom dock that can be made part of the main OBS windows, follow these steps:
- Open OBS
- Open the "View" menu on the top and select "Docks" -> "Custom Browser Docks..."
- Under "Dock Name" enter any name for the new panel, i suggest something like "Filter Status"
- On the right side under "URL" enter the URL to the monitor.html file. For example if your file is inside "C:\obsFilterMonitor-master\monitor.html" then use exactly that.
- Click the "Apply" button. This should open the dock. You can drag that into the obs interface or place it wherever you want.
- That's it. If you changed something in the file you can use CTRL + R to reload the page.

### Advanced usage

If you know what you are doing you can create a firewall exception for the obs-websocket port and modify the ip address in line 47 to be able to run this on any device in the network.

### Help

You have trouble setting it up or found a bug, then join my [Discord Server](https://discord.gg/PCYQJwX)
