"""ascii.py -- Has routines python_data <=> ascii_files."""
from typing import List

from enforce_typing import enforce_types
import numpy

# ===========================================================
# Routines for importing / exporting to simple ascii files


@enforce_types
def asciiRowToStrings(filename: str) -> List[str]:
    """Extract and returns a list of strings from the first row of the file.

    Args:
        filename

    Returns:
        list of string
    """
    f = open(filename, "r")
    line = f.readline()
    f.close()

    if "," in line:
        line = line.replace(",", " ")

    strings = line.split()

    return strings


@enforce_types
def asciiTo2dArray(filename: str):
    """Create 2d array.

    Extracts and returns a 2d array from the file; one row in X
    for each row of file.

    Args:
        filename -- indicates file to extract data from

    Return:
        X: 2d array of float [row #][column #] -- extracted output data
    """
    X = []
    f = open(filename, "r")

    for line in f:
        if "," in line:
            line = line.replace(",", " ")

        numbers = [float(entry) for entry in line.split()]
        if numbers:
            X.append(numbers)

    f.close()
    X = numpy.array(X) # type: ignore # skip mypy complaint
    return X


@enforce_types
def arrayToAscii(filename: str, X):
    """Puts 2d array X into ascii file.

    Args:
        filename -- file to create
        X: 2d array --
    """
    f = open(filename, "w")
    num_rows, num_columns = X.shape
    for row_index in range(num_rows):
        s = ""
        for col_index in range(num_columns):
            s += "%g " % X[row_index, col_index]
        s += "\n"
        f.write(s)
    f.close()


@enforce_types
def stringToAscii(filename: str, string: str):
    stringsToAscii(filename, [string])


@enforce_types
def stringsToAscii(filename: str, strings: List[str], add_whitespace: bool = True):
    """Puts list of strings into one row of an ascii file (which it creates)

    Args:
        filename -- file to create
        strings
        add_whitespace -- add whitespace?
    """
    s = ""
    for string in strings:
        s += string
        if add_whitespace:
            s += " "
    s += "\n"
    f = open(filename, "w")
    f.write(s)
    f.close()


# ===========================================================
# Routines for importing / exporting to .hdr + .val files


@enforce_types
def hdrValFilesToTrainingData(input_filebase: str, target_varname: str):
    """Extracts useful info from input_filebase.hdr and input_filebase.val

    Args:
      input_filebase -- points to two files
      target_varname -- this will be the y, and the rest will be the X

    Returns:
      Xy: 2d array [#vars][#samples] -- transpose of the data from .val file
      X:  2d array [#full_input_vars][#samples] -- Xy, except y
      y:  1d array [#samples] -- the vector in Xy corr. to target_varname
      all_varnames: List[str] -- essentially what .hdr file holds
      input_varnames: List[str] -- all_varnames, minus target_varname
    """
    # retrieve varnames
    all_varnames = asciiRowToStrings(input_filebase + ".hdr")

    # split apart input and output labels
    x_rows, y_rows, input_varnames = [], [], []
    for (row, varname) in enumerate(all_varnames):
        if varname == target_varname:
            y_rows.append(row)
        else:
            x_rows.append(row)
            input_varnames.append(varname)
    assert len(y_rows) == 1, "expected to find one and only one '%s', not: %s" % (
        target_varname,
        all_varnames,
    )

    # split apart input and output data
    Xy_tr = asciiTo2dArray(input_filebase + ".val")
    Xy = numpy.transpose(Xy_tr)
    X = numpy.take(Xy, x_rows, 0)
    y = numpy.take(Xy, y_rows, 0)[0]

    assert X.shape[0] + 1 == Xy.shape[0] == len(input_varnames) + 1 == len(all_varnames)
    assert X.shape[1] == Xy.shape[1] == len(y)

    return Xy, X, y, all_varnames, input_varnames


@enforce_types
def trainingDataToHdrValFiles(output_filebase: str, varnames: List[str], Xy):
    """Creates output_filebase.hdr and output_filebase.val files.

    Args:
        output_filebase
        varnames -- put into .hdr file
        Xy: 2d array [#vars][#samples] -- put transpose of this into .val file
      <<none>> but two files get created
    """
    stringsToAscii(output_filebase + ".hdr", varnames)
    arrayToAscii(output_filebase + ".val", numpy.transpose(Xy))
