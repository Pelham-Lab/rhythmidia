from guizero import *
from tkinter import Canvas
import pyautogui
from PIL import Image, ImageEnhance
from skimage.feature import canny
from skimage.transform import probabilistic_hough_line
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker
import numpy
import csv
import os
import sys
from scipy.signal import find_peaks
from scipy.signal import savgol_filter
from scipy.signal import lombscargle
from scipy.signal import periodogram
import webbrowser

screen_width = pyautogui.size().width  # Get screen width
screen_height = pyautogui.size().height  # Get screen height
numpy.set_printoptions(threshold=sys.maxsize)
csv.field_size_limit(sys.maxsize)

appParameters = {"workingDir":"", "colorGraph":"black", "colorHoriz":"orange", "colorVert":"red", "colorBand":"blue"}  # Dictionary of settings
openFile = ""  # Name of open experiment file
workingDir = ""  # Name of working directory
imageName = ""  # Name of opened image
rawImage = None  # Blank variable for raw uploaded image
finalImage = None  # Blank variable for finalized uploaded image
rotateDeg = 0  # Degree of rotation of finalized image compared to raw
markHours = []  # Blank variable for mark file converted to number of hours
tubeLength = -1  # Blank variable for user-set tube length in mm
analState = -1  # Analysis state
prelimContents = [["Tube", "# Marks", "Average Period (hrs)"]]
tubeBounds = []  # each element is a tube, then [[ymin, ymax],...]
meanTubeWidth = -1  # Mean width of race tubes in uploaded image in px
horizontalLines = []  # Horizontal lines separating tubes in form [slope, intercept]
meanTubeSlope = None  # Mean slope of horizontal lines separating tubes
timeMarkLines = []  # Vertical lines where tubes are marked for time in form [x, ycenter, tube]
bandLines = []  # Locations of conidial bands in form [x, ycenter, tube]
densityProfiles = []  # Density profiles of tubes in b/w image format
tubesMaster = []  # Master list of tubes saved to file in form (per tube): [setName, imageName, imageData, tubeNumber, markHours, densProfile, growthRate, tubeRange, timeMarks, bandMarks]
canvas = None  # Plot entity
keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Shift, Command, S, O, P, D, H
plotAxes = []


def openSetup():  # Tasks to run on opening app
    """Tasks to run open opening the application. Reads in local parameters file to get user-defined settings, and preselects home tab."""
    global appParameters
    global workingDir

    with open("./parameters.txt", newline="") as parametersFile:  # Open local parameters.txt file
        reader = csv.reader(parametersFile, delimiter="=")  # Define csv reader
        for line in reader:  # For each line in parameters.txt
            appParameters[line[0]] = line[1]  # Populate appropriate element of parameters dictionary
    if (appParameters["workingDir"] == "" or not (os.path.exists(appParameters["workingDir"]))):  # If a working directory is not already specified in parameters, or points to a nonexistent directory
        setWorkDir()  # Prompt user to set a working directory
    else:  # Otherwise
        workingDir = appParameters["workingDir"]  # Set working directory to directory specified in parameters dictionary
    experFrame.hide()  # Hide experiment tab
    homeFrame.show()  # Show home tab


def setWorkDir():
    """Prompt user to set a working directory for the application, and save this to the local parameters file."""
    global appParameters
    global workingDir
    workingDir = app.select_folder(title="Please select working directory:", folder="/")  # Set working directory variable to user-specified directory via file selection popup
    appParameters["workingDir"] = workingDir  # Populate parameters dictionary with user-specified working directory
    updateParams()


def updateParams():
    global appParameters
    
    with open("./parameters.txt", newline="", mode="w") as parametersFile:  # Open local parameters.txt file
        writer = csv.writer(parametersFile, delimiter="=")  # Define csv writer
        for key in appParameters:  # For each key in parameters dictionary
            writer.writerow([key, appParameters[key]])  # Write as a line of parameters.txt


def openExp():  # Open an experiment file
    """Open an existing experiment file containing data from past images/tubes. Populate appropriate variables, including tubesMaster, with relevant information."""
    global openFile
    global workingDir
    global tubesMaster

    cancelRT()  # Zero out any existing information from a different open file or a newly analyzed race tube image
    tubesMaster = []  # Blank out master tube list in preparation for population from opened file
    if openFile == "":
        openFile = app.select_file(
            title="Select experiment file",
            folder=workingDir,
            filetypes=[["CronoPy Experiment", "*.cpyn"]],
            save=False,
            filename="",
        )  # Prompt user by popup to select experiment file from working directory and save name as openFile
    if openFile == "":  # If openFile remains blank
        return  # Abort function
    with open(openFile, newline="") as experimentFile:  # Open user-specified txt file
        tubesInFile = csv.reader(experimentFile, delimiter="%")  # Define csv reader
        for tube in tubesInFile:  # For each line of experiment file
            parsedTube = []  # Blank variable for parsed tube
            parsedTube.append(str(tube[0]))  # Add string of set name to parsed tube data
            parsedTube.append(str(tube[1]))  # Add string of image name to parsed tube data
            imageData = []  # Blank image data variable
            imageDataRaw = tube[2][1:-1].split("],[")  # Image data from file as list
            for row in imageDataRaw:  # For each row of image data
                dataRow = []  # Blank variable for row values
                for pixel in (row.strip().replace("[", "").replace("]", "").split(",")):  # For each value in row, excluding punctuation and delimited by ","
                    if pixel != "":  # If value is not blank
                        dataRow.append(int(pixel))  # Convert value to integer and add to row data
                imageData.append(dataRow)  # Add row data to image data
            parsedTube.append(imageData)  # Add parsed image data to parsed tube data
            parsedTube.append(int(tube[3]))  # Add integer of tube number in set to parsed tube data
            markHoursRaw = (
                tube[4]
                .strip()
                .replace(" ", "")
                .replace("[", "")
                .replace("]", "")
                .split(",")
            )  # Raw list of mark hour values
            for hours in enumerate(markHoursRaw):  # For each element of raw mark hours data
                markHoursRaw[hours[0]] = float(hours[1])  # Convert value to float from string
            parsedTube.append(markHoursRaw)  # Add parsed mark hours values to parsed tube data
            densityProfilesRaw = (
                tube[5]
                .strip()
                .replace(" ", "")
                .replace("[", "")
                .replace("]", "")
                .split(",")
            )  # Raw list of densitometry values
            for num in enumerate(densityProfilesRaw):  # For each element of raw densitometry data
                densityProfilesRaw[num[0]] = float(num[1])  # Convert value to float from string
            parsedTube.append(densityProfilesRaw)  # Add parsed densitometry values to parsed tube data
            parsedTube.append(float(tube[6]))  # Add integer of growth rate to parsed tube data
            tubeBoundsRaw = (tube[7][1:-1].replace(" ", "").split("],["))  # Raw list of tube boundary doubles
            pairs = []  # Blank list of tube boundary doubles
            for pairRaw in tubeBoundsRaw:  # For each double in raw list of tube boundary doubles
                pair = pairRaw.replace("[", "").replace("]", "").split(",")  # Remove [, ], and split at commas into list
                for yVal in enumerate(pair):  # For each number in boundary double
                    pair[yVal[0]] = float(yVal[1])  # Convert number to float from string
                pairs.append(pair)  # Add boundary double to list of tube boundary doubles
            parsedTube.append(pairs)  # Add parsed tube boundary doubles to parsed tube data
            timeMarks = (
                tube[8]
                .strip()
                .replace(" ", "")
                .replace("[", "")
                .replace("]", "")
                .split(",")
            )  # Raw list of time mark x positions
            for xVal in enumerate(timeMarks):  # For each element of raw time marks data
                timeMarks[xVal[0]] = int(xVal[1])  # Convert value to int from string
            parsedTube.append(timeMarks)  # Add parsed time mark x values to parsed tube data
            bandMarks = (
                tube[9]
                .strip()
                .replace(" ", "")
                .replace("[", "")
                .replace("]", "")
                .split(",")
            )  # Raw list of band marks positions
            for xVal in enumerate(bandMarks):  # For each element of raw band marks data
                bandMarks[xVal[0]] = int(xVal[1])  # Convert value to int from string
            parsedTube.append(bandMarks)  # Add parsed band marks values to parsed tube data
            tubesMaster.append(parsedTube)  # Add parsed tube data to master list of tubes
        populateExper(tubesMaster)  # Populate experiment data table
        popStatAnal()  # Populate statistical analysis frame
        popPlotTubes()  # Populate plot data frame


def saveExp():  # Save current experiment
    """Save experiment file to existing file, or prompt user to save as new file if not editing existing experiment file."""
    global openFile
    global workingDir
    global tubesMaster

    if openFile == "":  # If no currently open file
        saveAs("")  # Prompt user to save as new file
    else:  # If a file is already open
        with open(openFile, newline="", mode="w") as experimentFile:  # Open current experiment file
            writer = csv.writer(experimentFile, delimiter="%")  # Define csv writer
            for tube in tubesMaster:  # For each tube in master tube list
                writer.writerow(tube)  # Write new line for tube to experiment file
        openExp()  # Open current experiment again to update application


def saveAs(name=""):  # Save current experiment as new experiment file
    """Prompt user to provide a file name to save current data as a new experiment file."""
    global openFile
    global workingDir

    openFile = app.select_file(
        title="Save as...",
        folder=workingDir,
        filetypes=[["Chronidia Experiment", "*.cpyn"]],
        save=True,
        filename=name,
    )  # Prompt user to create a new file name with popup, and save name as openFile
    if not (openFile == ""):  # If file name is not left blank
        saveExp()  # Save experiment as chosen file name


def selectHome():  # Swap to home tab
    """Select home tab."""
    if homeFrame.visible is False:  # If home tab is not already selected
        experFrame.hide()  # Hide experiment tab
        homeFrame.show()  # Show home tab
    app.update()  # Update app object


