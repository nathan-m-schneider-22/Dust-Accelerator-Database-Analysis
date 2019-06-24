seed = 13
maxX = 10
maxY = 10

random_factor = 20

array = intarr(maxX,maxY)
for i = 0,maxX-1 do begin $
  for j = 0,maxY-1 do begin $
    array(i,j) = (-3 * ((i-5)^2 + (j-5)^2)) + randomu(seed)*random_factor
    
WRITE_CSV, filepath("test_data2.csv"), array
print, "done"

