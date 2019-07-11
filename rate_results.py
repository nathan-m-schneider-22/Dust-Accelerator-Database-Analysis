import pickle
import sys
from datetime import datetime


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
    with open("temp_data.pkl","rb") as load_file:
        session_list = pickle.load(load_file)
        input_list = sys.stdin.readline().split(",")
        quality = int(input_list[0])
        start = int(input_list[1])
        stop = int(input_list[2])
        dustID = int(input_list[3])
        vmin = float(input_list[4])
        vmax = float(input_list[5])
        material = str(input_list[6]).strip()

        make_bins(quality, start, stop, dustID, vmin,vmax,material,session_list)
def make_bins(session_quality,start, end, dustID, v_min , v_max, material,session_list):
    print("For Material: %s, Time %s-%s DustID: %d Velocity %.2f-%.2f" %\
    (material, datetime.fromtimestamp(start/1000).strftime("%c"), \
        datetime.fromtimestamp(end/1000).strftime("%c"),dustID, v_min,v_max),file = sys.stderr)

    v_bins = [0]*int(accelerator_range/bin_size)
    p_bins = [0]*int(accelerator_range/bin_size)
    rates = [0]*int(accelerator_range/bin_size)
    session_time_sum =0
    session_sum = 0
    for session in session_list:   
        if session.start > start and session.end < end and session.quality >= session_quality:
            if (dustID ==-1 or session.dustID == dustID) and  (material == "Any Material" or session.material == material):
                for i in range(int(accelerator_range/bin_size)):
                    if session.min_V < (i+1)*bin_size and session.max_V > (i)*bin_size:
                        v_bins[i] += session.duration
                print(session,file = sys.stderr)
                session_time_sum += session.duration
                session_sum +=1
                for particle in session.p_list:
                    velocity = particle[2]/1000
                    if velocity >= v_min and velocity < v_max: p_bins[ int(velocity/bin_size)]+=1


    #print(p_bins,file=sys.stderr)
    for i in range(int(accelerator_range/bin_size)):
        if v_bins[i] !=0: rates[i] = p_bins[i]/(v_bins[i]/1000/60/60)
        else: rates[i] = 0

    print("%.3f particles per hour" %(sum (rate for rate in rates)))
    print("Total particles : ",sum(p_bins))
    print("Total time: %d sessions for %.2f hours" %(session_sum, session_time_sum/60/60/1000))

main()