# Copyright (c) 2010 Aldo Cortesi
# Copyright (c) 2010, 2014 dequis
# Copyright (c) 2012 Randall Ma
# Copyright (c) 2012-2014 Tycho Andersen
# Copyright (c) 2012 Craig Barnes
# Copyright (c) 2013 horsik
# Copyright (c) 2013 Tao Sauvage
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


#IMPORTANT: logs can be found at ~/.local/share/qtile/qtile.log

import re
import subprocess

from libqtile import bar, layout, qtile, widget, hook
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
from libqtile.qubes import QubesBorder, QubesTaskList
#from libqtile.log_utils import logger #only errors are visible in the qtile log by default

mod = "mod4"
terminal = "terminal"

keys = [
    # A list of available commands that can be bound to keys can be found
    # at https://docs.qtile.org/en/latest/manual/config/lazy.html

    # MonadTall specific hotkeys (see https://docs.qtile.org/en/latest/manual/ref/layouts.html#monadtall)
    Key([mod], "h", lazy.layout.left()),
    Key([mod], "l", lazy.layout.right()),
    Key([mod], "j", lazy.layout.down()),
    Key([mod], "k", lazy.layout.up()),
    Key([mod, "shift"], "h", lazy.layout.swap_left()),
    Key([mod, "shift"], "l", lazy.layout.swap_right()),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down()),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up()),
    Key([mod], "a", lazy.layout.grow()),
    Key([mod], "s", lazy.layout.shrink()),
    Key([mod], "n", lazy.layout.reset()),
    Key([mod, "shift"], "n", lazy.layout.normalize()),
    Key([mod], "o", lazy.layout.maximize()),
    Key([mod, "shift"], "s", lazy.layout.toggle_auto_maximize()),
    Key([mod, "shift"], "space", lazy.layout.flip()),

    # misc hotkeys
    Key([mod], "m", lazy.window.toggle_minimize()),
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod], "w", lazy.window.kill(), desc="Kill/Close focused window"),
    Key([mod, "shift"], "c", lazy.window.kill(), desc="Kill/Close focused window"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen on the focused window"),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating on the focused window"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
    Key([mod], "r", lazy.spawncmd(), desc="Spawn a command using a prompt widget"),

    #custom hotkeys
    Key([mod], "q", lazy.spawn("screenlock"), desc="Launch screen locker"),
    Key([mod], "e", lazy.spawn("qidled unpauseAllActiveWindows"), desc="Unpause active windows"),
    Key([mod], "Print", lazy.spawn("mkdir -p ~/screenshots && maim ~/screenshots/$(date +%s).png", shell=True), desc="Take a screenshot"), #requires maim in dom0
    #raise & lower volume, mute - requires qubes-wpctl (https://github.com/3hhh/qubes-terminal-hotkeys/tree/master/util) & blib (https://github.com/3hhh/blib) in dom0
    Key([mod], "F7", lazy.spawn("qubes-wpctl toggle default"), desc="Toggle mute status"),
    Key([mod], "F8", lazy.spawn("qubes-wpctl volumeOut 5%-"), desc="Decrease volume"),
    Key([mod], "F9", lazy.spawn("qubes-wpctl volumeOut 5%+"), desc="Increase volume"),
    Key([mod], "F11", lazy.spawn("qubes-wpctl switchOut"), desc="Switch audio sink"),
    #adjust brightness (requires brightnessctl in dom0)
    Key([mod], "F1", lazy.spawn("brightnessctl set 2%-"), desc="Decrease screen brightness"),
    Key([mod], "F2", lazy.spawn("brightnessctl set 2%+"), desc="Increase screen brightness"),
]

#whether or not to focus the next spawned window
FOCUS_NEXT = False

def focus_next():
    global FOCUS_NEXT
    FOCUS_NEXT = True

#never let any new client steal focus unless explicitly allowed via decide_focus()
@hook.subscribe.group_window_add
def decide_focus(group, win):
    global FOCUS_NEXT

    if not qtile.current_window: #empty screen
        return

    if win.is_transient_for() and qtile.current_window == win.is_transient_for(): #subwindow
        return

    if FOCUS_NEXT:
        FOCUS_NEXT = False
        return

    #default: disallow focus steal from this window
    win.can_steal_focus = False

#even if a focus steal was allowed, make sure it isn't allowed forever
@hook.subscribe.client_managed
def disallow_focus_steal(win):
    win.can_steal_focus = False

#position cursor in the middle on first startup
@hook.subscribe.startup_once
def warp_screen():
    qtile.warp_to_screen()

groups = [Group(i) for i in "12345678" ]
groups.append(Group('9', matches=[ Match(wm_class=re.compile(r'^chat:.*$')) ] )) #chat VM windows are always started in group 9

for i in groups:
    keys.extend(
        [
            # mod + group number = switch to group
            Key(
                [mod],
                i.name,
                lazy.group[i.name].toscreen(),
                desc=f"Switch to group {i.name}",
            ),
            # mod + shift + group number = switch to & move focused window to group
            Key(
                [mod, "shift"],
                i.name,
                lazy.window.togroup(i.name, switch_group=False),
                desc=f"Move focused window to group {i.name}",
            ),
        ]
    )

border = QubesBorder()
border_width = 7

