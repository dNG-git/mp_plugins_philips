# -*- coding: utf-8 -*-
##j## BOF

"""
dNG.pas.plugins.mp.tpvision_ambilight_control
"""
"""n// NOTE
----------------------------------------------------------------------------
MediaProvider
A device centric multimedia solution
----------------------------------------------------------------------------
(C) direct Netware Group - All rights reserved
http://www.direct-netware.de/redirect.py?mp;plugins_tpvision

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
http://www.direct-netware.de/redirect.py?licenses;gpl
----------------------------------------------------------------------------
#echo(mpPluginsTpVisionVersion)#
#echo(__FILEPATH__)#
----------------------------------------------------------------------------
NOTE_END //n"""

# pylint: disable=import-error,no-name-in-module,unused-argument

try: from urllib.parse import urlsplit
except ImportError: from urlparse import urlsplit

from dNG.pas.data.settings import Settings
from dNG.pas.data.logging.log_line import LogLine
from dNG.pas.data.tasks.memory import Memory as MemoryTasks
from dNG.pas.module.named_loader import NamedLoader
from dNG.pas.plugins.hooks import Hooks
from dNG.pas.runtime.instance_lock import InstanceLock
from dNG.pas.tasks.mp.tpvision_ambilight_control import TpvisionAmbilightControl

_lock = InstanceLock()
"""
Thread safety lock
"""

def plugin_control_point_device_add(params, last_return):
#
	"""
Called for "dNG.pas.upnp.ControlPoint.deviceAdd"

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:return: (mixed) Return value
:since:  v0.1.00
	"""

	# global: _lock, _STATUS_CHANGE_SLEEP_TIME, _STATUS_INITIAL_RETRIES_MAX
	_return = False

	identifier = params['identifier']
	upnp_control_point = NamedLoader.get_singleton("dNG.pas.net.upnp.ControlPoint")

	upnp_device = (upnp_control_point.rootdevice_get(identifier) if (upnp_control_point.rootdevice_is_known(device = identifier['device'])) else None)
	has_ambilight = (True if (upnp_device != None and upnp_device.get_manufacturer() == "Philips" and upnp_device.get_udn().startswith("F00DBABE-")) else False)

	if (has_ambilight):
	#
		url_data = urlsplit(identifier['url_base'])
		tid = (None if (url_data.hostname == None) else "dNG.pas.plugins.mp.tpvision_ambilight_control.{0}".format(url_data.hostname))

		memory_tasks = MemoryTasks.get_instance()

		if (tid != None and (not memory_tasks.is_registered(tid))):
		#
			# Task could be registered in another thread so check again
			with _lock:
			#
				if (not memory_tasks.is_registered(tid)):
				#
					LogLine.info("mp.plugins.tpvision_ambilight_control found a Philips TV at '{0}'".format(url_data.hostname))
					memory_tasks.task_add(tid, TpvisionAmbilightControl(tid, "http://{0}:1925".format(url_data.hostname)), 0)
				#
			#

			_return = True
		#
	#

	return _return
#

def plugin_control_point_device_remove(params, last_return):
#
	"""
Called for "dNG.pas.upnp.ControlPoint.deviceRemove"

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:return: (mixed) Return value
:since:  v0.1.00
	"""

	_return = False

	identifier = params['identifier']
	upnp_control_point = NamedLoader.get_singleton("dNG.pas.net.upnp.ControlPoint")

	upnp_device = (upnp_control_point.rootdevice_get(identifier) if (upnp_control_point.rootdevice_is_known(device = identifier['device'])) else None)
	has_ambilight = (True if (upnp_device != None and upnp_device.get_manufacturer() == "Philips" and upnp_device.get_udn().startswith("F00DBABE-")) else False)

	if (has_ambilight):
	#
		url_data = urlsplit(identifier['url_base'])
		tid = (None if (url_data.hostname == None) else "dNG.pas.plugins.mp.tpvision_ambilight_control.{0}".format(url_data.hostname))

		if (tid != None and MemoryTasks.get_instance().task_remove(tid)):
		#
			LogLine.info("mp.plugins.tpvision_ambilight_control lost a Philips TV at '{0}'".format(url_data.hostname))
			_return = True
		#
	#

	return _return
#

def plugin_deregistration():
#
	"""
Unregister plugin hooks.

:since: v0.1.00
	"""

	Hooks.unregister("dNG.pas.upnp.ControlPoint.deviceAdd", plugin_control_point_device_add)
	Hooks.unregister("dNG.pas.upnp.ControlPoint.deviceRemove", plugin_control_point_device_remove)
#

def plugin_registration():
#
	"""
Register plugin hooks.

:since: v0.1.00
	"""

	Settings.read_file("{0}/settings/mp/plugins/tpvision_ambilight_control.json".format(Settings.get("path_data")))

	Hooks.register("dNG.pas.upnp.ControlPoint.deviceAdd", plugin_control_point_device_add)
	Hooks.register("dNG.pas.upnp.ControlPoint.deviceRemove", plugin_control_point_device_remove)
#

##j## EOF