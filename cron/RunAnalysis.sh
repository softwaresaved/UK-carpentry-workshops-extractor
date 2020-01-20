#!/usr/bin/env bash
#
# Script to run Alek's analysis pipeline.

# Change to the correct directory - change for your system.
echo Changing to the analysis directory
cd /home/mario/carpentry-workshops-instructors-extractor
echo

# Make sure that we have the latest version of the code
echo Pulling from GitHub
git pull
echo

# Run the data extraction script.
echo Getting the data from Amy
python3 amy_data_extract.py -c GB 
echo

# Generate the input/output filenames for workshops.
infile=carpentry-workshops_GB_$(date +"%Y-%m-%d").csv
outfile1=analysed_carpentry-workshops_GB_$(date +"%Y-%m-%d").xlsx

# Produce workshop output data.
echo Analysing the workshop data
python3 analyse_workshops.py -in data/raw/${infile}
echo

# Generate the input/output filenames for instructors.
infile=carpentry-instructors_GB_$(date +"%Y-%m-%d").csv
outfile2=analysed_carpentry-instructors_GB_$(date +"%Y-%m-%d").xlsx

# Produce instructor output data.
echo Analysing the instructor data
python3 analyse_instructors.py -in data/raw/${infile}
echo

# Push the processed data back to GitHub
date=$(date +"%Y-%m-%d")
git add data/analyses/${outfile1} data/analyses/${outfile2}
git commit -m "Adding carpentry and workshop data for ${date}."
git push

# This next bit assumes that there is a clone of the metrics repository
# hanging off the home directory. We will copy the output files to that
# repository. Add them, commit them, do a git pull of the repo contents
# and then push them to the metrics repository.
cp ./data/analyses/${outfile1} ~/metrics/training/workshops/analyses
cp ./data/analyses/${outfile2} ~/metrics/training/workshops/analyses

# Go to the repository, add and commit the files.
cd ~/metrics/training/workshops/analyses
git add ${outfile1}
git add ${outfile2}
git commit -m "Adding carpentry and workshop data for ${date}."
# Make sure the repo is up to date.
git pull  
# Now push the results.
git push 
