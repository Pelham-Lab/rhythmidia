![rhythmidia](rhythmidiaLogoBanner.jpg)

Rhythmidia
==============================
<!--[//]: # (Badges)
[![GitHub Actions Build Status](https://github.com/REPLACE_WITH_OWNER_ACCOUNT/rhythmidia/workflows/CI/badge.svg)](https://github.com/REPLACE_WITH_OWNER_ACCOUNT/rhythmidia/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/REPLACE_WITH_OWNER_ACCOUNT/Rhythmidia/branch/main/graph/badge.svg)](https://codecov.io/gh/REPLACE_WITH_OWNER_ACCOUNT/Rhythmidia/branch/main)-->

### Race tube image analysis and Neurospora crassa circadian period elucidation in Python. (Rest of blurb here)
==============================
## Installation instructions pending.
==============================
## Race Tube Images
1. Crop your scanned race tube image as desired, leaving some background on either edge
2. No need to make your image greyscale, fix its rotation, or increase contrast- Rhythmidia will take care of all of this internally!
3. Race tube images can be .png, .tif, .tiff, .jpg, .jpeg, or .svg

## Rhythmidia out of the Box
1. The first time you open a new installation of the program, you will be prompted to select a working directory from which the program will by default get race tube images and to which the program will by default save data<br />
    a. This can be changed later at any time.<br />
    b. You are not restricted to using this directory, it is purely for your convenience<br />
2. That’s it! You can start analyzing images immediately.

## Uploading and Analyzing an Image
1. Upon opening the software, you will be greeted with the “Home” tab, which will look like this:
2. If you want to add tubes to an existing experiment file, go to File -> Open experiment File (or press ⌘O)
    a. If you want to start from scratch, you can skip this step
3. To upload a new race tube image, click the button labeled “Upload Race Tube Image”<br />
    a. Your image will appear in the center of the screen<br />
    b. Uploading an image enables the options to rotate and to lock & analyze your image<br />
4. Rotate your image so that the growth direction of the tubes is from left to right across your screen<br />
    a. To rotate your image 90 degrees clockwise, click the button labeled “Rotate”<br />
5. When you are satisfied with your image’s orientation, click the button labeled “Lock & Analyze Image”
6. Rhythmidia will try to identify horizontal lines corresponding to the horizontal boundaries of the tubes in your image, including the lower and upper bounds below and above the final and first tubes.
7. You will be directed to verify these lines:<br />
    a. To remove an incorrect line, simply click on the line<br />
    b. To add a missing line, simply click in an unoccupied position on the image<br />
8. When you are satisfied with the positions of all lines, click the button labeled “Proceed”
9. Repeat steps 6-8 for time marks (red) and for bands (orange)<br />
10. At any time before saving tubes to file, you may click the button labeled “Cancel image analysis”, which will reset the image analysis process and remove your uploaded image, while leaving open any open experiment file
11. After you are satisfied with the positions of bands and click “Proceed”, you will be able to see a preliminary calculation of the period of each tube below
12. You will now have the option to click the button labeled “Save Tubes to File”<br />
    a.  This will bring up a popup asking for a name for the pack of tubes in the current image before it saves them to file<br />
    b. If you are working within an existing experiment file, this will simply add this pack to the file and update it<br />
    c. Otherwise, you will be prompted to Save As a new experiment file for these tubes<br />

## The Experiment Tab
1. Whether opening an existing experiment file or working from a new pack image, granular experiment data, plots, and statistical analysis data are located on the Experiment tab
2. Experiment data (Entry, Pack, Tube # in pack, Period calculated 3 ways, Growth rate) is located in the table in the top left
3. In the top right is the frame for statistical analysis of any number of tubes:<br />
    a. Select packs, tubes, and a method of period analysis in the 3 lists<br />
    b. To select multiple packs or tubes, use control-click<br />
    c. Click the button labeled “Analyze” to generate mean period, standard deviation, and standard error<br />
    d. Click the button labeled “Export Data” to export a csv of the data for each tube selected<br />
    e. Click the button labeled “Export Analysis” to export a csv of the analysis of the selected tubes<br />
4. In the bottom half is the plot frame for plotting densitometry and a periodogram of a single tube:<br />
    a. Select pack, tube, and type of periodogram in the 3 lists<br />
    b. Click the button labeled “Plot” to generate a densitogram and periodogram of the selected plot<br />
    c. Click the button labeled “Save Densitogram” to save a .png of the densitogram<br />
    d. Click the button labeled “Save Periodogram” to save a .png of the periodogram<br />
    e. Click the button labeled “Save Densitometry” to save a .csv of the densitometry data<br />
    f. Click the button labeled “Save Periodogrammetry” to save a .csv of the periodogrammetry data<br />
5. At the bottom left is a button labeled "Display Pack Image". This button will display a popup window containing the greyscale version of the image corresponding to whichever pack is selected in the bottom left list.

## Functions Overview
Open Experiment File      (⌘O)<br />
Save File                 (⌘S)<br />
Save as…                 (↑⌘S)<br />
Set working directory     (⌘D)<br />
Open graphics preferences (⌘P)<br />

==============================
## Changelog
V0.01: 


==============================

### Copyright

Copyright (c) 2023, Alex Keeley


#### Acknowledgements
 
Project based on the 
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.1.

Logo generated with the assistance of [DALL·E](https://labs.openai.com/).
