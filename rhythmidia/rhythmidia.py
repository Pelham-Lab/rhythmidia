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

screenWidth = pyautogui.size().width  # Get screen width
screenHeight = pyautogui.size().height  # Get screen height
numpy.set_printoptions(threshold=sys.maxsize)
csv.field_size_limit(999999999)

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
tubesMaster = []  # Master list of tubes saved to file in form (per tube): [setName, imageName, imageData, tubeNumber, markHours, densityProfile, growthRate, tubeRange, timeMarks, bandMarks]
canvas = None  # Plot entity
keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Shift, Command, S, O, P, D, H
plotsInfo = []


def setWorkingDirectory():
    """Prompt user to set a working directory for the application, and save this to the local parameters file."""
    global appParameters
    global workingDir
    workingDir = app.select_folder(title="Please select working directory:", folder="/")  # Set working directory variable to user-specified directory via file selection popup
    appParameters["workingDir"] = workingDir  # Populate parameters dictionary with user-specified working directory
    updateAppParameters()


def updateAppParameters():
    global appParameters
    
    directoryPath = os.path.dirname(__file__)
    parametersPath = os.path.join(directoryPath, "parameters.txt")
    with open(parametersPath, newline="", mode="w") as parametersFile:  # Open parameters.txt file
        writer = csv.writer(parametersFile, delimiter="=")  # Define csv writer
        for key in appParameters:  # For each key in parameters dictionary
            writer.writerow([key, appParameters[key]])  # Write as a line of parameters.txt


def openExperimentFile(reopen=False):  # Open an experiment file
    """Open an existing experiment file containing data from past images/tubes. Populate appropriate variables, including tubesMaster, with relevant information."""
    global openFile
    global workingDir
    global tubesMaster

    cancelImageAnalysis()  # Zero out any existing information from a different open file or a newly analyzed race tube image
    tubesMaster = []  # Blank out master tube list in preparation for population from opened file
    if openFile == "" or reopen is False:
        openFile = app.select_file(
            title="Select experiment file",
            folder=workingDir,
            filetypes=[["Rhythmidia Experiment", "*.rmex"]],
            save=False,
            filename="",
        )  # Prompt user by popup to select experiment file from working directory and save name as openFile
    if openFile == "":  # If openFile remains blank
        return  # Abort function
    with open(openFile, newline="") as experimentFile:  # Open user-specified txt file
        tubesInFile = csv.reader(experimentFile, delimiter="%")  # Define csv reader
        for tube in tubesInFile:  # For each line of experiment file
            parsedTube = {"setName":None, "imageName":None, "imageData":None, "tubeNumber":None, "markHours":None, "densityProfile":None, "growthRate":None, "tubeRange":None, "timeMarks":None, "bandMarks":None}  # Blank variable for parsed tube
            parsedTube["setName"] = str(tube[0])
            parsedTube["imageName"] = str(tube[1])
            imageData = []  # Blank image data variable
            imageDataRaw = tube[2][1:-1].split("],[")  # Image data from file as list
            for row in imageDataRaw:  # For each row of image data
                dataRow = []  # Blank variable for row values
                for pixel in (row.strip().replace("[", "").replace("]", "").split(",")):  # For each value in row, excluding punctuation and delimited by ","
                    if pixel != "":  # If value is not blank
                        dataRow.append(int(pixel))  # Convert value to integer and add to row data
                imageData.append(dataRow)  # Add row data to image data
            parsedTube["imageData"] = imageData
            parsedTube["tubeNumber"] = int(tube[3])
            markHours = (
                tube[4]
                .strip()
                .replace(" ", "")
                .replace("[", "")
                .replace("]", "")
                .split(",")
            )  # Raw list of mark hour values
            for hours in enumerate(markHours):  # For each element of raw mark hours data
                markHours[hours[0]] = float(hours[1])  # Convert value to float from string
            parsedTube["markHours"] = markHours
            densityProfile = (
                tube[5]
                .strip()
                .replace(" ", "")
                .replace("[", "")
                .replace("]", "")
                .split(",")
            )  # Raw list of densitometry values
            for num in enumerate(densityProfile):  # For each element of raw densitometry data
                densityProfile[num[0]] = float(num[1])  # Convert value to float from string
            parsedTube["densityProfile"] = densityProfile
            parsedTube["growthRate"] = float(tube[6])
            tubeBoundsRaw = (tube[7][1:-1].replace(" ", "").split("],["))  # Raw list of tube boundary doubles
            pairs = []  # Blank list of tube boundary doubles
            for pairRaw in tubeBoundsRaw:  # For each double in raw list of tube boundary doubles
                pair = pairRaw.replace("[", "").replace("]", "").split(",")  # Remove [, ], and split at commas into list
                for yVal in enumerate(pair):  # For each number in boundary double
                    pair[yVal[0]] = float(yVal[1])  # Convert number to float from string
                pairs.append(pair)  # Add boundary double to list of tube boundary doubles
            parsedTube["tubeRange"] = pairs
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
            parsedTube["timeMarks"] = timeMarks
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
            parsedTube["bandMarks"] = bandMarks
            tubesMaster.append(parsedTube)  # Add parsed tube data to master list of tubes
        populateExperimentDataTable(tubesMaster)  # Populate experiment data table
        populateStatisticalAnalysisLists()  # Populate statistical analysis frame
        populatePlotTubeSelectionLists()  # Populate plot data frame


def saveExperimentFile():  # Save current experiment
    """Save experiment file to existing file, or prompt user to save as new file if not editing existing experiment file."""
    global openFile
    global workingDir
    global tubesMaster

    if openFile == "":  # If no currently open file
        saveExperimentFileAs("")  # Prompt user to save as new file
    else:  # If a file is already open
        with open(openFile, newline="", mode="w") as experimentFile:  # Open current experiment file
            writer = csv.writer(experimentFile, delimiter="%")  # Define csv writer
            for tube in tubesMaster:  # For each tube in master tube list
                tubeValuesList = list(tube.values())
                writer.writerow(tubeValuesList)  # Write new line for tube to experiment file
        openExperimentFile(True)  # Open current experiment again to update application


def saveExperimentFileAs(name=""):  # Save current experiment as new experiment file
    """Prompt user to provide a file name to save current data as a new experiment file."""
    global openFile
    global workingDir

    openFile = app.select_file(
        title="Save as...",
        folder=workingDir,
        filetypes=[["Rhythmidia Experiment", "*.rmex"]],
        save=True,
        filename=name,
    )  # Prompt user to create a new file name with popup, and save name as openFile
    if not (openFile == ""):  # If file name is not left blank
        saveExperimentFile()  # Save experiment as chosen file name


def selectHomeTab():  # Swap to home tab
    """Select home tab."""
    if homeTabFrame.visible is False:  # If home tab is not already selected
        experimentTabFrame.hide()  # Hide experiment tab
        homeTabFrame.show()  # Show home tab
    app.update()  # Update app object


def selectExperTab():  # Swap to experiments tab
    """Select experiment tab."""
    if experimentTabFrame.visible is False:  # If experiment tab not already selected
        homeTabFrame.hide()  # Hide home tab
        experimentTabFrame.show()  # Show experiment tab
    app.update()  # Update app object


def uploadRaceTubeImage():  # Prompt file upload of race tube image
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
        filetypes=[["TIFF", "*.tif"], ["TIFF", "*.tiff"], ["PNG", "*.png"], ["JPG", "*.jpg"], ["JPEG", "*.jpeg"], ["SVG", "*.svg"]],
        save=False,
        filename="",
    )  # Prompt user to select a .tif image in the working directory to analyze, and set file name as imageName
    rawImage = Image.open(imageName).resize((1160, 400))  # Open raw image file as 1160x400px image object
    rightImage = rawImage  # Set intermediate image to raw image
    displayRaceTubeImage(rightImage)  # Display race tube image
    lockAndAnalyzeButton.enable()  # Enable button to lock image and analyze
    rotateRaceTubeImageButton.enable()  # Enable button to rotate image 90 degrees
    resetRaceTubeImageAnalysisButton.enable()  # Enable button to reset analysis


def rotateRaceTubeImage():  # Rotate race tube image clockwise
    """Rotate current image 90 degrees clockwise."""
    global rawImage
    global rotateDeg

    rotateDeg += 90  # Increment rotation angle by 90 degrees clockwise
    rightImage = rawImage.rotate(rotateDeg, expand=1).resize((1160, 400))  # Set intermediate image to raw image rotated by rotateDeg degrees clockwise
    displayRaceTubeImage(rightImage)  # Display race tube image


def displayRaceTubeImage(image):
    """Display race tube image."""
    homeTabRaceTubeImageObject.clear()  # Clear image frame
    homeTabRaceTubeImageObject.image(0, 0, image)  # Display intermediate image in image frame


def lockAndAnalyzeRaceTubeImage():
    """Lock image in current rotation and begin analysis prompts."""
    global rotateDeg
    global rawImage
    global finalImage
    global tubeLength

    # Lock
    uploadRaceTubeImageButton.disable()  # Disable upload image button
    rotateRaceTubeImageButton.disable()  # Disable rotate image button
    raceTubeLengthTextBox.disable()  # Disable tube length input
    lockAndAnalyzeButton.disable()  # Disable lock and analyze button
    proceedButton.enable()  # Enable proceed button
    # Analyze
    finalDeg = 90 * ((rotateDeg / 90) % 4)  # Set final rotation angle to simplified rotation angle
    finalImage = rawImage.rotate(finalDeg, expand=1).resize((1160, 400))  # Set final image to raw image rotated by final rotation angle
    tubeLength = raceTubeLengthTextBox.value  # Set tube length to value in input box
    getTimeMarkTableData()  # Save tube mark time values to variable
    identifyHorizontalLines()  # Begin tube boundary analysis


def cancelImageAnalysis():
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
    homeTabRaceTubeImageObject.clear()  # Clear image frame
    rawImage, rightImage, finalImage = None, None, None  # Zero out image variables
    imageName = ""  # Zero out current image name
    prelimContents = [["Tube", "# Marks", "Average Period (hrs)"]]  # Reset preliminary data contents to headers
    homeTabPreliminaryDataAnalysisTextBox.value = ""  # Zero out preliminary data text box
    tubeLength = -1  # Zero out tube length
    tubeBounds = []  # Zero out tube boundaries list
    meanTubeWidth = -1  # Zero out mean tube width
    meanTubeSlope = None  # Zero out mean horizontal slope
    horizontalLines, timeMarkLines, bandLines = [], [], []  # Zero out horizontal, time mark, and band line lists
    densityProfiles = []  # Zero out densitometry
    homeTabConsoleTextBox.value = ""  # Zero out console text box

    saveTubesToFileButton.disable()
    uploadRaceTubeImageButton.enable()  # Enable upload race tube image button
    rotateRaceTubeImageButton.disable()  # Disable rotate image button
    raceTubeLengthTextBox.enable()  # Enable race tube length text box
    lockAndAnalyzeButton.disable()  # Disable lock and analyze button
    proceedButton.disable()  # Disable proceed button