def selectExper():  # Swap to experiments tab
    """Select experiment tab."""
    if experFrame.visible is False:  # If experiment tab not already selected
        homeFrame.hide()  # Hide home tab
        experFrame.show()  # Show experiment tab
    app.update()  # Update app object


def fUploadRT():  # Prompt file upload of race tube image
    """Prompt user to upload a new race tube image, and display it in the image frame."""
    global rawImage
    global imageName
    global rotateDeg
    global analState

    analState = 0  # Set analysis state to 0
    rotateDeg = 0  # Set degree of image rotation to 0
    imageName = app.select_file(
        title="Select race tube image",
        folder=workingDir,
        filetypes=[["TIFF", "*.tif"], ["PNG", "*.png"], ["JPG", "*.jpg"], ["JPEG", "*.jpeg"], ["SVG", "*.svg"]],
        save=False,
        filename="",
    )  # Prompt user to select a .tif image in the working directory to analyze, and set file name as imageName
    rawImage = Image.open(imageName).resize((1160, 400))  # Open raw image file as 1160x400px image object
    rightImage = rawImage  # Set intermediate image to raw image
    dispRTImage(rightImage)  # Display race tube image
    lockButt.enable()  # Enable button to lock image and analyze
    rotateRtButt.enable()  # Enable button to rotate image 90 degrees
    resetButt.enable()  # Enable button to reset analysis


def fRotateRT():  # Rotate race tube image clockwise
    """Rotate current image 90 degrees clockwise."""
    global rawImage
    global rotateDeg

    rotateDeg += 90  # Increment rotation angle by 90 degrees clockwise
    rightImage = rawImage.rotate(rotateDeg, expand=1).resize((1160, 400))  # Set intermediate image to raw image rotated by rotateDeg degrees clockwise
    dispRTImage(rightImage)  # Display race tube image


def dispRTImage(image):
    """Display race tube image."""
    imageDraw.clear()  # Clear image frame
    imageDraw.image(0, 0, image)  # Display intermediate image in image frame


def fLockRT():
    """Lock image in current rotation and begin analysis prompts."""
    global rotateDeg
    global rawImage
    global finalImage
    global tubeLength

    # Lock
    uploadRtButt.disable()  # Disable upload image button
    rotateRtButt.disable()  # Disable rotate image button
    rtLength.disable()  # Disable tube length input
    lockButt.disable()  # Disable lock and analyze button
    proceedButt.enable()  # Enable proceed button
    rescanButt.enable() # Enable rescan button
    # Analyze
    finalDeg = 90 * ((rotateDeg / 90) % 4)  # Set final rotation angle to simplified rotation angle
    finalImage = rawImage.rotate(finalDeg, expand=1).resize((1160, 400))  # Set final image to raw image rotated by final rotation angle
    tubeLength = rtLength.value  # Set tube length to value in input box
    getMarkInfo()  # Save tube mark time values to variable
    horizAnalyze()  # Begin tube boundary analysis


def cancelRT():
    """Cancel current race tube image being analyzed and zero out all relevant global variables."""
    global analState
    global rawImage
    global imageName
    global rightImage
    global finalImage
    global prelimContents
    global tubeLength
    global tubeBounds
    global meanTubeWidth
    global meanTubeSlope
    global horizontalLines
    global timeMarkLines
    global bandLines
    global densityProfiles

    analState = -1  # Set analysis state to -1
    imageDraw.clear()  # Clear image frame
    rawImage, rightImage, finalImage = None, None, None  # Zero out image variables
    imageName = ""  # Zero out current image name
    prelimContents = [["Tube", "# Marks", "Average Period (hrs)"]]  # Reset preliminary data contents to headers
    prelimText.value = ""  # Zero out preliminary data text box
    tubeLength = -1  # Zero out tube length
    tubeBounds = []  # Zero out tube boundaries list
    meanTubeWidth = -1  # Zero out mean tube width
    meanTubeSlope = None  # Zero out mean horizontal slope
    horizontalLines, timeMarkLines, bandLines = [], [], []  # Zero out horizontal, time mark, and band line lists
    densityProfiles = []  # Zero out densitometry
    consoleText.value = ""  # Zero out console text box

    uploadRtButt.enable()  # Enable upload race tube image button
    rotateRtButt.disable()  # Disable rotate image button
    rtLength.enable()  # Enable race tube length text box
    lockButt.disable()  # Disable lock and analyze button
    proceedButt.disable()  # Disable proceed button


def prelimUpdate():
    """Update preliminary data text box."""
    global prelimContents

    text = ""  # Blank string for text
    for line in prelimContents:  # For each line of preliminary data list
        text = (text + line[0] + " " * (7 - len(line[0])))  # Append tube number and spacing to text
        text = (text + line[1] + " " * (10 - len(line[1])))  # Append number of time marks and spacing to text
        text = (text + line[2] + " " * (23 - len(line[2])) + "\n")  # Append manually calculated period and spacing and newline to text
    prelimText.value = text  # Set preliminary data text box to text variable


def horizAnalyze():
    """Analyze horizontal boundaries of tubes in image."""
    global finalImage
    global analState
    global horizontalLines
    global meanTubeSlope
    global prelimContents

    analState = 1  # Set analysis state to 1
    editedImage = numpy.array(finalImage.convert("L"))  # Create numpy array of final image in greyscale
    cannyEdges = canny(editedImage, 2, 1, 25)  # Detect edges of greyscale image
    likelyHorizontalLines = probabilistic_hough_line(cannyEdges, threshold=10, line_length=75, line_gap=5)  # Get long lines from canny edges
    horizontalLineSlopes = []  # Empty list of slopes
    horizontalLineIntercepts = []  # Empty list of y intercepts
    for line in likelyHorizontalLines:  # For each probabilistic hough line
        if (line[1][0] - line[0][0]) == 0:  # If line is vertical
            slope = numpy.inf  # Set slope to infinity to avoid dividing by 0
        else:  # If line is not vertical
            slope = (line[1][1] - line[0][1]) / (line[1][0] - line[0][0])  # Set slope to slope of line calculated as rise/run
        intercept = (line[0][1] - slope * line[0][0])  # Set intercept to intercept of line calculated using slope and y position
        if abs(slope) < 2:  # If slope is not too steep
            horizontalLineSlopes.append(slope)  # Add slope to slope list
            horizontalLineIntercepts.append(intercept)  # Add intercept to intercept list
    horizontalLines = []  # Blank global list of tube boundary lines
    meanTubeSlope = numpy.mean(horizontalLineSlopes)  # Mean slope of horizontal tube boundary lines
    for line in range(0, len(horizontalLineSlopes)):  # For each horizontal line
        isDuplicate = 0  # Whether line is a duplicate of an accepted line (default to 0)
        for lin in horizontalLines:  # For each accepted horizontal line
            if (
                abs(horizontalLineIntercepts[line] - lin[1]) < 20
                or abs(meanTubeSlope - horizontalLineSlopes[line]) > 0.015
                or (numpy.sign(meanTubeSlope) != numpy.sign(horizontalLineSlopes[line]))
            ):  # If line intercept is too close to an accepted line, or slope is too divergent from mean slope of set, or sign of slope is different from mean slope
                isDuplicate = 1  # Line is a duplicate
        if isDuplicate == 0:  # If line is not a duplicate
            horizontalLines.append([horizontalLineSlopes[line], horizontalLineIntercepts[line]])  # Add line to accepted horizontal lines
    drawLines()  # Add lines to image
    analState = 2  # Set analysis state to 2
    consoleText.value = "Click a point on the image to add or remove race tube boundary lines. Please be sure to include lines a verytop and bottom of image. When satisfied, click the Proceed button."  # Set console text to horizontal line instructions


def identTubes():
    """Identify boundaries of tubes in image based on horizontal lines."""
    global finalImage
    global analState
    global horizontalLines
    global meanTubeSlope
    global meanTubeWidth
    global prelimContents

    analState = 3  # Set analysis state to 3
    for line in range(1, len(horizontalLines)):  # For gap between horizontal lines
        prelimContents.append([str(line), "", ""])  # Add a row to preliminary data contents list
    prelimUpdate()  # Update preliminary contents text box
    consoleText.value = ("Identifying race tube regions...")  # Set console box text to analysis step description
    horizontalLines.sort(key=lambda x: x[1])  # Sort horizontal lines by y value of intercepts (ie top to bottom of image)
    tubeCount = (len(horizontalLines) - 1)  # Set number of tubes to one less than number of boundary lines
    tubeWidths = []  # Blank list of tube widths
    for tube in range(0, tubeCount):  # For each tube
        pairs = []  # Blank list of tube boundary y position doubles
        for x in range(0, 1160):  # For each x along x axis of image
            yMin = (horizontalLines[tube][0] * x + horizontalLines[tube][1])  # Set low y to lower bound slope * x + lower bound y intercept
            yMax = (horizontalLines[tube + 1][0] * x + horizontalLines[tube + 1][1])  # Set high y to higher bound slope * x + higher bound y intercept
            pairs.append([yMin, yMax])  # Add double of y bounds to ranges list
            tubeWidths.append(yMax - yMin)  # Add difference in y bounds to widths list
        tubeBounds.append(pairs)  # Add ranges for tube to list of tube ranges
    meanTubeWidth = numpy.mean(tubeWidths)  # Set mean tube width to mean of tube widths
    vertAnalyze()  # Begin analysis of time mark locations


