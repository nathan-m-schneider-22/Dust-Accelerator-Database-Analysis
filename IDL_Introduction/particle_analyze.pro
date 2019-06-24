PRO particle_analyze

  min_speed = 5*10^3
  max_speed = 25*10^3
  
  target_count =0
  
  count = 0
  file = "C:\Users\CCLDAS\Downloads\TOBIN_TEST_TIME.csv"
  data = READ_CSV(file, COUNT=total_particles, N_TABLE_HEADER=1)
  
  array = data(0)
  ar = data.(4)

  for i=0, total_particles -1 do begin $
    val = ar[i]
    if (val GT min_speed) AND (val LT max_speed) THEN BEGIN
      target_count++
    endif
  endfor
  print, target_count
  print,min_speed, max_speed, target_count, total_particles, DOUBLE(target_count)/total_particles*100 , $
     FORMAT = '(%"Total Particles between %7.0f and %10.0f m/s: %d out of %d\n Percentage: %5.2f")'
  
   ;PRINT, ind, array[ind[0],ind[1]], $
     ;FORMAT = '(%"Value at [%d, %d] is %f")'


END