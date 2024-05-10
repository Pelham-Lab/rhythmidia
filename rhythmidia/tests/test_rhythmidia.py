"""
Unit and regression test for the rhythmidia package.
"""

# Import package, test suite, and other packages as needed
import sys
import os
import pytest
import numpy
import guizero
import rhythmidia
import csv
from PIL import Image, ImageEnhance


def test_rhythmidia_imported():
    """Sample test, will always pass so long as import statement worked."""
    
    assert "rhythmidia" in sys.modules


def test_calculatePeriodData():
    directoryPath = os.path.dirname(__file__)
    filePath = os.path.join(directoryPath, "unitTestFile.rmex")
    openFileOutput = rhythmidia.openExperimentFile(specifyFile=filePath, reopen=True)
    correctCalculatedPeriods = [
        (22.682618930565244, 23.35508428852803,	23.362599755420085, 23.50792258893955),
        (22.368398260756614, 22.97912801657649,	23.01147697533878, 23.171660540172763),
        (22.597961727572866, 22.972049674426234, 22.952756620895975, 23.04606201854591),
        (22.03981605211146,	22.757865960877066,	22.78423695713816,	22.96773254349345),
        (22.10750796876226,	22.718122801001243,	22.797811901413287,	22.87186139396556),
        (21.830767892015825, 22.11624540453645,	22.173579331020168,	23.09250458099304)
        ]
    calculatedPeriods = []
    for tube in openFileOutput:
        periodData = rhythmidia.calculatePeriodData(tube["densityProfile"], tube["markHours"], tube["timeMarks"], tube["bandMarks"], 14, 32, tube["tubeRange"], 0, 168)
        periodsSlice = (periodData["periodLinearRegression"], periodData["periodSokoloveBushell"], periodData["periodLombScargle"], periodData["periodWavelet"])
        calculatedPeriods.append(periodsSlice)
    
    assert numpy.allclose(calculatedPeriods, correctCalculatedPeriods)



def test_invertColor():
    colorsToTest = ["#cf23af", "#47e6ec", "#29d016", "#204bfc", "#886cad"]
    correctInvertedColors = ["#30dc50", "#b81913", "#d62fe9", "#dfb403", "#779352"]
    testInvertedColors = []
    for color in colorsToTest:
        testInvertedColors.append(rhythmidia.invertColor(color))
    
    assert testInvertedColors == correctInvertedColors


def test_parseTubeFromFile():
    testsTubeFile = os.path.join(os.path.dirname(__file__), "unitTestFile.rmex")
    parsedTube = None
    with open(testsTubeFile, newline="") as experimentFile:  # Open user-specified txt experiment file
        tubesInFile = csv.reader(experimentFile, delimiter="%")  # Define csv reader with delimiter %; generates iterable of all race tube datasets in specified experiment file
        for tube in tubesInFile:  # For each line of experiment file (each containing one race tube's data)
            parsedTube = rhythmidia.parseTubeFromFile(tube)
            break

    assert parsedTube["setName"]


def test_qIdentifyHorizontalLines():
    numpy.random.seed(42)
    testImageFile = os.path.join(os.path.dirname(__file__), "unitTestImage.jpg")
    testImage = numpy.array(Image.open(testImageFile).resize((1160, 400)).convert("L"))
    horizontalLineSlopes, horizontalLineIntercepts, meanTubeSlope = rhythmidia.qIdentifyHorizontalLines(testImage)
    
    assert len(horizontalLineIntercepts) <= 9 and len(horizontalLineIntercepts) > 4 and abs(meanTubeSlope) < 2


def test_qIdentifyRaceTubeBounds():
    testHorizontalLines = [[-0.015, 10], [-0.01, 20]]
    tubeBounds, meanTubeWidth = rhythmidia.qIdentifyRaceTubeBounds(testHorizontalLines)
    
    assert meanTubeWidth < 70


def test_qidentifyTimeMarks():
    testsTubeFile = os.path.join(os.path.dirname(__file__), "unitTestFile.rmex")
    testTubeData = None
    with open(testsTubeFile, newline="") as experimentFile:  # Open user-specified txt experiment file
        tubesInFile = csv.reader(experimentFile, delimiter="%")  # Define csv reader with delimiter %; generates iterable of all race tube datasets in specified experiment file
        ind = 0
        for tube in tubesInFile:  # For each line of experiment file (each containing one race tube's data)
            if ind == 1:
                testTubeData = rhythmidia.parseTubeFromFile(tube)
            ind += 1
    testImageFile = os.path.join(os.path.dirname(__file__), "unitTestImage.jpg")
    testImage = Image.open(testImageFile).resize((1160, 400)).convert("L")
    contraster = ImageEnhance.Contrast(testImage.convert("L"))  # Define contraster of numpy array of greyscale final image
    testImage = numpy.invert(numpy.array(contraster.enhance(3)))  # Set numpy image array to contrast level 3
    testTubeBounds = testTubeData["tubeRange"]
    timeMarkLines = rhythmidia.qidentifyTimeMarks(testImage, testTubeBounds, 1)
    
    regression_dataset = [[75, 100.34654309049077, 1], [214, 102.0960294857083, 1], [353, 103.84551588092582, 1], [507, 105.78379577203012, 1], [653, 107.62138579866148, 1], [823, 109.76104541871167, 1], [986, 111.81260140734805, 1], [1125, 113.56208780256557, 1]]

    assert numpy.allclose(timeMarkLines,regression_dataset)


def test_qidentifyBanding():
    testsTubeFile = os.path.join(os.path.dirname(__file__), "unitTestFile.rmex")
    testTubeData = None
    with open(testsTubeFile, newline="") as experimentFile:  # Open user-specified txt experiment file
        tubesInFile = csv.reader(experimentFile, delimiter="%")  # Define csv reader with delimiter %; generates iterable of all race tube datasets in specified experiment file
        ind = 0
        for tube in tubesInFile:  # For each line of experiment file (each containing one race tube's data)
            if ind == 1:
                testTubeData = rhythmidia.parseTubeFromFile(tube)
            ind += 1
    testImageFile = os.path.join(os.path.dirname(__file__), "unitTestImage.jpg")
    testImage = Image.open(testImageFile).resize((1160, 400)).convert("L")
    contraster = ImageEnhance.Contrast(testImage.convert("L"))  # Define contraster of numpy array of greyscale final image
    testImage = numpy.invert(numpy.array(contraster.enhance(3)))  # Set numpy image array to contrast level 3
    testTubeBounds = testTubeData["tubeRange"]
    timeMarkLines = rhythmidia.qidentifyTimeMarks(testImage, testTubeBounds, 1)
    bandLines = rhythmidia.qidentifyBanding(testImage, testTubeBounds, 0, timeMarkLines)
    
    regression_bandlines =  [[408, 104.53775869917736, 0], [868, 110.32742590637203, 0], [986, 111.81260140734805, 0], [1028, 112.34122319583105, 0]]
    assert numpy.allclose(bandLines, regression_bandlines)
