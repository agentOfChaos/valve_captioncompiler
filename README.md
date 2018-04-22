# valve_captioncompiler

Python (plus C) reimplementation of the `captioncompiler` utility, used to create caption files for source-engine games.  
It is intended to be a standalone tool, usable without needing to download and compile the whole source-engine codebase.

## Compiling

The crc32 utility is copied straight from the source engine 2013 implementation, and must be compiled before use:

    cd crc32/
    gcc valve_crc32.c -o valve_crc32
    
    
## Usage

Print the header of a closedcaption.dat file:

    python valve_captioncompiler.py closedcaption.dat
    
Print the header and the directory of a closedcaption.dat file:

    python valve_captioncompiler.py -d closedcaption.dat
    
    
Create a new .dat file from a source file with the proper formatting (see [the official documentation](https://developer.valvesoftware.com/wiki/Closed_Captions)):

    python valve_captioncompiler.py -c closecaption_source.txt newcaption.dat
