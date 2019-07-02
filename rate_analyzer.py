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



        self.generate_stops()
        print("Data retrieved")
        

        self.velocity_segment()
        self.experiment_segment()
        self.tag_sessions()

        self.session_list.sort( key = lambda x: x.duration)
        for s in self.session_list:
            if len(s.p_list)==1:
                print(s)
        print(sum(s.duration for s in self.session_list if len(s.p_list)==1))


        
        print(sum( s.duration for s in self.session_list))
        print(sum ( len(s.p_list) for s in self.session_list))
        print(len(self.particles))

        print(sum( s.duration for s in self.session_list if s.dustID == None))
        print(sum(1 for s in self.session_list if s.dustID == None))
        print(len(self.session_list))
        """for i in range(1,len(self.session_list)-1):
            if self.session_list[i].dustID==None:
                print(self.session_list[i-1])
                print(self.session_list[i])
                print(self.session_list[i+1])
                print("======================================")"""
        
    def tag_sessions(self):

        self.empty_sessions = []
        self.valid_sessions = []
        p_index =0
        for session in self.session_list:
            while self.particles[p_index][0] < session.start:
                p_index+=1
            if self.particles[p_index][0] <= session.end:
                session.dustID = self.particles[p_index][1]
                session.material = self.dust_type[self.particles[p_index][1]]
                self.valid_sessions.append(session)
                
            else: self.empty_sessions.append(session)
            
            while self.particles[p_index][0] <= session.end:
                session.p_list.append(self.particles[p_index])
                p_index+=1
        
    def experiment_segment(self):
        s_index = 0
        e_index = 0
        while s_index < len(self.session_list) and e_index < len(self.experiments):
            session = self.session_list[s_index]
            while e_index < len(self.experiments)-1 and \
                self.experiments[e_index][0] < session.start:
                e_index += 1

            session.experimentID = self.experiments[e_index][1]
            
            if self.experiments[e_index][0] < session.end:
                del self.session_list[s_index]
                self.session_list.insert(s_index, Session(self.experiments[e_index][0]+1,\
                                    session.end,session.min_V,session.max_V))
                self.session_list.insert(s_index, Session(session.start,\
                                    self.experiments[e_index][0]-1,session.min_V,session.max_V))
                
                e_index+=1
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
            cursor.execute("SELECT integer_timestamp, id_experiment_settings FROM ccldas_production.experiment_settings\
            where integer_timestamp > 1560973836029 order by integer_timestamp ASC")
            self.experiments = cursor.fetchall()

            
            cursor.execute("SELECT id_dust_type,dust_name \
            FROM ccldas_production.dust_type")
            dust_list = cursor.fetchall()
            self.dust_type ={}
            for d in dust_list:
                self.dust_type[d[0]] = d[1]
            print(self.dust_type)

            query = "SELECT integer_timestamp, id_dust_info, velocity\
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
            cursor.execute("SELECT integer_timestamp,id_experiment_settings\
            FROM ccldas_production.experiment_settings")
            self.experiments = cursor.fetchall()

            cursor.execute("SELECT id_dust_type,dust_name \
            FROM ccldas_production.dust_type")
            dust_list = cursor.fetchall()
            self.dust_type ={}
            for d in dust_list:
                self.dust_type[d[0]] = d[1]

            query = "SELECT integer_timestamp, id_dust_info,velocity\
            FROM ccldas_production.dust_event WHERE (velocity <= 100000 \
            AND velocity >= 0 ) ORDER BY integer_timestamp ASC"
            cursor.execute(query)
            self.particles = cursor.fetchall()

a = Rate_analyzer("localhost","root","dust","ccldas_production")
