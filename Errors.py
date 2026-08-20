# Errors.py is where every Hamri-level runtime error message lives.
# Each kind of error (undefined variable, undefined function, a loop
# that ran too long, ...) gets its own small "exception" class below -
# they all look almost identical on purpose: __init__ just remembers
# what went wrong (a name) and which line it happened on, and execute()
# formats a human-readable Swahili message and reports it. None of
# these classes actually use Python's own `raise`/`except` machinery -
# "throwing" one just means building it and immediately calling
# .execute() on it (see Errors.throwException below), then telling the
# symbol table to stop the script via symbolTable.exit(1).
from SymbolTable import symbolTable

def _report(message,line=None,column=None):
    # Route error text through whatever console the current run is using
    # (Tk Text widget, the web IDE's console shim, ...) so it's actually
    # visible there, same as chapa output. Falls back to print() for the
    # plain CLI (main.py), which never sets a console.
    #
    # Prefixes the source line (and, when available, the column within
    # that line) - either passed explicitly (see Errors.throwException's
    # 'line'/'column' arguments, used for 'leta', which fails at parse
    # time rather than execute time, and for 'mzunguko', which quotes
    # the loop's own header rather than wherever the body last ran) or,
    # for every other error, symbolTable.current_line/current_column -
    # kept up to date by every statement-list execution loop
    # (StatementParser.parse()'s own, and every kama/wakati/huku/
    # function-call body) right before each statement actually runs.
    # Falls back to no prefix at all only if neither line nor column is
    # set (e.g. an error somehow raised before any statement has started
    # executing); falls back to just the line, with no column, if only
    # the line is known.
    resolved_line = line if line is not None else symbolTable.current_line
    resolved_column = column if column is not None else symbolTable.current_column
    if resolved_line is not None and resolved_column is not None:
        prefix = 'Mstari {}, Nafasi {}: '.format(resolved_line,resolved_column)
    elif resolved_line is not None:
        prefix = 'Mstari {}: '.format(resolved_line)
    else:
        prefix = ''
    full_message = '{}{}'.format(prefix,message)

    if symbolTable.console is not None:
        symbolTable.console.insert('end','{}\n'.format(full_message))
    else:
        print(full_message)

class Errors:
    # A single instance of this class (see `Error = Errors()` at the
    # bottom of this file) is what the rest of the interpreter actually
    # imports and calls - e.g. `Error.throwException('anwani', name)`.
    def __init__(self):

        # Maps a short error-code string to the exception class that
        # knows how to report it. The keys are Swahili words describing
        # *what* is wrong (anwani="address", kazi="job/function",
        # mzunguko="loop/cycle", fahirisi="index", orodha="list",
        # darasa="class", leta="bring/import") - throwException below
        # uses whichever one is passed in to pick the right class out
        # of this dict.
        self.exceptions = {

        'anwani': VariableReferenceException,
        'kazi': FunctionReferenceException,
        'mzunguko': LoopLimitException,
        'fahirisi': IndexOutOfRangeException,
        'orodha': NotAListException,
        'darasa': NotAnObjectException,
        'leta': ImportException

        }

    def throwException(self,arg,args='',line=None,column=None):
        # Looks up the exception class for `arg` (e.g. 'anwani'),
        # constructs one with the extra details (`args`, `line`,
        # `column`), and immediately runs it. `self.exceptions[arg](args,
        # line,column)` reads as: fetch the class, then call it like a
        # function to build an instance - `.execute()` right after that
        # is what actually prints the message and stops the script.
        self.exceptions[arg](args,line,column).execute()

class VariableReferenceException:

    def __init__(self,arg,line=None,column=None):
        self.name = arg
        self.line = line
        self.column = column

    def execute(self):
        _report('Kosa La Anwani: Jina hili {' +self.name +'} halijulikani',self.line,self.column)
        symbolTable.exit(1)


class FunctionReferenceException:
    # 'kazi' = Swahili for "job/task" - used here for "function".

    def __init__(self,arg,line=None,column=None):
        self.name = arg
        self.line = line
        self.column = column

    def execute(self):
        _report('Kosa La Kazi: Kazi hii {' +self.name +'} haijaelezwa (undefined function)',self.line,self.column)
        symbolTable.exit(1)


class LoopLimitException:
    # 'mzunguko' = Swahili for "loop/cycle" - a wakati loop that never
    # became false ran too many iterations and was stopped, rather than
    # freezing the page forever.

    def __init__(self,arg,line=None,column=None):
        self.name = arg
        self.line = line
        self.column = column

    def execute(self):
        _report('Kosa La Mzunguko: mzunguko {} haujaisha (loop did not end - check your condition)'.format(self.name),self.line,self.column)
        symbolTable.exit(1)


class IndexOutOfRangeException:
    # 'fahirisi' = Swahili for "index" - reading or writing a list
    # position that doesn't exist (negative, or past the end).

    def __init__(self,arg,line=None,column=None):
        self.name = arg
        self.line = line
        self.column = column

    def execute(self):
        _report('Kosa La Fahirisi: fahirisi hii katika {' +self.name +'} haipo (index out of range)',self.line,self.column)
        symbolTable.exit(1)


class NotAListException:
    # 'orodha' = Swahili for "list" - trying to index/append/loop over a
    # variable that isn't actually holding a list.

    def __init__(self,arg,line=None,column=None):
        self.name = arg
        self.line = line
        self.column = column

    def execute(self):
        _report('Kosa La Orodha: {' +self.name +'} si orodha (not a list)',self.line,self.column)
        symbolTable.exit(1)


class NotAnObjectException:
    # 'darasa' = Swahili for "class" - trying to read/set a property or
    # call a method on a variable that isn't actually holding an object
    # (an instance of some darasa).

    def __init__(self,arg,line=None,column=None):
        self.name = arg
        self.line = line
        self.column = column

    def execute(self):
        _report('Kosa La Darasa: {' +self.name +'} si kitu (not an object)',self.line,self.column)
        symbolTable.exit(1)


class ImportException:
    # 'leta' = Swahili for "bring" - used for importing a class (or one of
    # its methods) from another file. Covers three failure shapes with one
    # message: the file itself couldn't be found/read, the requested class
    # isn't defined in it, or (for a selective method import) the
    # requested method isn't defined on that class.
    #
    # Unlike every other exception here, this one fires at *parse* time
    # (leta has no runtime behaviour of its own - see StatementParser's
    # 'leta' case) rather than execute time, so symbolTable.current_line
    # wouldn't reflect it. StatementParser passes the leta statement's
    # own line explicitly instead - see throwException's 'line' argument.

    def __init__(self,arg,line=None,column=None):
        self.name = arg
        self.line = line
        self.column = column

    def execute(self):
        _report('Kosa La Leta: {' +self.name +'} haipatikani (import failed - check the file name, class name, or method name)',self.line,self.column)
        symbolTable.exit(1)


# A single shared instance, imported everywhere else in the interpreter
# as `from Errors import Error` - there's never a need for more than
# one, so the module just builds it once here.
Error = Errors()