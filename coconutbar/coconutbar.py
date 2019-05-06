"""
Author : k0rventen
License : MIT
Version : 0.4
Home : https://github.com/k0rventen/coconutbar
"""

import socket  # For IP
import os  # for listing dirs
import argparse  # cli arg parser
import time  # sleepy
import subprocess  # both for
import threading  # bspc thread
import signal  # Exit cleanly
from datetime import datetime  # time
from tkinter import *  # UI

# All definition for __init__.py
__all__ = ["parse_cli_args","get_cpu", "get_temp", "get_ip_address", "get_net_speed", "get_mem",
           "get_time", "bspwm_thread", "print_bar", "init_tk", "system_infos", "main", "clean_stop"]

# Default/user config, updated by cli config
user_config = {
    "bspwm_focused": "()",
    "bspwm_fullscreen": "[]",
    "bspwm_active": "--"
}

# Global vars
is_running = True  # Global kill switch
prev_total, prev_busy, prev_up, prev_down = 0, 0, 0, 0

def parse_cli_args():
    """Parse the arguments, and display a helpful help when called with -h
    """

    global user_config
    parser = argparse.ArgumentParser(
        description='A clean, minimalistic bar for bspwm',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '-fg', help='color of the foreground in #RGB or #RRRGGGBBB format\n', default="#BBB")
    parser.add_argument(
        '-bg', help='color of the background in #RGB or #RRRGGGBBB format\n', default="#112")
    parser.add_argument(
        '-font', help='font config to use, e.g. "Roboto 14 bold" or "Helvetica 9 italic"\n', default="Helvetica 12 bold")
    parser.add_argument(
        '-date', help='date format to use, e.g. "%%H:%%M:%%S" for an ISO 8601 extended time format\n', default="%H:%M:%S")
    parser.add_argument('-system', help='''Which system informations to show and how. It will interpret the following sequences : 
        %%CPU for the cpu usage in %%
        %%RAM for the ram usage in %%
        %%IP  for the default IP
        %%UP for the current network upload (in MB/s)
        %%DOWN for the current network download (in MB/s)
        For example, "CPU is at %%CPU%%, IP is %%IP"\n''', default='CPU %CPU% | RAM %RAM% | %IP | ʌ %UP | v %DOWN')
    parser.add_argument(
        '-delay', help='delay between system status retrieval, in seconds\n', default=1)
    cli_config = vars(parser.parse_args())

    # Merge user config with default config
    user_config.update(cli_config)


def clean_stop(sig, fra):
    """Signal handler

    Kill the bspc child process before exiting :

    If we receive a SIGTERM and don't handle it,
    we will leave an orphan child running.
    So we kill it, then we exit.
    """
    global is_running
    is_running = False
    bspc_process.kill()
    exit()


def get_cpu():
    """Compute current CPU usage from /proc/stat
    Using the delta of working and idle jiffie over time
    """
    global prev_total, prev_busy
    try:
        with open("/proc/stat") as f:
            raw = f.readline()
        jiffies = [int(x) for x in raw.split()[1:5]]
        busy = sum(jiffies[:3])
        total = sum(jiffies)
        cpu = (busy - prev_busy) / (total - prev_total) * 100
        prev_total = total
        prev_busy = busy
        return str(int(cpu))
    except Exception as e:
        print(e.args)
        return "NaN"


def get_temp():
    """Return temp in Celsius from /sys/class/thermal"""

    try:
        dev = sorted([x for x in os.listdir(
            "/sys/class/thermal/") if "thermal_zone" in x])[-1]
        with open("/sys/class/thermal/"+dev+"/temp") as f:
            temp = f.read()
        return str(int(int(temp)/1000))
    except Exception as e:
        print(e.args)
        return "NaN"


