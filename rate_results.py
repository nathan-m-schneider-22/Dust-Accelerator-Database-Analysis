"""
rate_results.py     Nathan Schneider        July 18 2019
This program is called from the labview vi repeatedly to give particle rate results.
The program reads a list of inputs from stdin, which is a string list separated by 
a | delimiter. It then feeds out a rate, then a | , then more results information. 
The stderr outputs of this program can be viewed from the debugging tab.

The rate for given parameters is calculated by building several histograms with 
small bins that represent velocity ranges of .1km/s. As such, for any span of .1km/s, 
the amount of time the accelerator was run that selected for that span, and the number of 
particles in that range can be calculated. As such, the rate of that small range can be calculated.
To get a larger range, simply sum the rates of smaller spans. 

This program also generates a set of pngs, graphs to be displayed in the labview vi
"""

import pickle
import sys
from datetime import datetime
import time
import matplotlib.pyplot as plt
import math
import statistics
import numpy as np

#The accelerator range and bin size determines the number of bins
accelerator_velocity_range = 100
bin_size = .1


outlier_percentage = 10

#The session class structure must be included, as the list of 
# sessions from generate_sessions.py is to be directly loaded
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
        self.particle_list = []
        self.quality = 5
        self.performance_factor = 0

    def __str__(self):
        return "Session from %s to %s \nDuration: %.1f min Material: %s, %.1f-%.1fkm/s %d %d\nDustID: %s \
ExperimentID: %s # of particles: %d Session Quality: %d Avg dust quality: %.2f\n------------------------------------------\
" %(datetime.fromtimestamp(self.start/1000).strftime("%c"),\
            datetime.fromtimestamp(self.end/1000).strftime("%c"),\
            self.duration/1000/60,self.material,self.min_V,self.max_V,self.start,self.end,\
            self.dustID,self.experimentID,len(self.particle_list),self.quality,\
                sum(p[3] for p in self.particle_list)/(len(self.particle_list)+1))


def main():
    st = time.time()
    try:
        with open("temp_data.pkl","rb") as load_file:
            #Load entire list of session object
            session_list = pickle.load(load_file)

            #Read the stdin input and split along delimiter
            input_list = sys.stdin.readline().strip().split("|")
            #initialize arguments
            start, stop = int(input_list[0]), int(input_list[1])
            dustID = str(input_list[2])
            vmin,vmax = max(0,float(input_list[3])),min(accelerator_velocity_range,float(input_list[4]))
            material = str(input_list[5])
            pq_min = min(int(input_list[6]),int(input_list[7]))
            pq_max = max(int(input_list[6]),int(input_list[7]))
            sq_min = min(int(input_list[8]),int(input_list[9]))
            sq_max = max(int(input_list[8]),int(input_list[9]))
            experiment_id_string = str(input_list[10])



            #Both the dust ID and experiment ID come as a string representing a set, eg: 1-5,7,10-15, and
            # will be converted to a set
            dust_ID_set = make_ID_set(dustID)
            experiment_ID_set = make_ID_set(experiment_id_string)


            



            #Calculate the results based on the arguments
            calculate_results(pq_min,pq_max,sq_min,sq_max,start, stop, dust_ID_set, vmin ,\
                vmax, material,session_list,dustID,experiment_ID_set,experiment_id_string,"Average")

            print("Total runtime: ",time.time()-st,file = sys.stderr)


    except FileNotFoundError:
        print("temp_data.pkl not found, please run generate_sessions.py",file=sys.stderr)


