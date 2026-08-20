from SymbolTable import symbolTable

def _report(message):
    # Route error text through whatever console the current run is using
    # (Tk Text widget, the web IDE's console shim, ...) so it's actually
    # visible there, same as chapa output. Falls back to print() for the
    # plain CLI (main.py), which never sets a console.
    if symbolTable.console is not None:
        symbolTable.console.insert('end','{}\n'.format(message))
    else:
        print(message)

class Errors:
    def __init__(self):

        self.exceptions = {

        'anwani': VariableReferenceException,
        'kazi': FunctionReferenceException,
        'mzunguko': LoopLimitException,
        'fahirisi': IndexOutOfRangeException,
        'orodha': NotAListException,
        'darasa': NotAnObjectException,
        'leta': ImportException

        }

    def throwException(self,arg,args=''):

        self.exceptions[arg](args).execute()

class VariableReferenceException:

    def __init__(self,arg):
        self.name = arg

    def execute(self):
        _report('Kosa La Anwani: Jina hili {' +self.name +'} halijulikani')
        symbolTable.exit(1)


class FunctionReferenceException:
    # 'kazi' = Swahili for "job/task" - used here for "function".

    def __init__(self,arg):
        self.name = arg

    def execute(self):
        _report('Kosa La Kazi: Kazi hii {' +self.name +'} haijaelezwa (undefined function)')
        symbolTable.exit(1)


class LoopLimitException:
    # 'mzunguko' = Swahili for "loop/cycle" - a wakati loop that never
    # became false ran too many iterations and was stopped, rather than
    # freezing the page forever.

    def __init__(self,arg):
        self.name = arg

    def execute(self):
        _report('Kosa La Mzunguko: mzunguko {} haujaisha (loop did not end - check your condition)'.format(self.name))
        symbolTable.exit(1)


class IndexOutOfRangeException:
    # 'fahirisi' = Swahili for "index" - reading or writing a list
    # position that doesn't exist (negative, or past the end).

    def __init__(self,arg):
        self.name = arg

    def execute(self):
        _report('Kosa La Fahirisi: fahirisi hii katika {' +self.name +'} haipo (index out of range)')
        symbolTable.exit(1)


class NotAListException:
    # 'orodha' = Swahili for "list" - trying to index/append/loop over a
    # variable that isn't actually holding a list.

    def __init__(self,arg):
        self.name = arg

    def execute(self):
        _report('Kosa La Orodha: {' +self.name +'} si orodha (not a list)')
        symbolTable.exit(1)


class NotAnObjectException:
    # 'darasa' = Swahili for "class" - trying to read/set a property or
    # call a method on a variable that isn't actually holding an object
    # (an instance of some darasa).

    def __init__(self,arg):
        self.name = arg

    def execute(self):
        _report('Kosa La Darasa: {' +self.name +'} si kitu (not an object)')
        symbolTable.exit(1)


class ImportException:
    # 'leta' = Swahili for "bring" - used for importing a class (or one of
    # its methods) from another file. Covers three failure shapes with one
    # message: the file itself couldn't be found/read, the requested class
    # isn't defined in it, or (for a selective method import) the
    # requested method isn't defined on that class.

    def __init__(self,arg):
        self.name = arg

    def execute(self):
        _report('Kosa La Leta: {' +self.name +'} haipatikani (import failed - check the file name, class name, or method name)')
        symbolTable.exit(1)


Error = Errors()