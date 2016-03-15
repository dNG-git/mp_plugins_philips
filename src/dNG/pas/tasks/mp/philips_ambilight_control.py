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

# pylint: disable=import-error,no-name-in-module

from time import localtime, sleep

try:
#
	from http.client import BadStatusLine
	from urllib.parse import urlsplit
#
except ImportError:
#
	from httplib import BadStatusLine
	from urlparse import urlsplit
#

from dNG.data.json_resource import JsonResource
from dNG.net.http.client import Client as HttpClient
from dNG.pas.data.binary import Binary
from dNG.pas.data.settings import Settings
from dNG.pas.data.logging.log_line import LogLine
from dNG.pas.data.tasks.memory import Memory as MemoryTasks
from dNG.pas.runtime.exception_log_trap import ExceptionLogTrap
from dNG.pas.runtime.io_exception import IOException
from dNG.pas.tasks.abstract_lrt_hook import AbstractLrtHook

class PhilipsAmbilightControl(AbstractLrtHook):
#
	"""
"PhilipsAmbilightControl" is a LRT hook because it waits an defined time
between state changes.

:author:     direct Netware Group
:copyright:  direct Netware Group - All rights reserved
:package:    mp
:subpackage: plugins_philips
:since:      v0.1.00
:license:    https://www.direct-netware.de/redirect?licenses;gpl
             GNU General Public License 2
	"""

	MENU_TOGGLE_MODES_MAX = 3
	"""
On some models (like 2k13) the jointSPACE API "AmbilightOnOff" has the
defined menu options instead of toggling between the on and off state.
	"""
	STATUS_CHANGE_RETRIES_MAX = 12
	"""
Retries are required to differentiate between unsupported and slow
stopping models. 2k13 for example shuts down slowly and logs an error.
	"""
	STATUS_CHANGE_RETRY_TIME = 45
	"""
Time in seconds to wait in menu mode for animations and changes to
complete.
	"""
	STATUS_CHANGE_SLEEP_TIME = 1.4
	"""
Time in seconds to wait in menu mode for animations and changes to
complete.
	"""
	STATUS_INITIAL_RETRIES_MAX = 27
	"""
Initial retries are used to differentiate between unsupported and slow
starting models.
	"""

	def __init__(self, tid, js_url):
	#
		"""
Constructor __init__(PhilipsAmbilightControl)

:since: v0.1.00
		"""

		AbstractLrtHook.__init__(self)

		self.js_url = js_url
		"""
jointSPACE base URL
		"""
		self.last_state = None
		"""
Last Ambilight state known
		"""
		self.retries = PhilipsAmbilightControl.STATUS_INITIAL_RETRIES_MAX
		"""
Initial retries for communication
		"""
		self.tid = tid
		"""
Task ID
		"""

		self.context_id = "dNG.pas.tasks.mp.PhilipsAmbilightControl"
	#

	def _change_state(self, state_new = True):
	#
		"""
Requests the TV to activate the internal Ambilight algorithm.

:param state_new: True to active Ambilight

:return: (bool) True on success
:since:  v0.1.00
		"""

		# pylint: disable=broad-except

		_return = False

		try:
		#
			if (self.is_active() == (not state_new)):
			#
				http_client = self._get_js_http_client("{0}/1/input/key".format(self.js_url))
				is_menu_mode = False
				menu_toggle_modes = PhilipsAmbilightControl.MENU_TOGGLE_MODES_MAX

				while (menu_toggle_modes > 0):
				#
					http_response = http_client.request_post(JsonResource().data_to_json({ "key": "AmbilightOnOff" }))
					if (is_menu_mode): sleep(PhilipsAmbilightControl.STATUS_CHANGE_SLEEP_TIME)

					if (not http_response.is_readable()): menu_toggle_modes = 0
					elif (self.is_active() == state_new):
					#
						menu_toggle_modes = 0
						_return = True
					#
					elif (is_menu_mode): menu_toggle_modes -= 1
					else:
					#
						sleep(PhilipsAmbilightControl.STATUS_CHANGE_SLEEP_TIME)

						if (self.is_active() == state_new):
						#
							menu_toggle_modes = 0
							_return = True
						#
						else:
						#
							is_menu_mode = True
							menu_toggle_modes -= 1
						#
					#
				#

				if (is_menu_mode and _return):
				#
					http_response = http_client.request_post(JsonResource().data_to_json({ "key": "Confirm" }))

					if (isinstance(http_response.get_exception(), BadStatusLine)):
					# See "self.is_active()"
						http_client = self._get_js_http_client("{0}/1/input/key".format(self.js_url))
						http_client.request_post(JsonResource().data_to_json({ "key": "Confirm" }))
					#
				#
			#
		#
		except Exception: pass

		return _return
	#

	def is_active(self):
	#
		"""
Returns the current Ambilight state.

:return: (bool) True if active; False if inactive; None on error
:since:  v0.1.00
		"""

		# pylint: disable=broad-except

		_return = None

		try:
		#
			http_client = self._get_js_http_client("{0}/1/ambilight/mode".format(self.js_url))
			http_response = http_client.request_get()

			json_response = (JsonResource().json_to_data(Binary.str(http_response.read()))
			                 if (http_response.is_readable()) else
			                 None
			                )

			if (json_response is not None and json_response.get("current") == "internal"):
			#
				http_client.set_url("{0}/1/ambilight/processed".format(self.js_url))
				http_response = http_client.request_get()

				if (isinstance(http_response.get_exception(), BadStatusLine)):
				#
					"""
Older jointSPACE servers do not accept the second request for keep-alive
connections.
					"""

					http_client = self._get_js_http_client("{0}/1/ambilight/processed".format(self.js_url))
					http_response = http_client.request_get()
				#

				json_response = (JsonResource().json_to_data(Binary.str(http_response.read()))
				                 if (http_response.is_readable()) else
				                 None
				                )

				if (json_response is None): LogLine.debug("#echo(__FILEPATH__)# -{0!r}.is_active({1})- reporting: Ambilight data not received", self, self.js_url, context = "mp_plugins_philips_ambilight_control")
			#

			if (json_response is not None):
			#
				_return = False

				for layer in json_response:
				#
					layer_data = json_response[layer]

					for position in layer_data:
					#
						led_data = layer_data[position]

						for led_position in led_data:
						#
							rgb_data = led_data[led_position]

							for key in rgb_data:
							#
								if (rgb_data[key] > 0):
								#
									_return = True
									break
								#
							#
						#
					#
				#
			#
		#
		except Exception: _return = None

		return _return
	#

	def _get_js_http_client(self, url):
	#
		"""
Returns a preconfigured jointSPACE HTTP client.

:param url: jointSPACE API URL endpoint

:return: (bool) True if active; False if inactive; None on error
:since:  v0.1.00
		"""

		_return = HttpClient(url)
		_return.set_header("Content-Type", "application/json")

		return _return
	#

	def _run_hook(self):
	#
		"""
Hook execution

:since: v0.1.00
		"""

		switch_on_hour = int(Settings.get("mp_plugins_philips_ambilight_control_switch_on_hour", 20))
		switch_off_hour = int(Settings.get("mp_plugins_philips_ambilight_control_switch_off_hour", 8))

		with ExceptionLogTrap("mp_plugins_philips_ambilight_control"):
		#
			ambilight_active = self.is_active()
			url_data = urlsplit(self.js_url)

			if (ambilight_active is None):
			#
				self.retries -= 1

				if (self.retries > 0): MemoryTasks.get_instance().add(self.tid, self, PhilipsAmbilightControl.STATUS_CHANGE_SLEEP_TIME)
				else: LogLine.info("mp.plugins.philips_ambilight_control removed a TV in an unsupported or faulty state at '{0}'", url_data.hostname, context = "mp_plugins_philips_ambilight_control")
			#
			else:
			#
				is_ambilight_glowing_requested = None
				time_current = localtime()

				if (self.last_state != False and ambilight_active and time_current.tm_hour >= switch_off_hour and time_current.tm_hour < switch_on_hour):
				#
					if (not self._change_state(False)): raise IOException("Failed to change Ambilight state")
					is_ambilight_glowing_requested = False
				#

				if (self.last_state != True and (not ambilight_active) and (time_current.tm_hour >= switch_on_hour or time_current.tm_hour < switch_off_hour)):
				#
					if (not self._change_state(True)): raise IOException("Failed to change Ambilight state")
					is_ambilight_glowing_requested = True
				#

				"""
Some models (like 2k12) change the Ambilight state to the last known value
after they have initialized and the jointSPACE server is up and responding.
				"""

				if (self.retries > PhilipsAmbilightControl.STATUS_CHANGE_RETRIES_MAX):
				#
					is_wake_up_mode = True
					self.retries -= 1
				#
				else: is_wake_up_mode = False

				if (is_ambilight_glowing_requested is None): is_ambilight_glowing = (self.is_active() if (self.last_state is None and (not is_wake_up_mode)) else self.last_state)
				else:
				#
					is_ambilight_glowing = is_ambilight_glowing_requested

					if (is_ambilight_glowing): LogLine.info("mp.plugins.philips_ambilight_control switched Ambilight on", context = "mp_plugins_philips_ambilight_control")
					else: LogLine.info("mp.plugins.philips_ambilight_control switched Ambilight off", context = "mp_plugins_philips_ambilight_control")
				#

				self.last_state = is_ambilight_glowing

				MemoryTasks.get_instance().add(self.tid, self, (PhilipsAmbilightControl.STATUS_CHANGE_SLEEP_TIME if (is_wake_up_mode) else PhilipsAmbilightControl.STATUS_CHANGE_RETRY_TIME))
			#
		#
	#
#

##j## EOF