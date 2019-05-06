# coconutbar
a clean x11 system bar with bspwm integration, using only python3 magic.

## How does it look ? 

Pretty minimalistic, and easily configurable. 

**Default**
![](default.jpg)
`coconutbar`

**Matrix**
![](matrix.jpg)
`coconutbar -system "CPU %CPU% RAM %RAM%" -date "epoch %s" -font "Roboto 12" -fg "#1F1" -bg "#111"`

**Verbose** 
![](verbose.jpg)
`coconutbar -system "CPU is at %CPU%, RAM is at %RAM%, IP is %IP" -date "It's currently %Hh%Mm%Ss" -font "Helvetica 14 italic" -fg "#112" -bg "#DDD"`

## How to install ? 

Just get dependancies, clone and install :

```bash
# Get dependancies if necessary
sudo apt install python3-tk python3-pip # tkinter and pip
sudo pip3 install setuptools # setuptools

# Clone
git clone https://github.com/k0rventen/coconutbar.git
cd coconutbar

# Install
sudo python3 setup.py install

# Launch
coconutbar

# Get help
coconutbar -h
```

## Bspwm integration

coconutbar lists the virtual monitors and displays their status accordingly:
- (monitor1) means that monitor 1 is focused
- [monitor1] is focused and in fullscreen mode
- -monitor1- is active but not focused
- monitor1 is neither active nor focused

## How does it works ? 

Pure python. Only built-in libraries (tkinter comes by default if it's not a minimal python install). 

The collection of the system's state is done via the kernel procfs and sysfs (like `/proc/stat`, `/proc/mem/info` etc..).

The integration of bspwm is done via a subprocess `bspc subscribe`, and its output is parsed to determine the current state.

The UI is done via tkinter, nothing else.

## License

MIT