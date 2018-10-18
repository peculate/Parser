# Parser

## Requirements
- Requires python3 and python3-pip
- To install the requirements, simply run ```pip3 install -r requirements.txt```

## Run Instructions
- The script can be run directly from command line with ```python3 parser.py```
- Flags can be set with ```python3 parser.py [options]```

## Flags
- For more detailed information about the use of the script and possible flags, use ```python3 parser.py -help```
- Use ```-lf``` and / or ```-df``` to specify the name(s) of the log and data file respectively
- Use ```-i``` and / or ```-c``` to display logged information to the screen
- Use ```-E``` to go through every possible search page (will cause a large number of duplicates)

## Database
- The data is saved to a .csv file
- The columns of the csv are as follows: ```Course ID, Title, Author, Skin, Theme, Region, Country, Tag, Difficulty, Upload Date, Plays, Stars, Clears, Attempts, Shares, Thumbnail URL, Full URL```
- Using init.sql, a table containing the relevant data can be constructed