# The rate for given parameters is calculated by building several histograms with 
# small bins that represent velocity ranges of .1km/s. As such, for any span of .1km/s, 
# the amount of time the accelerator was run that selected for that span, and the number of 
# particles in that range can be calculated. As such, the rate of that small range can be calculated.
# To get a larger range, simply sum the rates of smaller spans. 
def calculate_results(pq_min,pq_max,sq_min,sq_max,start, end, dust_ID_set, v_min , \
    v_max, material,session_list,dust_ID_string,experiment_ID_set,\
        experiment_id_string,description_string,generate_graphics = True):     
    st = time.time()

    #Debugging statment to show the arrival of correct arguments
    print("For Material: %s, Time %s-%s DustID: %s ExperimentID: %s Velocity %.2f-%.2f" %\
    (material, datetime.fromtimestamp(start/1000).strftime("%c"), \
        datetime.fromtimestamp(end/1000).strftime("%c"),dust_ID_string, \
            experiment_id_string,v_min,v_max),file = sys.stderr)

    #To track the sessions that match the given parameters
    used_sessions = []

    session_to_rate_bins  = {}

    #Initialize the bins
    runtime_bins = [0]*int(accelerator_velocity_range/bin_size)
    particle_count_bins = [0]*int(accelerator_velocity_range/bin_size)
    rates = [0]*int(accelerator_velocity_range/bin_size)
    optimal_bins = [ [] for i in range(int(accelerator_velocity_range/bin_size))]
    #To track the total duration of the sessions
    session_time_sum =0

    #Check all the necessary parameters, making use of boolean short-circuiting to keep things fast
    for session in session_list:   
        #If it is within quality constraints
        if session.quality >= sq_min and session.quality <=sq_max \
            and session.start > start and session.end < end:

            #Within accepted dust ID
            if (-1 in dust_ID_set or session.dustID in dust_ID_set):

                #Accepted Material
                if (material == "" or material== "Any Material" or session.material == material):

                    #Accepted experiment ID
                    if (experiment_id_string == "" or experiment_id_string == "All"\
                         or session.experimentID in experiment_ID_set):

                        #Then add to used sessions, and initialize a list to replace the session's particle list
                        used_sessions.append(session)
                        used_particles = []
                        session_to_rate_bins[session] = [0]*int(accelerator_velocity_range/bin_size)

                        #Add the session duration to all the bins within the velocity range
                        for i in range(int(accelerator_velocity_range/bin_size)):
                            if session.min_V < (i+1)*bin_size and session.max_V > (i)*bin_size and\
                                v_min<(i+1)*bin_size and v_max >= (i)*bin_size:
                                runtime_bins[i] += session.duration
                                optimal_bins[i].append(session)

                        #Add the duration to the total time spent
                        session_time_sum += session.duration

                        #For each particle in the sessions
                        for particle in session.particle_list:
                            #if the quality is right
                            if particle[3] >= pq_min and particle[3] <= pq_max:
                                velocity = particle[2]/1000
                                if velocity >= v_min and velocity < v_max:
                                    #Add it to the correct histogram bin
                                    session_to_rate_bins[session][int(velocity/bin_size)] += 1
                                    particle_count_bins[ int(velocity/bin_size)]+=1
                                    used_particles.append(particle)
                        for i in range(int(accelerator_velocity_range/bin_size)):
                            session_to_rate_bins[session][i]/=session.duration
                        
                        #replace the session's list of particles with the particles within the arguments
                        session.particle_list = used_particles

    #Divide the particles by the runtimes, watching out for division by 0
    for i in range(int(accelerator_velocity_range/bin_size)):
        if runtime_bins[i] !=0: rates[i] = particle_count_bins[i]/(runtime_bins[i]/1000/60/60)
        else: rates[i] = 0
    
    #If there are no particles matching those arguments, the total sum rate will be 0
    if sum (rate for rate in rates) ==0:
        print("No data found",end = "|")
    #Send this output back to the labview program
    else: print("%.3f |" %(sum (rate for rate in rates)),end = "")
    # print("%.3f particles per hour" %(sum (rate for rate in rates)))
    # print("%d Total particles" %(sum(particle_count_bins)))
    print("%s Results: %d Total sessions, %.2f Hours total runtime, %d experiments" %\
        (description_string,len(used_sessions), session_time_sum/60/60/1000,\
            len(set([s.experimentID for s in used_sessions]))))
    
    #More stderr debug info

    print("Time to calculate %s results %f" %(description_string,time.time()-st),file = sys.stderr)
    generate_bins_graphs(used_sessions,runtime_bins,particle_count_bins,rates,v_min,v_max,description_string)
    #Graphs for display on the insights tab of the labview vi are generated here
    if generate_graphics:
        generate_results_graphs(used_sessions)


        st = time.time()
        winners,losers = find_optimum_rates(used_sessions,session_to_rate_bins,rates)
        print("Time to find optimum ",time.time()-st,file = sys.stderr)
        calculate_results(pq_min,pq_max,sq_min,sq_max,start,end,dust_ID_set,v_min,v_max,material,\
            winners,dust_ID_string,experiment_ID_set,experiment_id_string,"Optimal",generate_graphics=False)
        calculate_results(pq_min,pq_max,sq_min,sq_max,start,end,dust_ID_set,v_min,v_max,material,\
            losers,dust_ID_string,experiment_ID_set,experiment_id_string,"Poor",generate_graphics=False)

        check_connection(rates,used_sessions)
    return sum(rates)

