import mysql.connector
from datetime import datetime
class Session:
    def __init__(self, start, end, min_V, max_V):
        self.start = start
        self.end = end
        self.duration = end-start
        self.material = None
        self.dustID = None
        self.experimentID = None
        self.min_V = min_V
        self.max_V = max_V
        self.num_particles = 0
        self.p_list = []

    def __str__(self):
        return "Session from %s to %s \nDuration: %.1f min material: %s, %.1f-%.1fkm/s\nDustID: %s \
ExperimentID: %s" %(datetime.fromtimestamp(self.start/1000).strftime("%c"),\
                    datetime.fromtimestamp(self.end/1000).strftime("%c"),\
                    self.duration/1000/60,self.material,self.min_V,self.max_V,self.dustID,self.experimentID)
    
class Rate_analyzer:
    def __init__(self,hostname, user, password, database):
        print("Fetching Data",end  = "")
        self.pull_data(hostname,user, password, database)
        self.generate_stops()
        print("Data retrieved")
        self.get_sessions()
        self.tag_sessions()
        #self.find_sessions()
        
        #for i in range(-20,-1): print(self.session_list[i])
        #for s in self.empty_sessions: print(s)
        print(sum(s.duration for s in self.session_list))
        print(sum(s.duration for s in self.empty_sessions))
        print(len(self.session_list),len(self.empty_sessions))
        self.display_gaps()
        
    def display_gaps(self):
        for i in range(1,len(self.session_list)-1):
            if self.session_list[i].experimentID == None and self.session_list[i].duration > 60*60*1000:
                print(self.session_list[i-1])
                print(self.session_list[i])
                print(self.session_list[i+1])
                print("-----------------------------------------")

        
    def tag_sessions(self):
        p_index =0
        self.empty_sessions = []
        for session in self.session_list:
            while self.particles[p_index][0] < session.start: p_index+=1

            particle = self.particles[p_index]
            if particle[0] < session.end:
                session.dustID = particle[3]
                session.experimentID = particle[2]
                session.p_list.append(particle)
            else: self.empty_sessions.append(session)


    def generate_stops(self):
        times = []
        for i in range(len(self.particles)-1):
            time = self.particles[i][0]
            next_time = self.particles[i+1][0]

            times.append(next_time-time)
            
            if (next_time - time > 2*60*60*1000):
                self.stops.append(time)
                self.starts.append(next_time)
        self.stops.sort()

        """
    def find_sessions(self):
        groups = []
        cluster = []
        for i in range(len(self.particles)-1):
            cluster.append(self.particles[i])
            time = self.particles[i][0]
            next_time = self.particles[i+1][0]
            if next_time - time > 2400000:
                groups.append(cluster)
                cluster = []

        print(len(groups))
        print("Num: " ,len(groups))
        print(sum (1 for g in groups if len(g) == 1))
        for single in [g for g in groups if len(g)==1]:
            p = single[0]
            print(p[2])
        """
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

        

    def pull_data(self,hostname, usr, password, db):
    
        mydb = mysql.connector.connect(host=hostname, user=usr,passwd=password,database=db)
        cursor = mydb.cursor()
        limited = False
        if limited:
            query = "SELECT integer_timestamp, velocity, id_experiment_settings, id_dust_info\
            FROM ccldas_production.dust_event WHERE (integer_timestamp > 1560959101959 AND\
            estimate_quality >=3 AND velocity <= 100000 \
            AND velocity >= 0 ) ORDER BY integer_timestamp ASC"
            cursor.execute(query)
            self.particles = cursor.fetchall()

            print(".",end = "")
            cursor.execute("select integer_timestamp, velocity_max, \
            velocity_min from psu WHERE integer_timestamp > 1560959101959 \
            order by integer_timestamp ASC")
            self.velocities = cursor.fetchall()
            print(".",end = "")
            cursor.execute("SELECT integer_timestamp FROM ccldas_production.source_settings\
              WHERE integer_timestamp > 1560959101959 AND\
            !(frequency=0 OR needle_voltage=0 OR amplitude=0)")
            starts = cursor.fetchall()
            self.starts = [ time[0] for time in starts]
            print(".",end = "")

            cursor.execute("SELECT integer_timestamp FROM ccldas_production.source_settings\
            WHERE integer_timestamp > 1560959101959 AND\
            ( frequency=0 OR needle_voltage=0  OR amplitude=0)")
            stops = cursor.fetchall()
            self.stops = [time[0] for time in stops]
            print(".",end = "")
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

            for ex in experiments:
                self.starts.append(ex[0]+1)
                self.stops.append(ex[0])
            self.starts.sort()
            self.stops.sort()

            query = "SELECT integer_timestamp, velocity, id_experiment_settings, id_dust_info\
            FROM ccldas_production.dust_event WHERE (velocity <= 100000 \
            AND velocity >= 0 ) ORDER BY integer_timestamp ASC"
            cursor.execute(query)
            self.particles = cursor.fetchall()

        
a = Rate_analyzer("localhost","root","dust","ccldas_production")