def vertAnalyze():
    """Analyze positions of vertical time marks in tubes."""
    global finalImage
    global analState
    global prelimContents
    global tubeBounds
    global meanTubeWidth
    global horizontalLines
    global meanTubeSlope
    global timeMarkLines

    analState = 4  # Set analysis state to 4
    contraster = ImageEnhance.Contrast(finalImage.convert("L"))  # Define contraster of numpy array of greyscale final image
    editedImage = numpy.invert(numpy.array(contraster.enhance(3)))  # Set numpy image array to contrast level 3
    drawLines()  # Add lines to image
    for tube in tubeBounds:  # For each tube in tubeBounds
        tubeWidth = tube[0][1] - tube[0][0]  # Record width of current tube at left end
        tubeNumber = int(tubeBounds.index(tube))  # Index of current tube within tubeBounds
        densityProfile = brightScan(editedImage, tube=tubeBounds.index(tube), linewidth=int(tubeWidth - 5))  # Create density profile of current tube
        densityProfileSmooth = savgol_filter(densityProfile, window_length=30, polyorder=3, mode="interp")  # Create Savitzky-Golay smoothed density profile of marks-corrected dataset
        peakIndices = find_peaks(densityProfileSmooth, distance=25, threshold=(None, None), prominence=5, wlen=300)[0].tolist()  # Get indices of local maxima of smoothed density profile
        for peakIndex in peakIndices:  # For each peak index
            peakX = peakIndex  # Set x to peak index
            peakY = (tube[peakIndex][0] + (tube[peakIndex][1] - tube[peakIndex][0]) / 2)  # Set y to midline of tube at x
            slopesLeft = []  # Blank list of slopes left of peak
            slopesRight = []  # Blank list of slopes right of peak
            for xWalk in range(2, 12, 2):  # For each x to one side or the other of peak
                if peakX + xWalk < 1160:  # If xWalk to the right is within image
                    slopesRight.append(abs((densityProfileSmooth[peakX + xWalk] - densityProfileSmooth[peakX + xWalk - 2])) / 2)  # Add granular slope to list of slopes
                if peakX - xWalk > 0:  # If xWalk to the left is within image
                    slopesLeft.append(abs((densityProfileSmooth[peakX - xWalk] - densityProfileSmooth[peakX - xWalk + 2])) / 2)  # Add granular slope to list of slopes
            slopeRight = numpy.mean(slopesRight)  # Mean slope to right of peak
            slopeLeft = numpy.mean(slopesLeft)  # Mean slope to left of peak
            slopeMin = numpy.min([slopeLeft, slopeRight])  # Minimum of two adjacent slopes to peak
            if peakX > 10 and peakX < 1150 and slopeMin > 1:  # If x is not on edges of image
                timeMarkLines.append([peakX, peakY, tubeNumber])  # Add time mark to list of time mark lines
        drawLines()  # Add lines to image
    analState = 5  # Set analysis state to 5
    consoleText.value = "Click a point on the image to add or remove time marks. Please be sure to mark the start point. When satisfied, click the Proceed button."  # Add directions to console


def brightScan(image, tubeNumber, profileWidth):
    """Create a density profile of a given tube within a given image given a profile line width."""
    global tubeBounds
    
    densityProfile = []  # Blank list of output densitometry
    for x in range(0, 1160):  # For each x pixel in image
        yMid = (tubeBounds[tubeNumber][x][0] + (tubeBounds[tubeNumber][x][1] - tubeBounds[tubeNumber][x][0]) / 2)  # Set midline y value
        densities = []  # Blank list of brightnesses at current x value
        for y in range(int(yMid - profileWidth/2), int(yMid + profileWidth/2)):  # For each y within line width at current x value
            if y < 400 and y > 0:  # If y is within image
                densities.append(image[y, x])  # Add brightness value to list
        densityProfile.append(numpy.mean(densities))  # Add mean brightness at x value to densitometry
    return densityProfile  # Return densitometry profile


def bandAnalyze():
    """Analyze locations of conidial banding within tubes in current image."""
    global finalImage
    global analState
    global densityProfiles
    global horizontalLines
    global timeMarkLines
    global meanTubeSlope
    global meanTubeWidth
    global tubeBounds
    global bandLines
    global prelimContents

    analState = 6  # Set analysis state to 6
    for tube in range(0, len(tubeBounds)):  # For each tube in tubeBounds
        numberOfMarks = 0  # Set number of marks in tube to 0
        for line in timeMarkLines:  # For each line in list of all time marks
            if line[2] == tube:  # If line y is in current tube
                numberOfMarks += 1  # Increment number of marks in tube by 1
        prelimContents[tube + 1][1] = str(numberOfMarks)  # Add number of marks to appropriate line of preliminary data contents list
    prelimUpdate()  # Update preliminary data text box
    contraster = ImageEnhance.Contrast(finalImage.convert("L"))  # Define contraster of numpy array of greyscale final image
    editedImage = numpy.array(contraster.enhance(3))  # Set numpy image array to contrast level 3
    originalImage = numpy.array(finalImage.convert("L"))  # Set numpy image array for precontrast ('original') image
    drawLines()  # Add lines to image
    for tube in tubeBounds:  # For each tube in tubeBounds
        tubeWidth = tube[0][1] - tube[0][0]  # Width of current tube at left end
        tubeNumber = int(tubeBounds.index(tube))  # Index of current tube in tubeBounds
        densityProfile = brightScan(editedImage, tube=tubeBounds.index(tube), linewidth=int(tubeWidth - 5))  # Create density profile of current tube
        densityProfileOriginal = brightScan(originalImage, tube=tubeBounds.index(tube), linewidth=int(tubeWidth - 5))  # Create density profile of current tube
        densityProfiles.append(densityProfileOriginal)  # Add to global density profile list
        densityProfileNoTimeMarks = densityProfile  # Remove dips due to time marks from density data
        for line in timeMarkLines:  # For each time mark (make densityProfileNoTimeMarks)
            if line[2] == tubeNumber:  # If time mark is in current tube
                windowRadius = 10  # Set radius of time mark deletion window
                lowX = line[0] - windowRadius  # Leftmost bound of deletion window
                highX = line[0] + windowRadius  # Rightmost bound of deletion window
                if lowX < 0:
                    lowX = 0
                if highX > 1160:
                    highX = 1160
                yIncrement = (densityProfile[highX] - densityProfile[lowX]) / (2*windowRadius+1)  # Set y increment of interpolation
                xIncrement = 0  # Set x increment of interpolation
                for xWalk in range(line[0] - windowRadius, line[0] + windowRadius):  # For x value in interp window
                    if xWalk < len(densityProfileNoTimeMarks) - 1 and xWalk > 0:  # If x is within image
                        densityProfileNoTimeMarks[xWalk] = densityProfile[lowX] + yIncrement * xIncrement  # Interpolate density
                    xIncrement += 1  # Increase x increment of interpolation
        densityProfileSmooth = savgol_filter(densityProfileNoTimeMarks, window_length=30, polyorder=4, mode="interp")  # Create list for Savitzky-Golay smoothed density profile of marks-corrected dataset
        peakIndices = find_peaks(densityProfileSmooth, distance=20, prominence=20, height=numpy.max(densityProfileSmooth) * 0.75)[0]  # Get indices of local maxima of smoothed density profile
        for peakIndex in peakIndices:  # For each peak index in smoothed density profile
            peakX = peakIndex  # Set x to index
            peakY = (tube[peakIndex][0] + (tube[peakIndex][1] - tube[peakIndex][0])/2)  # Set y to midline of tube
            if peakX > numpy.min(line[0] for line in timeMarkLines):  # If band is further right than the first time mark for its tube
                bandLines.append([peakX, peakY, tubeNumber])  # Add band to list
    drawLines()  # Draw lines
    analState = 7  # Set analysis state to 7
    consoleText.value = "Click a point on the image to add or remove bands. Remove erroneously identified bands from any non-banding tubes. When satisfied, click the Proceed button."  # Update console text


def drawLines():
    """Redraw image along with current accepted horizontal and vertical lines for time and band marks."""
    global horizontalLines
    global timeMarkLines
    global bandLines
    global meanTubeWidth
    global finalImage
    global tubeBounds
    global appParameters

    imageDraw.clear()  # Clear image canvas
    imageDraw.image(0, 0, finalImage)  # Add image to canvas
    for line in horizontalLines:  # For each horizontal line
        imageDraw.line(
            0, 
            line[1],
            1160, 
            line[1] + 1160 * line[0], 
            color=appParameters["colorHoriz"], 
            width=2
        )  # Draw the horizontal line
    for line in timeMarkLines:  # For each time mark
        imageDraw.line(
            line[0],
            line[1] - (meanTubeWidth / 2 - 5),
            line[0],
            line[1] + (meanTubeWidth / 2 - 5),
            color=appParameters["colorVert"],
            width=2,
        )  # Draw the time mark line
    for line in bandLines:  # For each band
        imageDraw.line(
            line[0],
            line[1] - (meanTubeWidth / 2 - 5),
            line[0],
            line[1] + (meanTubeWidth / 2 - 5),
            color=appParameters["colorBand"],
            width=2,
        )  # Draw the line for the band peak


