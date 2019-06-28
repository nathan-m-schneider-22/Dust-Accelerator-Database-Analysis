import mysql.connector
import math
from accelerator_session import Session
#SQLTest.py retrieives the database information through mysql connector
#It then processes the results (see function comments for explanation)

#Determines bin size for the rate prediction, lower is better
rate_precision = .1
accelerator_range = 100
rate_bins = int(accelerator_range/rate_precision)
session_list = []
def main():

    #mySQL credentials
    hostname = "localhost"
    user = "root"
    password = "dust"
    database = "ccldas_production"

    #velocities in km/s
    max_target_v = 20
    min_target_v = 13
    

    #The relevant data is pulled from the sql database through the mysql connector
    #
    velocities, starts, stops, particles = pull_data(hostname, user, password, database, \
                                                 max_target_v, min_target_v)
    print("Data retrieved")
    #Velocities stores the minimum and maximum speeds, along with the timestamp of the switch
    #It is an array touples, (time, max, min)
    #Starts and stops are arrays of 
    #Parallel arrays for holding the total time spent firing for a given velocity
    #and for the total number of particles at that velocity

    if len(particles)==0:
        print("No particles found in that range")
        return 0
    rates = calculate(velocities, starts, stops,particles)
    #for i in range(rate_bins):
    #    print("For speed %d-%d rate is %f per hour" %(i*rate_precision,(i+1)*rate_precision,rates[i]))

    print("For the given velocities the rate will be: %.3f particles per hour" %(sum(rates)))

    
def calculate(velocities, starts, stops, particles):

    total_time = get_total_runtime(velocities, starts, stops)
    total_particles = get_total_particles(particles)


    rates = [0]*rate_bins
    for i in range(rate_bins):
        if total_time[i] == 0: rates[i]=0
        else:
            rates[i] = total_particles[i]/total_time[i] * 1000 * 3600
    return rates

def get_total_runtime(velocities, starts, stops):
    
    total_time = [0]*rate_bins
    
    def get_sessions(self):
        
        self.session_list = []
        
        sa_index = 0
        st_index = 0
        v_index = 0
        time = self.velocities[0][0]
        while self.starts[sa_index] < time: sa_index+=1
        while self.stops[st_index] < time or self.stops[st_index] < self.starts[sa_index]: st_index+=1

        min_V = self.velocities[v_index][2]
        max_V = self.velocities[v_index][1]
        v_index = 1
        
        session_start = self.starts[sa_index]
        session_end = 0
        session_duration = 0


        while sa_index < len(self.starts):
            if v_index < len(self.velocities) and self.velocities[v_index][0] < self.stops[st_index] :
                session_end = self.velocities[v_index][0]

                session_duration = session_end - session_start
                session_start = self.velocities[v_index][0]


            else:
                if st_index == len(self.stops): return
                session_end = self.stops[st_index]

                session_duration = session_end - session_start
                st_index +=1
                while sa_index < len(self.starts) and self.starts[sa_index] < session_end:
                    sa_index += 1
                
                if sa_index != len(self.starts): session_start = self.starts[sa_index]
                
                while st_index < len(self.stops) and self.stops[st_index] < session_start:
                    st_index+=1

            self.session_list.append(Session(session_end-session_duration,session_end,min_V,max_V))
            while v_index < len(self.velocities) and session_start >= self.velocities[v_index][0]:
                min_V = self.velocities[v_index][2]
                max_V = self.velocities[v_index][1]
                v_index += 1

            if v_index == len(self.velocities)-1 or st_index == len(self.stops)-1: return
    return total_time

def get_total_particles(particles):
    total_particles = [0]*rate_bins
    for p in particles:
        time = p[0]
        velocity = p[1]
        total_particles[ int(velocity/1000//rate_precision) ] +=1
        

    return total_particles
#pull_data takes the relevant credentials for SQL connection, then retrieves the
# data, returns it in a tuple of arrays after being trimmed to ints



main()