def updatePreliminaryDataDisplay():
    """Update preliminary data text box."""
    global prelimContents

    text = ""  # Blank string for text
    for line in prelimContents:  # For each line of preliminary data list
        text = (text + line[0] + " " * (7 - len(line[0])))  # Append tube number and spacing to text
        text = (text + line[1] + " " * (10 - len(line[1])))  # Append number of time marks and spacing to text
        text = (text + line[2] + " " * (23 - len(line[2])) + "\n")  # Append manually calculated period and spacing and newline to text
    homeTabPreliminaryDataAnalysisTextBox.value = text  # Set preliminary data text box to text variable


def identifyHorizontalLines():
    """Analyze horizontal boundaries of tubes in image."""
    global finalImage
    global analState
    global horizontalLines
    global meanTubeSlope
    global prelimContents

    analState = 1  # Set analysis state to 1
    editedImage = numpy.array(finalImage.convert("L"))  # Create numpy array of final image in greyscale
    
    rowMeansLeft = []
    rowMeansRight = []
    for row in enumerate(list(editedImage)):
        rowMeansLeft.append(0-int(numpy.mean(row[1][:25])))
        rowMeansRight.append(0-int(numpy.mean(row[1][550:575])))
    rowMeansLeftSmooth = savgol_filter(rowMeansLeft, window_length=30, polyorder=2, mode="interp")
    rowMeansRightSmooth = savgol_filter(rowMeansRight, window_length=30, polyorder=2, mode="interp")
    rowMeansLeftSmoothMin = numpy.min(rowMeansLeftSmooth)
    rowMeansRightSmoothMin = numpy.min(rowMeansRightSmooth)
    for num in range(0, 400):
        rowMeansLeftSmooth[num] -= rowMeansLeftSmoothMin
        rowMeansRightSmooth[num] -= rowMeansRightSmoothMin
    rowMeansLeftMinimaIndices = find_peaks(rowMeansLeftSmooth, distance=25, threshold=(None, None), height=0.88*numpy.max(rowMeansLeftSmooth), prominence=5, wlen=300)[0].tolist()
    rowMeansRightMinimaIndices = find_peaks(rowMeansRightSmooth, distance=25, threshold=(None, None), height=0.88*numpy.max(rowMeansRightSmooth), prominence=5, wlen=300)[0].tolist()
    rowMeansLeftMinima = []
    rowMeansRightMinima = []
    for peakIndex in rowMeansLeftMinimaIndices:  # For each peak index
            peakX = peakIndex  # Set x to peak index
            peakY = rowMeansLeftSmooth[peakIndex]  # Set y to midline of tube at x
            slopesLeft = []  # Blank list of slopes left of peak
            slopesRight = []  # Blank list of slopes right of peak
            for xWalk in range(2, 12, 2):  # For each x to one side or the other of peak
                if peakX + xWalk < 1160:  # If xWalk to the right is within image
                    slopesRight.append(abs((rowMeansLeftSmooth[peakX + xWalk] - rowMeansLeftSmooth[peakX + xWalk - 2])) / 2)  # Add granular slope to list of slopes
                if peakX - xWalk > 0:  # If xWalk to the left is within image
                    slopesLeft.append(abs((rowMeansLeftSmooth[peakX - xWalk] - rowMeansLeftSmooth[peakX - xWalk + 2])) / 2)  # Add granular slope to list of slopes
            slopeRight = numpy.mean(slopesRight)  # Mean slope to right of peak
            slopeLeft = numpy.mean(slopesLeft)  # Mean slope to left of peak
            slopeMin = numpy.min([slopeLeft, slopeRight])  # Minimum of two adjacent slopes to peak
            if peakX > 10 and peakX < 1150 and slopeMin > 1:  # If x is not on edges of image
                rowMeansLeftMinima.append(peakY)  # Add time mark to list of time mark lines
    for peakIndex in rowMeansLeftMinimaIndices:  # For each peak index
            peakX = peakIndex  # Set x to peak index
            peakY = rowMeansRightSmooth[peakIndex]  # Set y to midline of tube at x
            slopesLeft = []  # Blank list of slopes left of peak
            slopesRight = []  # Blank list of slopes right of peak
            for xWalk in range(2, 12, 2):  # For each x to one side or the other of peak
                if peakX + xWalk < 1160:  # If xWalk to the right is within image
                    slopesRight.append(abs((rowMeansRightSmooth[peakX + xWalk] - rowMeansRightSmooth[peakX + xWalk - 2])) / 2)  # Add granular slope to list of slopes
                if peakX - xWalk > 0:  # If xWalk to the left is within image
                    slopesLeft.append(abs((rowMeansRightSmooth[peakX - xWalk] - rowMeansRightSmooth[peakX - xWalk + 2])) / 2)  # Add granular slope to list of slopes
            slopeRight = numpy.mean(slopesRight)  # Mean slope to right of peak
            slopeLeft = numpy.mean(slopesLeft)  # Mean slope to left of peak
            slopeMin = numpy.min([slopeLeft, slopeRight])  # Minimum of two adjacent slopes to peak
            if peakX > 10 and peakX < 1150 and slopeMin > 1:  # If x is not on edges of image
                rowMeansRightMinima.append(peakY)  # Add time mark to list of time mark lines
    rowMeansLeftMinimaIndices.append(5)
    rowMeansLeftMinimaIndices.append(395)
    horizontalLineSlopes1 = []  # Empty list of slopes
    horizontalLineIntercepts1 = []  # Empty list of y intercepts
    for minIndex in rowMeansLeftMinimaIndices:#each left index
        leftYVal = minIndex
        rightYVal = minIndex
        for yVal in rowMeansRightMinimaIndices:
            if abs(yVal-leftYVal) <= 15:
                rightYVal = yVal
        slope = (rightYVal - leftYVal) / (562.5-12.5) # Set slope to slope of line calculated as rise/run#get slope with corresponding right index
        intercept = (leftYVal - slope * 12.5) #set intercept
        horizontalLineSlopes1.append(slope)
        horizontalLineIntercepts1.append(intercept)


    cannyEdges = canny(editedImage, 2, 1, 25)  # Detect edges of greyscale image
    likelyHorizontalLines = probabilistic_hough_line(cannyEdges, threshold=10, line_length=75, line_gap=5)  # Get long lines from canny edges
    horizontalLineSlopes2 = []  # Empty list of slopes
    horizontalLineIntercepts2 = []  # Empty list of y intercepts
    for line in likelyHorizontalLines:  # For each probabilistic hough line
        if (line[1][0] - line[0][0]) == 0:  # If line is vertical
            slope = numpy.inf  # Set slope to infinity to avoid dividing by 0
        else:  # If line is not vertical
            slope = (line[1][1] - line[0][1]) / (line[1][0] - line[0][0])  # Set slope to slope of line calculated as rise/run
        intercept = (line[0][1] - slope * line[0][0])  # Set intercept to intercept of line calculated using slope and y position
        if abs(slope) < 2:  # If slope is not too steep
            horizontalLineSlopes2.append(slope)  # Add slope to slope list
            horizontalLineIntercepts2.append(intercept)  # Add intercept to intercept list

    if len(horizontalLineIntercepts1) > len(horizontalLineIntercepts2):
        horizontalLineIntercepts = horizontalLineIntercepts1
        horizontalLineSlopes = horizontalLineSlopes1
    else:
        horizontalLineIntercepts = horizontalLineIntercepts2
        horizontalLineSlopes = horizontalLineSlopes2

    horizontalLines = []  # Blank global list of tube boundary lines
    if len(horizontalLineIntercepts) > 4:
        meanTubeSlope = numpy.mean(horizontalLineSlopes)  # Mean slope of horizontal tube boundary lines
    else:
        meanTubeSlope = 0
    for line in range(0, len(horizontalLineSlopes)):  # For each horizontal line
        isDuplicate = 0  # Whether line is a duplicate of an accepted line (default to 0)
        for lin in horizontalLines:  # For each accepted horizontal line
            if (
                (len(horizontalLineIntercepts2) > len(horizontalLineIntercepts1))
                and (
                    abs(horizontalLineIntercepts[line] - lin[1]) < 20
                    or abs(meanTubeSlope - horizontalLineSlopes[line]) > 0.015
                    or (numpy.sign(meanTubeSlope) != numpy.sign(horizontalLineSlopes[line]))
                )
            ):  # If line intercept is too close to an accepted line, or slope is too divergent from mean slope of set, or sign of slope is different from mean slope
                isDuplicate = 1  # Line is a duplicate
        if isDuplicate == 0:  # If line is not a duplicate
            horizontalLines.append([horizontalLineSlopes[line], horizontalLineIntercepts[line]])  # Add line to accepted horizontal lines
    drawLines()  # Add lines to image
    analState = 2  # Set analysis state to 2
    homeTabConsoleTextBox.value = "Click a point on the image to add or remove race tube boundary lines. Please be sure to include lines a verytop and bottom of image. When satisfied, click the Proceed button."  # Set console text to horizontal line instructions


def identifyRaceTubeBounds():
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
    updatePreliminaryDataDisplay()  # Update preliminary contents text box
    homeTabConsoleTextBox.value = ("Identifying race tube regions...")  # Set console box text to analysis step description
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
    identifyTimeMarks()  # Begin analysis of time mark locations


def identifyTimeMarks():
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
        densityProfile = generateDensityProfile(editedImage, tubeNumber=tubeBounds.index(tube), profileWidth=int(tubeWidth - 20))  # Create density profile of current tube
        densityProfileSmooth = savgol_filter(densityProfile, window_length=30, polyorder=8, mode="interp")  # Create Savitzky-Golay smoothed density profile of marks-corrected dataset
        peakIndices = find_peaks(densityProfileSmooth, distance=5, threshold=(None, None), prominence=3, wlen=300)[0].tolist()  # Get indices of local maxima of smoothed density profile
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
            xWalk = 1
            while densityProfileSmooth[peakX-xWalk] <= densityProfileSmooth[peakX-xWalk+1] and peakX-xWalk > 1:
                xWalk += 1
            baseLeft = peakX - xWalk
            baseYLeft = densityProfileSmooth[baseLeft]
            xWalk = 1
            while densityProfileSmooth[peakX+xWalk] <= densityProfileSmooth[peakX+xWalk-1] and peakX+xWalk < 1159:
                xWalk += 1
            baseRight = peakX + xWalk
            baseYRight = densityProfileSmooth[baseRight]
            promLeft = densityProfileSmooth[peakX] - baseYLeft
            promRight = densityProfileSmooth[peakX] - baseYRight
            prominenceFraction = numpy.max([promLeft, promRight])/numpy.max(densityProfileSmooth)
            if prominenceFraction > .2 and prominenceFraction < 0.9 and slopeMin > (-20/3)*prominenceFraction+(26/3) and peakX > 10 and peakX < 1150:
                timeMarkLines.append([peakX, peakY, tubeNumber])  # Add time mark to list of time mark lines
        drawLines()  # Add lines to image
    analState = 5  # Set analysis state to 5
    homeTabConsoleTextBox.value = "Click a point on the image to add or remove time marks. Please be sure to mark the start point. When satisfied, click the Proceed button."  # Add directions to console