def get_ip_address():
    """Return the default IP addr"""

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("255.0.0.0", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return "No network"


def get_net_speed():
    """Compute current upload and download speeds using /proc/net/dev"""

    global prev_up, prev_down
    try:
        up, down = 0, 0
        with open("/proc/net/dev") as f:
            raw = f.readlines()
        interfaces = raw[2:]
        for inter in interfaces:
            vals = inter.split()
            down += int(vals[1])
            up += int(vals[8])

        up_speed = round((up-prev_up)/1000000, 1)
        down_speed = round((down-prev_down)/1000000, 1)

        up_str = str(up_speed)+"Mb/s"
        down_str = str(down_speed)+"Mb/s"

        prev_up = up
        prev_down = down
        return up_str, down_str
    except Exception as e:
        print(e.args)
        return "NaN"


def get_mem():
    """Return total free (as in available) memory (RAM only)"""

    try:
        with open("/proc/meminfo") as f:
            raw = f.readlines()
            free = int(raw[1].split()[1]) + int(raw[4].split()[1])
            total = int(raw[0].split()[1])
            mem = int(100 - (free/total * 100))
            return str(mem)
    except Exception as e:
        print(e.args)
        return "NaN"


def get_time():
    """Pretty obvious.."""
    return datetime.now().strftime(user_config["date"])


def bspwm_thread():
    """Thread for bspc

    When bspc updates we don't wait on the
    main thread to update the bar
    and we can redraw only the bspc section
    """
    global bspc_process

    # Cache the separators to avoid looking up the dict everytime
    bspwm_focused_l = user_config["bspwm_focused"][0]
    bspwm_focused_r = user_config["bspwm_focused"][1]
    bspwm_active_l = user_config["bspwm_active"][0]
    bspwm_active_r = user_config["bspwm_active"][1]
    bspwm_fullscreen_l = user_config["bspwm_fullscreen"][0]
    bspwm_fullscreen_r = user_config["bspwm_fullscreen"][1]

    bspc_process = subprocess.Popen(
        ["bspc", "subscribe"], stdout=subprocess.PIPE)
    while True:
        output = bspc_process.stdout.readline()
        if output:
            config = []
            vals = output.split(b":")[1:]
            layout = vals[-3].decode()
            desktops = [x.decode() for x in output.split(
                b":")[1:] if b"f" in x or b"F" in x or b"o" in x or b"O" in x]
            for i in desktops:
                if i[0] == "F" or i[0] == "O":
                    if layout == "LM":
                        config.append(bspwm_fullscreen_l +
                                      i[1:]+bspwm_fullscreen_r)
                    else:
                        config.append(bspwm_focused_l + i[1:]+bspwm_focused_r)
                elif i[0] == "o":
                    config.append(bspwm_active_l+i[1:]+bspwm_active_r)
                else:
                    config.append(" "+i[1:]+" ")

            print_bar(2, " ".join(config))

        else:
            break


def print_bar(refresh, infos):
    """Refreshes the tkinter bar text labels

    0: Refreshes left
    1: Refreshes center
    2: Refreshes right
    """
    if is_running:
        if refresh is 0:
            text_left.set(infos)
        elif refresh is 1:
            text_center.set(infos)
        elif refresh is 2:
            text_right.set(infos)


def init_tk():
    """Init of tkinter stuff :
        - setup the root window,
        - configure the WM settings (dock mode) so it stays above other windows
        - create and configure the canvas and text labels
    """
    global text_left, text_center, text_right
    root = Tk(className='coconutbar')
    screen_width = root.winfo_screenwidth()
    root.configure(background=user_config["bg"])
    root.geometry(str(screen_width)+"x" +
                  str(int(user_config["font"].split()[1])*2))

    root.wm_attributes('-type', 'dock')
    text_left, text_center, text_right = StringVar(), StringVar(), StringVar()

    Label(root, textvariable=text_left,
          font=user_config["font"], bg=user_config["bg"], fg=user_config["fg"]).place(x=0, y=0, anchor=NW)
    Label(root, textvariable=text_center, font=user_config["font"], bg=user_config["bg"], fg=user_config["fg"]).place(
        x=screen_width/2, y=0, anchor=N)
    Label(root, textvariable=text_right, font=user_config["font"], bg=user_config["bg"], fg=user_config["fg"]).place(
        x=screen_width, y=0, anchor=NE)

    return root


def system_infos():
    """Collect the sys infos using the various functions
    defined above

    Once everything is retrieved, refresh the bar
    """
    # Loopy code
    while is_running:
        infos = user_config['system']

        # Retrieve system status (if displayed)
        if "%IP" in infos:
            infos = infos.replace("%IP", get_ip_address())
        if "%CPU" in infos:
            infos = infos.replace("%CPU", get_cpu())
        if "%RAM" in infos:
            infos = infos.replace("%RAM", get_mem())
        if "%UP" in infos or "%DOWN" in infos:
            net = get_net_speed()
            infos = infos.replace("%UP", net[0])
            infos = infos.replace("%DOWN", net[1])

        # Print the formated infos
        print_bar(0, infos)

        # Get the current time
        clock = get_time()
        print_bar(1, clock)

        # Sleepy time
        time.sleep(user_config["delay"])


def main():
    """entry point

    Enable the signal catcher,
    setup the GUI stuff,

    create and launch the two threads
        - for bspc interaction
        - for data retrieval
    """
    # Attach the signals
    signal.signal(signal.SIGQUIT, clean_stop)
    signal.signal(signal.SIGTERM, clean_stop)
    signal.signal(signal.SIGINT, clean_stop)

    # parse args
    parse_cli_args()

    # setup ui accordingly
    root = init_tk()

    # thread for bspc update
    bspc_thread = threading.Thread(target=bspwm_thread)
    bspc_thread.start()

    # thread for stats gathering
    main_thread = threading.Thread(target=system_infos)
    main_thread.start()

    # start ui
    root.mainloop()


if __name__ == "__main__":
    main()