def imageClickHandler(mouseClick):
    """Based on global analysis state, handle clicks on image to adjust line locations."""
    global analState
    global horizontalLines
    global timeMarkLines
    global bandLines
    global meanTubeSlope
    global meanTubeWidth
    global tubeBounds

    match analState:  # Based on analysis state
        case 2:  # Analysis state 2 (tube bounds)
            targetLineIndex = -1  # Set target to -1
            for line in horizontalLines:  # For each horizontal line
                if (abs(line[0] * mouseClick.x + line[1] - mouseClick.y) < 10):  # If click is close enough to an existing horizontal line
                    targetLineIndex = horizontalLines.index(line)  # Set proximal line to click as target line
            if targetLineIndex == -1:  # If no line is targeted by click
                newLineIntercept = (mouseClick.y - meanTubeSlope * mouseClick.x)  # Generate new intercept based on click position and mean horizontal slope
                horizontalLines.append([meanTubeSlope, newLineIntercept])  # Add new line to list of horizontal lines
            else:  # If a line is targeted by click
                horizontalLines.pop(targetLineIndex)  # Delete that line
            drawLines()  # Add lines to image
        case 5:  # Analysis state 5 (time marks)
            targetLineIndex = -1  # Set target to -1
            for line in timeMarkLines:  # For each time mark line
                if abs(line[0] - mouseClick.x) < 5 and abs(line[1] - mouseClick.y) < (meanTubeWidth/2+2):  # If click is close enough to an existing time mark line
                    targetLineIndex = timeMarkLines.index(line)  # Set proximal line to click as target line
            if targetLineIndex == -1:  # If no line is targeted by click
                newMarkX = mouseClick.x  # Set x to x of click
                newMarkTubeNumber = -1  # Set tube ID to -1
                for tube in tubeBounds:  # For each tube in tubeBounds
                    if (mouseClick.y > tube[newMarkX][0] and mouseClick.y < tube[newMarkX][1]):  # If click is within tube
                        newMarkTubeNumber = tubeBounds.index(tube)  # Set tube ID to current tube
                newMarkY = (tubeBounds[newMarkTubeNumber][newMarkX][0] + meanTubeWidth / 2)  # Set y to midline of tube containing click at x of click
                timeMarkLines.append([newMarkX, newMarkY, newMarkTubeNumber])  # Add new line to list of time mark lines
            else:  # If a line is targeted by click
                timeMarkLines.pop(targetLineIndex)  # Delete that line
            drawLines()  # Add lines to image
        case 7:  # Analysis state 7 (band locations)
            targetLineIndex = -1  # Set target to -1
            for line in bandLines:  # For each band line
                if abs(line[0] - mouseClick.x) < 5 and abs(line[1] - mouseClick.y) < (meanTubeWidth/2+2):  # If click is close enough to an existing band line
                    targetLineIndex = bandLines.index(line)  # Set proximal line to click as target line
            if targetLineIndex == -1:  # If no line is targeted by click
                newBandX = mouseClick.x  # Set x to x of click
                newBandTubeNumber = -1  # Set tube ID to -1s
                for tube in tubeBounds:  # For each tube in tubeBounds
                    if (mouseClick.y > tube[newBandX][0] and mouseClick.y < tube[newBandX][1]):  # If click is within tube
                        newBandTubeNumber = tubeBounds.index(tube)  # Set tube ID to current tube
                newBandY = (tubeBounds[newBandTubeNumber][newBandX][0] + meanTubeWidth / 2)  # Set y to midline of tube containing click at x of click
                bandLines.append([newBandX, newBandY, newBandTubeNumber])  # Add new line to list of band lines
            else:  # If a line is targeted by click
                bandLines.pop(targetLineIndex)  # Delete that line
            drawLines()  # Add lines to image


def getMarkInfo():
    """Save information from time mark table to variable."""
    global markHours

    numberOfHours = 0  # Set number of hours in row to 0
    for datum in markData:  # For each row of time mark table
        match (markData.index(datum) % 3):  # Based on index of text box in list of time mark data table cells
            case 0:  # If in first column
                numberOfHours = 24 * (int(datum.value))  # Set hours to number of days in row * 24
            case 1:  # If in second column
                numberOfHours += int(datum.value)  # Add to hours number of hours in row
            case 2:  # If in third column
                numberOfHours += (int(datum.value) / 60)  # Add to hours number of minutes in row / 60
                markHours.append(numberOfHours)  # Add number of hours to markHours


def storeTubesPrompt():
    """Create popup window prompting user to name set of tubes in current image before saving to file."""
    setNamePopup = Window(app, title="Pack name...", width=200, height=120)  # Popup window
    setNamePopup.show(wait=True)  # Show window as popup
    setNameTextBox = TextBox(setNamePopup)  # Text box for name of tube set
    setNameTextBox.focus()  # Focus name text box
    setNameButton = PushButton(setNamePopup, text="Confirm", command=lambda: [storeTubes(setName=setNameTextBox.value), setNamePopup.destroy()])  # Button to save tubes to file and close popup


def calcPeriods(densProfile, markHours, timeMarks, bandMarks, hrsLow, hrsHigh, tubeRange):
    """Calculate periods of a given tube's densitometry profile"""
    slopeCoeff = abs(1 / numpy.cos(numpy.arctan(((tubeRange[-1][1] + tubeRange[-1][0]) / 2- (tubeRange[0][1] + tubeRange[0][0]) / 2) / (1160))))  # Calculate coefficient to correct for slope
    # Calculate 'manual' period
    timeGaps = []  # List of time gaps in pixels per hour
    for mark in range(0, len(timeMarks) - 1):  # For each 2 consecutive time marks and corresponding hour values
        timeGaps.append((timeMarks[mark + 1] - timeMarks[mark])/ (markHours[mark + 1] - markHours[mark]))  # Add length of gap in pixels per hour to list of time gaps
    meanTimeGap = numpy.mean(timeGaps)  # Mean time gap in pixels per hour
    bandGaps = []  # List of band gaps in pixels
    for mark in range(0, len(bandMarks) - 1):  # For each 2 consecutive band marks
        bandGaps.append((bandMarks[mark + 1] - bandMarks[mark]))  # Add length of gap in pixels to list of band marks
    periodMan = ((numpy.mean(bandGaps) / numpy.mean(timeGaps)) * slopeCoeff)  # Set manual period to mean period between band gaps in hours, corrected for slope of tube in image
    # Calculate high and low periods in pixels
    plow = int(hrsLow * meanTimeGap)  # Lowest period to test (in pixels)
    phigh = int(hrsHigh * meanTimeGap)  # Highest period to test (in pixels)
    # Calculate Sokolove-Bushell periodogram
    freqSB, pgramSB = periodogram(densProfile, scaling="spectrum")  # Get Sokolove-Bushell periodogram (frequencies, power spectra in V^2)
    freqSB = freqSB.tolist()[1:]  # Convert S-B frequencies to list
    pgramSB = pgramSB.tolist()[1:]  # Convert S-B periodogram values to list
    # Calculate Lomb-Scargle Periodogram
    freqInterval = int(((2 * numpy.pi) / plow - (2 * numpy.pi) / phigh) / 0.0001)  # Number of angular frequencies to test for Lomb-Scargle at an interval of 0.0001
    freqLS = (numpy.linspace((2 * numpy.pi) / phigh, (2 * numpy.pi) / plow, freqInterval).tolist())  # Create list of angular frequencies to test for Lomb-Scargle periodogram
    pgramLS = lombscargle(list(range(0, 1160)), densProfile, freqLS)  # Get Lomb-Scargle periodogram
    pgramLS = pgramLS.tolist()  # Convert L-S periodogram values to list
    # Convert frequencies to periods
    perLenLS = ((2 * numpy.pi) / freqLS[pgramLS.index(numpy.max(pgramLS))])  # Convert frequency of maximal spectral density from Lomb-Scargle periodogram to horizontal length in pixels
    perLenSB = (1 / freqSB[pgramSB.index(numpy.max(pgramSB))])  # Convert frequency of maximal spectral density from Sokolove-Bushell periodogram to horizontal length in pixels
    pixPerHr = numpy.mean(timeGaps)
    hrPerPix = 1 / pixPerHr
    periodLS = perLenLS * hrPerPix * slopeCoeff
    periodSB = perLenSB * hrPerPix * slopeCoeff
    return (
        periodMan,
        periodSB,
        periodLS,
        freqSB,
        pgramSB,
        freqLS,
        pgramLS,
        hrsLow,
        hrsHigh,
        slopeCoeff,
    )


def populateExper(tubesMaster):
    """Populate experiment data table."""
    global experTable
    tableRows = [
        [
            "Entry",
            "Pack",
            "Tube #",
            "Period (Manual)",
            "Period (Sokolove-Bushell)",
            "Period (Lomb-Scargle)",
            "Growth Rate (mm/hr)"
        ],
        ["", "", "", "", "", "", ""],
    ]  # Populate table rows with headers and a blank row
    maxLengths = [6, 5, 6, 16, 26, 22, 19]  # Set maximum lengths of columns for spacing
    for tube in tubesMaster:  # For each tube in master tube list
        tubePeriods = calcPeriods(tube[5], tube[4], tube[8], tube[9], 14, 32, tube[7])  # Calculate periods and periodograms for current tube
        tableRows.append(
            [
                str(tubesMaster.index(tube) + 1),
                str(tube[0]),
                str(tube[3] + 1),
                str(round(tubePeriods[0], 3)) + " hrs",
                str(round(tubePeriods[1], 3)) + " hrs",
                str(round(tubePeriods[2], 3)) + " hrs",
                str(tube[6])
            ]
        )  # Add row to experiment table of [Entry number, Set number, Tube number in set, Periods]
        # Update max column lengths to fit data
        if len(str(tubesMaster.index(tube) + 1)) + 1 > maxLengths[0]:
            maxLengths[0] = len(str(tubesMaster.index(tube) + 1)) + 1
        if len(str(tube[0])) + 1 > maxLengths[1]:
            maxLengths[1] = len(str(tube[0])) + 1
        if len(str(tube[3] + 1)) + 1 > maxLengths[2]:
            maxLengths[2] = len(str(tube[3] + 1)) + 1
        if len(str(round(tubePeriods[0], 3))) + 1 > maxLengths[3]:
            maxLengths[3] = len(str(round(tubePeriods[0], 3))) + 1
        if len(str(round(tubePeriods[1], 3))) + 1 > maxLengths[4]:
            maxLengths[4] = len(str(round(tubePeriods[1], 3))) + 1
        if len(str(round(tubePeriods[2], 3))) + 1 > maxLengths[5]:
            maxLengths[5] = len(str(round(tubePeriods[2], 3))) + 1
        if len(str(tube[6])) + 1 > maxLengths[6]:
            maxLengths[6] = len(str(tube[6])) + 1
    tableText = ""  # Blank string for experiment table text
    for row in tableRows:  # For each row of table rows list
        for col in range(0, len(tableRows[0])):  # For each column
            tableText = (tableText + row[col] + " " * (maxLengths[col] - len(row[col])))  # Append column and spacing to table text
        tableText = tableText + "\n"  # Append newline to table text
    experTable.value = tableText  # Set experiment table text box value to text string