def generateDensityProfile(image, tubeNumber, profileWidth):
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


def identifyBanding():
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
    updatePreliminaryDataDisplay()  # Update preliminary data text box
    contraster = ImageEnhance.Contrast(finalImage.convert("L"))  # Define contraster of numpy array of greyscale final image
    editedImage = numpy.array(contraster.enhance(3))  # Set numpy image array to contrast level 3
    originalImage = numpy.array(finalImage.convert("L"))  # Set numpy image array for precontrast ('original') image
    drawLines()  # Add lines to image
    for tube in tubeBounds:  # For each tube in tubeBounds
        tubeWidth = tube[0][1] - tube[0][0]  # Width of current tube at left end
        tubeNumber = int(tubeBounds.index(tube))  # Index of current tube in tubeBounds
        densityProfile = generateDensityProfile(editedImage, tubeNumber=tubeBounds.index(tube), profileWidth=int(tubeWidth - 5))  # Create density profile of current tube
        densityProfileOriginal = generateDensityProfile(originalImage, tubeNumber=tubeBounds.index(tube), profileWidth=int(tubeWidth - 5))  # Create density profile of current tube
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
            if peakX > numpy.min(list(line[0] for line in timeMarkLines)) and peakX < 1150:  # If band is further right than the first time mark for its tube
                bandLines.append([peakX, peakY, tubeNumber])  # Add band to list
    drawLines()  # Draw lines
    analState = 7  # Set analysis state to 7
    homeTabConsoleTextBox.value = "Click a point on the image to add or remove bands. Remove erroneously identified bands from any non-banding tubes. When satisfied, click the Proceed button."  # Update console text


