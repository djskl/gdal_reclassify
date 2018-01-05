#!/usr/bin/env python
import sys
from osgeo import gdal
from gdalconst import *
import numpy as np
import operator

gdal.AllRegister()


def getIntType(array_of_numbers):
    low, high = min(array_of_numbers), max(array_of_numbers)
    int_types = [
        (0, 255, np.uint8),
        (-128, 127, np.int16),
        (0, 65535, np.uint16),
        (-32768, 32767, np.int16),
        (0, 4294967295, np.uint32),
        (-2147483648, 2147483647, np.int32),
        (0, 18446744073709551615, np.uint64),
        (-9223372036854775808, 9223372036854775807, np.int64)
        ]

    for i in int_types:
        if low >= i[0] and high <= i[1]:
            int_np_type = i[2]
            break
    return int_np_type


def parseOutClasses(number_string):

    data_types = {
            np.dtype(np.uint8): GDT_Byte,
            np.dtype(np.int8): GDT_Int16,
            np.dtype(np.uint16): GDT_UInt16,
            np.dtype(np.int16): GDT_Int16,
            np.dtype(np.uint32): GDT_UInt32,
            np.dtype(np.int32): GDT_Int32,
            np.dtype(np.float32): GDT_Float32,
            np.dtype(np.int64): GDT_Int32,
            np.dtype(np.float64): GDT_Float64
        }

    out_classes = [i.strip() for i in number_string]
    pytype = int
    for i in out_classes:
        if '.' in i:
            pytype = float

    out_classes_parsed = [pytype(g) for g in out_classes]
    if pytype == float:
        np_dtype = np.float_
    else:
        np_dtype = getIntType(out_classes_parsed)
    gdal_dtype = data_types[np.dtype(np_dtype)]
    return np_dtype, gdal_dtype, out_classes_parsed


def parseDefault(default_in):
    if '.' in default_in:
        default_out = float(default_in)
    else:
        default_out = int(default_in)
    return default_out


def parseInClasses(classes, pytype):
    parsed_classes = []
    for cls in classes:
        parsed_classes.append(pytype(cls))
    return parsed_classes


def reclassArray(np_array, in_classes, out_classes, np_dtype):
    if np_dtype not in (np.uint8, np.int8, np.uint16, np.int16, np.uint32, np.int32, np.uint64):
        in_array = np_array.astype(float)
    else:
        in_array = np_array
    try:
        #rr = np.piecewise(in_array, [op_dict[i[0]](in_array,i[1]) for i in in_classes], out_classes)
        filters = [operator.eq(in_array,i) for i in in_classes]
        select_result = np.select(filters, out_classes)
        select_result_type_set = select_result.astype(np_dtype)
    finally:
        in_array = None
    return select_result_type_set


def processDataset(infile, outfile, classes, rules, nodata, output_format, compress_type):

    old_classes, new_classes = [], []
    rules = rules.split(",")
    for rule in rules:
        item = rule.strip().split(":")
        old_classes.append(item[0])
        new_classes.append(item[1])

    for clz in classes:
        cls = str(clz)
        if cls not in old_classes:
            old_classes.append(cls)
            new_classes.append(cls)

    np_dtype, gdal_dtype, out_classes = parseOutClasses(new_classes)
    src_ds = gdal.Open(infile)
    if src_ds is None:
        print 'Could not open image'
        sys.exit(1)

    rows, cols = src_ds.RasterYSize, src_ds.RasterXSize
    transform = src_ds.GetGeoTransform()
    block_size = src_ds.GetRasterBand(1).GetBlockSize()
    proj = src_ds.GetProjection()
    driver = gdal.GetDriverByName(output_format)
    dst_ds = driver.Create(outfile, cols, rows, 1, gdal_dtype, options = compress_type)

    out_band = dst_ds.GetRasterBand(1)
    x_block_size = block_size[0]
    y_block_size = block_size[1]
    sample = src_ds.ReadAsArray(0, 0, 1, 1)
    pytype = float
    if sample.dtype in (np.uint8, np.int8, np.uint16, np.int16, np.uint32, np.int32, np.uint64):
        pytype = int
    in_classes = parseInClasses(old_classes, pytype)
    for i in range(0, rows, y_block_size):
        if i + y_block_size < rows:
            num_rows = y_block_size
        else:
            num_rows = rows - i
        for j in range(0, cols, x_block_size):
            if j + x_block_size < cols:
                num_cols = x_block_size
            else:
                num_cols = cols - j
            block = src_ds.ReadAsArray(j, i, num_cols, num_rows)
            reclassed_block = reclassArray(block, in_classes, out_classes, np_dtype)
            out_band.WriteArray(reclassed_block, j, i)
    out_band.FlushCache()
    dst_ds.SetGeoTransform(transform)
    if nodata is not None:
        out_band.SetNoDataValue(nodata)
        print 'setting', nodata, 'as no data value'
    out_band.GetStatistics(0, 1)
    dst_ds.SetProjection(proj)
    src_ds = None

if __name__ == '__main__':
    processDataset("/root/wms_clip.tiff", "/root/wms_reclass.tiff", range(1, 8), "2:5, 3:6", 0, "GTiff", ["COMPRESS=NONE"])

