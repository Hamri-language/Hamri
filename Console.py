from SymbolTable import symbolTable

import tkinter as tk

from Logger import Log

class Console:
    def __init__(self,console=None):
        self.print_string = ''
        self.begin_execution_str = '=====================================\nRunning Hamri script\n=====================================\n'
        self.execution_success_str = '\n=====================================\nHamri script execution success with exit code 0\n====================================='
        self.execution_failed_str = '\n=====================================\nHamri script execution fail with exit code 0\n====================================='
        self.console = console
        
    def use_console(self,arg):
        self.console = arg
        
    def print_to_console(self,arg):
                
        
        if self.console is not None:
            self.console.insert(tk.END,'{}\n'.format(arg))
        else:
            print('{}\n'.format(arg))
            
    def clear_console(self):
        Log('clearing console...')
        if self.console is not None:
            self.console.delete(1.0,tk.END)
        
    def start_console(self):
        self.clear_console()
        #print out execution code statement at the start of the execution loop
        self.print_to_console(self.begin_execution_str)
            
        
    def close_console(self):
        #print out execution code statement at the end of the execution loop
        
        if symbolTable.exit() == 0:
            self.print_to_console(self.execution_success_str)
        else:        
            self.print_to_console(self.execution_failed_str)
                
        
    
    
    
    
    
console = Console()
