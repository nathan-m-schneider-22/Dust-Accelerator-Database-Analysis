import mysql.connector
from datetime import datetime
import tkinter
import matplotlib.pyplot as plt


gap_size = 20*60*1000
accelerator_range = 100
bin_size = .1
 


import time
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
        self.quality = 4

    def __str__(self):
        return "Session from %s to %s \nDuration: %.1f min material: %s, %.1f-%.1fkm/s %d %d\nDustID: %s \
ExperimentID: %s particles: %d\n------------------------------------------\
" %(datetime.fromtimestamp(self.start/1000).strftime("%c"),\
            datetime.fromtimestamp(self.end/1000).strftime("%c"),\
            self.duration/1000/60,self.material,self.min_V,self.max_V,self.start,self.end,\
            self.dustID,self.experimentID,len(self.p_list))
    
class Rate_analyzer:
    def __init__(self,hostname, user, password, database):
        print("Fetching Data",end  = "")
        start_time = time.time()
        self.pull_data(hostname,user, password, database)
        print(time.time() - start_time)
        start_time = time.time()
        print("Data retrieved")
        self.generate_stops()
        
        print("Done stops")
        self.frequency_segment()
        self.velocity_segment()
        self.experiment_segment()
        self.tag_sessions()
        #self.voltage_tag()

        self.frequency_tag()

        print("Done segments")
        print("Done tags")
        for s in self.session_list:
            if 1562082557513 > s.start and 1562082557513 < s.end: print("RRREEEEEE")
        self.make_bins(material="Iron")


        print("Total runtime: ",sum(s.duration for s in self.session_list)/1000/60/60)

    def make_bins(self, session_quality = 4,material = None, start = 1380573080182, end = 2000000000000, dustID = -1, v_min = 0, v_max = accelerator_range):
        self.v_bins = [0]*int(accelerator_range/bin_size)
        self.p_bins = [0]*int(accelerator_range/bin_size)
        self.rates = [0]*int(accelerator_range/bin_size)
        for session in self.session_list:   
            if session.start > start and session.end < end and session.quality >= session_quality:
                if (dustID ==-1 or session.dustID == dustID) and  (material == None or session.material == material):
                    for i in range(int(accelerator_range/bin_size)):
                        if session.min_V < (i+1)*bin_size and session.max_V > (i)*bin_size:
                            self.v_bins[i] += session.duration
                    for particle in session.p_list:
                        velocity = particle[2]/1000
                        if velocity >= v_min and velocity < v_max: self.p_bins[ int(velocity/bin_size)]+=1

        print("For Material: %s, Time %s-%s DustID: %d Velocity %.2f-%.2f" %\
            (material, datetime.fromtimestamp(start/1000).strftime("%c"), \
                datetime.fromtimestamp(end/1000).strftime("%c"),dustID, v_min,v_max))

                
        for i in range(int(accelerator_range/bin_size)):
            if self.v_bins[i] !=0: self.rates[i] = self.p_bins[i]/(self.v_bins[i]/1000/60/60)
            else: self.rates[i] = 0
            # print("%6.2f - %6.2fdkm/s total %8.3f hours %8d particles %8.3f  particles per hour" % \
            #    (i*bin_size, (i+1)*bin_size,self.v_bins[i]/1000/60/60,\
            #        self.p_bins[i],self.rates[i]))

        #print("Total of %d particles" %(sum(p for p in self.p_bins)))



        print("Total rate for range is %f particles per hour" % \
            ( sum (rate for rate in self.rates)))

        # plt.subplot(231)
        # self.v_bins = [ s/1000/60/60 for s in self.v_bins]
        # plt.plot(self.v_bins)
        # plt.title("Run time totals")
        # plt.subplot(232)
        # p_ar = [p[2]/1000 for p in self.particles]
        # plt.hist(p_ar,bins = [i for i in range(0,accelerator_range,1)])
        # plt.title("Particle distribution")

        # plt.subplot(233)
        # plt.plot(self.rates)

        # plt.title("Rates of detection")
        # plt.subplot(234)

        # qualities = [s.quality for s in self.session_list]
        # plt.bar([0,1,2,3,4,5],[qualities.count(i) for i in range(6)])
        # plt.title("Session qualities")

        # plt.subplot(235)

        # p_ar = [p[2]/1000 for p in self.particles]
        # plt.hist(p_ar,bins = [i for i in range(0,accelerator_range,1)])
        # plt.title("Particle distribution (log scale)")
        # plt.yscale("log")

        # plt.subplot(236)
        # plt.plot(self.rates)

        # plt.title("Rates of detection (log scale)")
        # plt.yscale("log")
        # #plt.show(block= False)

        plt.figure()
        plt.suptitle('1: Maintenance    2: Event Count <10    3: Frequency to 0 during session \
    4: 10 < Event Count < 300    5: Event Count > 300', fontsize=16)
        plt.subplots_adjust(wspace=.35)
        plt.subplot(131)

        qualities = [s.quality for s in self.session_list]
        plt.bar([0,1,2,3,4,5],[qualities.count(i) for i in range(6)])
        plt.title("Session quality counts")
        plt.xlabel("Quality")
        plt.ylabel("Number of sessions")

        plt.subplot(132)
        plt.title("Particles of each quality")
        plt.xlabel("Quality")
        plt.ylabel("Number of particles")

        ar = [0]*6
        for s in self.session_list: ar[s.quality]+= len(s.p_list)

        plt.bar([i for i in range(6)], ar)

        plt.subplot(133)

        qualities = [0]*6
        plt.bar([0,1,2,3,4,5],[sum(s.duration for s in self.session_list if s.quality==i)/1000/60/60 for i in range(6)])
        plt.title("Session runtimes")
        plt.xlabel("Quality")
        plt.ylabel("Hours")

        plt.show(block = False)
        plt.figure()
        bins = [i for i in range(50)]
        vals = [len(s.p_list) for s in self.session_list]
        plt.hist(vals,bins = bins)
        plt.show()

    def tag_sessions(self):

        self.empty_sessions = []
        self.valid_sessions = []
        p_index =0
        for session in self.session_list:
            while self.particles[p_index][0] < session.start:
                p_index+=1
            if self.particles[p_index][0] <= session.end:
                session.dustID = self.particles[p_index][1]
                session.material = self.type_to_name[self.info_to_type[self.particles[p_index][1]]]
                self.valid_sessions.append(session)
                
            else: self.empty_sessions.append(session)
            
            while self.particles[p_index][0] <= session.end:
                if self.particles[p_index][3] >= 3: 
                    session.p_list.append(self.particles[p_index])
                p_index+=1

            if session.quality>2 and len(session.p_list) < 10 :session.quality = 2
            if session.quality==4 and len(session.p_list) > 300: session.quality = 5

    def frequency_segment(self):
        f_index =0
        s_index =0
        while s_index < len(self.session_list):
            session = self.session_list[s_index]
            while f_index< len(self.frequency_gaps)-2 and self.frequency_gaps[f_index][0] < session.start:
                f_index+=1

            if f_index< len(self.frequency_gaps)-2 and self.frequency_gaps[f_index][1] <= session.end \
                and self.frequency_gaps[f_index][1] > session.start:
                del self.session_list[s_index]
                self.session_list.insert(s_index, Session(self.frequency_gaps[f_index][1]+1,\
                                    session.end,session.min_V,session.max_V))
                self.session_list.insert(s_index, Session(session.start,\
                                    self.frequency_gaps[f_index][0]-1,session.min_V,session.max_V))
                f_index -=2
                s_index -=2
            s_index+=1

    def frequency_tag(self):
        s_index =0
        for session in self.session_list:
            while s_index< len(self.stops)-1 and self.stops[s_index][0] < session.start:
                s_index+=1

            stop_count = 0
            while s_index< len(self.stops)-1 and self.stops[s_index][0] <= session.end:
                stop_count+=1
                s_index+=1
            if stop_count >1 and session.duration > 5*60*1000: 
                print(session,stop_count)
                if session.quality>3: session.quality=3

    def voltage_tag(self):
        v_index =0
        for session in self.session_list:
            while self.voltages[v_index][0] < session.start:
                v_index+=1
                
            v_list = []            
            while self.voltages[v_index][0] <= session.end:
                v_list.append(self.voltages[v_index][1])
                v_index+=1

            if len(v_list) > 0: average = sum(v_list)/len(v_list)
            else: average = -1
            if average < 1.5 and average >0: 
                if session.quality >=3: session.quality = 2
                print(session,average)

    def experiment_segment(self):
        s_index = 0
        e_index = 0
        while s_index < len(self.session_list) and e_index < len(self.experiments):
            session = self.session_list[s_index]
            while e_index < len(self.experiments)-1 and \
                self.experiments[e_index][0] < session.start:
                e_index += 1

            session.experimentID = self.experiments[e_index-1][1]
            if self.experiments[e_index-1][2] == 9: session.quality = 1
            if self.experiments[e_index][0] < session.end:
                del self.session_list[s_index]
                self.session_list.insert(s_index, Session(self.experiments[e_index][0]+1,\
                                    session.end,session.min_V,session.max_V))
                self.session_list.insert(s_index, Session(session.start,\
                                    self.experiments[e_index][0]-1,session.min_V,session.max_V))
                e_index-=1
                s_index -=1
                
            s_index+=1
            
    def velocity_segment(self):
        s_index = 0
        v_index = 0
        while s_index < len(self.session_list) and v_index < len(self.velocities):
            session = self.session_list[s_index]
            while v_index < len(self.velocities)-1 and \
                  self.velocities[v_index][0] < session.start:
                v_index += 1
            session.min_V = self.velocities[v_index-1][2]
            session.max_V = self.velocities[v_index-1][1]
          
            if self.velocities[v_index][0] < session.end:
                del self.session_list[s_index]
                self.session_list.insert(s_index, Session(self.velocities[v_index][0]+1,\
                                    session.end,session.min_V,session.max_V))
                self.session_list.insert(s_index, Session(session.start,\
                                    self.velocities[v_index][0]-1,session.min_V,session.max_V))

                s_index -=1
                v_index -=1
                
            s_index+=1

    def generate_stops(self):
        self.session_list = []

        v_index = 0
        p_index = 1
        time = self.velocities[0][0]
        while self.particles[p_index][0] < time: p_index+=1
        session_start = self.particles[p_index][0]
        p_index +=1
        while p_index < len(self.particles):

            prev = self.particles[p_index-1][0]
            time = self.particles[p_index][0]
            if (time-prev > gap_size):
                session_end = prev
                self.session_list.append(Session(session_start-1,session_end+1,-1,-1))
                session_start = time
            p_index+=1
                            
        

    def pull_data(self,hostname, usr, password, db):
    
        mydb = mysql.connector.connect(host=hostname, user=usr,\
            passwd=password,database=db,auth_plugin='mysql_native_password')
        cursor = mydb.cursor()
        
        print(".",end = "")
        cursor.execute("select integer_timestamp, velocity_max, \
        velocity_min from psu order by integer_timestamp ASC")
        self.velocities = cursor.fetchall()
        print(".",end = "")

        # cursor.execute("SELECT integer_timestamp FROM ccldas_production.source_settings\
        # WHERE !(frequency=0 OR needle_voltage=0 OR amplitude=0)")
        # starts = cursor.fetchall()
        # self.starts = [ time[0] for time in starts]
        # print(".",end = "")

        cursor.execute("SELECT integer_timestamp FROM ccldas_production.source_settings\
        WHERE (frequency=0) order by integer_timestamp ASC")
        self.stops = cursor.fetchall()
        #self.stops = [time[0] for time in stops]
        print(".",end = "")

        cursor.execute("SELECT integer_timestamp,LEAD(integer_timestamp) over \
            (order by integer_timestamp) as next FROM ccldas_production.source_settings\
                 where frequency = 0 order by integer_timestamp asc")
        self.frequency_gaps = cursor.fetchall()

        cursor.execute("SELECT integer_timestamp,id_experiment_settings,id_groups\
        FROM ccldas_production.experiment_settings")
        self.experiments = cursor.fetchall()

        cursor.execute("SELECT id_dust_type,dust_name \
        FROM ccldas_production.dust_type")
        dust_type = cursor.fetchall()

        cursor.execute("SELECT id_dust_info,dust_type \
        FROM ccldas_production.dust_info")
        dust_info = cursor.fetchall()

        self.info_to_type = {}
        for d in dust_info:
            self.info_to_type[d[0]] = d[1]
        self.type_to_name = {}
        for d in dust_type:
            self.type_to_name[d[0]] = d[1]   


        self.particles = []
        try:
            with open('particles.csv', 'r') as particle_file:
                print("Fetching particles locally")
                for line in particle_file:
                    vals = line.split(",")
                    part = (int(vals[0]),int(vals[1]),float(vals[2]),int(vals[3]))
                    self.particles.append(part)
                query = "SELECT integer_timestamp, id_dust_info,velocity,estimate_quality\
                FROM ccldas_production.dust_event WHERE (integer_timestamp >%d and velocity <= 100000 \
                AND velocity >= 0) ORDER BY integer_timestamp ASC" % (self.particles[-1][0])
                cursor.execute(query)
                for particle in cursor.fetchall():
                    self.particles.append(particle)

        except FileNotFoundError:
            print("Fetching particles by web")
            query = "SELECT integer_timestamp, id_dust_info,velocity,estimate_quality\
            FROM ccldas_production.dust_event WHERE ( velocity <= 100000 \
            AND velocity >= 0) ORDER BY integer_timestamp ASC"
            cursor.execute(query)
            self.particles = cursor.fetchall()
            particle_file = open("particles.csv","w")
            for particle in self.particles:
                particle_file.write("%d,%d,%f,%d\n" %(particle[0],particle[1],particle[2],particle[3]))
            particle_file.close()

        # self.voltages = []                
        # try:
        #     with open('voltages.csv', 'r') as voltage_file:
        #         print("Fetching voltages locally")
        #         for line in voltage_file:
        #             vals = line.split(",")
        #             volt = (int(vals[0]),float(vals[1]))
        #             self.voltages.append(volt)
        #         query = "SELECT integer_timestamp, high_voltage\
        #         FROM ccldas_production.pelletron_data WHERE (integer_timestamp >%d)\
        #              ORDER BY integer_timestamp ASC" % (self.voltages[-1][0])
        #         cursor.execute(query)
        #         for voltage in cursor.fetchall():
        #             self.voltages.append(voltage)

        # except FileNotFoundError:
        #     print("Fetching voltages by web")

        #     query = "SELECT integer_timestamp, high_voltage\
        #         FROM ccldas_production.pelletron_data \
        #              ORDER BY integer_timestamp ASC"
        #     cursor.execute(query)
        #     self.voltages = cursor.fetchall()
        #     voltage_file = open("voltages.csv","w")
        #     for volt in self.voltages:
        #         voltage_file.write("%d,%f\n" %(volt[0],volt[1]))
        #     voltage_file.close()

a = Rate_analyzer("localhost","root","dust","ccldas_production")

#a = Rate_analyzer("192.168.1.102","nathan","dust","ccldas_production") 