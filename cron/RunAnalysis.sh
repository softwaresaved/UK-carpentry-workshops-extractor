#!/usr/bin/env bash
#
# Script to run Alek's analysis pipeline.

# Add python to the path
export PATH=$PATH:/home/mario/anaconda3/bin

# Change to the correct directory - change for your system.
echo Changing to the analysis directory
cd /home/mario/carpentry-data-analysis
echo

# Make sure that we have the latest version of the code
echo Pulling from GitHub
git pull
echo

# Define the data files
WORKSHOPS_DATAFILE="data/processed/processed_carpentry_workshops_UK_$(date +'%Y-%m-%d')_redash.csv"
INSTRUCTORS_DATAFILE="data/processed/processed_carpentry_instructors_UK_$(date +'%Y-%m-%d')_redash.csv"

# Get the data from redash
echo Getting the data
python extract_and_process_redash.py -pw $WORKSHOPS_DATAFILE -pi $INSTRUCTORS_DATAFILE
echo

# Define the analysis files
ANALYSED_WORKSHOPS="data/analyses/analysed_carpentry_workshops_UK_$(date +'%Y-%m-%d').csv"
ANALYSED_INSTRUCTORS="data/analyses/analysed_carpentry_instructors_UK_$(date +'%Y-%m-%d').csv"

# Produce workshop output data.
echo Analysing the workshop data
python analyse_workshops.py -in $WORKSHOPS_DATAFILE -out $ANALYSED_WORKSHOPS
echo

# Produce instructor output data.
echo Analysing the instructor data
python analyse_instructors.py -in $INSTRUCTORS_DATAFILE -out $ANALYSED_INSTRUCTORS
echo

# Push the processed and analysed data back to GitHub
date=$(date +"%Y-%m-%d")
git add data/analyses/ data/processed data/raw
git commit -m "Adding carpentry and workshop data for ${date}."
git push

# This next bit assumes that there is a clone of the metrics repository
# hanging off the home directory. We will copy the output files to that
# repository. Add them, commit them, do a git pull of the repo contents
# and then push them to the metrics repository.
#cp ./data/analyses/${outfile1} ~/metrics/training/workshops/analyses
#cp ./data/analyses/${outfile2} ~/metrics/training/workshops/analyses

# Go to the repository, add and commit the files.
#cd ~/metrics/training/workshops/analyses
#git add ${outfile1}
#git add ${outfile2}
#git commit -m "Adding carpentry and workshop data for ${date}."
# Make sure the repo is up to date.
#git pull  
# Now push the results.
#git push 