def drawLines():
    """Redraw image along with current accepted horizontal and vertical lines for time and band marks."""
    global horizontalLines
    global timeMarkLines
    global bandLines
    global meanTubeWidth
    global finalImage
    global tubeBounds
    global appParameters

    homeTabRaceTubeImageObject.clear()  # Clear image canvas
    homeTabRaceTubeImageObject.image(0, 0, finalImage)  # Add image to canvas
    for line in horizontalLines:  # For each horizontal line
        homeTabRaceTubeImageObject.line(
            0, 
            line[1],
            1160, 
            line[1] + 1160 * line[0], 
            color=appParameters["colorHoriz"], 
            width=2
        )  # Draw the horizontal line
    for line in timeMarkLines:  # For each time mark
        homeTabRaceTubeImageObject.line(
            line[0],
            line[1] - (meanTubeWidth / 2 - 5),
            line[0],
            line[1] + (meanTubeWidth / 2 - 5),
            color=appParameters["colorVert"],
            width=2,
        )  # Draw the time mark line
    for line in bandLines:  # For each band
        homeTabRaceTubeImageObject.line(
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


def getTimeMarkTableData():
    """Save information from time mark table to variable."""
    global markHours

    numberOfHours = 0  # Set number of hours in row to 0
    for datum in timeMarkTableDataTextBoxes:  # For each row of time mark table
        match (timeMarkTableDataTextBoxes.index(datum) % 3):  # Based on index of text box in list of time mark data table cells
            case 0:  # If in first column
                numberOfHours = 24 * (int(datum.value))  # Set hours to number of days in row * 24
            case 1:  # If in second column
                numberOfHours += int(datum.value)  # Add to hours number of hours in row
            case 2:  # If in third column
                numberOfHours += (int(datum.value) / 60)  # Add to hours number of minutes in row / 60
                markHours.append(numberOfHours)  # Add number of hours to markHours


def saveTubesToFilePrompt():
    """Create popup window prompting user to name set of tubes in current image before saving to file."""
    setNamePopup = Window(app, title="Pack name...", width=200, height=120)  # Popup window
    setNamePopup.show(wait=True)  # Show window as popup
    setNameTextBox = TextBox(setNamePopup)  # Text box for name of tube set
    setNameTextBox.focus()  # Focus name text box
    setNameButton = PushButton(setNamePopup, text="Confirm", command=lambda: [saveTubesToFile(setName=setNameTextBox.value), setNamePopup.destroy()])  # Button to save tubes to file and close popup


def calculatePeriodData(densityProfile, markHours, timeMarks, bandMarks, minPeriod, maxPeriod, tubeRange):
    """Calculate periods of a given tube's densitometry profile"""
    slopeCoeff = abs(1 / numpy.cos(numpy.arctan(((tubeRange[-1][1] + tubeRange[-1][0]) / 2- (tubeRange[0][1] + tubeRange[0][0]) / 2) / (1160))))  # Calculate coefficient to correct for slope
    # Calculate 'manual' period
    growthRates = []  # List of time gaps in pixels per hour
    for mark in range(0, len(timeMarks) - 1):  # For each 2 consecutive time marks and corresponding hour values
        growthRates.append((timeMarks[mark + 1] - timeMarks[mark]) / (markHours[mark + 1] - markHours[mark]))  # Add length of gap in pixels per hour to list of time gaps
    meanGrowthPixelsPerHour = numpy.mean(growthRates)  # Mean time gap in pixels per hour
    meanGrowthHoursPerPixel = 1 / meanGrowthPixelsPerHour
    bandGaps = []  # List of band gaps in pixels
    for mark in range(0, len(bandMarks) - 1):  # For each 2 consecutive band marks
        bandGaps.append((bandMarks[mark + 1] - bandMarks[mark]))  # Add length of gap in pixels to list of band marks
    periodManual = ((numpy.mean(bandGaps) / numpy.mean(growthRates)) * slopeCoeff)  # Set manual period to mean period between band gaps in hours, corrected for slope of tube in image
    # Calculate high and low periods in pixels
    minPeriodPixels = int(minPeriod * meanGrowthPixelsPerHour)  # Lowest period to test (in pixels)
    maxPeriodPixels = int(maxPeriod * meanGrowthPixelsPerHour)  # Highest period to test (in pixels)
    # Calculate Sokolove-Bushell periodogram
    frequenciesSokoloveBushell, periodogramPowerSpectrumSokoloveBushell = periodogram(densityProfile, scaling="spectrum")  # Get Sokolove-Bushell periodogram (frequencies, power spectra in V^2)
    frequenciesSokoloveBushell = frequenciesSokoloveBushell.tolist()[1:]  # Convert S-B frequencies to list
    periodogramPowerSpectrumSokoloveBushell = periodogramPowerSpectrumSokoloveBushell.tolist()[1:]  # Convert S-B periodogram values to list
    # Calculate Lomb-Scargle Periodogram
    frequencyInterval = int(((2 * numpy.pi) / minPeriodPixels - (2 * numpy.pi) / maxPeriodPixels) / 0.0001)  # Number of angular frequencies to test for Lomb-Scargle at an interval of 0.0001
    frequenciesLombScargle = (numpy.linspace((2 * numpy.pi) / maxPeriodPixels, (2 * numpy.pi) / minPeriodPixels, frequencyInterval).tolist())  # Create list of angular frequencies to test for Lomb-Scargle periodogram
    periodogramChiSquaredLombScargle = lombscargle(list(range(0, 1160)), densityProfile, frequenciesLombScargle)  # Get Lomb-Scargle periodogram
    periodogramChiSquaredLombScargle = periodogramChiSquaredLombScargle.tolist()  # Convert L-S periodogram values to list
    # Convert frequencies to periods
    periodLombScarglePixels = ((2 * numpy.pi) / frequenciesLombScargle[periodogramChiSquaredLombScargle.index(numpy.max(periodogramChiSquaredLombScargle))])  # Convert frequency of maximal spectral density from Lomb-Scargle periodogram to horizontal length in pixels
    periodSokoloveBushellPixels = (1 / frequenciesSokoloveBushell[periodogramPowerSpectrumSokoloveBushell.index(numpy.max(periodogramPowerSpectrumSokoloveBushell))])  # Convert frequency of maximal spectral density from Sokolove-Bushell periodogram to horizontal length in pixels
    periodLombScargle = periodLombScarglePixels * meanGrowthHoursPerPixel * slopeCoeff
    periodSokoloveBushell = periodSokoloveBushellPixels * meanGrowthHoursPerPixel * slopeCoeff
    return (
        periodManual,
        periodSokoloveBushell,
        periodLombScargle,
        frequenciesSokoloveBushell,
        periodogramPowerSpectrumSokoloveBushell,
        frequenciesLombScargle,
        periodogramChiSquaredLombScargle,
        minPeriod,
        maxPeriod,
        slopeCoeff,
    )


def populateExperimentDataTable(tubesMaster):
    """Populate experiment data table."""
    global experimentTabTableTextBox
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
    maxColumnLengths = [6, 5, 7, 16, 26, 22, 19]  # Set maximum lengths of columns for spacing
    for tube in tubesMaster:  # For each tube in master tube list
        tubePeriods = calculatePeriodData(tube["densityProfile"], tube["markHours"], tube["timeMarks"], tube["bandMarks"], 14, 32, tube["tubeRange"])  # Calculate periods and periodograms for current tube
        tableRows.append(
            [
                str(tubesMaster.index(tube) + 1),
                str(tube["setName"]),
                str(tube["tubeNumber"] + 1),
                str(round(tubePeriods[0], 3)) + " hrs",
                str(round(tubePeriods[1], 3)) + " hrs",
                str(round(tubePeriods[2], 3)) + " hrs",
                str(tube["growthRate"])
            ]
        )  # Add row to experiment table of [Entry number, Set number, Tube number in set, Periods]
        # Update max column lengths to fit data
        if len(str(tubesMaster.index(tube) + 1)) + 1 > maxColumnLengths[0]:
            maxColumnLengths[0] = len(str(tubesMaster.index(tube) + 1)) + 1
        if len(str(tube["setName"])) + 1 > maxColumnLengths[1]:
            maxColumnLengths[1] = len(str(tube["setName"])) + 1
        if len(str(tube["tubeNumber"] + 1)) + 1 > maxColumnLengths[2]:
            maxColumnLengths[2] = len(str(tube["tubeNumber"] + 1)) + 1
        if len(str(round(tubePeriods[0], 3))) + 1 > maxColumnLengths[3]:
            maxColumnLengths[3] = len(str(round(tubePeriods[0], 3))) + 1
        if len(str(round(tubePeriods[1], 3))) + 1 > maxColumnLengths[4]:
            maxColumnLengths[4] = len(str(round(tubePeriods[1], 3))) + 1
        if len(str(round(tubePeriods[2], 3))) + 1 > maxColumnLengths[5]:
            maxColumnLengths[5] = len(str(round(tubePeriods[2], 3))) + 1
        if len(str(tube["growthRate"])) + 1 > maxColumnLengths[6]:
            maxColumnLengths[6] = len(str(tube["growthRate"])) + 1
    tableText = ""  # Blank string for experiment table text
    for row in tableRows:  # For each row of table rows list
        for col in range(0, len(tableRows[0])):  # For each column
            tableText = (tableText + row[col] + " " * (maxColumnLengths[col] - len(row[col])))  # Append column and spacing to table text
        tableText = tableText + "\n"  # Append newline to table text
    experimentTabTableTextBox.value = tableText  # Set experiment table text box value to text string


def populateStatisticalAnalysisLists():
    """Populate statistical analysis option lists."""
    global tubesMaster
    global experimentTabStatisticalAnalysisSetList
    global experimentTabStatisticalAnalysisTubeList

    setsToDisplay = []  # Blank list of tube sets
    tubesToDisplay = []  # Blank list of tubes in selected sets
    setsSelected = experimentTabStatisticalAnalysisSetList.value  # Set list of selected sets
    if setsSelected is None:  # If no sets are selected
        setsSelected = []  # Set setsSelected to blank list instead of None
    tubesSelected = experimentTabStatisticalAnalysisTubeList.value  # Set list of selected tubes
    if tubesSelected is None:  # If no tubes are selected
        tubesSelected = []  # Set tubesSelected to blank list instead of None
    for tube in tubesMaster:  # For each tube in master tubes list
        if tube["setName"] not in setsToDisplay:  # If tube set name is not in list of set options
            setsToDisplay.append(tube["setName"])  # Add tube set name to list of set options
        if tube["setName"] in setsSelected:  # If tube set name is in list of selected sets
            tubesToDisplay.append(tube["setName"] + " | " + str(tube["tubeNumber"] + 1))  # Add set and tube to list of tube options
    experimentTabStatisticalAnalysisSetList.destroy()
    experimentTabStatisticalAnalysisTubeList.destroy()
    experimentTabStatisticalAnalysisSetList = ListBox(
        experimentTabStatisticalAnalysisSetListFrame,
        multiselect=True,
        scrollbar=True,
        align="top",
        width=150,
        height="fill",
        command=populateStatisticalAnalysisLists,
        items=setsToDisplay,
        selected=setsSelected,
    )  # Reinitialize set options list with sets from file
    experimentTabStatisticalAnalysisTubeList = ListBox(
        experimentTabStatisticalAnalysisTubeListFrame,
        multiselect=True,
        scrollbar=True,
        align="top",
        width=150,
        height="fill",
        command=populateStatisticalAnalysisLists,
        items=tubesToDisplay,
        selected=tubesSelected,
    )  # Reinitialize tube options list with tubes from selected sets


def performStatisticalAnalysis():
    """Perform statistical analaysis of periods of selected tubes and display results."""
    global tubesMaster
    global experimentTabStatisticalAnalysisTubeList
    global experimentTabStatisticalAnalysisMethodList
    global experimentTabStatisticalAnalysisOutputTextBox

    tubesSelected = experimentTabStatisticalAnalysisTubeList.value  # Set list of selected tubes from options list
    method = None  # Initialize method
    match experimentTabStatisticalAnalysisMethodList.value:  # Based on selected method from options list
        case "Manual":  # If method is Manual
            method = 0  # Set method to 0
        case "Sokolove-Bushell":  # If method is Sokolove-Bushell
            method = 1  # Set method to 1
        case "Lomb-Scargle":  # If method is Lomb-Scargle
            method = 2  # Set method to 2
    selectedPeriods = []  # Blank list of periods for analysis
    for tube in tubesMaster:  # For each tube in master tubes list
        if (tube["setName"] + " | " + str(tube["tubeNumber"] + 1)) in tubesSelected:  # If tube and set name match a selected tube option
            selectedPeriods.append(calculatePeriodData(tube["densityProfile"], tube["markHours"], tube["timeMarks"], tube["bandMarks"], 14, 32, tube["tubeRange"])[method])  # Add selected period to list of periods for analysis
    meanPeriod = numpy.mean(selectedPeriods)  # Calculate mean of selected periods
    standardDeviation = numpy.std(selectedPeriods)  # Calculate standard deviation of selected periods
    standardErrorOfMeans = standardDeviation / numpy.sqrt(len(selectedPeriods))  # Calculate standard error of selected periods
    experimentTabStatisticalAnalysisOutputTextBox.value = (
        "Mean Period ("
        + experimentTabStatisticalAnalysisMethodList.value
        + "):\n"
        + str(meanPeriod)
        + " hrs\n\nStandard Deviation:\n"
        + str(standardDeviation)
        + "\n\nStandard Error of Means:\n"
        + str(standardErrorOfMeans)
        + "\n\nn:\n"
        + str(len(selectedPeriods))
    )  # Populate output box with analysis results


def populatePlots():
    """Populate densitogram and periodogram plots based on selected tube."""
    global tubesMaster
    global experimentTabPlotFrame
    global experimentTabPlotCanvas
    global experimentTabPlotTubeSelectionSetList
    global experimentTabPlotTubeSelectionTubeList
    global experimentTabPlotTubeSelectionMethodList
    global canvas
    global plotsInfo
    global appParameters

    method = None  # Initialize method variable
    match experimentTabPlotTubeSelectionMethodList.value:  # Based on plot method selected
        case "Sokolove-Bushell":  # If method is Sokolove-Bushell
            method = 4  # Set method to 4
        case "Lomb-Scargle":  # If method is Lomb-Scargle
            method = 6  # Set method to 6
    tubesSelected = experimentTabPlotTubeSelectionTubeList.value
    tubeToPlot = []
    timeMarks = []
    markHours = []
    for tube in tubesMaster:
        if (tube["setName"] + " | " + str(tube["tubeNumber"] + 1)) == tubesSelected:
            tubeToPlot = tube
    timeMarks = tubeToPlot["timeMarks"]
    markHours = tubeToPlot["markHours"]
    densitometryXValsRaw = list(range(0, 1160))
    timeGaps = []
    for mark in range(0, len(timeMarks) - 1):
        timeGaps.append((timeMarks[mark + 1] - timeMarks[mark]) / (markHours[mark + 1] - markHours[mark]))#gaps in px/hr
    meanGrowthPixelsPerHour = numpy.mean(timeGaps)
    meanGrowthHoursPerPixel = 1 / meanGrowthPixelsPerHour
    densitometryXValsHours = []
    for xPixel in densitometryXValsRaw:
        densitometryXValsHours.append(round((xPixel - timeMarks[0]) * meanGrowthHoursPerPixel, 2))
    timeMarksHours = []
    for xPixel in tubeToPlot["timeMarks"]:
        timeMarksHours.append(round((xPixel - timeMarks[0]) * meanGrowthHoursPerPixel, 2))
    bandMarksHours = []
    for xPixel in tubeToPlot["bandMarks"]:
        bandMarksHours.append(round((xPixel - timeMarks[0]) * meanGrowthHoursPerPixel, 2))
    densitometryYVals = tubeToPlot["densityProfile"]
    #Create period plot data
    periodData = calculatePeriodData(tubeToPlot["densityProfile"], markHours, timeMarks, tubeToPlot["bandMarks"], 14, 32, tubeToPlot["tubeRange"])
    periodogramXVals = []
    periodogramYVals = []
    calculatedPeriodogramFrequencies = periodData[method-1]
    calculatedPeriodogramYVals = periodData[method]
    slopeCoeff = periodData[9]
    for frequency in range(0, len(calculatedPeriodogramFrequencies)):
        if method == 4:  # SB
            period = 1 / calculatedPeriodogramFrequencies[frequency]
        else:  # LS
            period = (2 * numpy.pi) / calculatedPeriodogramFrequencies[frequency]
        xVal = period * meanGrowthHoursPerPixel * slopeCoeff
        if xVal >= 14 and xVal <= 32:#Within 14-32 x range
            periodogramXVals.append(xVal)
            periodogramYVals.append(calculatedPeriodogramYVals[frequency])
    #Plotting stuff
    gridSpecLayout = gridspec.GridSpec(2,1)
    numPixelsForFigureDownload = 1/plt.rcParams['figure.dpi']
    tubeDoubleFigure = plt.figure(figsize=(int(screenWidth*0.5)*numPixelsForFigureDownload, int(screenWidth*0.2)*numPixelsForFigureDownload))
    tubeDoubleFigurePlots = [None, None]
    tubeDoubleFigurePlots[0] = tubeDoubleFigure.add_subplot(gridSpecLayout[0])
    tubeDoubleFigurePlots[1] = tubeDoubleFigure.add_subplot(gridSpecLayout[1])
    densitometryXAxisLabels = matplotlib.ticker.FixedLocator(list(range(-24, 193, 12)))
    densitometryYAxisLabels = matplotlib.ticker.FixedLocator([0, 60, 120, 180, 240, 255])
    densitometryXAxisMinorLabels = matplotlib.ticker.FixedLocator(list(range(-24, 193, 3)))
    periodogramXAxisLabels = matplotlib.ticker.FixedLocator(list(range(periodData[7], periodData[8] + 1)))
    plotsInfo = [densitometryXValsHours, densitometryYVals, timeMarksHours, bandMarksHours, periodogramXVals, periodogramYVals, periodogramXAxisLabels]
    tubeDoubleFigurePlots[0].plot(densitometryXValsHours, densitometryYVals, label="Density profile", color=appParameters["colorGraph"])
    tubeDoubleFigurePlots[0].xaxis.set_major_locator(densitometryXAxisLabels)
    tubeDoubleFigurePlots[0].yaxis.set_major_locator(densitometryYAxisLabels)
    tubeDoubleFigurePlots[0].xaxis.set_minor_locator(densitometryXAxisMinorLabels)
    tubeDoubleFigurePlots[0].set(
        xlabel="Time (hrs)", 
        ylabel="Density", 
        title="Densitogram"
    )
    tubeDoubleFigurePlots[0].vlines(
        timeMarksHours,
        numpy.min(densitometryYVals),
        numpy.max(densitometryYVals),
        colors=appParameters["colorVert"],
        label="Time Marks",
    )
    tubeDoubleFigurePlots[0].vlines(
        bandMarksHours, 
        numpy.min(densitometryYVals), 
        numpy.max(densitometryYVals), 
        colors=appParameters["colorBand"], 
        label="Bands"
    )
    tubeDoubleFigurePlots[0].grid()
    tubeDoubleFigurePlots[0].legend(ncol=3, loc="best", fontsize="x-small")
    if method == 4:
        tubeDoubleFigurePlots[1].plot(periodogramXVals, periodogramYVals, label="Chi Squared", color=appParameters["colorGraph"])
    else:
        tubeDoubleFigurePlots[1].plot(periodogramXVals, periodogramYVals, label="Spectral Density", color=appParameters["colorGraph"])
    tubeDoubleFigurePlots[1].xaxis.set_major_locator(periodogramXAxisLabels)
    tubeDoubleFigurePlots[1].set(
        xlabel="Period (hrs)",
        title="Periodogram",
    )
    if method == 4:
        tubeDoubleFigurePlots[1].set(ylabel="Chi Squared")
    else:
        tubeDoubleFigurePlots[1].set(ylabel="Spectral Density")
    tubeDoubleFigurePlots[1].grid()
    tubeDoubleFigurePlots[1].legend(fontsize="x-small")
    tubeDoubleFigure.tight_layout()
    if canvas is not None:
        canvas.get_tk_widget().pack_forget()
    canvas = FigureCanvasTkAgg(tubeDoubleFigure, master=experimentTabPlotCanvas)
    canvas.draw()
    canvas.get_tk_widget().pack()


def populatePlotTubeSelectionLists():
    """Populate plotting option lists"""
    global tubesMaster
    global experimentTabPlotTubeSelectionSetList
    global experimentTabPlotTubeSelectionTubeList

    setsToDisplay = []  # Blank list of tube sets
    tubesToDisplay = []  # Blank list of tubes
    setsSelected = experimentTabPlotTubeSelectionSetList.value  # Set selected set
    if setsSelected is None:  # If no set selected
        setsSelected = ""  # Set selected set to blank string instead of None
    tubesSelected = experimentTabPlotTubeSelectionTubeList.value  # Set selected tube
    if tubesSelected is None:  # If no tube selected
        tubesSelected = ""  # Set selected set to blank string instead of None
    for tube in tubesMaster:  # For each tube in master tubes list
        if tube["setName"] not in setsToDisplay:  # If set name of tube is not in list of set options
            setsToDisplay.append(tube["setName"])  # Add tube set name to list of set options
        if tube["setName"] in setsSelected:  # If tube set name is in list of selected sets
            tubesToDisplay.append(tube["setName"] + " | " + str(tube["tubeNumber"] + 1))  # Add set and tube to list of tube options
    experimentTabPlotTubeSelectionTubeList.destroy()
    experimentTabPlotTubeSelectionSetList.destroy()
    experimentTabPlotTubeSelectionSetList = ListBox(
        experimentTabPlotTubeSelectionSetListFrame,
        scrollbar=True,
        width=150,
        height="fill",
        align="top",
        command=populatePlotTubeSelectionLists,
        items=setsToDisplay,
        selected=setsSelected,
    )  # Reinitialize set options list with sets from file
    experimentTabPlotTubeSelectionTubeList = ListBox(
        experimentTabPlotTubeSelectionTubeListFrame,
        scrollbar=True,
        width=150,
        height="fill",
        align="top",
        command=populatePlotTubeSelectionLists,
        items=tubesToDisplay,
        selected=tubesSelected,
    )  # Reinitialize tube options list with tubes from file


def saveStatisticalAnalysisData():#all periods etc
    global workingDir
    global experimentTabStatisticalAnalysisSetList
    global experimentTabStatisticalAnalysisTubeList
    global experimentTabStatisticalAnalysisMethodList
    global tubesMaster
    
    setNamesSelected = experimentTabStatisticalAnalysisSetList.value
    tubesSelected = experimentTabStatisticalAnalysisTubeList.value
    fileRows = []  # Blank list of periods for analysis
    for tube in tubesMaster:  # For each tube in master tubes list
        if (tube["setName"] + " | " + str(tube["tubeNumber"] + 1)) in tubesSelected:  # If tube and set name match a selected tube option
            fileRow = [tube["setName"], str(tube["tubeNumber"]+1)] + list(calculatePeriodData(tube["densityProfile"], tube["markHours"], tube["timeMarks"], tube["bandMarks"], 14, 32, tube["tubeRange"])[0:3])
            fileRows.append(fileRow)  # Add selected period to list of periods for analysis
    periodsManual = []
    periodsSokoloveBushell= []
    periodsLombScargle = []
    for row in fileRows:
        periodsManual.append(row[2])
        periodsSokoloveBushell.append(row[3])
        periodsLombScargle.append(row[4])
    fileRows.append(["Mean", "n = "+str(len(periodsManual)), numpy.mean(periodsManual), numpy.mean(periodsSokoloveBushell), numpy.mean(periodsLombScargle)])
    fileRows.append(["Standard Deviation", "", numpy.std(periodsManual), numpy.std(periodsSokoloveBushell), numpy.std(periodsLombScargle)])
    fileRows.append(["Standard Error of Means", "", numpy.std(periodsManual)/numpy.sqrt(len(periodsManual)), numpy.std(periodsSokoloveBushell)/numpy.sqrt(len(periodsSokoloveBushell)), numpy.std(periodsLombScargle)/numpy.sqrt(len(periodsLombScargle))])
    dataFileName = app.select_file(
        title="Save period data as...",
        folder=workingDir,
        filetypes=[["CSV", "*.csv"]],
        save=True,
        filename=("_".join(setNamesSelected) + "_period_data"),
    )
    with open(dataFileName, 'w', newline='') as dataFile:
        rowWriter = csv.writer(dataFile, delimiter=',')
        rowWriter.writerow(["Pack Name", "Tube #", "τ (hrs) (Manually Calculated)", "τ (hrs) (Sokolove-Bushell)", "τ (hrs) (Lomb-Scargle)"])
        for fileRow in fileRows:
            rowWriter.writerow(fileRow)


def saveDensitometryPlot():
    global plotsInfo
    global workingDir
    global experimentTabPlotTubeSelectionSetList
    global experimentTabPlotTubeSelectionTubeList
    global appParameters
    
    if plotsInfo is not []:
        tubeNumber = experimentTabPlotTubeSelectionTubeList.value[experimentTabPlotTubeSelectionTubeList.value.rindex("|")+2:]
        plotFileName = app.select_file(
            title="Save plot as...",
            folder=workingDir,
            filetypes=[["PNG", "*.png"], ["JPG", "*.jpg"], ["JPEG", "*.jpeg"], ["TIFF", "*.tif"], ["SVG", "*.svg"]],
            save=True,
            filename=(experimentTabPlotTubeSelectionSetList.value + "_tube" + tubeNumber + "_densitometry"),
        )
        densitometryXValsHours = plotsInfo[0]
        densitometryYVals = plotsInfo[1]
        timeMarksHours = plotsInfo[2]
        bandMarksHours = plotsInfo[3]
        densitometryXAxisLabels = matplotlib.ticker.FixedLocator(list(range(-24, 193, 12)))
        densitometryYAxisLabels = matplotlib.ticker.FixedLocator([0, 60, 120, 180, 240, 255])
        densitometryXAxisMinorLabels = matplotlib.ticker.FixedLocator(list(range(-24, 193, 3)))
        densitometrySingleFigure = plt.figure(figsize=[7.5, 2.1])
        densitometrySingleFigurePlot = densitometrySingleFigure.add_subplot()
        densitometrySingleFigurePlot.plot(densitometryXValsHours, densitometryYVals, label="Density profile", color=appParameters["colorGraph"])
        densitometrySingleFigurePlot.xaxis.set_major_locator(densitometryXAxisLabels)
        densitometrySingleFigurePlot.yaxis.set_major_locator(densitometryYAxisLabels)
        densitometrySingleFigurePlot.xaxis.set_minor_locator(densitometryXAxisMinorLabels)
        densitometrySingleFigurePlot.set(
            xlabel="Time (hrs)", 
            ylabel="Density", 
            title="Densitogram"
        )
        densitometrySingleFigurePlot.vlines(
            timeMarksHours,
            numpy.min(densitometryYVals),
            numpy.max(densitometryYVals),
            colors=appParameters["colorVert"],
            label="Time Marks",
        )
        densitometrySingleFigurePlot.vlines(
            bandMarksHours, 
            numpy.min(densitometryYVals), 
            numpy.max(densitometryYVals), 
            colors=appParameters["colorBand"], 
            label="Bands"
        )
        densitometrySingleFigurePlot.grid()
        densitometrySingleFigurePlot.legend(ncol=3, loc="best", fontsize="x-small")
        densitometrySingleFigure.tight_layout(pad=2)
        densitometrySingleFigure.savefig(plotFileName)


def savePeriodogramPlot():
    global plotsInfo
    global workingDir
    global experimentTabPlotTubeSelectionSetList
    global experimentTabPlotTubeSelectionTubeList
    global experimentTabPlotTubeSelectionMethodList
    global appParameters

    if plotsInfo is not []:
        tubeNumber = experimentTabPlotTubeSelectionTubeList.value[experimentTabPlotTubeSelectionTubeList.value.rindex("|")+2:]
        plotFileName = app.select_file(
            title="Save plot as...",
            folder=workingDir,
            filetypes=[["PNG", "*.png"], ["JPG", "*.jpg"], ["JPEG", "*.jpeg"], ["TIFF", "*.tif"], ["SVG", "*.svg"]],
            save=True,
            filename=(experimentTabPlotTubeSelectionSetList.value + "_tube" + tubeNumber + "_" + experimentTabPlotTubeSelectionMethodList.value),
        )
        periodogramXVals = plotsInfo[4]
        periodogramYVals = plotsInfo[5]
        periodogramXAxisLabels = plotsInfo[6]
        periodogramSingleFigure = plt.figure(figsize=[7.5, 2.1])
        periodogramSingleFigurePlot = periodogramSingleFigure.add_subplot()
        if experimentTabPlotTubeSelectionMethodList.value == "Sokolove-Bushell":
            periodogramSingleFigurePlot.plot(periodogramXVals, periodogramYVals, label="Chi Squared", color=appParameters["colorGraph"])
        else:
            periodogramSingleFigurePlot.plot(periodogramXVals, periodogramYVals, label="Spectral Density", color=appParameters["colorGraph"])
        periodogramSingleFigurePlot.xaxis.set_major_locator(periodogramXAxisLabels)
        periodogramSingleFigurePlot.set(
            xlabel="Period (hrs)",
            title="Periodogram",
        )
        if experimentTabPlotTubeSelectionMethodList.value == "Sokolove-Bushell":
            periodogramSingleFigurePlot.set(ylabel="Chi Squared")
        else:
            periodogramSingleFigurePlot.set(ylabel="Spectral Density")
        periodogramSingleFigurePlot.grid()
        periodogramSingleFigurePlot.legend(fontsize="x-small")
        periodogramSingleFigure.tight_layout(pad=2)
        periodogramSingleFigure.savefig(plotFileName)


def saveDensitometryData():
    global workingDir
    global experimentTabPlotTubeSelectionSetList
    global experimentTabPlotTubeSelectionTubeList
    global tubesMaster
    
    setName = experimentTabPlotTubeSelectionSetList.value
    tubeNumber = int(experimentTabPlotTubeSelectionTubeList.value[experimentTabPlotTubeSelectionTubeList.value.rindex("|")+2:])-1
    densitometryFileName = app.select_file(
        title="Save densitometry as...",
        folder=workingDir,
        filetypes=[["CSV", "*.csv"]],
        save=True,
        filename=(setName + "_tube" + str(tubeNumber) + "_densitometry_data"),
    )
    densityProfile = []
    timeMarks = []
    bandMarks = []
    markHours = []
    for tube in tubesMaster:
        if tube["setName"] == setName and tube["tubeNumber"] == tubeNumber:
            densityProfile = tube["densityProfile"]
            timeMarks = tube["timeMarks"]
            bandMarks = tube["bandMarks"]
            markHours = tube["markHours"]
    timeGaps = []
    for mark in range(0, len(timeMarks) - 1):
        timeGaps.append((timeMarks[mark + 1] - timeMarks[mark]) / (markHours[mark + 1] - markHours[mark]))
    meanGrowthPixelsPerHour = numpy.mean(timeGaps)
    meanGrowthHoursPerPixel = 1 / meanGrowthPixelsPerHour
    with open(densitometryFileName, 'w', newline='') as csvfile:
        rowWriter = csv.writer(csvfile, delimiter=',')
        rowWriter.writerow(["Pixel (from left)", "Time (hrs)", "Density Profile", "Time/Band Marks"])
        for index in range(0, 1160):
            densityInHours = round((index - timeMarks[0]) * meanGrowthHoursPerPixel, 4)
            newLine = [index, densityInHours, densityProfile[index], "N/A"]
            markNote = []
            if index in timeMarks:
                markNote.append("Time")
            if index in bandMarks:
                markNote.append("Band")
            if markNote is not []:
                newLine[3] = "/".join(markNote)
            rowWriter.writerow(newLine)


def savePeriodogramData():
    global workingDir
    global experimentTabPlotTubeSelectionSetList
    global experimentTabPlotTubeSelectionTubeList
    global experimentTabPlotTubeSelectionMethodList
    global tubesMaster
    global plotsInfo

    setName = experimentTabPlotTubeSelectionSetList.value
    tubeNumber = int(experimentTabPlotTubeSelectionTubeList.value[experimentTabPlotTubeSelectionTubeList.value.rindex("|")+2:])-1
    method = experimentTabPlotTubeSelectionMethodList.value
    periodogrammetryFileName = app.select_file(
        title="Save densitometry as...",
        folder=workingDir,
        filetypes=[["CSV", "*.csv"]],
        save=True,
        filename=(setName + "_tube" + str(tubeNumber) + "_" + method + "_data"),
    )
    method = None  # Initialize method variable
    match experimentTabPlotTubeSelectionMethodList.value:  # Based on plot method selected
        case "Sokolove-Bushell":  # If method is Sokolove-Bushell
            method = 4  # Set method to 4
        case "Lomb-Scargle":  # If method is Lomb-Scargle
            method = 6  # Set method to 6
    tubeToPlot = []
    timeMarks = []
    markHours = []
    for tube in tubesMaster:
        if tube["setName"] == setName and tube["tubeNumber"] == tubeNumber:
            tubeToPlot = tube
            timeMarks = tubeToPlot["timeMarks"]
            markHours = tubeToPlot["markHours"]
    timeGaps = []
    for mark in range(0, len(timeMarks) - 1):
        timeGaps.append((timeMarks[mark + 1] - timeMarks[mark]) / (markHours[mark + 1] - markHours[mark]))
    meanGrowthPixelsPerHour = numpy.mean(timeGaps)
    meanGrowthHoursPerPixel = 1 / meanGrowthPixelsPerHour
    periodData = calculatePeriodData(tubeToPlot["densityProfile"], markHours, timeMarks, tubeToPlot["bandMarks"], 14, 32, tubeToPlot["tubeRange"])
    periodogramXVals = []
    periodogramYVals = []
    periodogramFrequencies = []
    calculatedPeriodogramFrequencies = periodData[method-1]
    calculatedPeriodogramYVals = periodData[method]
    slopeCoeff = periodData[9]
    for index in range(0, len(calculatedPeriodogramFrequencies)):
        if method == 4:  # SB
            period = 1 / calculatedPeriodogramFrequencies[index]
        else:# LS
            period = (2 * numpy.pi) / calculatedPeriodogramFrequencies[index]
        xVal = period * meanGrowthHoursPerPixel * slopeCoeff
        if xVal >= 14 and xVal <= 32:
            periodogramXVals.append(xVal)
            periodogramYVals.append(calculatedPeriodogramYVals[index])
            periodogramFrequencies.append(calculatedPeriodogramFrequencies[index])
    with open(periodogrammetryFileName, 'w', newline='') as csvfile:
        rowWriter = csv.writer(csvfile, delimiter=',')
        if method == 4:
            rowWriter.writerow(["Frequency", "τ (hrs)", "Spectral Density"])
        elif method == 6:
            rowWriter.writerow(["Angular Frequency", "τ (hrs)", "Spectral Density"])
        for index in range(0, len(periodogramXVals)):
            newLine = [periodogramFrequencies[index], periodogramXVals[index], periodogramYVals[index]]
            rowWriter.writerow(newLine)


def saveTubesToFile(setName):
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

    setNamesInFile = []
    for tube in tubesMaster:
        setNamesInFile.append(tube["setName"])
    if setName in setNamesInFile:
        setName = setName + "_1"
    topTubeTimeMarks = []  # Blank list of time mark x values
    for line in timeMarkLines:  # For each line in list of time marks
        if line[2] == 0:  # If line is in current tube
            topTubeTimeMarks.append(line[0])  # Add line x to timeMarks
    topTubeTimeMarks.sort()  # Sort time marks low to high/left to right
    mmPerPixelInImage = int(tubeLength) / (topTubeTimeMarks[-1] - topTubeTimeMarks[0])
    for tube in range(0, len(tubeBounds)):  # For each tube in tubeBounds
        tubeRange = tubeBounds[tube]  # Y bounds of tube
        densityProfile = densityProfiles[tube]  # Density profile of tube
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
        meanGrowthPixelsPerHour = numpy.mean(timeGaps)  # Mean time gap in pixels per hour
        growthRate = round(mmPerPixelInImage * meanGrowthPixelsPerHour, 2)#mm per hour
        tubesMaster.append(
            {
                "setName":setName,
                "imageName":imageName,
                "imageData":imageString,
                "tubeNumber":tube,
                "markHours":markHours,
                "densityProfile":densityProfile,
                "growthRate":growthRate,
                "tubeRange":tubeRange,
                "timeMarks":timeMarks,
                "bandMarks":bandMarks
            }
        )  # Add tube info to master tubes list
    saveExperimentFile()  # Save tubes to file
    cancelImageAnalysis()  # Reset image analysis
    populateExperimentDataTable(tubesMaster)  # Populate experiment data table


def proceedHandler():
    """Handle clicks on proceed button based on analysis state."""
    global analState
    global tubeBounds
    global markHours
    global timeMarkLines
    global bandLines

    match analState:  # Based on analysis state
        case 2:  # Analysis state 2 (tube bounds)
            identifyRaceTubeBounds()
        case 5:  # Analysis state 5 (time marks)
            identifyBanding()
        case 7:  # Analysis state 7 (band locations)
            analState = 8  # Set analysis state to 8
            for tube in range(0, len(tubeBounds)):  # For each tube in tubeBounds
                tubeRange = tubeBounds[tube]  # Y bounds of tube
                densityProfile = densityProfiles[tube]  # Density profile of tube
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
                periods = calculatePeriodData(densityProfile, markHours, timeMarks, bandMarks, 14, 32, tubeRange)  # Calculate period data of tube
                prelimContents[tube + 1][2] = str(round(periods[0], 2))  # Add manually calculated period (rounded) to preliminary data list
            updatePreliminaryDataDisplay()  # Update preliminary data text box
            proceedButton.disable()  # Disable proceed button
            saveTubesToFileButton.enable()  # Enable save tubes button


def keyBindHandler(keys):  # Shift, Command, S, O, P, D, H
    """Handle uses of multikey hotkeys to perform program functions"""
    global keyPresses

    match keys:  # Based on list of pressed keys
        case [0, 1, 1, 0, 0, 0, 0]:  # If command, s pressed
            saveExperimentFile()  # Save experiment
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [1, 1, 1, 0, 0, 0, 0]:  # If shift, command, s pressed
            saveExperimentFileAs()  # Save as
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [0, 1, 0, 1, 0, 0, 0]:  # If command, o pressed
            openExperimentFile()  # Open experiment file
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [0, 1, 0, 0, 0, 1, 0]:  # If command, d pressed
            setWorkingDirectory()  # Set working directory
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [0, 1, 0, 0, 0, 0, 1]:  # If command, h pressed
            helpMain()  # Open main help page
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list
        case [0, 1, 0, 0, 1, 0, 0]:  # If command, p pressed
            graphicsPreferencesPrompt()  # Open graphics settings
            keyPresses = [0, 0, 0, 0, 0, 0, 0]  # Reset key press list


def keyPress(keyPressed):
    """Handle each key press registered by app object."""
    global keyPresses

    match [str(keyPressed.key), str(keyPressed.keycode)]:  # Based on key and keycode of key pressed
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
    match [str(keyReleased.key), str(keyReleased.keycode)]:  # Based on key and keycode of key released
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
    )


