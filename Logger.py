class Logger:
    # Class variables to store logs and keys
    logs = []
    keys = []
    
    def __init__(self, message, key=''):
        # Initialize a new log with the given message and key (optional)
        self.log_key = key
        self.log_message = message
        
        # Add the log to the logs list
        self.addLog(self.log_message, self.log_key)
        
    def addLog(self, message, key=''):
        # Add a new log with the given message and key (optional) to the logs list
        
        # Append the log as a tuple (key, message)
        self.logs.append((key, message))
        
        # Append the key to the keys list if it's not already present
        self.keys.append(key) if key not in self.keys else None 
        
    def printLogs(self, arg=''):
        # Print the logs based on the provided argument (optional)
        
        print('=====================================')
        print('Running Hamri Logger')
        print('=====================================')
        
        if arg == '':
            # If no argument is provided, print all logs
            for i in self.logs:
                print('{}: {}'.format(i[0], i[1]) if i[0] != '' else '{}'.format(i[1]))
        else:
            # If an argument is provided, print logs with matching keys
            for i in self.logs:
                print('{}: {}'.format(i[0], i[1])) if i[0] == arg else None
        
    def getKeys(self):
        # Return the list of unique keys used in the logs
        return self.keys
            
# Create an instance of the Logger class and assign it to the variable "Logger"
Logger = Logger('')

# Create a reference to the getKeys method of the Logger instance and assign it to the variable "LogKeys"
LogKeys = Logger.getKeys

# Create a reference to the addLog method of the Logger instance and assign it to the variable "Log"
Log = Logger.addLog

# Create a reference to the printLogs method of the Logger instance and assign it to the variable "Logs"
Logs = Logger.printLogs




# - The Logger class provides logging functionality.
# - It allows creating logs with messages and optional keys.
# - Logs are stored in the logs list and keys in the keys list.
# - The printLogs method can be used to print logs based on keys.
# - The getKeys method returns the list of unique keys used in the logs.
