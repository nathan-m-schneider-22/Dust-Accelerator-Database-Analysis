import pickle
import sys
from datetime import datetime
import time

accelerator_range = 100
bin_size = .1



class Session:
    def __init__(self, start, end,minV,maxV):
        
        self.start = start
        self.end = end
        self.duration = end-start   
        self.material = None
        self.dustID = None
        self.experimentID = None
        self.min_V = minV
        self.max_V = maxV
        self.p_list = []
        self.quality = 5
    def __str__(self):
        return "Session from %s to %s \nDuration: %.1f min material: %s, %.1f-%.1fkm/s %d %d\nDustID: %s \
ExperimentID: %s particles: %d Quality: %d\n------------------------------------------\
" %(datetime.fromtimestamp(self.start/1000).strftime("%c"),\
            datetime.fromtimestamp(self.end/1000).strftime("%c"),\
            self.duration/1000/60,self.material,self.min_V,self.max_V,self.start,self.end,\
            self.dustID,self.experimentID,len(self.p_list),self.quality)


def main():
    st = time.time()
    with open("temp_data.pkl","rb") as load_file:
        session_list = pickle.load(load_file)
        input_list = sys.stdin.readline().split("|")
        start = int(input_list[0])
        stop = int(input_list[1])
        dustID = str(input_list[2])
        vmin = float(input_list[3])
        vmax = float(input_list[4])
        material = str(input_list[5])
        pq_min = int(input_list[6])
        pq_max = int(input_list[7])
        sq_min = int(input_list[8])
        sq_max = int(input_list[9])
        experiment_id_string = str(input_list[10])
        print("Time to read data: %.2f seconds" %(time.time() -st),file = sys.stderr)
        st = time.time()
        dust_ID_set = make_ID_set(dustID)
        experiment_ID_set = make_ID_set(experiment_id_string)
        make_bins(pq_min,pq_max,sq_min,sq_max,start, stop, dust_ID_set, vmin ,\
             vmax, material,session_list,dustID,experiment_ID_set,experiment_id_string)


        print("Time to calculate results: %.2f seconds" %(time.time() -st),file = sys.stderr)


def make_bins(pq_min,pq_max,sq_min,sq_max,start, end, dust_ID_set, v_min , \
    v_max, material,session_list,dust_ID_string,experiment_ID_set,experiment_id_string):            
    print("For Material: %s, Time %s-%s DustID: %s ExperimentID: %s Velocity %.2f-%.2f" %\
    (material, datetime.fromtimestamp(start/1000).strftime("%c"), \
        datetime.fromtimestamp(end/1000).strftime("%c"),dust_ID_string, experiment_id_string,v_min,v_max),file = sys.stderr)

    v_bins = [0]*int(accelerator_range/bin_size)
    p_bins = [0]*int(accelerator_range/bin_size)
    rates = [0]*int(accelerator_range/bin_size)
    session_time_sum =0
    session_sum = 0
    for session in session_list:   
        if session.quality >= sq_min and session.quality <=sq_max \
            and session.start > start and session.end < end:
            if (dust_ID_string == "" or dust_ID_string == "Any" or session.dustID in dust_ID_set):
                if (material == "" or material== "Any Material" or session.material == material):
                    if (experiment_id_string == "" or experiment_id_string == "All" or session.experimentID in experiment_ID_set):
                        for i in range(int(accelerator_range/bin_size)):
                            if session.min_V < (i+1)*bin_size and session.max_V > (i)*bin_size:
                                v_bins[i] += session.duration
                        session_time_sum += session.duration
                        session_sum +=1
                        for particle in session.p_list:
                            if particle[3] >= pq_min and particle[3] <= pq_max:
                                velocity = particle[2]/1000
                                if velocity >= v_min and velocity < v_max: p_bins[ int(velocity/bin_size)]+=1


    for i in range(int(accelerator_range/bin_size)):
        if v_bins[i] !=0: rates[i] = p_bins[i]/(v_bins[i]/1000/60/60)
        else: rates[i] = 0
    
    if sum (rate for rate in rates) ==0:
        print("0|")
        print("No particles found within those parameters")
    else:
        print(sum (rate for rate in rates),end = "|")
        print("%.3f particles per hour" %(sum (rate for rate in rates)))
        print("Total particles : ",sum(p_bins))
        print("Total time: %d sessions for %.2f hours" %(session_sum, session_time_sum/60/60/1000))

def make_ID_set(string_list):
    valid_ID_set = set()
    if string_list== "Any" or string_list == "" or string_list == "All":
        valid_ID_set.add(-1)
        return valid_ID_set
    sequence = string_list.split(",")
    for entry in sequence:
        if "-" in entry:
            vals = entry.split("-")
            try:
                start = int(vals[0])
                end = int(vals[1])
                for val in range(start, end+1):
                    valid_ID_set.add(val)
            except ValueError:
                print("Error converting: %s to valid sequence" % (entry),file = sys.stderr)
        else:
            try:
                val = int(entry)
                valid_ID_set.add(val)
            except ValueError:
                print("Error converting: %s to valid ID" % (entry),file = sys.stderr)
    return valid_ID_set

main()