def invertColor(hex):
    """Invert color given as hex code and return hex code of inverted color."""
    
    hex = hex.lstrip('#')
    rgb =  tuple(255 - int(hex[i:i + len(hex) // 3], 16) for i in range(0, len(hex), len(hex)//3))
    out = '#%02x%02x%02x' % rgb
    return out


def graphicsPreferencesPrompt():
    """Present popup window for changing graphics preferences."""
    global appParameters

    graphicsPreferencesWindow = Window(app, title="Graphics Preferences", layout="grid", width=375, height=300)
    graphicsPreferencesWindow.show()

    changeGraphColorButton = PushButton(graphicsPreferencesWindow, grid=[0,0], text="Graph Color", height=0, width=20, command=colorPickHandler, args=[0])
    changeGraphColorTextBox = TextBox(graphicsPreferencesWindow, grid=[2,0], text=appParameters["colorGraph"], width=7)
    changeHorizontalLineColorButton = PushButton(graphicsPreferencesWindow, grid=[0,1], text="Horizontal Line Color", height=0, width=20, command=colorPickHandler, args=[1])
    changeHorizontalLineColorTextBox = TextBox(graphicsPreferencesWindow, grid=[2,1], text=appParameters["colorHoriz"], width=7)
    changeVerticalLineColorButton = PushButton(graphicsPreferencesWindow, grid=[0,2], text="Time Mark Color", height=0, width=20, command=colorPickHandler, args=[2])
    changeVerticalLineColorTextBox = TextBox(graphicsPreferencesWindow, grid=[2,2], text=appParameters["colorVert"], width=7)
    changeBandLineColorButton = PushButton(graphicsPreferencesWindow, grid=[0,3], text="Band Mark Color", height=0, width=20, command=colorPickHandler, args=[3])
    changeBandLineColorTextBox = TextBox(graphicsPreferencesWindow, grid=[2,3], text=appParameters["colorBand"], width=7)

    changeGraphColorTextBox.text_color = appParameters["colorGraph"]
    changeGraphColorTextBox.bg = invertColor(appParameters["colorGraph"])
    changeHorizontalLineColorTextBox.text_color = appParameters["colorHoriz"]
    changeHorizontalLineColorTextBox.bg = invertColor(appParameters["colorHoriz"])
    changeVerticalLineColorTextBox.text_color = appParameters["colorVert"]
    changeVerticalLineColorTextBox.bg = invertColor(appParameters["colorVert"])
    changeBandLineColorTextBox.text_color = appParameters["colorBand"]
    changeBandLineColorTextBox.bg = invertColor(appParameters["colorBand"])

    graphicsPreferencesWindow.repeat(200, graphicsPreferencesPromptUpdate, args=[[changeGraphColorTextBox, changeHorizontalLineColorTextBox, changeVerticalLineColorTextBox, changeBandLineColorTextBox]])


def colorPickHandler(button):
    """Prompt user to pick a new color when a button to change a color preference is clicked."""
    global appParameters

    newColor = ""
    match button:
        case 0:
            newColor = app.select_color(color=appParameters["colorGraph"])
            appParameters["colorGraph"] = newColor
            updateAppParameters()
        case 1:
            newColor = app.select_color(color=appParameters["colorHoriz"])
            appParameters["colorHoriz"] = newColor
            updateAppParameters()
        case 2:
            newColor = app.select_color(color=appParameters["colorVert"])
            appParameters["colorVert"] = newColor
            updateAppParameters()
        case 3:
            newColor = app.select_color(color=appParameters["colorBand"])
            appParameters["colorBand"] = newColor
            updateAppParameters()
    drawLines()


def graphicsPreferencesPromptUpdate(texts):
    """Update graphics preferences window."""
    global appParameters
    
    texts[0].text_color = appParameters["colorGraph"]
    texts[0].value = appParameters["colorGraph"]
    texts[0].bg = invertColor(appParameters["colorGraph"])
    texts[1].text_color = appParameters["colorHoriz"]
    texts[1].value = appParameters["colorHoriz"]
    texts[1].bg = invertColor(appParameters["colorHoriz"])
    texts[2].text_color = appParameters["colorVert"]
    texts[2].value = appParameters["colorVert"]
    texts[2].bg = invertColor(appParameters["colorVert"])
    texts[3].text_color = appParameters["colorBand"]
    texts[3].value = appParameters["colorBand"]
    texts[3].bg = invertColor(appParameters["colorBand"])


def displaySetImagePopup():
    global tubesMaster
    #global experimentTabTableTextBox
    global experimentTabPlotTubeSelectionSetList

    #fontSizePt = experimentTabTableTextBox.text_size
    #fontSizeMap = {7:9, 8:11, 9:12, 10:13, 11:14, 12:16, 13:17, 14:19, 15:20}
    #fontHeightPx = fontSizeMap[fontSizePt]
    #fontHeightPx = 4*fontSizePt/3+1
    #textBoxLine = clickData.y/fontHeightPx
    #print(textBoxLine)
    #print(clickData.y)
    
    tubeNumber = -1
    for tube in enumerate(tubesMaster):
        if tube[1][0]:
            tubeNumber = tube[0]
    #tubeNumber = 3
    setName = tubesMaster[tubeNumber][0]
    imageName = tubesMaster[tubeNumber][1]
    imageData = tubesMaster[tubeNumber][2]
    imageArray = numpy.array(imageData).astype(numpy.uint8)
    imageConverted = Image.fromarray(imageArray).convert('RGB')
    imageThumbnailWindow = Window(app, title="Pack Image: "+setName+" ("+imageName+")", width=1160, height=400)
    imageThumbnailPicture = Drawing(imageThumbnailWindow, width="fill", height="fill")
    imageThumbnailPicture.image(0, 0, imageConverted, 1160, 400)
    imageThumbnailWindow.show()


def setupTasksOnOpenAndRun():  # Tasks to run on opening app
    """Tasks to run open opening the application. Reads in local parameters file to get user-defined settings, and preselects home tab."""
    global appParameters
    global workingDir

    directoryPath = os.path.dirname(__file__)
    parametersPath = os.path.join(directoryPath, "parameters.txt")
    with open(parametersPath, newline="") as parametersFile:  # Open parameters.txt file
        reader = csv.reader(parametersFile, delimiter="=")  # Define csv reader
        for line in reader:  # For each line in parameters.txt
            appParameters[line[0]] = line[1]  # Populate appropriate element of parameters dictionary
    if (appParameters["workingDir"] == "" or not (os.path.exists(appParameters["workingDir"]))):  # If a working directory is not already specified in parameters, or points to a nonexistent directory
        setWorkingDirectory()  # Prompt user to set a working directory
    else:  # Otherwise
        workingDir = appParameters["workingDir"]  # Set working directory to directory specified in parameters dictionary
    experimentTabFrame.hide()  # Hide experiment tab
    homeTabFrame.show()  # Show home tab


def openAndRun():
    """
    Colors
    Bright orange: #F29F05
    Bright blue: #69C5FF
    Accent dark: #676975
    Dull orange: #deb15e
    Dull blue: #9fcdea
    Light grey: grey95
    Rhythmidia logo red orange: #e05b4c or #eab47c
    """
    setupTasksOnOpenAndRun()
    app.display()



# Create app object
app = App(layout="auto", title="Rhythmidia (Alpha)")
app.when_closed = sys.exit
app.width = screenWidth
app.height = screenHeight
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
            ["Open Experiment                (⌘O)", openExperimentFile],
            ["Save Experiment                (⌘S)", saveExperimentFile],
            ["Save Experiment As...    (\u2191⌘S)", saveExperimentFileAs],
            ["Set Working Directory          (⌘D)", setWorkingDirectory],
            ["Graphics Preferences           (⌘P)", graphicsPreferencesPrompt]
        ],
        [["Help 1", helpMain]],
    ],
)

