# Dust Accelerator Database Analysis

## Project
This tool is designed to give insight on historical data of the dust accelerator, mainly the rate at which it can produce dust given certain parameters. This labVIEW vi with associated python scripts support the collection, processing, and display of accelerator dust event rate data. 

## Windows Setup
1. Install python 3, this was designed on python 3.6 but later versions will likely work. If you don't have Python installed install it from https://www.python.org/ftp/python/3.7.4/python-3.7.4-amd64.exe
2. Run the setup utility to install the mySQL Python Connector and matplotlib library. This will also install python package utility pip.
3. If this doesn't work as intended, use pip to install the necessary packages
      - On windows, open the command line by pressing Windows+R, entering cmd and pressing enter
      - To install matplotlib install use `pip install matplotlib`
      - To install the mysql connector, use `pip install 

# Usage
To run this tool launch the results_interface.vi application

## Troubleshooting
If the program fails to give results, consult the debugging tab of the vi
 - Error: ModuleNotFoundError: No module named 'mysql'
    - Failed to install the mySQL python connector
    - Install through pip with `pip install mysql-connector-python`
    - If that fails, download from https://dev.mysql.com/downloads/connector/python/
 - Error; ModuleNotFoundError: No module named 'matplotlib'
    - Failed to install the matplotlib Python package
    - Install through pip with `pip install matplotlib`
    - Or download from https://matplotlib.org/downloads.html
 - Setup error: 'pip' is not recognized as an internal or external command
    - Failed to install pip, run setup.bat again, or install from https://pip.pypa.io/en/stable/installing/

# Implementation
 - See Dust_Data_Project.pptx for details on session generation