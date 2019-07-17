import pickle
import sys
from datetime import datetime
import time
import matplotlib.pyplot as plt


accelerator_range = 100
bin_size = .1

default_quality_min = 4
maintenance_quality =1
maintenance_id = 9
low_count_quality = 2
low_count_quality_count = 10
default_quality = 4
high_count_quality = 5
high_count_quality_count = 300
low_time_quality = 3
low_time_quality_time = 20*60*1000


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
        input_list = sys.stdin.readline().strip().split("|")
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
        dust_ID_set = make_ID_set(dustID)
        experiment_ID_set = make_ID_set(experiment_id_string)
        make_bins(pq_min,pq_max,sq_min,sq_max,start, stop, dust_ID_set, vmin ,\
             vmax, material,session_list,dustID,experiment_ID_set,experiment_id_string)


def generate_results_graphs(session_list):
    plt.figure()

    qualities = [s.quality for s in session_list]
    plt.bar([0,1,2,3,4,5],[qualities.count(i) for i in range(6)])
    plt.title("Session quality breakdown")
    plt.xlabel("Session quality",fontsize = 14)
    plt.ylabel("Number of sessions",fontsize = 14)
    plt.savefig("results_session_qualities.png")


    plt.figure(figsize=(7,5))
    quality_counts = [0]*6
    for s in session_list:
        for p in s.p_list:
            quality_counts[p[3]] +=1
    plt.bar([i for i in range(6)], quality_counts)
    plt.title("Particle Quality Breakdown")
    plt.xlabel("Particle quality",fontsize = 14)
    plt.ylabel("Number of particles",fontsize = 14)
    plt.savefig("results_particles_qualities.png")

    plt.figure()
    durations = [s.duration/1000/60 for s in session_list]
    bins=[0,5,15,30,60,120,3000000]
    labels = ["0-5","5-15","15-30","30-60","60-120","Over 120"]
    counts = [0]*(len(bins)-1)
    for time in durations:
        for i in range(len(bins)-1):
            if bins[i] <= time < bins[i+1]: 
                counts[i]+=1
                break
    plt.bar(labels,counts)
    plt.title("Session Durations")
    plt.xlabel("Session duration in minutes",fontsize = 14)
    plt.ylabel("Number of sessions",fontsize = 14)
    plt.savefig("results_sessions_durations.png")


    plt.figure()
    p_counts = [len(s.p_list) for s in session_list]
    bins=[0,5,20,100,1000,3000000]
    labels = ["0-5","5-20","20-100","100-1000","Over 1000"]
    counts = [0]*(len(bins)-1)
    for num in p_counts:
        for i in range(len(bins)-1):
            if bins[i] <= num < bins[i+1]: 
                counts[i]+=1
                break
    plt.bar(labels,counts)
    plt.title("Session Detection Counts")
    plt.xlabel("Number of dust events in a session within parameters",fontsize = 14)
    plt.ylabel("Number of sessions",fontsize = 14)
    plt.savefig("results_sessions_particle_counts.png")

def generate_bins_graphs(session_list,v_bins,p_bins,rates):

    plt.figure()
    v_bins = [ s/1000/60/60 for s in v_bins]
    plt.plot([i/10 for i in range(accelerator_range*10)],v_bins)
    plt.title("Run time total for each velocity bin")
    plt.xlabel("Velocity range bins")
    plt.ylabel("Total active time (hours)")
    plt.savefig("results_runtime.png")

    plt.figure()
    particles = []
    for s in session_list: 
        for p in s.p_list: particles.append(p[2]/1000)
    plt.hist(particles,bins = [i for i in range(0,accelerator_range,1)])
    plt.title("Particle count total total for each velocity bin")
    plt.yscale("log")
    plt.xlabel("Velocity range bins")
    plt.ylabel("Total particles in bin")
    plt.savefig("results_particle_count.png")
    
    plt.figure()
    plt.plot([i/10 for i in range(accelerator_range*10)],rates)
    plt.title("Rates of dust detection")
    plt.yscale("log")
    plt.xlabel("Velocity range bins")
    plt.ylabel("Rate of detection (particles/hour")
    plt.savefig("results_rates.png")

def make_bins(pq_min,pq_max,sq_min,sq_max,start, end, dust_ID_set, v_min , \
    v_max, material,session_list,dust_ID_string,experiment_ID_set,experiment_id_string):     
    st = time.time()
    print("For Material: %s, Time %s-%s DustID: %s ExperimentID: %s Velocity %.2f-%.2f" %\
    (material, datetime.fromtimestamp(start/1000).strftime("%c"), \
        datetime.fromtimestamp(end/1000).strftime("%c"),dust_ID_string, experiment_id_string,v_min,v_max),file = sys.stderr)

    used_sessions = []

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
                        used_sessions.append(session)
                        used_particles = []
                        for i in range(int(accelerator_range/bin_size)):
                            if session.min_V < (i+1)*bin_size and session.max_V > (i)*bin_size:
                                v_bins[i] += session.duration
                        session_time_sum += session.duration
                        session_sum +=1
                        for particle in session.p_list:
                            if particle[3] >= pq_min and particle[3] <= pq_max:
                                velocity = particle[2]/1000
                                if velocity >= v_min and velocity < v_max:
                                    p_bins[ int(velocity/bin_size)]+=1
                                    used_particles.append(particle)
                        session.p_list = used_particles


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
    
    print("Time to calculate results: %.2f seconds" %(time.time() -st),file = sys.stderr)
    st = time.time()
    generate_results_graphs(used_sessions)
    generate_bins_graphs(used_sessions,v_bins,p_bins,rates)
    print("Time to generate graphs: %.2f seconds" %(time.time() -st),file = sys.stderr)

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