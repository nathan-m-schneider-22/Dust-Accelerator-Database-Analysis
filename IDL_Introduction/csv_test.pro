
data = read_csv(("C:\Users\CCLDAS\IDLWorkspace85\default\test_data2.csv"))

print, data
print, filepath("test_data2.csv")

mx = MAX(array, location)
ind = ARRAY_INDICES(array, location)
PRINT, ind, array[ind[0],ind[1]], $
  FORMAT = '(%"Value at [%d, %d] is %f")'
  