# Set up navigation tabs
navigationTabsFrame = Box(
    app, width="fill", align="top", layout="grid", border="0"
)  # Frame for Home, Experiment tabs
homeTab = Box(navigationTabsFrame, grid=[0, 0], border="0", height="30")  # Home tab button
homeTabText = Text(
    homeTab, text="Home", width=20, size=14, color="black", font="Arial"
)  # Home tab button text
experimentTab = Box(
    navigationTabsFrame, grid=[3, 0], border="0", height="30"
)  # Experiment tab button
experimentTabText = Text(
    experimentTab, text="Experiment", width=20, size=14, color="black", font="Arial"
)  # Home tab button text
# Set up tab colors
navigationTabsFrame.bg = "#676975"  # Dark grey nav bar
homeTab.bg = "#eab47c"  # Conidia orange home tab
experimentTab.bg = "#9fcdea"  # Baby blue experiment tab
# Set up tab functions
homeTabText.when_clicked = selectHomeTab
experimentTabText.when_clicked = selectExperTab

directoryPath = os.path.dirname(__file__)
imagePath = os.path.join(directoryPath, "rhythmidiaLogoBannerText.jpg")
logoFrame = Box(app, width="fill", height=50, align="bottom", layout="auto")
logoFrame.bg = "grey95"
logo = Picture(logoFrame, image=imagePath, width=181, height=50, align="left")

