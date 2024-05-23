User Guide
===============

Preprocessing of Race Tube Images
---------------
1. Crop your scanned race tube image as desired, in the image viewer program of choice, leaving a small amount of background on either long edge
2. No need to make your image greyscale, fix its rotation, or increase contrast- Rhythmidia will take care of all of this internally!
3. Race tube images can be .png, .tif, .tiff, .jpg, .jpeg, or .svg

Uploading and Analyzing an Image
---------------

1. Upon opening the software, you will be greeted with the “Home” tab, which will look like this:
![Home Tab (blank)](images/screenshots/HomeTabBlank.png)
 .. image:: https://github.com/Pelham-Lab/rhythmidia/blob/main/images/screenshots/HomeTabBlank.png?raw=true
    NOTE:If you want to add tubes to an existing experiment file, go to File -> Open experiment File (or press ⌘O), although this is not necessary
2. To upload a new race tube image, click the button labeled “Upload Race Tube Image”
![Upload Image Button](images/screenshots/UploadImageButton.png)
    a. Your image will appear in the center of the screen
    ![Image Analysis](images/screenshots/ImageAnal1.png)
    b. Uploading an image enables the options to rotate and to lock & analyze your image
    ![Image Adjustment Buttons](images/screenshots/ImageChangeButtons.png)
3. Rotate your image so that the growth direction of the tubes is from left to right across your screen
    a. To rotate your image 90 degrees clockwise, click the button labeled “Rotate”
4. When you are satisfied with your image’s orientation, click the button labeled “Lock & Analyze Image”
5. Rhythmidia will try to identify horizontal lines corresponding to the horizontal boundaries of the tubes in your image, including the lower and upper bounds below and above the final and first tubes
    a. One line between each two tubes
![Horizontal Line Identification](images/screenshots/ImageAnal2.png)
6. You will be directed to verify these lines:
    a. To remove an incorrect line, simply click on the line
    b. To add a missing line, simply click in an unoccupied position on the image
7. When you are satisfied with the positions of all tube demarcation lines, click the button labeled “Proceed”
8. Repeat steps 6-8 for time marks (red) and for bands (orange)
![Time Mark Identification](images/screenshots/ImageAnal3.png)
![Banding Identification](images/screenshots/ImageAnal4.png)
![Time Marks and Banding Identification](images/screenshots/ImageAnal5.png)
    NOTE: At any time before saving tubes to the file, you may click the button labeled “Cancel image analysis”, which will reset the image analysis process and remove your uploaded image, while leaving open any open experiment file
    NOTE: Be certain to record any differences in marking times in the mark sheet (left) before proceeding further. If tubes were marked at the same time every day, leave as the default setting (0 for all)
    NOTE: The time marks will temporarily disappear while marking conidial peaks.
9. After you are satisfied with the positions of the bands and click “Proceed”, you will be able to see a preliminary calculation of the period of each tube below
    NOTE: if there is an issue at this stage (i.e. a missed or duplicated identifier) cancel image analysis and reload the image
![Preliminary Data](images/screenshots/ImageAnal6.png)
10. You will now have the option to click the button labeled “Save Tubes to File”
    a.  This will bring up a popup asking for a name for the pack of tubes in the current image before it saves them to file
    ![Pack Name Prompt](images/screenshots/PackName.png)
    b. If you are working within an existing experiment file, this will simply add this pack to the file and update it
    c. Otherwise, you will be prompted to Save As a new experiment file for these tubes

The Experiment Tab
---------------

1. Whether opening an existing experiment file or working from a new pack image, granular experiment data, plots, and statistical analysis data are located on the Experiment tab
![Experiment Tab](images/screenshots/ExperimentTabBlank.png)
2. Experiment data (Entry, Pack, Tube # in pack, Period calculated 3 ways, and Growth rate) is located in the table in the top left
![Experiment tab](images/screenshots/ExperimentTab.png)
![Experiment tab](images/screenshots/ExperimentTab2.png)
3. In the top right is the frame for statistical analysis of any number of tubes:
![Manual Statistical Analysis](images/screenshots/ManualStatAnal.png)
![CWT Statistical Analysis](images/screenshots/WaveletStatAnal.png)
    a. Select packs, tubes, and a method of period analysis in the 3 lists
    b. To select multiple packs or tubes, use control-click
    c. Click the button labeled “Analyze” to generate mean period, standard deviation, and standard error
    d. Click the button labeled “Export Data” to export a .csv of the data for each tube selected
    e. Click the button labeled “Export Analysis” to export a .csv of the analysis of the selected tubes
4. In the bottom half is the plot frame for plotting densitometry and a periodogram of a single tube:
![Sokolove-Bushell Periodogram](images/screenshots/SokoloveBushellPlot.png)
![Lomb-Scargle Periodogram](images/screenshots/LombScarglePlot.png)
![CWT Heatmap](images/screenshots/WaveletPlot.png)
    a. Select pack, tube, and type of periodogram in the 3 lists
    b. Click the button labeled “Plot” to generate a densitometry plot and periodogram of the selected data
    c. Click the button labeled “Save Plot” to save an image of the dual plot in file format of choice
    d. Click the button labeled “Save Densitometry” to save a .csv of the densitometry data
    e. Click the button labeled “Save Periodogrammetry” to save a .csv of the periodogrammetry data
5. At the bottom left is a button labeled "Display Pack Image"
    a. This button will display a popup window containing the greyscale version of the image corresponding to whichever pack is selected in the bottom left list that was the exact image used for analysis
![Image Popup](images/screenshots/PackImagePopup.png)

Functions Overview
---------------

Open Experiment File      (⌘O)

Close Experiment File     (⌘C)

Save File                 (⌘S)

Save as…                 (↑⌘S)

Set working directory     (⌘D)

Open graphics preferences (⌘P)