def popStatAnal():
    """Populate statistical analysis option lists."""
    global tubesMaster
    global setList
    global tubeList

    sets = []  # Blank list of tube sets
    tubes = []  # Blank list of tubes in selected sets
    setsSel = setList.value  # Set list of selected sets
    if setsSel is None:  # If no sets are selected
        setsSel = []  # Set setsSel to blank list instead of None
    tubesSel = tubeList.value  # Set list of selected tubes
    if tubesSel is None:  # If no tubes are selected
        tubesSel = []  # Set tubesSel to blank list instead of None
    for tube in tubesMaster:  # For each tube in master tubes list
        if tube[0] not in sets:  # If tube set name is not in list of set options
            sets.append(tube[0])  # Add tube set name to list of set options
        if tube[0] in setsSel:  # If tube set name is in list of selected sets
            tubes.append(tube[0] + " | " + str(tube[3] + 1))  # Add set and tube to list of tube options
    setList.destroy()
    tubeList.destroy()
    setList = ListBox(
        setListBox,
        multiselect=True,
        scrollbar=True,
        align="top",
        width=150,
        height="fill",
        command=popStatAnal,
        items=sets,
        selected=setsSel,
    )  # Reinitialize set options list with sets from file
    tubeList = ListBox(
        tubeListBox,
        multiselect=True,
        scrollbar=True,
        align="top",
        width=150,
        height="fill",
        command=popStatAnal,
        items=tubes,
        selected=tubesSel,
    )  # Reinitialize tube options list with tubes from selected sets


def statAnal():
    """Perform statistical analaysis of periods of selected tubes and display results."""
    global tubesMaster
    global tubeList
    global methodList
    global analText

    tubesSel = tubeList.value  # Set list of selected tubes from options list
    method = None  # Initialize method
    match methodList.value:  # Based on selected method from options list
        case "Manual":  # If method is Manual
            method = 0  # Set method to 0
        case "Sokolove-Bushell":  # If method is Sokolove-Bushell
            method = 1  # Set method to 1
        case "Lomb-Scargle":  # If method is Lomb-Scargle
            method = 2  # Set method to 2
    periods = []  # Blank list of periods for analysis
    for tube in tubesMaster:  # For each tube in master tubes list
        if (tube[0] + " | " + str(tube[3] + 1)) in tubesSel:  # If tube and set name match a selected tube option
            periods.append(calcPeriods(tube[5], tube[4], tube[8], tube[9], 14, 32, tube[7])[method])  # Add selected period to list of periods for analysis
    meanPeriod = numpy.mean(periods)  # Calculate mean of selected periods
    stdDev = numpy.std(periods)  # Calculate standard deviation of selected periods
    stdErr = stdDev / numpy.sqrt(len(periods))  # Calculate standard error of selected periods
    analText.value = (
        "Mean Period ("
        + methodList.value
        + "):\n"
        + str(meanPeriod)
        + " hrs\n\nStandard Deviation:\n"
        + str(stdDev)
        + "\n\nStandard Error:\n"
        + str(stdErr)
        + "\n\nn:\n"
        + str(len(periods))
    )  # Populate output box with analysis results


def popPlots():
    """Populate densitogram and periodogram plots based on selected tube."""
    global tubesMaster
    global plotFrame
    global plotCanvas
    global setList2
    global tubeList2
    global methodList2
    global canvas
    global plotAxes
    global appParameters

    method = None  # Initialize method variable
    match methodList2.value:  # Based on plot method selected
        case "Sokolove-Bushell":  # If method is Sokolove-Bushell
            method = 4  # Set method to 4
        case "Lomb-Scargle":  # If method is Lomb-Scargle
            method = 6  # Set method to 6
    tubesSel = tubeList2.value
    plotTube = []
    timeMarks = []
    markHours = []
    for tube in tubesMaster:
        if (tube[0] + " | " + str(tube[3] + 1)) == tubesSel:
            plotTube = tube
            timeMarks = plotTube[8]
            markHours = plotTube[4]
    densX = list(range(0, 1160))
    timeGaps = []
    for mark in range(0, len(timeMarks) - 1):
        timeGaps.append((timeMarks[mark + 1] - timeMarks[mark]) / (markHours[mark + 1] - markHours[mark]))
    pixPerHr = numpy.mean(timeGaps)
    hrPerPix = 1 / pixPerHr
    densXHrs = []
    for x in densX:
        densXHrs.append(round((x - timeMarks[0]) * hrPerPix, 2))
    timeMarkHrs = []
    for x in plotTube[8]:
        timeMarkHrs.append(round((x - timeMarks[0]) * hrPerPix, 2))
    bandMarkHrs = []
    for x in plotTube[9]:
        bandMarkHrs.append(round((x - timeMarks[0]) * hrPerPix, 2))
    densY = plotTube[5]
    #Create period plot data
    periodData = calcPeriods(plotTube[5], markHours, timeMarks, plotTube[9], 14, 32, plotTube[7])
    perX = []
    perY = []
    calcXVals = periodData[method-1]
    calcYVals = periodData[method]
    slopeCoeff = periodData[9]
    for index in range(0, len(calcXVals)):
        if method == 4:  # SB
            period = 1 / calcXVals[index]
        else:  # LS
            period = (2 * numpy.pi) / calcXVals[index]
        xVal = period * hrPerPix * slopeCoeff
        if xVal >= 14 and xVal <= 32:#Within 14-32 x range
            perX.append(xVal)
            perY.append(calcYVals[index])
    #Plotting stuff
    gs = gridspec.GridSpec(2,1)
    px = 1/plt.rcParams['figure.dpi']
    fig = plt.figure(figsize=(int(screen_width*0.5)*px, int(screen_width*0.2)*px))
    ax = [None, None]
    ax[0] = fig.add_subplot(gs[0])
    ax[1] = fig.add_subplot(gs[1])
    locatorDensX = matplotlib.ticker.FixedLocator(list(range(-24, 193, 12)))
    locatorDensY = matplotlib.ticker.FixedLocator([0, 60, 120, 180, 240, 255])
    locatorDensMinorX = matplotlib.ticker.FixedLocator(list(range(-24, 193, 3)))
    locatorPerX = matplotlib.ticker.FixedLocator(list(range(periodData[7], periodData[8] + 1)))
    plotAxes = [densXHrs, densY, timeMarkHrs, bandMarkHrs, perX, perY, locatorPerX]
    ax[0].plot(densXHrs, densY, label="Density profile", color=appParameters["colorGraph"])
    ax[0].xaxis.set_major_locator(locatorDensX)
    ax[0].yaxis.set_major_locator(locatorDensY)
    ax[0].xaxis.set_minor_locator(locatorDensMinorX)
    ax[0].set(
        xlabel="Time (hrs)", 
        ylabel="Density", 
        title="Densitogram"
    )
    ax[0].vlines(
        timeMarkHrs,
        numpy.min(densY),
        numpy.max(densY),
        colors=appParameters["colorVert"],
        label="Time Marks",
    )
    ax[0].vlines(
        bandMarkHrs, 
        numpy.min(densY), 
        numpy.max(densY), 
        colors=appParameters["colorBand"], 
        label="Bands"
    )
    ax[0].grid()
    ax[0].legend(ncol=3, loc="best", fontsize="x-small")
    ax[1].plot(perX, perY, label="Power spectral density (V\u00b2)", color=appParameters["colorGraph"])
    ax[1].xaxis.set_major_locator(locatorPerX)
    ax[1].set(
        xlabel="Period (hrs)",
        ylabel="Power spectral\ndensity (V\u00b2)",
        title="Periodogram",
    )
    ax[1].grid()
    ax[1].legend(fontsize="x-small")
    fig.tight_layout()
    if canvas is not None:
        canvas.get_tk_widget().pack_forget()
    canvas = FigureCanvasTkAgg(fig, master=plotCanvas)
    canvas.draw()
    canvas.get_tk_widget().pack()


def popPlotTubes():
    """Populate plotting option lists"""
    global tubesMaster
    global setList2
    global tubeList2

    sets = []  # Blank list of tube sets
    tubes = []  # Blank list of tubes
    setsSel = setList2.value  # Set selected set
    if setsSel is None:  # If no set selected
        setsSel = ""  # Set selected set to blank string instead of None
    tubesSel = tubeList2.value  # Set selected tube
    if tubesSel is None:  # If no tube selected
        tubesSel = ""  # Set selected set to blank string instead of None
    for tube in tubesMaster:  # For each tube in master tubes list
        if tube[0] not in sets:  # If set name of tube is not in list of set options
            sets.append(tube[0])  # Add tube set name to list of set options
        if tube[0] in setsSel:  # If tube set name is in list of selected sets
            tubes.append(tube[0] + " | " + str(tube[3] + 1))  # Add set and tube to list of tube options
    tubeList2.destroy()
    setList2.destroy()
    setList2 = ListBox(
        setListBox2,
        scrollbar=True,
        width=150,
        height="fill",
        align="top",
        command=popPlotTubes,
        items=sets,
        selected=setsSel,
    )  # Reinitialize set options list with sets from file
    tubeList2 = ListBox(
        tubeListBox2,
        scrollbar=True,
        width=150,
        height="fill",
        align="top",
        command=popPlotTubes,
        items=tubes,
        selected=tubesSel,
    )  # Reinitialize tube options list with tubes from file