def find_optimum_rates(session_list,session_to_rate_bins,rates):
        upper_session_list,low_session_list = [],[]

        for session in session_list:
            performance_total = []
            
            for i in range(int(session.min_V/bin_size),min(int(session.max_V/bin_size),int(accelerator_velocity_range/bin_size))):
                if rates[i]!=0:
                    expected_bin_rate =  session_to_rate_bins[session][i]*1000*60*60
                    performance_total.append(expected_bin_rate/rates[i])
            #if len(performance_total)>0: session.performance_factor = statistics.median(performance_total)
            if len(performance_total)>0: session.performance_factor = statistics.mean(performance_total)
        for session in session_list:
                if session.performance_factor < 1 and session.performance_factor!=0:
                    session.performance_factor = -1/session.performance_factor
        winners = [session.performance_factor for session in session_list]
        winners.sort()
        
        optimal_lower_bound = winners[ int(len(winners)*.6)]
        optimal_upper_bound = winners[ int(len(winners)*.9)]
        
        suboptimal_lower_bound = winners[ int(len(winners)*.1)]
        suboptimal_upper_bound = winners[ int(len(winners)*.4)]

        for session in session_list:
            if optimal_lower_bound < session.performance_factor < optimal_upper_bound : upper_session_list.append(session)
            if suboptimal_lower_bound < session.performance_factor < suboptimal_upper_bound  : low_session_list.append(session)


            winners.append(session.performance_factor)

        winners = [s.performance_factor for s in session_list if s.performance_factor != 0]
        
        plt.figure(figsize=(7,5))
        plt.title("Distribution of sessions by factor of performance compared to mean")
        plt.xlabel("Factor of performance compared to mean")
        plt.ylabel("Number of sessions")
        plt.hist(winners,histtype ="bar",bins = 100,stacked=True,range = (-10,10),label=(">20 min","<20 min"))
        plt.savefig("session_performance_distribution")

        plt.close("all")
        plt.subplot(121)
        plt.xlabel("Factor of decrease compared to average rates")
        plt.ylabel("Number of sessions of this factor")
        plt.xlim(10,0)
        plt.title("Worse than average sessions")

        plt.hist([w*-1 for w in winners if w<0],histtype ="bar",bins = 100,stacked=True,range = (0,10),label=(">20 min","<20 min"))

        plt.subplot(122)
        plt.xlabel("Factor of increase compared to average rates")
        plt.ylabel("Number of sessions of this factor")
        plt.hist([w for w in winners if w>0],histtype ="bar",bins = 100,stacked=True,range = (0,10),label=(">20 min","<20 min"))
        plt.title("Better than average sessions")

        fig = plt.gcf()
        fig.set_size_inches(15, 8)

        plt.savefig("double_performance_distribution.png")
        #plt.show()
        return upper_session_list,low_session_list


def check_connection(rates, session_list):
    st = time.time()
    plt.close("all")

    plt.figure()
    plt.title("Session performance factor variance over minimum selected velocity")
    plt.xlabel("Minimum session velocity")
    plt.ylabel("Session performance factor (winner-ness)")
    mv = [ s.min_V for s in session_list if abs(s.performance_factor) <30]
    pf = [ s.performance_factor for s in session_list if abs(s.performance_factor) <30]

    plt.scatter(mv,pf)
    plt.plot(np.unique(mv), np.poly1d(np.polyfit(mv, pf, 1))(np.unique(mv)))
    plt.savefig("Throttle_graph.png")
    # plt.show(block = False)

    plt.figure()
    mv_map = {}
    for v in mv: mv_map[v] = []
    plt.title("Session performance factor variance over minimum selected velocity (MEDIAN)")
    plt.xlabel("Minimum session velocity")
    plt.ylabel("Session performance factor (winner-ness)")
    for session in session_list:
        if session.min_V in mv_map: mv_map[session.min_V].append(session.performance_factor)
    
    min_vs = mv_map.keys()
    mvs = []
    pfs = []
    # print(len(session_list))
    # print(sum(1 for s in session_list if s.performance_factor==0))
    for key in min_vs:
        if statistics.median(mv_map[key])<10 and len(mv_map[key])>10:
            pfs.append(statistics.median(mv_map[key]))
            mvs.append(key)
    plt.scatter(mvs,pfs)
    # plt.show()

    print("Time to check connection: ",time.time()-st,file = sys.stderr)
            

