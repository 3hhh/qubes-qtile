# qubes-qtile

[qtile](https://qtile.org/) installer and configuration for [Qubes OS](https://www.qubes-os.org/).

## Installation

Installation is generally expected in dom0 as [GUI VM](https://www.qubes-os.org/doc/gui-domain/), but _should_ also work in GUI VM templates or standalone VMs.

1. Install some dependencies in your GUI VM: `sudo qubes-dom0-update pango python3-pip dex-autostart google-noto-sans-mono-fonts` (command for dom0 as GUI VM)
2. Download this repository in a VM and switch to its directory via e.g. `cd qubes-qtile`.
3. (Optional) Download a current or more trustworthy version of `qtile` and its dependencies via `rm -f pkgs/* && pip3 download --destination-directory ./pkgs qtile qtile-extras dbus-fast`.
4. Move the repository to your GUI VM, e.g. to `~/qubes-qtile`, and make sure the directory persists across VM restarts.
5. Run `~/qubes-qtile/installer install`.
6. Choose `qtile` as window manager in `lightdm` the next time you login.

## Uninstall

1. Run `~/qubes-qtile/installer uninstall`.
2. Remove `~/qubes-qtile`.

## Configuration

Your own custom [config.py](https://docs.qtile.org/en/latest/manual/config/index.html) can be placed at `~/.config/qtile/config.py`. It'll overwrite the example configuration shipped for Qubes OS at `/etc/xdg/qtile/config.py`, i.e. you may want to base your changes on that configuration.

### Autostart

The configuration provided in this repository will autostart `*.desktop` files in `/etc/xdg/autostart/` via `dex-autostart`.

It'll also execute `~/.config/qtile/autostart_once.sh` and `~/.config/qtile/autostart.sh`, if any of these exist. The former is executed on the first `qtile` start after boot only; the latter is executed on every `qtile` start.

Feel free to use any of these methods to autostart your own custom applications.

The installer also creates `/etc/xdg/qtile/autostart*.sh` scripts for its own use. Please do not modify those.

If you see an error such as "XFCE PolicyKit error: An authentication agent already exists" on boot, remove `/etc/xdg/autostart/xfce-polkit.desktop` in your GUI VM/dom0.

### Focus steal hardening

The configuration shipped with this repository is hardened against focus steals using the methods mentioned in this section.

#### Definition

We'll define _wanted focus changes_ as one of the following:

* mouse move & click afterwards
* workspace/group change
* pre-defined key combinations for focus changes (e.g. Mod-j & Mod-k)
* focused window moved to other group <sup>1</sup>
* focused window closed <sup>1</sup>
* new window created in a workspace with only unfocused windows or in an empty workspace

(<sup>1</sup> These are allowed to cause a focus switch to another window according to a predefined algorithm as otherwise no window would be focused.)

Everything else is considered an unwanted _focus steal_.

In particular the following events are not meant to cause a focus change:

* new window created in a workspace with a focused window
* unfocused window closed
* unfocused window moved to another workspace
* application request
* mouse move without click (sloppy focus)

For the below example other requests from applications to the window manager are meant to be ignored in general as well, e.g.:

* windows shouldn't be able to maximize themselves without the user giving a respective command to the WM (simple test: Firefox F11 next to another window)
* windows shouldn't be able to change their size themselves
* windows shouldn't be able to modify their borders in any way

Users may want to adjust their definitions and respective implementations according to their needs.

#### Implementation

##### Prevent focus steal by new windows

By default `qtile` passes the focus to newly created windows. We can disable that via:

```python
@hook.subscribe.client_new
def decide_focus(win):
    win.can_steal_focus = False
```

The `config.py` shipped with this repository provides a slightly more complex variant, which allows a focus steal under certain circumstances.

##### Disable sloppy focus

It is easily possible to disable the focus following the mouse movements via `follow_mouse_focus = False`.

##### Disable window fullscreen

It is necessary to explicitly set `auto_fullscreen = False` as windows may otherwise fullscreen themselves. In Qubes OS windows should never be able to hide the security relevant-borders of other windows by themselves.

##### Ignore focus requests from windows

This can easily be set via `focus_on_window_activation = "never"`.

## Copyright

© 2024 David Hobach

qubes-qtile is released under the GPLv3 license; see `LICENSE` for details.
