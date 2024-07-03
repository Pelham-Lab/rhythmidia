<!--<img src="images/icons/rhythmidiaLogoBanner.jpg" width=50% margin-left=25%></img>-->
<img src="https://github.com/Pelham-Lab/rhythmidia/blob/main/images/icons/rhythmidiaLogoBanner.jpg?raw=true" width=50% margin-left=25%></img>

Rhythmidia
---
### Race tube image analysis for circadian period elucidation in Python.
---
## Installation and Program Launch
1. Rhythmidia must be installed in a Python environment running Python 3.11 or higher using pip. Rhythmidia runs on Unix-like operating systems including macOS and Linux. In order to install Rhythmidia, simply run the command: 
```console
pip install rhythmidia
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
<!--![Home Tab (blank)](images/screenshots/HomeTabBlank.png)-->
![Home Tab (blank)](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/HomeTabBlank.png?raw=true)
    NOTE:If you want to add tubes to an existing experiment file, go to File -> Open experiment File (or press ⌘O), although this is not necessary
2. To upload a new race tube image, click the button labeled “Upload Race Tube Image”<br />
<!--![Upload Image Button](images/screenshots/UploadImageButton.png)-->
![Upload Image Button](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/UploadImageButton.png?raw=true)
    a. Your image will appear in the center of the screen<br />
    <!--![Image Analysis](images/screenshots/ImageAnal1.png)-->
    ![Image Analysis](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ImageAnal1.png?raw=true)
    b. Uploading an image enables the options to rotate and to lock & analyze your image<br />
    <!--![Image Adjustment Buttons](images/screenshots/ImageChangeButtons.png)-->
    ![Image Adjustment Buttons](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ImageChangeButtons.png?raw=true)
3. Rotate your image so that the growth direction of the tubes is from left to right across your screen<br />
    a. To rotate your image 90 degrees clockwise, click the button labeled “Rotate”<br />
4. When you are satisfied with your image’s orientation, click the button labeled “Lock & Analyze Image”
5. Rhythmidia will try to identify horizontal lines corresponding to the horizontal boundaries of the tubes in your image, including the lower and upper bounds below and above the final and first tubes
    a. One line between each two tubes
<!--![Horizontal Line Identification](images/screenshots/ImageAnal2.png)-->
![Horizontal Line Identification](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ImageAnal2.png?raw=true)
6. You will be directed to verify these lines:<br />
    a. To remove an incorrect line, simply click on the line<br />
    b. To add a missing line, simply click in an unoccupied position on the image<br />
7. When you are satisfied with the positions of all tube demarcation lines, click the button labeled “Proceed”
8. Repeat steps 6-8 for time marks (red) and for bands (orange)<br />
<!--![Time Mark Identification](images/screenshots/ImageAnal3.png)-->
<!--![Banding Identification](images/screenshots/ImageAnal4.png)-->
<!--![Time Marks and Banding Identification](images/screenshots/ImageAnal5.png)-->
![Time Mark Identification](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ImageAnal3.png?raw=true)
![Banding Identification](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ImageAnal4.png?raw=true)
![Time Marks and Banding Identification](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ImageAnal5.png?raw=true)
    NOTE: At any time before saving tubes to the file, you may click the button labeled “Cancel image analysis”, which will reset the image analysis process and remove your uploaded image, while leaving open any open experiment file<br />
    NOTE: Be certain to record any differences in marking times in the mark sheet (left) before proceeding further. If tubes were marked at the same time every day, leave as the default setting (0 for all)<br />
    NOTE: The time marks will temporarily disappear while marking conidial peaks.
9. After you are satisfied with the positions of the bands and click “Proceed”, you will be able to see a preliminary calculation of the period of each tube below<br />
    NOTE: if there is an issue at this stage (i.e. a missed or duplicated identifier) cancel image analysis and reload the image
<!--![Preliminary Data](images/screenshots/ImageAnal6.png)-->
![Preliminary Data](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ImageAnal6.png?raw=true)
10. You will now have the option to click the button labeled “Save Tubes to File”<br />
    a.  This will bring up a popup asking for a name for the pack of tubes in the current image before it saves them to file<br />
    <!--![Pack Name Prompt](images/screenshots/PackName.png)-->
    ![Pack Name Prompt](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/PackName.png?raw=true)
    <br />b. If you are working within an existing experiment file, this will simply add this pack to the file and update it<br />
    c. Otherwise, you will be prompted to Save As a new experiment file for these tubes<br />

## The Experiment Tab
1. Whether opening an existing experiment file or working from a new pack image, granular experiment data, plots, and statistical analysis data are located on the Experiment tab
<!--![Experiment Tab](images/screenshots/ExperimentTabBlank.png)-->
![Experiment Tab](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ExperimentTabBlank.png?raw=true)
2. Experiment data (Entry, Pack, Tube # in pack, Period calculated 3 ways, and Growth rate) is located in the table in the top left
<!--![Experiment tab](images/screenshots/ExperimentTab.png)-->
<!--![Experiment tab](images/screenshots/ExperimentTab2.png)-->
![Experiment tab](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ExperimentTab.png?raw=true)
![Experiment tab](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ExperimentTab2.png?raw=true)
3. In the top right is the frame for statistical analysis of any number of tubes:<br />
<!--![Manual Statistical Analysis](images/screenshots/ManualStatAnal.png)-->
<!--[CWT Statistical Analysis](images/screenshots/WaveletStatAnal.png)-->
![Manual Statistical Analysis](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/ManualStatAnal.png?raw=true)
![CWT Statistical Analysis](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/WaveletStatAnal.png?raw=true)
    a. Select packs, tubes, and a method of period analysis in the 3 lists<br />
    b. To select multiple packs or tubes, use control-click<br />
    c. Click the button labeled “Analyze” to generate mean period, standard deviation, and standard error<br />
    d. Click the button labeled “Export Data” to export a .csv of the data for each tube selected<br />
    e. Click the button labeled “Export Analysis” to export a .csv of the analysis of the selected tubes<br />
4. In the bottom half is the plot frame for plotting densitometry and a periodogram of a single tube:<br />
<!--![Sokolove-Bushell Periodogram](images/screenshots/SokoloveBushellPlot.png)-->
<!--![Lomb-Scargle Periodogram](images/screenshots/LombScarglePlot.png)-->
<!--![CWT Heatmap](images/screenshots/WaveletPlot.png)-->
![Sokolove-Bushell Periodogram](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/SokoloveBushellPlot.png?raw=true)
![Lomb-Scargle Periodogram](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/LombScarglePlot.png?raw=true)
![CWT Heatmap](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/WaveletPlot.png?raw=true)
    a. Select pack, tube, and type of periodogram in the 3 lists<br />
    b. Click the button labeled “Plot” to generate a densitometry plot and periodogram of the selected data<br />
    c. Click the button labeled “Save Plot” to save an image of the dual plot in file format of choice<br />
    d. Click the button labeled “Save Densitometry” to save a .csv of the densitometry data<br />
    e. Click the button labeled “Save Periodogrammetry” to save a .csv of the periodogrammetry data<br />
5. At the bottom left is a button labeled "Display Pack Image"
    a. This button will display a popup window containing the greyscale version of the image corresponding to whichever pack is selected in the bottom left list that was the exact image used for analysis<br />
<!--![Image Popup](images/screenshots/PackImagePopup.png)-->
![Image Popup](https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/PackImagePopup.png?raw=true)

## Functions Overview
Open Experiment File      (⌘O)<br />
Close Experiment File     (⌘C)<br />
Save File                 (⌘S)<br />
Save as…                 (↑⌘S)<br />
Set working directory     (⌘D)<br />
Open graphics preferences (⌘P)<br />

---
## Changelog
v0.2.1: Fixed a failure to save experiment files introduced by a change in a dependency.

v0.1.1: Changed calculation of growth rate to scale with dynamic time windows. Minor bugfix re: dynamic time window selection UI. Temporarily removed "Edit Packs" feature pending improvements. NOT backwards compatible with experiment files generated pre-v0.1.1.

v0.0.5 - V0.0.13: Documentation update to display images in PyPI documentation.

V0.0.2 - V0.0.4: Documentation update to create readthedocs files.

V0.0.1: First public, stable release concurrent with upload to PyPI.


---

### Copyright

Copyright (c) 2024, Pelham Lab - Washington University School of Medicine 


#### Acknowledgements
 
Project based on the 
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.1.

Logo adapted from a [DALL·E](https://labs.openai.com/)-generated image.
