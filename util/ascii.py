"""ascii.py -- Has routines python_data <=> ascii_files."""
import logging
log = logging.getLogger('ascii')

import types

import numpy

#===========================================================
# Routines for importing / exporting to simple ascii files

def asciiRowToStrings(filename):
    """
    @description

      Extracts and returns a list of strings from the first row of the file.
      
    @arguments

      filename -- string 

    @return

      string_list -- list of string

    @exceptions

    @notes
    """
    f = open(filename, 'r')
    line = f.readline()
    f.close()
    
    if ',' in line:
        line = line.replace(',', ' ')
        
    strings = line.split()
        
    return strings

def asciiTo2dArray(filename):
    """
    @description

      Extracts and returns a 2d array from the file; one row in X
      for each row of file.
      
    @arguments

      filename -- string -- indicates file to extract data from

    @return

      X -- 2d array of float [row #][column #] -- extracted output data

    @exceptions

    @notes
    """
    X = []
    f = open(filename, 'r')

    
    for line in f:
        if ',' in line:
            line = line.replace(',', ' ')
            
        numbers = [float(entry) for entry in line.split()]
        if numbers:
            X.append(numbers)

    f.close()
    X = numpy.array(X)
    log.info('Loaded in array of size %d x %d from %s' %
             (X.shape[0], X.shape[1], filename))

    #HACK: make an array with 1/factor of the values
#     log.info("Make reduced: begin")
#     factor = 10
#     filename_red = filename + '.reduced' + str(factor)
#     X_red = numpy.take(X, range(0, X.shape[0], factor), 0)
#     arrayToAscii(filename_red, X_red)
#     log.info("Make reduced: size %d x %d, filename = %s; done" %
#              (X_red.shape[0], X_red.shape[1], filename_red))

    return X

def arrayToAscii(filename, X):
    """
    @description

      Puts 2d array X into ascii
      
    @arguments

      filename -- string -- file to create
      X -- 2d array -- 

    @return

      <<nothing>> but a file is created

    @exceptions

    @notes
    """
    f = open(filename, 'w')
    num_rows, num_columns = X.shape
    for row_index in range(num_rows):
        s = ""
        for col_index in range(num_columns):
            s += "%g " % X[row_index, col_index]
        s += "\n"
        f.write(s)
    f.close()

def stringToAscii(filename, string):
    stringsToAscii(filename, [string])

def stringsToAscii(filename, strings, add_whitespace=True):
    """
    @description

      Puts list of strings into one row of an ascii file
      
    @arguments

      filename -- string -- file to create
      strings -- list of string 

    @return

      <<nothing>> but a file is created

    @exceptions

    @notes
    """
    s = ""
    for string in strings:
        s += string
        if add_whitespace:
            s += " "
    s += "\n"
    f = open(filename, 'w')
    f.write(s)
    f.close()

#===========================================================
# Routines for importing / exporting to .hdr + .val files


def hdrValFilesToTrainingData(input_filebase, target_varname):
    """
    @description

      Extracts useful info from input_filebase.hdr and input_filebase.val

    @arguments

      input_filebase -- string -- points to two files
      target_varname -- string -- this will be the y, and the
        rest will be the X

    @return
    
      Xy -- 2d array [#vars][#samples] -- transpose of the data from .val file
      X -- 2d array [#full_input_vars][#samples] -- Xy, except y
      y -- 1d array [#samples] -- the vector in Xy corresponding
        to target_varname
      all_varnames -- list of string -- essentially what .hdr file holds
      input_varnames -- list of string -- all_varnames, minus target_varname
      
    @exceptions

    @notes
    """
    #retrieve varnames
    all_varnames = asciiRowToStrings(input_filebase + '.hdr')

    #split apart input and output labels
    x_rows, y_rows, input_varnames = [], [], []
    for (row, varname) in enumerate(all_varnames):
        if varname == target_varname:
            y_rows.append(row)
        else:
            x_rows.append(row)
            input_varnames.append(varname)
    assert len(y_rows) == 1, \
           "expected to find one and only one '%s', not: %s" % (target_varname, all_varnames)

    #split apart input and output data
    Xy_tr = asciiTo2dArray(input_filebase + '.val')
    Xy = numpy.transpose(Xy_tr)
    X = numpy.take(Xy, x_rows, 0)
    y = numpy.take(Xy, y_rows, 0)[0]

    assert X.shape[0]+1 == Xy.shape[0] == \
           len(input_varnames)+1 == len(all_varnames)
    assert X.shape[1] == Xy.shape[1] == len(y)
        
    return Xy, X, y, all_varnames, input_varnames


def trainingDataToHdrValFiles(output_filebase, varnames, Xy):
    """
    @description

      Creates output_filebase.hdr and output_filebase.val

    @arguments

      output_filebase -- string --
      varnames -- list of string -- put into .hdr file
      Xy -- 2d array [#vars][#samples] -- put transpose of this into .val file

    @return

      <<none>> but two files get created
      
    @exceptions

    @notes
    """
    stringsToAscii(output_filebase + '.hdr', varnames)
    arrayToAscii(output_filebase + '.val', numpy.transpose(Xy))