# Set up home tab
homeTabFrame = Box(app, width="fill", height="fill", align="top", layout="auto")
homeTabFrame.bg = "grey95"
homeTabFrame.set_border(5, "#eab47c")
homeTabFrame.text_color = "black"
homeTabVerticalSpacer1 = Box(homeTabFrame, height=5, width="fill", align="top")
# Home buttons
homeTabTopButtonRowFrame = Box(
    homeTabFrame, width="fill", height="20", align="top", layout="grid", border="0"
)
uploadRaceTubeImageButton = PushButton(
    homeTabTopButtonRowFrame, grid=[0, 0], text="Upload Race Tube Image", command=uploadRaceTubeImage
)
uploadRaceTubeImageButton.text_size = 13
homeTabTopButtonRowSpacer1 = Box(homeTabTopButtonRowFrame, grid=[1,0], height="fill", width=5)
rotateRaceTubeImageButton = PushButton(
    homeTabTopButtonRowFrame, grid=[2, 0], text="Rotate Image", command=rotateRaceTubeImage
)
rotateRaceTubeImageButton.text_size = 13
rotateRaceTubeImageButton.disable()
raceTubeLengthFrame = Box(homeTabTopButtonRowFrame, grid=[3, 0], border="0", height="20", layout="grid")
raceTubeLengthLabel = Text(
    raceTubeLengthFrame,
    color="black",
    grid=[0, 0],
    text="Length from first to last\ntime mark of 1st tube (mm)",
    size=12
)
raceTubeLengthTextBox = TextBox(raceTubeLengthFrame, text="300", grid=[1, 0])
raceTubeLengthTextBox.text_size = 13
homeTabTopButtonRowSpacer2 = Box(homeTabTopButtonRowFrame, grid=[4,0], height="fill", width=5)
lockAndAnalyzeButton = PushButton(
    homeTabTopButtonRowFrame, grid=[5, 0], text="Lock and Analyze", command=lockAndAnalyzeRaceTubeImage
)
lockAndAnalyzeButton.text_size = 13
lockAndAnalyzeButton.disable()
homeTabVerticalSpacer2 = Box(homeTabFrame, height=5, width="fill", align="top")
homeTabMiddleContentFrame = Box(homeTabFrame, align="top", border="0", width="fill")
timeMarkTableFrame = Box(homeTabMiddleContentFrame, width=180, height=400, align="left")
timeMarkTableRows = [Box(timeMarkTableFrame, align="top", layout="grid", width="fill")]
timeMarkTableRows[0].bg = "grey75"
timeMarkTableLabels = []
timeMarkTableDataTextBoxes = []
timeMarkTableHeader1 = Text(timeMarkTableRows[0], grid=[0, 0], text="Mark ", font="Courier", size=14)
timeMarkTableHeader2 = Text(timeMarkTableRows[0], grid=[1, 0], text="Day ", font="Courier", size=14)
timeMarkTableHeader3 = Text(timeMarkTableRows[0], grid=[2, 0], text="Hour ", font="Courier", size=14)
timeMarkTableHeader4 = Text(timeMarkTableRows[0], grid=[3, 0], text="Min", font="Courier", size=14)
for row in range(1, 11):
    timeMarkTableRows.append(Box(timeMarkTableFrame, align="top", layout="grid", width="fill"))
    if timeMarkTableRows[row - 1].bg == "grey75":
        timeMarkTableRows[row].bg = "grey85"
    else:
        timeMarkTableRows[row].bg = "grey75"
    timeMarkTableLabels.append(
        Text(
            timeMarkTableRows[row],
            grid=[0, 0],
            text=str(row) + " " * (5 - len(str(row))),
            font="Courier",
            size=14,
        )
    )
    timeMarkTableDataTextBoxes.append(
        TextBox(timeMarkTableRows[row], grid=[1, 0], text=str(row - 1), width=3)
    )
    timeMarkTableDataTextBoxes.append(TextBox(timeMarkTableRows[row], grid=[2, 0], text="0", width=3))
    timeMarkTableDataTextBoxes.append(TextBox(timeMarkTableRows[row], grid=[3, 0], text="0", width=3))
