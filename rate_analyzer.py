import mysql.connector
from datetime import datetime

gap_size = 20*60*1000


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
        self.num_particles = 0
        self.p_list = []

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


        #self.particles = [(100,0),(200,0),(500,0),(600,0),(700,0),(800,0),(1100,0),(1150,0),(1500,0)]
        #self.velocities = [(300,10,5),(650,100,0),(1600,5,4)]

        self.generate_stops()
        print("Data retrieved")
    


        
        #self.get_sessions()
        self.segment_sessions()

        self.tag_sessions()

        print(sum( s.duration for s in self.session_list))
        print(sum ( len(s.p_list) for s in self.session_list))
        print(len(self.particles))
        

        #for s in self.session_list:print(s)

    def display_gaps(self):
        for i in range(1,len(self.session_list)-1):
            if self.session_list[i].experimentID == None and self.session_list[i].duration > 60*60*1000:
                print(self.session_list[i-1])
                print(self.session_list[i])
                print(self.session_list[i+1])
                print("-----------------------------------------")

        
    def tag_sessions(self):

        self.empty_sessions = []
        self.valid_sessions = []
        p_index =0
        counter = 0
        total = 0
        for session in self.session_list:
            while self.particles[p_index][0] < session.start:
                p_index+=1
                counter +=1
                total +=1
            if self.particles[p_index][0] <= session.end:
                #session.dustID = self.particles[p_index][3]
                #session.experimentID = self.particles[p_index][2]
                self.valid_sessions.append(session)
                
            else: self.empty_sessions.append(session)

            while self.particles[p_index][0] <= session.end:
                session.p_list.append(self.particles[p_index])
                p_index+=1
        counter =0
        print("Count: ",total)

    def segment_sessions(self):
        s_index = 0
        v_index = 0
        for s in self.session_list:print(s)
        print ("===============================")
        print("Len: ",len(self.session_list))
        while s_index < len(self.session_list) and v_index < len(self.velocities):
            session = self.session_list[s_index]
            while v_index < len(self.velocities)-1 and \
                  self.velocities[v_index][0] < session.start:
                v_index += 1
            session.min_V = self.velocities[v_index][2]
            session.max_V = self.velocities[v_index][1]
            if self.velocities[v_index][0] < session.end:
                del self.session_list[s_index]
                self.session_list.insert(s_index, Session(self.velocities[v_index][0]+1,\
                                    session.end,session.min_V,session.max_V))
                self.session_list.insert(s_index, Session(session.start,\
                                    self.velocities[v_index][0]-1,session.min_V,session.max_V))
                
                v_index+=1
                s_index -=1
                
            s_index+=1
        print("=========================================")
                
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
                            

    #get_sessions splits the timeline into a list of active sessions
    #These sessions are divided by gaps in detections, 
    def get_sessions(self):


        #initialize parallel indices
        sa_index = 0
        st_index = 0
        v_index = 0
        #Set start time
        time = self.velocities[0][0]

        #Start after the velocities are set
        while self.starts[sa_index] < time: sa_index+=1
        while self.stops[st_index] < time or self.stops[st_index] < self.starts[sa_index]: st_index+=1

        #Set initial velocities
        min_V = self.velocities[v_index][2]
        max_V = self.velocities[v_index][1]
        v_index = 1

        #Initialize session start times and session stop times
        session_start = self.starts[sa_index]
        session_end = 0
        session_duration = 0

        #Until you run out of start signals
        while sa_index < len(self.starts):

            #If the velocity changes between stop signals, split the session
            if v_index < len(self.velocities) and self.velocities[v_index][0] < self.stops[st_index] :
                session_end = self.velocities[v_index][0]
                session_duration = session_end - session_start
                session_start = self.velocities[v_index][0]

            #Else there is a stop signal before the next velocity change
            else:
                #Edge finish case
                if st_index == len(self.stops): return

                session_end = self.stops[st_index]
                session_duration = session_end - session_start
                st_index +=1

                #In case there are multiple starts in the middle of the session
                while sa_index < len(self.starts) and self.starts[sa_index] < session_end:
                    sa_index += 1

                #Set the new start after the end of the current session
                session_start = self.starts[sa_index]

                #If there are multiple stops between the end of session and the start of the next session
                while st_index < len(self.stops) and self.stops[st_index] < session_start:
                    st_index+=1


            while v_index < len(self.velocities) and session_start >= self.velocities[v_index][0]:
                min_V = self.velocities[v_index][2]
                max_V = self.velocities[v_index][1]
                v_index += 1
            self.session_list.append(Session(session_end-session_duration,session_end,min_V,max_V))
            if v_index == len(self.velocities)-1 or st_index == len(self.stops)-1: return
        return total_time

        

    def pull_data(self,hostname, usr, password, db):
    
        mydb = mysql.connector.connect(host=hostname, user=usr,passwd=password,database=db)
        cursor = mydb.cursor()
        limited = False
        if limited:
            print(".",end = "")
            cursor.execute("select integer_timestamp, velocity_max, \
            velocity_min from psu where integer_timestamp > 1560973836029  order by integer_timestamp ASC")
            self.velocities = cursor.fetchall()
            print(".",end = "")
            cursor.execute("SELECT integer_timestamp FROM ccldas_production.source_settings\
            WHERE integer_timestamp > 1560973836029 AND !(frequency=0 OR needle_voltage=0 \
            OR amplitude=0) order by integer_timestamp ASC")
            starts = cursor.fetchall()
            self.starts = [ time[0] for time in starts]
            print(".",end = "")

            cursor.execute("SELECT integer_timestamp FROM ccldas_production.source_settings\
            WHERE integer_timestamp > 1560973836029 AND (frequency=0 OR \
            needle_voltage=0  OR amplitude=0) order by integer_timestamp ASC")
            stops = cursor.fetchall()
            self.stops = [time[0] for time in stops]
            print(".",end = "")
            cursor.execute("SELECT integer_timestamp FROM ccldas_production.experiment_settings\
            where integer_timestamp > 1560973836029 order by integer_timestamp ASC")
            experiments = cursor.fetchall()
            for ex in experiments:
                self.starts.append(ex[0]+1)
                self.stops.append(ex[0])
            self.starts.sort()
            self.stops.sort()

            query = "SELECT integer_timestamp, velocity, id_experiment_settings, id_dust_info\
            , estimate_quality FROM ccldas_production.dust_event \
            WHERE integer_timestamp > 1560973836029 AND (velocity <= 100000 \
            AND velocity >= 0 ) ORDER BY integer_timestamp ASC"
            cursor.execute(query)
            self.particles = cursor.fetchall()
        else:
            
            print(".",end = "")
            cursor.execute("select integer_timestamp, velocity_max, \
            velocity_min from psu order by integer_timestamp ASC")
            self.velocities = cursor.fetchall()
            print(".",end = "")
            cursor.execute("SELECT integer_timestamp FROM ccldas_production.source_settings\
            WHERE !(frequency=0 OR needle_voltage=0 OR amplitude=0)")
            starts = cursor.fetchall()
            self.starts = [ time[0] for time in starts]
            print(".",end = "")

            cursor.execute("SELECT integer_timestamp FROM ccldas_production.source_settings\
            WHERE (frequency=0 OR needle_voltage=0  OR amplitude=0)")
            stops = cursor.fetchall()
            self.stops = [time[0] for time in stops]
            print(".",end = "")
            cursor.execute("SELECT integer_timestamp FROM ccldas_production.experiment_settings")
            experiments = cursor.fetchall()
            
            """
            for ex in experiments:
                self.starts.append(ex[0]+1)
                self.stops.append(ex[0])
            self.starts.sort()
            self.stops.sort()"""

            query = "SELECT integer_timestamp\
            FROM ccldas_production.dust_event WHERE (velocity <= 100000 \
            AND velocity >= 0 ) ORDER BY integer_timestamp ASC"
            cursor.execute(query)
            self.particles = cursor.fetchall()

a = Rate_analyzer("localhost","root","dust","ccldas_production")