#IMPORTANT: You must explicitly set the QubesBorder() or it won't be drawn!
layouts = [
    layout.MonadTall(
        border_width = border_width,
        single_border_width = border_width,
        border_normal = border,
        border_focus = border,
        new_client_position = "bottom",
    ),
    layout.Max(
        border_width = border_width,
        border_normal = border,
        border_focus = border,
    ),
    # Try more layouts by unleashing below layouts.
    # layout.Columns(border_focus_stack=["#d75f5f", "#8f3d3d"], border_width=4),
    # layout.Stack(num_stacks=2),
    # layout.Bsp(),
    # layout.Matrix(),
    # layout.MonadWide(),
    # layout.RatioTile(),
    # layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]

widget_defaults = dict(
    font="Noto Sans Mono SemiBold",
    fontsize=10,
    padding=3,
)
extension_defaults = widget_defaults.copy()

def open_ical():
    focus_next()
    qtile.spawn('terminal -e ical') #for whatever reason lazy doesn't work here!

# The volume widget is currently broken and therefore disabled, cf. https://github.com/qtile/qtile/issues/5354.
#if subprocess.call('qubes-prefs default_audiovm', shell=True) == 'dom0':
#    vol_widget = widget.Volume(
#        fmt=r'Vol: {}',
#        mute_format=r'<span color="yellow">M</span>',
#        unmute_format=r'<span color="lime">{volume}%</span>',
#        )
#else:
#    #a non-dom0 audio VM currently requires qubes-wpctl (https://github.com/3hhh/qubes-terminal-hotkeys/tree/master/util) & blib (https://github.com/3hhh/blib) in dom0 for the volume widget
#    vol_widget = widget.Volume(
#        fmt=r'Vol: {}',
#        mute_format=r'<span color="yellow">M</span>',
#        unmute_format=r'<span color="lime">{volume}%</span>',
#        check_mute_command=r'qubes-wpctl printDefault | grep -E "^Out: .*MUTED.*$" &> /dev/null && echo "[off]"',
#        get_volume_command=r'qubes-wpctl printDefault | sed -rn "s/Out: .*\[vol: ([0-9]+)\.([0-9]+)\]$/\1\2%/p"',
#        mute_command=r'qubes-wpctl toggle default',
#        volume_up_command=r'qubes-wpctl volumeOut 5%+',
#        volume_down_command=r'qubes-wpctl volumeOut 5%-',
#        volume_app=r'qubes-wpctl app',
#        update_interval=30,
#        )

screens = [ Screen(
        top=bar.Bar(
            [
                widget.LaunchBar(progs = [('/usr/share/icons/hicolor/16x16/apps/qubes-logo-icon.png', \
                    'qubes-app-menu', 'Qubes OS menu'),]),
                widget.GroupBox(highlight_method='block'),
                widget.Prompt(bell_style="visual"),
                QubesTaskList(title_width_method='uniform', border=border),
                # NB Systray is incompatible with Wayland, consider using StatusNotifier instead
                # widget.StatusNotifier(),
                #widget.KeyboardLayout(),
                widget.Systray(),
                widget.Battery(format='Bat({char}): {percent:2.0%} {hour:d}:{min:02d}h {watt:.2f}W', show_short_text=False),
                widget.Sep(padding=10),
                #vol_widget,
                #widget.Sep(padding=10),
                widget.Clock(format="%a %b %d %H:%M:%S", mouse_callbacks={'Button1': open_ical}),
                widget.CurrentLayoutIcon(),
            ],
            24,
            # border_width=[2, 0, 2, 0],  # Draw top and bottom borders
            # border_color=["ff00ff", "000000", "ff00ff", "000000"]  # Borders are magenta
        ),
        # You can uncomment this variable if you see that on X11 floating resize/moving is laggy
        # By default we handle these events delayed to already improve performance, however your system might still be struggling
        # This variable is set to None (no cap) by default, but you can set it to 60 to indicate that you limit it to 60 events per second
        # x11_drag_polling_rate = 60,
    ), ]

# mouse hotkeys
mouse = [
    #NOTE: set_position() snaps to the layout position, set_position_floating() starts floating mode
    Drag([mod], "Button1", lazy.window.set_position(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []
follow_mouse_focus = False
bring_front_click = False #NOTE: this bypasses override-redirect window stacking, i.e. enabling this breaks e.g. firefox context menus
floats_kept_above = True
cursor_warp = False
floating_layout = layout.Floating( #NOTE: this cannot be disabled, so we better configure it properly (it doesn't apply to override-redirect windows)
    border_width = border_width,
    fullscreen_border_width = border_width,
    max_border_width = border_width,
    border_normal = border,
    border_focus = border,
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(func=lambda c: bool(c.is_transient_for())), #these are usually context menus, menu bars, ...
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
    ]
)
auto_fullscreen = False
focus_on_window_activation = "never"
reconfigure_screens = True

# If things like steam games want to auto-minimize themselves when losing
# focus, should we respect this or not?
auto_minimize = True

# When using the Wayland backend, this can be used to configure input devices.
wl_input_rules = None

# xcursor theme (string or None) and size (integer) for Wayland backend
wl_xcursor_theme = None
wl_xcursor_size = 24

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"
