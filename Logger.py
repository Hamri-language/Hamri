class Logger:
    
    logs = []
    
    keys = []
    
    def __init__(self,message,key=''):
        
        self.log_key = key
        self.log_message = message
        
        self.addLog(self.log_message,self.log_key)
        
    def addLog(self,message,key=''):
        self.logs.append((key,message))
        self.keys.append(key) if key not in self.keys else None 
        
        
    def printLogs(self,arg=''):
        print('=====================================\nRunning Hamri Logger\n=====================================')
        if arg == '':        
            for i in self.logs:
                
                print('{}: {}'.format(i[0],i[1]) if i[0] != '' else '{}'.format(i[1]))
                
        else:
            for i in self.logs:
                
                print('{}: {}'.format(i[0],i[1])) if i[0] == arg else None
                
        
    def getKeys(self):
        return self.keys
            
            
Logger = Logger('')
LogKeys = Logger.getKeys
Log = Logger.addLog
Logs = Logger.printLogs