def saveData():#all periods etc
    global workingDir
    global setList
    global tubeList
    global methodList
    global tubesMaster
    
    setNames = setList.value
    tubesSel = tubeList.value
    periods = []  # Blank list of periods for analysis
    for tube in tubesMaster:  # For each tube in master tubes list
        if (tube[0] + " | " + str(tube[3] + 1)) in tubesSel:  # If tube and set name match a selected tube option
            entry = [tube[0], str(tube[3]+1)] + list(calcPeriods(tube[5], tube[4], tube[8], tube[9], 14, 32, tube[7])[0:2])
            periods.append(entry)  # Add selected period to list of periods for analysis
    dataFile = app.select_file(
        title="Save period data as...",
        folder=workingDir,
        filetypes=[["CSV", "*.csv"]],
        save=True,
        filename=("_".join(setNames) + "_period_data"),
    )
    with open(dataFile, 'w', newline='') as csvfile:
        rowWriter = csv.writer(csvfile, delimiter=',')
        rowWriter.writerow(["Pack Name", "Tube #", "Period (hrs) (Manually Calculated)", "Period (hrs) (Sokolove-Bushell)", "Period (hrs) (Lomb-Scargle)"])
        for entry in periods:
            rowWriter.writerow(entry)


def saveDensPlot():
    global plotAxes
    global workingDir
    global setList2
    global tubeList2
    global appParameters
    
    if plotAxes is not []:
        tubeNum = tubeList2.value[tubeList2.value.rindex("|")+2:]
        plotFile = app.select_file(
            title="Save plot as...",
            folder=workingDir,
            filetypes=[["PNG", "*.png"], ["JPG", "*.jpg"], ["JPEG", "*.jpeg"], ["TIFF", "*.tif"], ["SVG", "*.svg"]],
            save=True,
            filename=(setList2.value + "_tube" + tubeNum + "_densitometry"),
        )
        densXHrs = plotAxes[0]
        densY = plotAxes[1]
        timeMarkHrs = plotAxes[2]
        bandMarkHrs = plotAxes[3]
        locatorDensX = matplotlib.ticker.FixedLocator(list(range(-24, 193, 12)))
        locatorDensY = matplotlib.ticker.FixedLocator([0, 60, 120, 180, 240, 255])
        locatorDensMinorX = matplotlib.ticker.FixedLocator(list(range(-24, 193, 3)))
        fig = plt.figure(figsize=[7.5, 2.1])
        axes = fig.add_subplot()
        axes.plot(densXHrs, densY, label="Density profile", color=appParameters["colorGraph"])
        axes.xaxis.set_major_locator(locatorDensX)
        axes.yaxis.set_major_locator(locatorDensY)
        axes.xaxis.set_minor_locator(locatorDensMinorX)
        axes.set(
            xlabel="Time (hrs)", 
            ylabel="Density", 
            title="Densitogram"
        )
        axes.vlines(
            timeMarkHrs,
            numpy.min(densY),
            numpy.max(densY),
            colors=appParameters["colorVert"],
            label="Time Marks",
        )
        axes.vlines(
            bandMarkHrs, 
            numpy.min(densY), 
            numpy.max(densY), 
            colors=appParameters["colorBand"], 
            label="Bands"
        )
        axes.grid()
        axes.legend(ncol=3, loc="best", fontsize="x-small")
        fig.tight_layout(pad=2)
        fig.savefig(plotFile)


def savePerPlot():
    global plotAxes
    global workingDir
    global setList2
    global tubeList2
    global methodList2
    global appParameters

    if plotAxes is not []:
        tubeNum = tubeList2.value[tubeList2.value.rindex("|")+2:]
        plotFile = app.select_file(
            title="Save plot as...",
            folder=workingDir,
            filetypes=[["PNG", "*.png"], ["JPG", "*.jpg"], ["JPEG", "*.jpeg"], ["TIFF", "*.tif"], ["SVG", "*.svg"]],
            save=True,
            filename=(setList2.value + "_tube" + tubeNum + "_" + methodList2.value),
        )
        perX = plotAxes[4]
        perY = plotAxes[5]
        locatorPerX = plotAxes[6]
        fig = plt.figure(figsize=[7.5, 2.1])
        axes = fig.add_subplot()
        axes.plot(perX, perY, label="Power spectral density (V\u00b2)", color=appParameters["colorGraph"])
        axes.xaxis.set_major_locator(locatorPerX)
        axes.set(
            xlabel="Period (hrs)",
            ylabel="Power spectral\ndensity (V\u00b2)",
            title="Periodogram",
        )
        axes.grid()
        axes.legend(fontsize="x-small")
        fig.tight_layout(pad=2)
        fig.savefig(plotFile)


def saveDensData():
    global workingDir
    global setList2
    global tubeList2
    global tubesMaster
    
    setName = setList2.value
    tubeNum = int(tubeList2.value[tubeList2.value.rindex("|")+2:])-1
    densFile = app.select_file(
        title="Save densitometry as...",
        folder=workingDir,
        filetypes=[["CSV", "*.csv"]],
        save=True,
        filename=(setName + "_tube" + str(tubeNum) + "_densitometry_data"),
    )
    dens = []
    timeMarks = []
    bandMarks = []
    markHours = []
    for tube in tubesMaster:
        if tube[0] == setName and tube[3] == tubeNum:
            dens = tube[5]
            timeMarks = tube[8]
            bandMarks = tube[9]
            markHours = tube[4]
    timeGaps = []
    for mark in range(0, len(timeMarks) - 1):
        timeGaps.append((timeMarks[mark + 1] - timeMarks[mark]) / (markHours[mark + 1] - markHours[mark]))
    pixPerHr = numpy.mean(timeGaps)
    hrPerPix = 1 / pixPerHr
    with open(densFile, 'w', newline='') as csvfile:
        rowWriter = csv.writer(csvfile, delimiter=',')
        rowWriter.writerow(["Pixel (from left)", "Time (hrs)", "Density Profile", "Time/Band Marks"])
        for index in range(0, 1160):
            densHr = round((index - timeMarks[0]) * hrPerPix, 4)
            newLine = [index, densHr, dens[index], "N/A"]
            markNote = []
            if index in timeMarks:
                markNote.append("Time")
            if index in bandMarks:
                markNote.append("Band")
            if markNote is not []:
                newLine[3] = "/".join(markNote)
            rowWriter.writerow(newLine)


def savePerData():
    global workingDir
    global setList2
    global tubeList2
    global methodList2
    global tubesMaster
    global plotAxes

    setName = setList2.value
    tubeNum = int(tubeList2.value[tubeList2.value.rindex("|")+2:])-1
    method = methodList2.value
    perFile = app.select_file(
        title="Save densitometry as...",
        folder=workingDir,
        filetypes=[["CSV", "*.csv"]],
        save=True,
        filename=(setName + "_tube" + str(tubeNum) + "_" + method + "_data"),
    )
    method = None  # Initialize method variable
    match methodList2.value:  # Based on plot method selected
        case "Sokolove-Bushell":  # If method is Sokolove-Bushell
            method = 4  # Set method to 4
        case "Lomb-Scargle":  # If method is Lomb-Scargle
            method = 6  # Set method to 6
    plotTube = []
    timeMarks = []
    markHours = []
    for tube in tubesMaster:
        if tube[0] == setName and tube[3] == tubeNum:
            plotTube = tube
            timeMarks = plotTube[8]
            markHours = plotTube[4]
    timeGaps = []
    for mark in range(0, len(timeMarks) - 1):
        timeGaps.append((timeMarks[mark + 1] - timeMarks[mark]) / (markHours[mark + 1] - markHours[mark]))
    pixPerHr = numpy.mean(timeGaps)
    hrPerPix = 1 / pixPerHr
    periodData = calcPeriods(plotTube[5], markHours, timeMarks, plotTube[9], 14, 32, plotTube[7])
    perX = []
    perY = []
    freqs = []
    calcXVals = periodData[method-1]
    calcYVals = periodData[method]
    slopeCoeff = periodData[9]
    for index in range(0, len(calcXVals)):
        if method == 4:  # SB
            period = 1 / calcXVals[index]
        else:# LS
            period = (2 * numpy.pi) / calcXVals[index]
        xVal = period * hrPerPix * slopeCoeff
        if xVal >= 14 and xVal <= 32:
            perX.append(xVal)
            perY.append(calcYVals[index])
            freqs.append(calcXVals[index])
    with open(perFile, 'w', newline='') as csvfile:
        rowWriter = csv.writer(csvfile, delimiter=',')
        if method == 4:
            rowWriter.writerow(["Frequency", "Period (hrs)", "Spectral Density"])
        elif method == 6:
            rowWriter.writerow(["Angular Frequency", "Period (hrs)", "Spectral Density"])
        for index in range(0, len(perX)):
            newLine = [freqs[index], perX[index], perY[index]]
            rowWriter.writerow(newLine)


def storeTubes(setName):
    """Store tubes from image in master tubes list, and save master tubes list to file."""
    global tubeBounds
    global timeMarkLines
    global bandLines
    global tubesMaster
    global densityProfiles
    global markHours
    global imageName
    global finalImage
    global tubeLength
    global openFile

    setNames = []
    for tube in tubesMaster:
        setNames.append(tube[0])
    if setName in setNames:
        setName = setName + "_1"
    topTubeTimeMarks = []  # Blank list of time mark x values
    for line in timeMarkLines:  # For each line in list of time marks
        if line[2] == tube:  # If line is in current tube
            topTubeTimeMarks.append(line[0])  # Add line x to timeMarks
    topTubeTimeMarks.sort()  # Sort time marks low to high/left to right
    mmPerPix = int(tubeLength) / (topTubeTimeMarks[-1] - topTubeTimeMarks[0])
    for tube in range(0, len(tubeBounds)):  # For each tube in tubeBounds
        tubeRange = tubeBounds[tube]  # Y bounds of tube
        densProfile = densityProfiles[tube]  # Density profile of tube
        timeMarks = []  # Blank list of time mark x values
        for line in timeMarkLines:  # For each line in list of time marks
            if line[2] == tube:  # If line is in current tube
                timeMarks.append(line[0])  # Add line x to timeMarks
        timeMarks.sort()  # Sort time marks low to high/left to right
        bandMarks = []  # Blank list of band mark x values
        for line in bandLines:  # For each line in list of band marks
            if line[2] == tube:  # If line is in current tube
                bandMarks.append(line[0])  # Add line x to bandMarks
        bandMarks.sort()  # Sort band marks low to high/left to right
        imageString = (
            numpy.array2string(numpy.array(finalImage.convert("L")), separator=",")
            .replace(" ", "")
            .replace("\n", "")
        )  # Convert numpy image array to string for storage to file
        timeGaps = []  # List of time gaps in pixels per hour
        for mark in range(0, len(timeMarks) - 1):  # For each 2 consecutive time marks and corresponding hour values
            timeGaps.append((timeMarks[mark + 1] - timeMarks[mark])/ (markHours[mark + 1] - markHours[mark]))  # Add length of gap in pixels per hour to list of time gaps
        pixPerHr = numpy.mean(timeGaps)  # Mean time gap in pixels per hour
        growthRate = round(mmPerPix * pixPerHr, 2)#mm per hour
        tubesMaster.append(
            [
                setName,
                imageName,
                imageString,
                tube,
                markHours,
                densProfile,
                growthRate,
                tubeRange,
                timeMarks,
                bandMarks,
            ]
        )  # Add tube info to master tubes list
    saveExp()  # Save tubes to file
    cancelRT()  # Reset image analysis
    populateExper(tubesMaster)  # Populate experiment data table


