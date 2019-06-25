seed = 111
array = RANDOMN(seed, 10, 10, /RAN1)
mx = MAX(array, location)
ind = ARRAY_INDICES(array, location)
PRINT, ind, array[ind[0],ind[1]], $
  FORMAT = '(%"Value at [%d, %d] is %f")'