homeTabRaceTubeImageFrame = Box(homeTabMiddleContentFrame, width=1160, height=400, align="left")
homeTabRaceTubeImageObject = Drawing(homeTabRaceTubeImageFrame, width="fill", height="fill")
homeTabVerticalSpacer3 = Box(homeTabFrame, height=5, width="fill", align="top")
homeTabBottomButtonRowFrame = Box(homeTabFrame, width="fill", height=50)
proceedButton = PushButton(homeTabBottomButtonRowFrame, text="Proceed", command=proceedHandler, align="left")
proceedButton.text_size = 13
proceedButton.disable()
homeTabBottomButtonRowFrameSpacer1 = Box(homeTabBottomButtonRowFrame, height="fill", width=5, align="left")
homeTabConsoleTextBox = TextBox(homeTabBottomButtonRowFrame, width=80, height=4, multiline=True, align="left")
homeTabConsoleTextBox.disable()
homeTabBottomButtonRowFrameSpacer2 = Box(homeTabBottomButtonRowFrame, height="fill", width=5, align="left")
saveTubesToFileButton = PushButton(homeTabBottomButtonRowFrame, text="Save Tubes to File", command=saveTubesToFilePrompt, align="left")
saveTubesToFileButton.text_size = 13
saveTubesToFileButton.disable()
homeTabBottomButtonRowFrameSpacer3 = Box(homeTabBottomButtonRowFrame, height="fill", width=5, align="left")
resetRaceTubeImageAnalysisButton = PushButton(homeTabBottomButtonRowFrame, text="Cancel image analysis", command=cancelImageAnalysis, align="left")
resetRaceTubeImageAnalysisButton.text_size = 13
resetRaceTubeImageAnalysisButton.disable()
homeTabPreliminaryDataAnalysisFrame = Box(homeTabFrame, width="fill", height=400, align="top")
homeTabPreliminaryDataAnalysisTextBox = Text(homeTabPreliminaryDataAnalysisFrame, font="Courier", size=14, align="top")
# Set up home tab colors
raceTubeLengthFrame.bg = "gray95"
raceTubeLengthTextBox.text_color = "black"
homeTabRaceTubeImageFrame.bg = "#676975"
homeTabConsoleTextBox.text_color = "black"
# Set up home functions
homeTabRaceTubeImageObject.when_clicked = imageClickHandler


# Set up experiments tab
experimentTabFrame = Box(app, width="fill", height="fill", align="top")
experimentTabFrame.bg = "grey95"
experimentTabFrame.text_color = "black"
experimentTabFrame.set_border(5, "#9fcdea")
experimentTabTopContentRow = Box(experimentTabFrame, width="fill", height=appHeight*0.22, align="top")
experimentTabTableFrame = Box(experimentTabTopContentRow, width=screenWidth*0.45, height=appHeight*0.22, align="left")
experimentTabTableTextBox = TextBox(experimentTabTableFrame, multiline=True, width="fill", height="fill")
experimentTabTableTextBox.text_size = 11
experimentTabTableTextBox.disable()
experimentTabTableTextBox.when_double_clicked = displaySetImagePopup
experimentTabTableTextBox.wrap = False
experimentTabTableTextBox.font = "Courier"
experimentTabTableFrame.set_border(2, "#9fcdea")
experimentTabTableTextBox.text_color = "black"
experimentTabStatisticalAnalysisFrame = Box(experimentTabTopContentRow, width="fill", height="fill", align="left")
experimentTabStatisticalAnalysisFrame.set_border(2, "#9fcdea")
experimentTabStatisticalAnalysisSetListFrame = Box(experimentTabStatisticalAnalysisFrame, width=150, height="fill", align="left")
experimentTabStatisticalAnalysisSetListTitle = Text(experimentTabStatisticalAnalysisSetListFrame, text="\n\nSets:", align="top")
experimentTabStatisticalAnalysisSetList = ListBox(
    experimentTabStatisticalAnalysisSetListFrame,
    multiselect=True,
    scrollbar=True,
    align="top",
    width=150,
    height="fill",
    command=populateStatisticalAnalysisLists,
)
experimentTabStatisticalAnalysisTubeListFrame = Box(experimentTabStatisticalAnalysisFrame, width=150, height="fill", align="left")
experimentTabStatisticalAnalysisTubeListTitle = Text(experimentTabStatisticalAnalysisTubeListFrame, text="\n\nTubes:", align="top")
experimentTabStatisticalAnalysisTubeList = ListBox(
    experimentTabStatisticalAnalysisTubeListFrame,
    multiselect=True,
    scrollbar=True,
    align="top",
    width=150,
    height="fill",
    command=populateStatisticalAnalysisLists,
)
experimentTabStatisticalAnalysisMethodListFrame = Box(experimentTabStatisticalAnalysisFrame, width=150, height="fill", align="left")
experimentTabStatisticalAnalysisMethodListTitle = Text(experimentTabStatisticalAnalysisMethodListFrame, text="Statistical\nPeriod Analysis\nMethods:", align="top")
experimentTabStatisticalAnalysisMethodList = ListBox(
    experimentTabStatisticalAnalysisMethodListFrame,
    width=120,
    height="fill",
    align="top",
    items=["Manual", "Sokolove-Bushell", "Lomb-Scargle"],
    selected="Manual",
)
experimentTabStatisticalAnalysisButtonsFrame = Box(experimentTabStatisticalAnalysisFrame, height="fill", align="right")
experimentTabStatisticalAnalysisAnalyzeButton = PushButton(experimentTabStatisticalAnalysisButtonsFrame, text="Analyze", width="fill", command=performStatisticalAnalysis, align="top")
experimentTabStatisticalAnalysisAnalyzeButton.text_size = 13
experimentTabStatisticalAnalysisExportDataButton = PushButton(experimentTabStatisticalAnalysisButtonsFrame, text="Save\nPeriods and\nAnalysis\nData", width="fill", pady=2, command=saveStatisticalAnalysisData, align="top")
experimentTabStatisticalAnalysisExportDataButton.text_size = 13
experimentTabStatisticalAnalysisOutputFrame = Box(experimentTabStatisticalAnalysisFrame, width="fill", height="fill", align="right")
experimentTabStatisticalAnalysisOutputTitle = Text(experimentTabStatisticalAnalysisOutputFrame, text="\n\nStatistical Analysis:", align="top")
experimentTabStatisticalAnalysisOutputTextBox = TextBox(experimentTabStatisticalAnalysisOutputFrame, multiline=True, width=35, height=18, align="top")
experimentTabStatisticalAnalysisOutputTextBox.text_size = 11

experimentTabBottomContentRow = Box(experimentTabFrame, width="fill", height=screenWidth*0.2, align="top")
experimentTabPlotTubeSelectionFrame = Box(experimentTabBottomContentRow, width=screenWidth*0.45, height="fill", align="left")
experimentTabPlotTubeSelectionFrame.set_border(2, "#9fcdea")
experimentTabPlotTubeSelectionSetListFrame = Box(experimentTabPlotTubeSelectionFrame, width=150, height="fill", align="left")
experimentTabPlotTubeSelectionSetListTitle = Text(experimentTabPlotTubeSelectionSetListFrame, text="\n\nSets:", align="top")
experimentTabSetImagePopupButton = PushButton(experimentTabPlotTubeSelectionSetListFrame, text="Display pack image", align="bottom", width=150, height=0, command=displaySetImagePopup)
experimentTabSetImagePopupButton.text_size = 13

experimentTabPlotTubeSelectionSetList = ListBox(
    experimentTabPlotTubeSelectionSetListFrame,
    scrollbar=True,
    width=150,
    height="fill",
    align="top",
    command=populatePlotTubeSelectionLists,
)
experimentTabPlotTubeSelectionTubeListFrame = Box(experimentTabPlotTubeSelectionFrame, width=150, height="fill", align="left")
experimentTabPlotTubeSelectionTubeListTitle = Text(experimentTabPlotTubeSelectionTubeListFrame, text="\n\nTubes:", align="top")
experimentTabPlotTubeSelectionTubeList = ListBox(
    experimentTabPlotTubeSelectionTubeListFrame,
    scrollbar=True,
    width=150,
    height="fill",
    align="top",
    command=populatePlotTubeSelectionLists,
)
experimentTabPlotTubeSelectionMethodListFrame = Box(experimentTabPlotTubeSelectionFrame, width=150, height="fill", align="left")
experimentTabPlotTubeSelectionMethodListTitle = Text(experimentTabPlotTubeSelectionMethodListFrame, text="Plot\nPeriod Analysis\nMethods:", align="top")
experimentTabPlotTubeSelectionMethodList = ListBox(
    experimentTabPlotTubeSelectionMethodListFrame,
    width=120,
    height="fill",
    align="top",
    items=["Sokolove-Bushell", "Lomb-Scargle"],
    selected="Manual",
)
experimentTabPlotTubeSelectionButtonsFrame = Box(experimentTabPlotTubeSelectionFrame)
experimentTabPlotTubeSelectionCreatePlotsButton = PushButton(experimentTabPlotTubeSelectionButtonsFrame, text="Plot", command=populatePlots, width="fill")
experimentTabPlotTubeSelectionCreatePlotsButton.text_size = 13
experimentTabPlotTubeSelectionSaveDensitometryPlotButton = PushButton(
    experimentTabPlotTubeSelectionButtonsFrame, 
    text="Save\nDensitometry\nPlot", 
    pady=2, 
    command=saveDensitometryPlot, 
    width="fill"
)
experimentTabPlotTubeSelectionSaveDensitometryPlotButton.text_size = 13
experimentTabPlotTubeSelectionSaveDensitometryButton = PushButton(
    experimentTabPlotTubeSelectionButtonsFrame,
    text="Save\nDensitometry\nData",
    pady=2,
    command=saveDensitometryData,
    width="fill",
)
experimentTabPlotTubeSelectionSaveDensitometryButton.text_size = 13
experimentTabPlotTubeSelectionSavePeriodogramPlotButton = PushButton(
    experimentTabPlotTubeSelectionButtonsFrame, 
    text="Save\nPeriodogram\nPlot", 
    pady=2, 
    command=savePeriodogramPlot, 
    width="fill"
)
experimentTabPlotTubeSelectionSavePeriodogramPlotButton.text_size = 13
experimentTabPlotTubeSelectionSavePeriodogramDataButton = PushButton(
    experimentTabPlotTubeSelectionButtonsFrame,
    text="Save\nPeriodogram\nData",
    pady=2,
    command=savePeriodogramData,
    width="fill",
)
experimentTabPlotTubeSelectionSavePeriodogramDataButton.text_size = 13
experimentTabPlotFrame = Box(experimentTabBottomContentRow, width=screenWidth*0.5, height=screenWidth*0.2, align="left")
experimentTabPlotFrame.set_border(2, "#9fcdea")
experimentTabPlotCanvas = Canvas(experimentTabPlotFrame.tk, width=screenWidth*0.5, height=screenWidth*0.2)
experimentTabPlotFrame.add_tk_widget(experimentTabPlotCanvas)


if __name__ == "__main__":
    openAndRun()#this just runs the gui when you run the script; this is the function to run from command line when you have the full package installed