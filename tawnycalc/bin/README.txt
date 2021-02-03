THERMOCALC BINARIES
-------------------
This directory contains the THERMOCALC executable binaries
for different platforms. All binaries are compiled for 64bit
architecture using the following command:

    $ fpc -O3 thermo.pas

for Windows & FPC 3.2.0 the following was required

    $ fpc -Fu"C:\Program Files\FPC\units\i386-win32\rtl-objpas" -O3 thermo.pas
