from Logger import Log

class SymbolTable:
    def __init__(self):
        self.table = {
            "variables" :{
                "global":{},
                "local":{}
            },
            "functions":{
                "kwanza":[]
            },
            "classes":{
                "kwanza":[]
            }
        }
        self.context =  {"var-scope": "global","function-scope":"kwanza","class-scope":"kwanza"}
        
        self.def_flag = False
        
        self.call_flag = False
        
        self.exit_flag = 0
        
    def reset_flags(self):
        self.def_flag = False
        
        self.call_flag = False
        
    def en_flag(self,arg,value=True):
        
        if arg == 'call':
            self.call_flag = value
            
        else:
            self.def_flag = value
        
    def fetch_variable(self,key):
        
        Log('fetching.......: '+key)
        
        return_val = None
        
        
        if self.call_flag and 'function-{}-{}'.format(self.call_flag,key) in self.table['variables']['local'].keys():
            Log('found in function local scope')
            val = 'function-{}-{}'.format(self.call_flag,key)
            return_val = self.table['variables']['local'][val]
        elif key in self.table['variables']['local'].keys():
            Log('found in local scope')
            return_val = self.table['variables']['local'][key]
        elif key in self.table['variables']['global'].keys():
            Log('found in global scope')
            return_val = self.table['variables']['global'][key]
        else:
            return_val = False
            
        Log('result.......: {}'.format(return_val))    
        return return_val
    
    def exit(self,arg='get'):
        
        res = False
        
        if arg == 'get':
            res = self.exit_flag
        else:
            self.exit_flag = arg
            res = True 
            
        return res
        
            
        
    
    def set_variable(self,obj):
        
        name,value,scope = obj
        
        self.table['variables'][scope][i] = ''
        
    def set_function(self,arg):
        
         
        self.table['functions'][arg] = []
        
    def get_function_arguments(self,arg):
        
        res = []
        
        keys = [k for k in self.table['variables']['local'].keys()]
        
        for k in keys:
            if k.startswith('function-{}-'.format(arg)):
                
                res.append(k)
                
                        
        
        return res if len(res)>0 else []
        
        
        
    def set_scope(self,arg):
        
        name,value = arg
        
        self.context[name] = value
        
    def get_scope(self,arg):
        
        return self.context[arg]
        
        
        
symbolTable = SymbolTable()