def proceedHandler():
    """Handle clicks on proceed button based on analysis state."""
    global analState
    global tubeBounds
    global markHours
    global timeMarkLines
    global bandLines
    match analState:  # Based on analysis state
        case 2:  # Analysis state 2 (tube bounds)
            rescanButt.disable()
            identTubes()
        case 5:  # Analysis state 5 (time marks)
            bandAnalyze()
        case 7:  # Analysis state 7 (band locations)
            analState = 8  # Set analysis state to 8
            for tube in range(0, len(tubeBounds)):  # For each tube in tubeBounds
                tubeRange = tubeBounds[tube]  # Y bounds of tube
                densProfile = densityProfiles[tube]  # Density profile of tube
                timeMarks = []  # Blank list of time mark x values
                for line in timeMarkLines:  # For each line in list of time marks
                    if line[2] == tube:  # If line is in current tube
                        timeMarks.append(line[0])  # Add line x to timeMarks
                timeMarks.sort()  # Sort time marks low to high/left to right
                bandMarks = []  # Blank list of band mark x values
                for line in bandLines:  # For each line in list of band marks
                    if line[2] == tube:  # If line is in current tube
                        bandMarks.append(line[0])  # Add line x to bandMarks
                bandMarks.sort()  # Sort band marks low to high/left to right
                periods = calcPeriods(
                    densProfile, markHours, timeMarks, bandMarks, 14, 32, tubeRange
                )  # Calculate period data of tube
                prelimContents[tube + 1][2] = str(round(periods[0], 2))  # Add manually calculated period (rounded) to preliminary data list
            prelimUpdate()  # Update preliminary data text box
            proceedButt.disable()  # Disable proceed button
            saveTubesButt.enable()  # Enable save tubes button


def keyBindHandler(keys):  # Shift, Command, S, O, P, D, H
    """Handle uses of multikey hotkeys to perform program functions"""
    global keyPresses
    match keys:  # Based on list of pressed keys
        case [0, 1, 1, 0, 0, 0, 0]:  # If command, s pressed
            saveExp()  # Save experiment
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [1, 1, 1, 0, 0, 0, 0]:  # If shift, command, s pressed
            saveAs()  # Save as
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [0, 1, 0, 1, 0, 0, 0]:  # If command, o pressed
            openExp()  # Open experiment file
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [0, 1, 0, 0, 0, 1, 0]:  # If command, d pressed
            setWorkDir()  # Set working directory
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [0, 1, 0, 0, 0, 0, 1]:  # If command, h pressed
            helpMain()  # Open main help page
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [0, 1, 0, 0, 1, 0, 0]:  # If command, p pressed
            graphicsPrefs()  # Open graphics settings
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list


def keyPress(keyPressed):
    """Handle each key press registered by app object."""
    global keyPresses
    match [str(keyPressed.key), str(keyPressed.keycode),
    ]:  # Based on key and keycode of key pressed
        case ["", "943782142"]:  # Shift
            keyPresses[0] = 1
        case ["", "922810622"]:  # Command
            keyPresses[1] = 1
        case ["s", "16777331"] | ["S", "20971603"]:  # S
            keyPresses[2] = 1
        case ["o", "520093807"] | ["O", "524288079"]:  # O
            keyPresses[3] = 1
        case ["p", "587202672"] | ["P", "591396944"]:  # P
            keyPresses[4] = 1
        case ["d", "33554532"] | ["D", "37748804"]:  # D
            keyPresses[5] = 1
        case ["h", "67108968"] | ["H", "71303240"]:  # H
            keyPresses[6] = 1
    keyBindHandler(keyPresses)


def keyRelease(keyReleased):
    """Handle each key release registered by app object."""
    global keyPresses
    match [str(keyReleased.key), str(keyReleased.keycode),
    ]:  # Based on key and keycode of key released
        case ["", "943782142"]:  # Shift
            keyPresses[0] = 0
        case ["", "922810622"]:  # Command
            keyPresses[1] = 0
        case ["s", "16777331"] | ["S", "20971603"]:  # S
            keyPresses[2] = 0
        case ["o", "520093807"] | ["O", "524288079"]:  # O
            keyPresses[3] = 0
        case ["p", "587202672"] | ["P", "591396944"]:  # P
            keyPresses[4] = 0
        case ["d", "33554532"] | ["D", "37748804"]:  # D
            keyPresses[5] = 0
        case ["h", "67108968"] | ["H", "71303240"]:  # H
            keyPresses[6] = 0


def helpMain():
    """Direct user to main help page/documentation for app."""
    webbrowser.open(
        "https://github.com/PelhamLab", new=0, autoraise=True
    )  # Open google in browser :p


