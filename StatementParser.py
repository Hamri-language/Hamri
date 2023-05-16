import sys

from ExpressionParser import ExpressionParser

from Objects import * 

from SymbolTable import symbolTable

from Logger import Log

from LexicalParser import TokenObj
import tkinter as tk

global variables
variables= {"variables" :{
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

global console
console = None



context = {"var-scope": "global","function-scope":"kwanza","class-scope":"kwanza"}
definition_flag = False
call_flag = False

def breadcrumb(json_dict_or_list, value):
    if json_dict_or_list == value:
        return [json_dict_or_list]
    elif isinstance(json_dict_or_list, dict):
        for k, v in json_dict_or_list.items():
            p = breadcrumb(v, value)
            if p:
                return [k] + p
    elif isinstance(json_dict_or_list, list):
        lst = json_dict_or_list
        for i in range(len(lst)):
            p = breadcrumb(lst[i], value)
            if p:
                return [str(i)] + p
            
class StatementParser:
    compound_statement = {"kwanza":[],"functions":{}}
    context = compound_statement['kwanza']
    prev_context = compound_statement['kwanza']
    global call_flag
    global definition_flag

    function_flag = 'kwanza'
    
    def __init__(self,tokens):
        self.tokens = tokens
        self.token_position = 0

        

        

    def parseStatement(self,parse_token):
        global call_flag
        
        
        next_ = self.next_token() if self.token_position < len(self.tokens)-1 else None
        prev_ = self.prev_token() if self.token_position > 0 else None
        Log(parse_token.value,"parsing token")
        
        statement = None
        
        if parse_token.value == 'chapa' and next_ != None:
            Log('case for print')
            #print(ExpressionParser(self.fetch_express()).parse())
            statement = PrintStatement(ExpressionParser(self.fetch_express()).parse())
        elif parse_token.value == '=' and next_ != None and prev_ != None:
            Log('case for assignment')
            
            obj = Var((prev_.value,ExpressionParser(self.fetch_express()).parse(),symbolTable.get_scope('var-scope')))
            statement = AssignmentStatement(obj)
        elif parse_token.value == 'eleza':
            Log('case for function definition')
            symbolTable.def_flag = True
            function_name = next_.value
            self.token_position = next_.position() + 1

            statement = FunctionDefinitionStatement((function_name,self.fetch_express()))
                         
          
            
        elif parse_token.value == 'kwisha':
            Log('case for end block')
            symbolTable.reset_flags()
            statement = EndBlockStatement(symbolTable.context)
            
        elif parse_token.value == 'jaza':
            Log('case for user input')
            self.token_position = self.token_position + 1
            #Log(type(self.fetch_express()))
            
            statement = InputStatement(self.fetch_express())
            
        elif parse_token.token_type == 'variable' and next_.value == '(':
            Log('case for function call')
            call_flag = True
            function_name = parse_token.value
            
            self.token_position = self.token_position + 1 #advance by one to fly over the first divider
            #Log(self.fetch_express())
            
            statement = FunctionCallStatement((function_name,self.fetch_express()))
            
        else:
            Log('default case')
            
            
            

        #statement = switcher[parse_token.token_type][parse_token.value] if parse_token.token_type in switcher.keys() else None
            
        return statement

    
    def fetch_express(self):
        next_ = self.next_token()
        
        Log('Fetching expression ')
        
        if next_.token_type == 'divider':
            return_val = []
            
                
        else:
            
            return_val = [Object(self.next_token()).cast()]
            Log(return_val[0],'First Token')
            
            self.token_position = self.token_position + 1
            
            while self.next_token().token_type == 'operator':
                return_val.append(Object(self.next_token()).cast()) if self.next_token().value != ',' else None #add our operator
                    
                self.token_position = self.token_position + 1 #advance our execution loop
                
                return_val.append(Object(self.next_token()).cast()) #add our term
                self.token_position = self.token_position + 1            
            
        
        Log(return_val,'Evaluated expression')
        return return_val
        
    
    def print_statements(self):
        print(symbolTable.table)
            
    def next_token(self):
        return self.tokens[self.token_position + 1]
    
    def prev_token(self): 
        
        return self.tokens[self.token_position - 1]    

    def parse(self,arg=None):
        global console
        
        console = arg
        
        Log('=======================')
        Log('Statement Parsing')
        Log('=======================')        
        
        while self.token_position < len(self.tokens):
            
            statement = self.parseStatement(self.tokens[self.token_position])
            
            #print('Function definition flag:',symbolTable.def_flag)
 
            Log(statement,'Evaluated statement')
            Log(symbolTable.get_scope('function-scope'),'Current context')
            
            symbolTable.table['functions'][symbolTable.get_scope('function-scope')].append(statement) if statement else None
            
            Log(symbolTable.table,'Current symbol table state')
            
            if type(statement).__name__ == 'FunctionDefinitionStatement':
                
                #change to function scope
                
                symbolTable.set_scope(('var-scope','local'))
                symbolTable.set_scope(('function-scope',statement.name))           
            
            self.token_position = self.token_position + 1

                
            
        return self
        

    def execute(self):
        #clear our console
        
        global console
        
        if console is not None:
            console.insert(1.0,'=====================================\nRunning Hamri script\n=====================================\n')
        Log('=======================')
        Log('Statement Execution')
        Log('=======================')
        
        for i in symbolTable.table['functions'][symbolTable.get_scope('function-scope')]:
             
            if symbolTable.exit() == 0:
                Log(symbolTable.get_scope('function-scope'),'Executing from scope')
                Log(i,'Executing statement')
                i.execute()
                
            else:
                break
            
        if symbolTable.exit() == 0:
            if console is not None:
                console.insert(tk.END,'\n=====================================\nHamri script execution success with exit code 0\n=====================================')
                
            Log('\n=====================================\nHamri script execution success with exit code 0\n=====================================','Executing Success')
        else:
            if console is not None:          
                console.insert(tk.END,'\n=====================================\nHamri script execution fail with exit code 1\n=====================================')
        
        
        #try:
            
            #for i in symbolTable.table['functions'][symbolTable.get_scope('function-scope')]:
                
                #Log(symbolTable.get_scope('function-scope'),'Executing from scope')
                
                #Log(i,'Executing statement')
                #i.execute()
                
                
            #print('\n=====================================\nHamri script execution success with exit code 0\n=====================================')
                    
        #except Exception as e:
            #Log(e,'Exception')
            #print('\n=====================================\nHamri script execution failed with exit code 1\n=====================================')






class Statement:
    def __init__(self):
        None

    def execute(self):
        None


    
class FunctionCallStatement(Statement):
    def __init__(self,arg):
        self.name = arg[0]
        self.params = arg[1]
            
        
        
    def execute(self):

        #assign our function definition arguments to the calling argument values before running function
        assignments = list(zip(symbolTable.get_function_arguments(self.name),self.params))
        
        Log(list(assignments),'Function Arguments')
        
        for i in assignments:
            
            Var((i[0],i[1],'local')).evaluate()
            
        #enable our call flag
        
        symbolTable.en_flag('call',self.name)
            
        for i in symbolTable.table["functions"][self.name]:
            
            Log(self.name,'Executing from function scope')
            
            Log(i,'Executing statement')            
            
            i.execute()
            
        symbolTable.reset_flags()
        
    
class FunctionDefinitionStatement(Statement):
    def __init__(self,arg):
        self.name = arg[0]
        self.params = arg[1]
        symbolTable.set_function(self.name)
        Log('created new function {}'.format(self.name),'Function Definition')
        
                         
    def execute(self):
        
        
        #create new argument placeholders in our local variable scope
        
        Log('creating new arguments')

        for i in self.params:
            
            Var(('function-{}-{}'.format(self.name,i.name),'','local')).evaluate()
            

            Log("created new argument: {}".format(i))        
        
class InputStatement(Statement):
    
    def __init__(self,arg):
        
        self.value = arg[0].evaluate()
        
        self.storage = arg[1].name
        
        
        
    def execute(self):
        
        var = Object(TokenObj('string',input(str(self.value)),0,0,0)).cast()
        
        Var((self.storage,var,symbolTable.get_scope('var-scope'))).evaluate()
        
        

class EndBlockStatement(Statement):
    def __init__(self,value):
        self.value = value
        #find parent keys and relinquish flow to parent's first object
        symbolTable.set_scope(('var-scope','global'))
        symbolTable.set_scope(('function-scope','kwanza'))        


class PrintStatement(Statement):
    def __init__(self,value):
        self.value = value

    def execute(self):
        if self.value.evaluate():
            if console is not None:
                console.insert(tk.END,'{}\n'.format(self.value.evaluate()))
            Log("{}".format(self.value.evaluate()),"Print Statement") 
        

class AssignmentStatement(Statement):
    def __init__(self,value):
        self.value = value
    
            
    def execute(self):
        self.value.evaluate()
            
        
        
'''

    def parse_next_expression(self):
        
        results = None
        
        expressions = [] 
        
        value = self.next_token().value if self.next_token().token_type != 'variable' else getattr(sys.modules['__main__'], self.value)
        
        
        
        while(self.get_token_by_index(self.token_position + 2).token_type == 'operator'):
            val_ = self.get_token_by_index(self.token_position + 2).value
            next_val = self.get_token_by_index(self.token_position + 3).value 
            
            if val_ == '+' :
                value = value + next_val if next_val != 'variable' else getattr(sys.modules['__main__'], next_val)
                self.token_position = self.token_position + 

'''