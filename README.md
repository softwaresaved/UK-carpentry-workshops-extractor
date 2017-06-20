# UK-carpentry-workshops-extractor
This project contains a Ruby script that extracts the details of all UK Carpentry workshops recorded in Software Carpentry's AMY system and saves them to a set of CSV files (named after the date they are generated).

This includes Software Carpentry, Data Carpentry and Train The Trainer (instructor training) workshops (as well as Library Carpentry workshops when they start being recorded in AMY, any any other future workshop types).

The script uses AMY's public API to extract certain information, but also accesses some private pages (to extract additional data not exposed via the API). Hence, in order for the script to work fully, one needs to have an account in AMY (with a proper username and password, not AMY's authentication via GitHub).

Tested with `ruby 2.2.1`.

## Setup
Create a copy of `amy_login.yml.pre` config file (located in the project root), rename it to `amy_login.yml` and configure your username and password there accordingly. Make sure you do not share this file with the others as it contains sensitive information. Or pass your credentials directly to the `authenticate_with_amy()` method inside the script `extract-UK-workshops.rb`.

## Running the script
From the project root, do:

```$ ruby extract-UK-workshops.rb```