def invertColor(hex):
    hex = hex.lstrip('#')
    rgb =  tuple(255 - int(hex[i:i + len(hex) // 3], 16) for i in range(0, len(hex), len(hex)//3))
    out = '#%02x%02x%02x' % rgb
    return out


def graphicsPrefs():
    global appParameters

    graphicsWin = Window(app, title="Graphics Preferences", layout="grid", width=375, height=300)
    graphicsWin.show()

    colorGraphButt = PushButton(graphicsWin, grid=[0,0], text="Graph Color", height=0, width=20, command=colorPickHandler, args=[0])
    colorGraphText = TextBox(graphicsWin, grid=[2,0], text=appParameters["colorGraph"], width=7)
    colorHorizButt = PushButton(graphicsWin, grid=[0,1], text="Horizontal Line Color", height=0, width=20, command=colorPickHandler, args=[1])
    colorHorizText = TextBox(graphicsWin, grid=[2,1], text=appParameters["colorHoriz"], width=7)
    colorVertButt = PushButton(graphicsWin, grid=[0,2], text="Time Mark Color", height=0, width=20, command=colorPickHandler, args=[2])
    colorVertText = TextBox(graphicsWin, grid=[2,2], text=appParameters["colorVert"], width=7)
    colorBandButt = PushButton(graphicsWin, grid=[0,3], text="Band Mark Color", height=0, width=20, command=colorPickHandler, args=[3])
    colorBandText = TextBox(graphicsWin, grid=[2,3], text=appParameters["colorBand"], width=7)

    colorGraphText.text_color = appParameters["colorGraph"]
    colorGraphText.bg = invertColor(appParameters["colorGraph"])
    colorHorizText.text_color = appParameters["colorHoriz"]
    colorHorizText.bg = invertColor(appParameters["colorHoriz"])
    colorVertText.text_color = appParameters["colorVert"]
    colorVertText.bg = invertColor(appParameters["colorVert"])
    colorBandText.text_color = appParameters["colorBand"]
    colorBandText.bg = invertColor(appParameters["colorBand"])

    graphicsWin.repeat(200, graphicsPrefsUpdate, args=[[colorGraphText, colorHorizText, colorVertText, colorBandText]])


def colorPickHandler(button):
    global appParameters

    newColor = ""
    match button:
        case 0:
            newColor = app.select_color(color=appParameters["colorGraph"])
            appParameters["colorGraph"] = newColor
            updateParams()
        case 1:
            newColor = app.select_color(color=appParameters["colorHoriz"])
            appParameters["colorHoriz"] = newColor
            updateParams()
        case 2:
            newColor = app.select_color(color=appParameters["colorVert"])
            appParameters["colorVert"] = newColor
            updateParams()
        case 3:
            newColor = app.select_color(color=appParameters["colorBand"])
            appParameters["colorBand"] = newColor
            updateParams()
    drawLines()


def graphicsPrefsUpdate(texts):
    global appParameters
    
    texts[0].text_color = appParameters["colorGraph"]
    texts[0].value = appParameters["colorGraph"]
    texts[0].bg = invertColor(appParameters["colorGraph"])
    texts[1].text_color = appParameters["colorHoriz"]
    texts[1].value = appParameters["colorHoriz"]
    texts[1].bg = invertColor(appParameters["colorHoriz"])
    texts[2].text_color = appParameters["colorVert"]
    texts[2].value = appParameters["colorVert"]
    texts[3].bg = invertColor(appParameters["colorVert"])
    texts[3].text_color = appParameters["colorBand"]
    texts[3].value = appParameters["colorBand"]
    texts[4].bg = invertColor(appParameters["colorBand"])


# Create app object
app = App(layout="auto", title="Chronidia")
#app.image = "./icon.png"
app.when_closed = sys.exit
app.width = screen_width
app.height = screen_height
appHeight = app.height
appWidth = app.width

# Keybinds
app.when_key_pressed = keyPress
app.when_key_released = keyRelease

# Set up OS menu bar
menubar = MenuBar(
    app,
    toplevel=["File", "Help"],
    options=[
        [
            ["Open Experiment (⌘O)", openExp],
            ["Save Experiment (⌘S)", saveExp],
            ["Save Experiment As... (\u2191⌘S)", saveAs],
            ["Set Working Directory (⌘D)", setWorkDir],
            ["Graphics Preferences (⌘P)", graphicsPrefs]
        ],
        [["Help 1", helpMain]],
    ],
)

"""
Colors
Bright orange: #F29F05
Bright blue: #69C5FF
Accent dark: #676975
Dull orange: #deb15e
Dull blue: #9fcdea
Light grey: grey95
"""

# Set up navigation tabs
navBox = Box(
    app, width="fill", align="top", layout="grid", border="0"
)  # Frame for Home, Experiment tabs
imageTab = Box(navBox, grid=[0, 0], border="0", height="30")  # Home tab button
imageText = Text(
    imageTab, text="Home", width=20, size=14, color="black", font="Arial"
)  # Home tab button text
experimentTab = Box(
    navBox, grid=[3, 0], border="0", height="30"
)  # Experiment tab button
experimentText = Text(
    experimentTab, text="Experiment", width=20, size=14, color="black", font="Arial"
)  # Home tab button text
# Set up tab colors
navBox.bg = "#676975"  # Dark grey nav bar
imageTab.bg = "#deb15e"  # Conidia orange home tab
experimentTab.bg = "#9fcdea"  # Baby blue experiment tab
# Set up tab functions
imageText.when_clicked = selectHome
experimentText.when_clicked = selectExper


# Set up home tab
homeFrame = Box(app, width="fill", height="fill", align="top", layout="auto")
homeFrame.bg = "grey95"
homeFrame.set_border(5, "#deb15e")
homeFrame.text_color = "black"
# Home buttons
homeButtonBox = Box(
    homeFrame, width="fill", height="20", align="top", layout="grid", border="0"
)
uploadRtButt = PushButton(
    homeButtonBox, grid=[0, 0], text="Upload Race Tube Image", command=fUploadRT
)
rotateRtButt = PushButton(
    homeButtonBox, grid=[2, 0], text="Rotate Image", command=fRotateRT
)
rotateRtButt.disable()
lengthBox = Box(homeButtonBox, grid=[3, 0], border="0", height="20", layout="grid")
rtLengthLabel = Text(
    lengthBox,
    color="black",
    grid=[0, 0],
    text="Length from first to last\ntime mark of 1st tube (mm)",
)
rtLength = TextBox(lengthBox, text="300", grid=[1, 0])
lockButt = PushButton(
    homeButtonBox, grid=[4, 0], text="Lock and Analyze", command=fLockRT
)
lockButt.disable()
# Home data
dataBox = Box(homeFrame, align="top", border="0", width="fill")
markBox = Box(dataBox, width=180, height=400, align="left")
markRowBoxes = [Box(markBox, align="top", layout="grid", width="fill")]
markRowBoxes[0].bg = "grey75"
markLabels = []
markData = []
markHeader1 = Text(markRowBoxes[0], grid=[0, 0], text="Mark ", font="Courier", size=14)
markHeader2 = Text(markRowBoxes[0], grid=[1, 0], text="Day ", font="Courier", size=14)
markHeader3 = Text(markRowBoxes[0], grid=[2, 0], text="Hour ", font="Courier", size=14)
markHeader4 = Text(markRowBoxes[0], grid=[3, 0], text="Min", font="Courier", size=14)
for line in range(1, 11):
    markRowBoxes.append(Box(markBox, align="top", layout="grid", width="fill"))
    if markRowBoxes[line - 1].bg == "grey75":
        markRowBoxes[line].bg = "grey85"
    else:
        markRowBoxes[line].bg = "grey75"
    markLabels.append(
        Text(
            markRowBoxes[line],
            grid=[0, 0],
            text=str(line) + " " * (5 - len(str(line))),
            font="Courier",
            size=14,
        )
    )
    markData.append(
        TextBox(markRowBoxes[line], grid=[1, 0], text=str(line - 1), width=3)
    )
    markData.append(TextBox(markRowBoxes[line], grid=[2, 0], text="0", width=3))
    markData.append(TextBox(markRowBoxes[line], grid=[3, 0], text="0", width=3))
imageBox = Box(dataBox, width=1160, height=400, align="left")
imageDraw = Drawing(imageBox, width="fill", height="fill")
consoleBox = Box(homeFrame, width="fill", height="50")
rescanButt = PushButton(consoleBox, text="Rescan", command=horizAnalyze, align="left")
rescanButt.disable()
proceedButt = PushButton(consoleBox, text="Proceed", command=proceedHandler, align="left")
proceedButt.disable()
consoleText = TextBox(consoleBox, width=80, height=4, multiline=True, align="left")
consoleText.disable()
saveTubesButt = PushButton(
    consoleBox,
    text="Save Tubes to File",
    command=storeTubesPrompt,
    align="left",
)
saveTubesButt.disable()
resetButt = PushButton(
    consoleBox,
    text="Cancel image analysis",
    command=cancelRT,
    align="left",
)
resetButt.disable()
prelimBox = Box(homeFrame, width="fill", height=400, align="top")
prelimText = Text(prelimBox, font="Courier", size=14, align="top")
# Set up home tab colors
lengthBox.bg = "gray95"
rtLength.text_color = "black"
imageBox.bg = "#676975"
consoleText.text_color = "black"
# Set up home functions
imageDraw.when_clicked = imageClickHandler


# Set up experiments tab
experFrame = Box(app, width="fill", height="fill", align="top")
experFrame.bg = "grey95"
experFrame.text_color = "black"
experFrame.set_border(5, "#9fcdea")
experBoxTop = Box(experFrame, width="fill", height=appHeight*0.22, align="top")
experTableFrame = Box(experBoxTop, width=screen_width*0.45, height=appHeight*0.22, align="left")
experTable = TextBox(experTableFrame, multiline=True, width="fill", height="fill")
experTable.wrap = False
experTable.font = "Courier"
experTableFrame.set_border(2, "#9fcdea")
experTable.text_color = "black"
statTable = Box(experBoxTop, width="fill", height="fill", align="left")
statTable.set_border(2, "#9fcdea")
setListBox = Box(statTable, width=150, height="fill", align="left")
setListTitle = Text(setListBox, text="\nSets:", align="top")
setList = ListBox(
    setListBox,
    multiselect=True,
    scrollbar=True,
    align="top",
    width=150,
    height="fill",
    command=popStatAnal,
)
tubeListBox = Box(statTable, width=150, height="fill", align="left")
tubeListTitle = Text(tubeListBox, text="\nTubes:", align="top")
tubeList = ListBox(
    tubeListBox,
    multiselect=True,
    scrollbar=True,
    align="top",
    width=150,
    height="fill",
    command=popStatAnal,
)
methodListBox = Box(statTable, width=150, height="fill", align="left")
methodListTitle = Text(methodListBox, text="Period Analysis\nMethods:", align="top")
methodList = ListBox(
    methodListBox,
    width=120,
    height="fill",
    align="top",
    items=["Manual", "Sokolove-Bushell", "Lomb-Scargle"],
    selected="Manual",
)
buttonList = Box(statTable, height="fill", align="right")
analyzeButt = PushButton(buttonList, text="Analyze", width="fill", command=statAnal, align="top")
expDataButt = PushButton(buttonList, text="Export\nData", width="fill", pady=2, command=saveData, align="top")
analTextBox = Box(statTable, width="fill", height="fill", align="right")
analTextTitle = Text(analTextBox, text="\nStatistical Analysis:", align="top")
analText = TextBox(analTextBox, multiline=True, width=35, height=18, align="top")

experBoxBot = Box(experFrame, width="fill", height=screen_width*0.2, align="top")
plotTubeFrame = Box(experBoxBot, width=screen_width*0.45, height="fill", align="left")
plotTubeFrame.set_border(2, "#9fcdea")
setListBox2 = Box(plotTubeFrame, width=150, height="fill", align="left")
setListTitle2 = Text(setListBox2, text="\nSets:", align="top")
setList2 = ListBox(
    setListBox2,
    scrollbar=True,
    width=150,
    height="fill",
    align="top",
    command=popPlotTubes,
)
tubeListBox2 = Box(plotTubeFrame, width=150, height="fill", align="left")
tubeListTitle2 = Text(tubeListBox2, text="\nTubes:", align="top")
tubeList2 = ListBox(
    tubeListBox2,
    scrollbar=True,
    width=150,
    height="fill",
    align="top",
    command=popPlotTubes,
)
methodListBox2 = Box(plotTubeFrame, width=150, height="fill", align="left")
methodListTitle2 = Text(methodListBox2, text="Period Analysis\nMethods:", align="top")
methodList2 = ListBox(
    methodListBox2,
    width=120,
    height="fill",
    align="top",
    items=["Sokolove-Bushell", "Lomb-Scargle"],
    selected="Manual",
)
plotButtBox = Box(plotTubeFrame, grid=[3, 1])
plotButt = PushButton(plotButtBox, text="Plot", command=popPlots, width="fill")
saveDensButt = PushButton(
    plotButtBox, text="Save Densitogram", pady=2, command=saveDensPlot, width="fill"
)
saveDensDatButt = PushButton(
    plotButtBox,
    text="Save\nDensitogrammetry",
    pady=2,
    command=saveDensData,
    width="fill",
)
savePerButt = PushButton(
    plotButtBox, text="Save Periodogram", pady=2, command=savePerPlot, width="fill"
)
savePerDatButt = PushButton(
    plotButtBox,
    text="Save\nPeriodogrammetry",
    pady=2,
    command=savePerData,
    width="fill",
)
plotFrame = Box(experBoxBot, width=screen_width*0.5, height=screen_width*0.2, align="left")
plotFrame.set_border(2, "#9fcdea")
plotCanvas = Canvas(plotFrame.tk, width=screen_width*0.5, height=screen_width*0.2)
plotFrame.add_tk_widget(plotCanvas)
print(str(plotTubeFrame.width))

openSetup()
app.display()