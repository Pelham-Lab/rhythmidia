"""
Unit and regression test for the rhythmidia package.
"""

# Import package, test suite, and other packages as needed
import sys
import pytest
import guizero
import rhythmidia


def test_rhythmidia_imported():
    """Sample test, will always pass so long as import statement worked."""
    assert "rhythmidia" in sys.modules


def test_calculatePeriodData():
    openFileOutput = rhythmidia.openExperimentFile(specifyFile="/Users/akeeley/Documents/Python/CronoPy/unitTestFile.rmex", reopen=True)
    correctCalculatedPeriods = [
        (22.062491232117967, 21.01929236240736, 21.747914694534735),
        (22.238809969841444, 22.869698195936238, 21.46045999051059),
        (21.76142950634971, 22.64646372072278, 21.391344737477173),
        (22.14988486993049, 22.671058631575914, 21.508816412681682),
        (21.37948987689272, 22.57300508846683, 21.542899035706718),
        (21.784646378480584, 22.945087589925073, 21.864250981064462)
        ]
    calculatedPeriods = []
    for tube in openFileOutput:
        periodData = rhythmidia.calculatePeriodData(tube["densityProfile"], tube["markHours"], tube["timeMarks"], tube["bandMarks"], 14, 32, tube["tubeRange"])[:3]
        calculatedPeriods.append(periodData)
    assert calculatedPeriods == correctCalculatedPeriods


def test_invertColor():
    colorsToTest = ["#cf23af", "#47e6ec", "#29d016", "#204bfc", "#886cad"]
    correctInvertedColors = ["#30dc50", "#b81913", "#d62fe9", "#dfb403", "#779352"]
    testInvertedColors = []
    for color in colorsToTest:
        testInvertedColors.append(rhythmidia.invertColor(color))
    assert testInvertedColors == correctInvertedColors
    