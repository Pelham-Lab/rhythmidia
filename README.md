<img src="images/icons/rhythmidiaLogoBanner.jpg" width=50% margin-left=25%></img>

Rhythmidia
---
<!--[//]: # (Badges)
[![GitHub Actions Build Status](https://github.com/REPLACE_WITH_OWNER_ACCOUNT/rhythmidia/workflows/CI/badge.svg)](https://github.com/REPLACE_WITH_OWNER_ACCOUNT/rhythmidia/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/REPLACE_WITH_OWNER_ACCOUNT/Rhythmidia/branch/main/graph/badge.svg)](https://codecov.io/gh/REPLACE_WITH_OWNER_ACCOUNT/Rhythmidia/branch/main)-->

### Race tube image analysis for circadian period elucidation in Python.
---
## Installation and Program Launch
<!--1. Download the rhythmidia-main.zip file and move it to your Documents folder (or location of choice)
2. Unzip rhythmidia-main.zip
    <br />a. This will create the folder rhythmidia-main
3. Open the Terminal application on Mac
4. Navigate to the rhythmidia-main folder in Terminal
5. Run the command pip install .
6. To run Rhythmidia, run the command -->
1. In a conda environment running Python >=3.11, run the command 
```console
pip install git+https://github.com/Pelham-Lab/rhythmidia.git
```
2. To run Rhythmidia run the command 
```console
rhythmidia
```
<br />  NOTE: The terminal window used to launch Rhythmidia must remain open while the program is in use.

---

## Rhythmidia Right Out of the Box
1. The first time you open a new installation of the program, you will be prompted to select a working directory. From this directory, the program will, by default, look for race tube images, and will by default, save data<br />
    a. This can be changed later at any time<br />
    b. You are not restricted to using this directory, it is purely for your convenience<br />
    c. This is where analysis data will be exported by default<br />
2. That’s it! You can start analyzing images immediately.
<br />        NOTE: On some newer Mac laptops with variable-force-click trackpads, you may find that some clicks are not picked up effectively unless you click with full force.
   
---
## Preprocessing of Race Tube Images
1. Crop your scanned race tube image as desired, in the image viewer program of choice, leaving a small amount of background on either long edge
2. No need to make your image greyscale, fix its rotation, or increase contrast- Rhythmidia will take care of all of this internally!
3. Race tube images can be .png, .tif, .tiff, .jpg, .jpeg, or .svg

---
## Uploading and Analyzing an Image
1. Upon opening the software, you will be greeted with the “Home” tab, which will look like this:
![Home Tab (blank)](images/screenshots/HomeTabBlank.png)
    NOTE:If you want to add tubes to an existing experiment file, go to File -> Open experiment File (or press ⌘O), although this is not necessary
2. To upload a new race tube image, click the button labeled “Upload Race Tube Image”<br />
![Upload Image Button](images/screenshots/UploadImageButton.png)
    a. Your image will appear in the center of the screen<br />
    ![Image Analysis](images/screenshots/ImageAnal1.png)
    b. Uploading an image enables the options to rotate and to lock & analyze your image<br />
    ![Image Adjustment Buttons](images/screenshots/ImageChangeButtons.png)
3. Rotate your image so that the growth direction of the tubes is from left to right across your screen<br />
    a. To rotate your image 90 degrees clockwise, click the button labeled “Rotate”<br />
4. When you are satisfied with your image’s orientation, click the button labeled “Lock & Analyze Image”
5. Rhythmidia will try to identify horizontal lines corresponding to the horizontal boundaries of the tubes in your image, including the lower and upper bounds below and above the final and first tubes.
    a. One line between each two tubes.
![Horizontal Line Identification](images/screenshots/ImageAnal2.png)
6. You will be directed to verify these lines:<br />
    a. To remove an incorrect line, simply click on the line<br />
    b. To add a missing line, simply click in an unoccupied position on the image<br />
7. When you are satisfied with the positions of all tube demarcation lines, click the button labeled “Proceed”
8. Repeat steps 6-8 for time marks (red) and for bands (orange)<br />
![Time Mark Identification](images/screenshots/ImageAnal3.png)
![Banding Identification](images/screenshots/ImageAnal5.png)
    NOTE: At any time before saving tubes to the file, you may click the button labeled “Cancel image analysis”, which will reset the image analysis process and remove your uploaded image, while leaving open any open experiment file<br />
    NOTE: Be certain to record any differences in marking times in the mark sheet (left) before proceeding further. If tubes were marked at the same time every day, leave as the default setting (0 for all).<br />
    NOTE: The time marks will temporarily disappear while marking conidial peaks. 
10. After you are satisfied with the positions of the bands and click “Proceed”, you will be able to see a preliminary calculation of the period of each tube below
![Preliminary Data](images/screenshots/ImageAnal6.png)
11. You will now have the option to click the button labeled “Save Tubes to File”<br />
    a.  This will bring up a popup asking for a name for the pack of tubes in the current image before it saves them to file<br />
    ![Pack Name Prompt](images/screenshots/PackName.png)
    <br />b. If you are working within an existing experiment file, this will simply add this pack to the file and update it<br />
    c. Otherwise, you will be prompted to Save As a new experiment file for these tubes<br />

## The Experiment Tab
1. Whether opening an existing experiment file or working from a new pack image, granular experiment data, plots, and statistical analysis data are located on the Experiment tab
![Experiment Tab](images/screenshots/ExperimentTabBlank.png)
2. Experiment data (Entry, Pack, Tube # in pack, Period calculated 3 ways, and Growth rate) is located in the table in the top left
![Experiment tab](images/screenshots/ExperimentTab.png)
![Experiment tab](images/screenshots/ExperimentTab2.png)
3. In the top right is the frame for statistical analysis of any number of tubes:<br />
![Manual Statistical Analysis](images/screenshots/ManualStatAnal.png)
![CWT Statistical Analysis](images/screenshots/WaveletStatAnal.png)
    a. Select packs, tubes, and a method of period analysis in the 3 lists<br />
    b. To select multiple packs or tubes, use control-click<br />
    c. Click the button labeled “Analyze” to generate mean period, standard deviation, and standard error<br />
    d. Click the button labeled “Export Data” to export a .csv of the data for each tube selected<br />
    e. Click the button labeled “Export Analysis” to export a .csv of the analysis of the selected tubes<br />
4. In the bottom half is the plot frame for plotting densitometry and a periodogram of a single tube:<br />
![Sokolove-Bushell Periodogram](images/screenshots/SokoloveBushellPlot.png)
![Lomb-Scargle Periodogram](images/screenshots/LombScarglePlot.png)
![CWT Heatmap](images/screenshots/WaveletPlot.png)
    a. Select pack, tube, and type of periodogram in the 3 lists<br />
    b. Click the button labeled “Plot” to generate a densitometry plot and periodogram of the selected data<br />
    c. Click the button labeled “Save Plot” to save an image of the dual plot in file format of choice<br />
    d. Click the button labeled “Save Densitometry” to save a .csv of the densitometry data<br />
    e. Click the button labeled “Save Periodogrammetry” to save a .csv of the periodogrammetry data<br />
5. At the bottom left is a button labeled "Display Pack Image". This button will display a popup window containing the greyscale version of the image corresponding to whichever pack is selected in the bottom left list that was the exact image used for analysis.
![Image Popup](images/screenshots/PackImagePopup.png)

## Functions Overview
Open Experiment File      (⌘O)<br />
Close Experiment File     (⌘C)<br />
Save File                 (⌘S)<br />
Save as…                 (↑⌘S)<br />
Set working directory     (⌘D)<br />
Open graphics preferences (⌘P)<br />

---
## Changelog
V0.01: 


---

### Copyright

Copyright (c) 2024, Pelham Lab - Washington University School of Medicine 


#### Acknowledgements
 
Project based on the 
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.1.

Logo adapted from a [DALL·E](https://labs.openai.com/)-generated image.
