from Logger import Log

class SymbolTable:
    def __init__(self):
        self.table = {
            "variables" :{
                "global":{},
                "local":{}
            },
            "functions":{
                # 'kwanza' ("first") is the required main block - only
                # statements inside an explicit kwanza...kwisha run.
                # 'nje' ("outside") holds anything parsed before/outside
                # kwanza - e.g. helper function definitions - which is
                # never auto-executed, only called into from 'kwanza'.
                "kwanza":[],
                "nje":[]
            },
            "classes":{
                # Simple presence-registry populated by 'darasa' - maps a
                # class name to True, purely so a call like `Mtu(args)`
                # can tell "this name is a class, construct an instance"
                # apart from "this name is a function, call it".
            }
        }
        self.context =  {"var-scope": "global","function-scope":"nje","class-scope":"kwanza"}

        # Stack of (function-scope, var-scope) pairs, pushed when entering
        # a block (kwanza/eleza/kama) and popped on 'kwisha', so nested
        # blocks correctly return to their *enclosing* scope instead of
        # always resetting to the top level.
        self.scope_stack = []

        self.def_flag = False

        self.call_flag = False

        # Stack of currently-executing call names (function/method
        # qualified names), innermost last. call_flag always mirrors the
        # top of this stack - kept as a separate attribute since it's
        # already read all over the place (fetch_variable, local_key).
        # Needed so that when a nested call finishes (e.g. function A
        # calls function B), execution correctly resumes "inside A" -
        # rather than unconditionally forgetting there was ever an
        # active call at all - so any of A's own local variables written
        # *after* the call to B still land back in A's own call-qualified
        # storage instead of leaking into globals.
        self.call_stack = []

        self.exit_flag = 0

        # Shared handle to whatever 'console' object the current run is
        # using (a Tk Text widget in the desktop Notepad, or None for
        # plain CLI use, in which case output falls back to a bare
        # print()). Lets Errors.py surface messages the same way chapa
        # does.
        self.console = None

        # Pluggable hook used by 'leta' (import) to fetch another
        # module's source text by name - a callable taking a filename and
        # returning its source (or None if not found). Left as None,
        # load_module_source() falls back to reading a real file off
        # disk, so a plain script (e.g. via main.py) can 'leta' from a
        # sibling .ham file. A host embedding this interpreter elsewhere
        # (e.g. a GUI with its own in-memory files) can override this to
        # resolve module names however makes sense there instead.
        self.module_loader = None

        # Pluggable hook used by 'jaza' (input) to actually collect a
        # value from whoever's running the script - a callable taking the
        # prompt text and returning the typed string. Left as None, so a
        # plain script (e.g. via main.py) falls back to a normal
        # terminal input() prompt. A host with its own UI (e.g. the
        # desktop Notepad) can override this to pop up a proper dialog
        # instead of silently expecting input on whatever terminal
        # happened to launch it.
        self.input_handler = None

        # Set by 'rudisha' (return) so every enclosing block loop (kama,
        # wakati, huku) knows to stop running further statements and
        # unwind, all the way up to the function-call boundary - the one
        # place (FunctionCallStatement.execute) that actually absorbs the
        # flag and reads return_value, so it never leaks past the
        # function that returned into the caller's own control flow.
        self.return_flag = False
        self.return_value = None

        # Ever-increasing counter handing out a unique id to every object
        # created via a 'darasa' class, so each instance gets its own
        # distinct storage key even across multiple objects of the same
        # class.
        self.next_instance_id = 1


    def new_instance_id(self):
        id_ = self.next_instance_id
        self.next_instance_id = self.next_instance_id + 1
        return id_

    def set_class(self,name):
        self.table['classes'][name] = True

    def load_module_source(self,filename):
        # Used by 'leta' to fetch another file's Hamri source by name.
        # See module_loader above - the host environment can override
        # how a filename resolves to source text; without one, fall back
        # to a plain local file read so a script run from disk can still
        # 'leta' a sibling file.
        if self.module_loader is not None:
            return self.module_loader(filename)
        try:
            with open(filename,'r') as f:
                return f.read()
        except (IOError,OSError):
            return None

    def read_input(self,prompt):
        # Used by 'jaza' to actually collect a value - see input_handler
        # above. Falls back to a plain terminal input() prompt so a
        # script run from disk (main.py) behaves exactly as before.
        if self.input_handler is not None:
            return self.input_handler(prompt)
        return input(prompt)

    def alias_function(self,new_name,original_name):
        # Backs 'leta's selective method import ('leta salamu kutoka Mtu
        # kutoka "faili"') - copies an already-parsed function/method's
        # body and parameter placeholders under a new bare name, so it
        # can be called standalone (e.g. `salamu(...)`) exactly like any
        # other function. Deliberately does NOT copy a '-nafsi' binding -
        # a method pulled out of its class this way has no instance to
        # bind 'nafsi' to, so if its body still reaches for nafsi.anything
        # it'll fail the same way referencing any other undefined
        # variable would (Kosa La Anwani), rather than silently doing the
        # wrong thing. Returns False (no error thrown here - the caller
        # decides how to report it) if the original function doesn't
        # exist at all.
        if original_name not in self.table['functions']:
            return False

        self.table['functions'][new_name] = self.table['functions'][original_name]

        old_prefix = 'function-{}-'.format(original_name)
        new_prefix = 'function-{}-'.format(new_name)
        for key in list(self.table['variables']['local'].keys()):
            if key.startswith(old_prefix) and not key.endswith('-nafsi'):
                suffix = key[len(old_prefix):]
                self.table['variables']['local'][new_prefix + suffix] = self.table['variables']['local'][key]

        return True

    def set_return(self,value):
        self.return_flag = True
        self.return_value = value

    def clear_return(self):
        self.return_flag = False
        self.return_value = None

    def is_returning(self):
        return self.return_flag

    def reset_flags(self):
        self.def_flag = False
        
        self.call_flag = False
        
    def en_flag(self,arg,value=True):

        if arg == 'call':
            self.call_stack.append(value)
            self.call_flag = value

        else:
            self.def_flag = value

    def pop_call(self):
        # Ends the innermost active call, restoring call_flag to whichever
        # call (if any) was running before it - see call_stack above.
        if self.call_stack:
            self.call_stack.pop()
        self.call_flag = self.call_stack[-1] if self.call_stack else False

    def local_key(self,name):
        # Qualifies a variable name to the currently-executing function/
        # method call, if any, exactly the same way function parameters
        # already are ('function-{call}-{param}') - so an ordinary local
        # variable assigned inside a function body (anything that isn't
        # one of its declared parameters) gets its own isolated storage
        # slot per call, instead of every function in the whole program
        # sharing one flat bare-name entry in 'local'. fetch_variable()
        # already checks this qualified form first whenever call_flag is
        # set, so no changes were needed there.
        return 'function-{}-{}'.format(self.call_flag,name) if self.call_flag else name

    def write_local(self,name,value):
        self.table['variables']['local'][self.local_key(name)] = value

    def write_variable(self,scope,name,value):
        # Central write path for a variable assignment - used by ordinary
        # '=' assignment (Var.evaluate) as well as huku/for-each loop
        # variables and jaza input, so all of them get the same per-call
        # isolation instead of only function parameters getting it.
        if scope == 'local':
            self.write_local(name,value)
        else:
            self.table['variables'][scope][name] = value

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
            # '-nafsi' is 'self' for a method call, bound the same way a
            # normal parameter is (see FunctionCallStatement) but isn't
            # one of the function's own declared parameters, so it must
            # never be zipped against the caller's actual argument list.
            if k.startswith('function-{}-'.format(arg)) and not k.endswith('-nafsi'):

                res.append(k)



        return res if len(res)>0 else []
        
        
        
    def set_scope(self,arg):

        name,value = arg

        self.context[name] = value

    def get_scope(self,arg):

        return self.context[arg]

    def push_scope(self,function_scope,var_scope=None):
        # Remember the current (enclosing) scope, then switch into the
        # new block. var_scope is only overridden for blocks that need
        # their own fresh variable scope (functions); kama/kwanza share
        # whatever variable scope was already active.
        self.scope_stack.append((self.context['function-scope'],self.context['var-scope']))
        self.context['function-scope'] = function_scope
        if var_scope is not None:
            self.context['var-scope'] = var_scope

    def pop_scope(self):
        if self.scope_stack:
            function_scope,var_scope = self.scope_stack.pop()
            self.context['function-scope'] = function_scope
            self.context['var-scope'] = var_scope
        else:
            # Stray/unmatched kwisha - fall back to the safe top-level default.
            self.context['function-scope'] = 'nje'
            self.context['var-scope'] = 'global'

    def reset(self):
        # Clears all variables/functions/if-blocks and flags so a fresh
        # script run (e.g. clicking "Execute" again in the desktop
        # Notepad) doesn't inherit state left over from a previous run.
        self.__init__()


symbolTable = SymbolTable()