#Generate the graphs of the session breakdown
def generate_results_graphs(session_list):
    st = time.time()


    plt.figure()

    #Graph of the session qualites used in the results
    qualities = [s.quality for s in session_list]
    plt.bar([0,1,2,3,4,5],[qualities.count(i) for i in range(6)])
    plt.title("Session quality breakdown")
    plt.xlabel("Session quality",fontsize = 14)
    plt.ylabel("Number of sessions",fontsize = 14)
    plt.savefig("results_session_qualities.png")


    #Graph of the particle qualities used in the results
    plt.figure(figsize=(7,5))
    quality_counts = [0]*6
    for s in session_list:
        for p in s.particle_list:
            quality_counts[p[3]] +=1
    plt.bar([i for i in range(6)], quality_counts)
    plt.title("Particle Quality Breakdown")
    plt.xlabel("Particle quality",fontsize = 14)
    plt.ylabel("Number of particles",fontsize = 14)
    plt.savefig("results_particles_qualities.png")

    #Graph of the duration breakdown

    plt.figure()
    durations = [s.duration/1000/60 for s in session_list]
    bins=[0,5,15,30,60,120,3000000]
    labels = ["0-5","5-15","15-30","30-60","60-120","Over 120"]
    counts = [0]*(len(bins)-1)
    for runtime in durations:
        for i in range(len(bins)-1):
            if bins[i] <= runtime < bins[i+1]: 
                counts[i]+=1
                break
    plt.bar(labels,counts)
    plt.title("Session Durations")
    plt.xlabel("Session duration in minutes",fontsize = 14)
    plt.ylabel("Number of sessions",fontsize = 14)
    plt.savefig("results_sessions_durations.png")


    #Graph of the particle count breakdown
    plt.figure()
    p_counts = [len(s.particle_list) for s in session_list]
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
    plt.xlabel("Number of dust events per session within parameters",fontsize = 14)
    plt.ylabel("Number of sessions",fontsize = 14)
    plt.savefig("results_sessions_particle_counts.png")

    # print("Time for breakdown graphs: ",time.time()-st,file = sys.stderr))

#Generate graphs of the histogram bins
def generate_bins_graphs(session_list,v_bins,p_bins,rates,v_min,v_max,description_string):
    st = time.time()
    #2.24
    #Runtime bins
    plt.figure()
    v_bins =  v_bins[int(v_min*10):int(v_max*10)]
    plt.bar( [(i/10) for i in range(int(v_min*10),int(v_max*10))], v_bins)
    plt.title(description_string+" Results Run time total for each velocity bin")
    plt.xlabel("Velocity range bins, bin size = 0.1km/s")
    plt.ylabel("Total active time (hours)")
    plt.savefig(description_string+"_results_runtime.png")


    #1.4
    #Particle count bins
    plt.figure()
    particles = []
    for s in session_list: 
        for p in s.particle_list: particles.append(p[2]/1000)
    plt.hist(particles,range=(v_min,v_max),bins = int(v_max*10)-int(v_min*10))
    plt.title(description_string+" Results Particle count total total for each velocity bin")
    plt.yscale("log")
    plt.xlabel("Velocity range bins, bin size = 0.1km/s")
    plt.ylabel("Total particles in bin")
    plt.savefig(description_string+"_results_particle_count.png")

    #3.0
    #Rate bins
    plt.figure()
    bins = [(i/10) for i in range(int(v_min*10),int(v_max*10))]
    rates = [rates[int(i*10)] for i in bins]
    plt.bar(bins,rates)
    plt.title(description_string+" Results Rates of dust detection")
    plt.yscale("log")
    plt.xlabel("Velocity range bins, bin size = 0.1km/s")
    plt.ylabel("Rate of detection (particles/hour)")
    plt.savefig(description_string+"_results_rates.png")


    # for session in session_list:
    #     print(session,file = sys.stderr)
    print("Time for %s rate graphs %f" %(description_string,time.time()-st),file = sys.stderr)

#Make a set out of a string like 1-4,5,11,13-19
def make_ID_set(string_list):
    #Make an empty set
    valid_ID_set = set()
    if string_list in ["","Any","Any,","All"]:
        valid_ID_set.add(-1)
        return valid_ID_set
    
    #Split the string into a sequence of items
    sequence = string_list.split(",")
    for entry in sequence:
        #if it's a span of numbers
        if "-" in entry:
            vals = entry.split("-")
            try:
                #Try splitting it and adding all span values to the set
                start = int(vals[0])
                end = int(vals[1])
                for val in range(start, end+1):
                    valid_ID_set.add(val)
            except ValueError:
                print("Error converting: %s to valid sequence" % (entry),file = sys.stderr)
        else:
            try:
                #Try adding it to the set
                val = int(entry)
                valid_ID_set.add(val)
            except ValueError:
                if entry=="Any":
                    valid_ID_set.add(-1)
                    return valid_ID_set
                print("Error converting: %s to valid ID" % (entry),file = sys.stderr)
                
    return valid_ID_set

main()
