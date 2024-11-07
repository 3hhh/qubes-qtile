#!/usr/bin/env python3
# vim: fileencoding=utf-8
#
# Copyright (C) 2024
#                   David Hobach <tripleh@hackingthe.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import asyncio
import re
import time
import subprocess

from libqtile import hook
from libqtile.widget import TaskList
from libqtile.confreader import ConfigError
from qtile_extras.layout.decorations import ConditionalBorder #https://qtile-extras.readthedocs.io/en/stable/manual/ref/borders.html

class QubesPropertyCache():
    ''' Cache Qubes OS VM properties provided via `qvm-ls`.
    '''

    def __init__(self, prop='label', timeout=600):
        ''' Init.
        :param property: Name of the property to cache.
        :param timeout: Time in seconds after which to definitely refresh the cache.
        '''
        self.prop = prop
        self.timeout = timeout
        self.vms = {}
        self.last = 0 #unix timestamp of last update
        self.update(force=True)

    def get(self, vm, default=None, error=None):
        ''' Get the property for the given VM.
        :param vm: VM name.
        :param default: Returned, if nothing was found and no error occurred.
        :param error: Returned on unexpected errors.
        :return: Property string or the default, if not found.
        '''
        try:
            self.update(try_vm=vm)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return error
        return self.vms.get(vm, default)

    def _update(self):
        ret = subprocess.run(['qvm-ls', '--raw-data', '-O', f'name,{self.prop}'],
                timeout=10, check=True, capture_output=True, encoding='UTF-8')

        for line in ret.stdout.splitlines():
            data = line.split('|')
            self.vms[data[0]] = data[1]

        self.last = time.time()
        return True

    def update(self, force=False, try_vm=None):
        ''' Update the cache, if necessary.
        :param force: Skip the necessity check.
        :param try_vm: Check whether this VM is available in our data and if so, skip the update.
        :return: Whether or not an update was executed.
        '''
        if not force:
            diff = time.time() - self.last
            if diff < self.timeout and diff > 0 \
                and ( try_vm is None or self.vms.get(try_vm) is not None):
                return False
        return self._update()

QUBES_CACHE = QubesPropertyCache()

def get_vm_name(client):
    ''' Get the VM name for a client.
    :return: VM name string or None, if it couldn't be identified (usually dom0). If such a VM doesn't exist, it's usually dom0 as well.
    '''
    #NOTES:
    # - as per https://github.com/QubesOS/qubes-gui-daemon/blob/89d0254683a904485dc04e526cb75d4be4957417/gui-daemon/xside.c#L2934 this should be safe to use
    # - characters allowed in VM names: https://github.com/QubesOS/qubes-core-admin/blob/main/qubes/vm/__init__.py#L65
    match = re.match(r'^([a-zA-Z][a-zA-Z0-9_.-]*):.*$', client.get_wm_class()[0])
    if match:
        return match.group(1)
    return None

def get_border_color(client, error=None, dom0='black'):
    ''' Get the border color for a client.
    :param error: Returned on unexpected errors.
    :param dom0: Returned for dom0 windows.
    :return: Border color as string, e.g. 'green'.
    '''
    vm_name = get_vm_name(client)
    if vm_name:
        return QUBES_CACHE.get(vm_name,default='black',error=error)
    return dom0

class QubesBorder(ConditionalBorder):
    ''' Use this class as border decoration for focused and unfocused windows on Qubes OS to color windows according
        to their Qube/VM label.
    '''
    # Note that ConditionalBorder is the only border with access to the window, which is what we need.

    color_defaults = {
        #color name --> [unfocused RGB hex, focused RGB hex]
        'red':          ['#780000', '#CC0000'],
        'orange':       ['#AD6D00', '#F57900'],
        'yellow':       ['#B19900', '#FFE200'],
        'green':        ['#006700', '#00E300'],
        'gray':         ['#909090', '#CCCCCC'],
        'blue':         ['#00007E', '#0000EA'],
        'purple':       ['#9949A3', '#D700E9'],
        'black':        ['#303030', '#606060'], #black borders cannot be 100% black as that is not visible
    }

    defaults = [
        ("colors", color_defaults, "Map of color names (e.g. 'green') to list of RGB color definitions used for drawing (first item is for unfocused windows, second for focused windows)."),
        ("fallback", "#FFFFFF", "Border color to use on errors (RGB hex)."),
        ("dom0", "black", "Border color to use for dom0 (color name)."),
    ]

    def __init__(self, **config):
        ConditionalBorder.__init__(self, **config)
        self.add_defaults(self.defaults)

        if not self.colors or not isinstance(self.colors, dict):
            raise ConfigError("Color map is not set or of an incorrect type.")

        for color in self.colors.values():
            if not isinstance(color, list) or len(color) != 2:
                raise ConfigError("Unexpected color map contents. Each entry must be a list of exactly 2 colors (unfocused/focused).")

    def compare(self, win):
        ''' Override ConditionalBorder.compare().
            We just use it to get access to the window.
        :return: RGB border color as needed by qtile, e.g. 'fff'.
        '''
        if not win:
            return self.fallback

        color = get_border_color(win, dom0=self.dom0)
        if not color:
            return self.fallback

        ret = self.colors.get(color)
        if ret:
            index = 0
            if win.has_focus:
                index = 1
            return ret[index]

        return self.fallback

class QubesTaskList(TaskList):
    ''' Use this class as task list on Qubes OS to prefix window names with the VM names.
    '''

    def __init__(self, **config):
        TaskList.__init__(self, **config)
        self.cond_border = None
        if isinstance(self.border, ConditionalBorder):
            self.cond_border = self.border

    #override to put the VM name in front of the window title
    def get_taskname(self, window):
        ret = TaskList.get_taskname(self, window)
        vm = get_vm_name(window)
        if not vm:
            vm = "dom0"
        return f'[{vm}] {ret}'

    def get_active_window(self):
        ''' Get the currently active window. '''
        #self.windows contains the list of windows of the currently active group
        for win in self.windows:
            return win.group.current_window
        return None

    #override to support border colors for focused windows
    def draw(self):
        if self.cond_border:
            active = self.get_active_window()
            self.border = self.cond_border.compare(active)
        #NOTE: this hack cannot work for unfocused windows as there are many unfocused windows, but just one border_unfocused property
        TaskList.draw(self)

# autostart hooks
@hook.subscribe.startup_once
async def qubes_autostart_once():
    system_autostart = asyncio.create_subprocess_shell('/etc/xdg/qtile/autostart_once.sh |& logger -t autostart_once.sh_system')
    user_autostart = asyncio.create_subprocess_shell('~/.config/qtile/autostart_once.sh |& logger -t autostart_once.sh_user')
    await asyncio.gather(user_autostart, system_autostart)

@hook.subscribe.startup
async def qubes_autostart():
    system_autostart = asyncio.create_subprocess_shell('/etc/xdg/qtile/autostart.sh |& logger -t autostart.sh_system')
    user_autostart = asyncio.create_subprocess_shell('~/.config/qtile/autostart.sh |& logger -t autostart.sh_user')
    await asyncio.gather(user_autostart, system_autostart)
