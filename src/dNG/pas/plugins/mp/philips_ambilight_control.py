# -*- coding: utf-8 -*-
##j## BOF

"""
MediaProvider
A device centric multimedia solution
----------------------------------------------------------------------------
(C) direct Netware Group - All rights reserved
https://www.direct-netware.de/redirect?mp;plugins_philips

The following license agreement remains valid unless any additions or
changes are being made by direct Netware Group in a written form.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc.,
59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
----------------------------------------------------------------------------
https://www.direct-netware.de/redirect?licenses;gpl
----------------------------------------------------------------------------
#echo(mpPluginsPhilipsVersion)#
#echo(__FILEPATH__)#
"""

# pylint: disable=import-error,no-name-in-module,unused-argument

try: from urllib.parse import urlsplit
except ImportError: from urlparse import urlsplit

from dNG.pas.data.settings import Settings
from dNG.pas.data.logging.log_line import LogLine
from dNG.pas.data.tasks.memory import Memory as MemoryTasks
from dNG.pas.net.upnp.control_point import ControlPoint
from dNG.pas.plugins.hook import Hook
from dNG.pas.runtime.instance_lock import InstanceLock
from dNG.pas.tasks.mp.philips_ambilight_control import PhilipsAmbilightControl

_lock = InstanceLock()
"""
Thread safety lock
"""

def on_device_added(params, last_return = None):
#
	"""
Called for "dNG.pas.upnp.ControlPoint.onDeviceAdded"

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:return: (mixed) Return value
:since:  v0.1.00
	"""

	# global: _lock
	_return = False

	identifier = params['identifier']
	upnp_control_point = ControlPoint.get_instance()

	upnp_device = (upnp_control_point.get_rootdevice(identifier) if (upnp_control_point.is_rootdevice_known(device = identifier['device'])) else None)
	has_ambilight = (True if (upnp_device is not None and upnp_device.get_manufacturer() == "Philips" and upnp_device.get_udn().startswith("F00DBABE-")) else False)

	if (has_ambilight):
	#
		url_data = urlsplit(identifier['url_base'])
		tid = (None if (url_data.hostname is None) else "dNG.pas.plugins.mp.philips_ambilight_control.{0}".format(url_data.hostname))

		memory_tasks = MemoryTasks.get_instance()

		if (tid is not None and (not memory_tasks.is_registered(tid))):
		# Thread safety
			with _lock:
			#
				if (not memory_tasks.is_registered(tid)):
				#
					LogLine.info("mp.plugins.philips_ambilight_control found a Philips TV at '{0}'", url_data.hostname, context = "mp_plugins_philips_ambilight_control")
					memory_tasks.add(tid, PhilipsAmbilightControl(tid, "http://{0}:1925".format(url_data.hostname)), 0)
				#
			#

			_return = True
		#
	#

	return _return
#

def on_device_removed(params, last_return = None):
#
	"""
Called for "dNG.pas.upnp.ControlPoint.onDeviceRemoved"

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:return: (mixed) Return value
:since:  v0.1.00
	"""

	_return = False

	identifier = params['identifier']
	upnp_control_point = ControlPoint.get_instance()

	upnp_device = (upnp_control_point.get_rootdevice(identifier) if (upnp_control_point.is_rootdevice_known(device = identifier['device'])) else None)
	has_ambilight = (True if (upnp_device is not None and upnp_device.get_manufacturer() == "Philips" and upnp_device.get_udn().startswith("F00DBABE-")) else False)

	if (has_ambilight):
	#
		url_data = urlsplit(identifier['url_base'])
		tid = (None if (url_data.hostname is None) else "dNG.pas.plugins.mp.philips_ambilight_control.{0}".format(url_data.hostname))

		if (tid is not None and MemoryTasks.get_instance().remove(tid)):
		#
			LogLine.info("mp.plugins.philips_ambilight_control lost a Philips TV at '{0}'", url_data.hostname, context = "mp_plugins_philips_ambilight_control")
			_return = True
		#
	#

	return _return
#

def register_plugin():
#
	"""
Register plugin hooks.

:since: v0.1.00
	"""

	if (Settings.read_file("{0}/settings/mp/plugins/philips_ambilight_control.json".format(Settings.get("path_data")))):
	#
		Hook.register("dNG.pas.upnp.ControlPoint.onDeviceAdded", on_device_added)
		Hook.register("dNG.pas.upnp.ControlPoint.onDeviceRemoved", on_device_removed)
	#
#

def unregister_plugin():
#
	"""
Unregister plugin hooks.

:since: v0.1.00
	"""

	Hook.unregister("dNG.pas.upnp.ControlPoint.onDeviceAdded", on_device_added)
	Hook.unregister("dNG.pas.upnp.ControlPoint.onDeviceRemoved", on_device_removed)
#

##j## EOF