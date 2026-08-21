# BuiltinModules.py is Hamri's equivalent of Python's own standard
# library modules (math, os, ...) - small, always-available Python
# functionality exposed to Hamri scripts under a Hamri-language name,
# without the script having to 'leta' (import) a separate .ham file for
# it. A built-in module is activated with the new 'tumia' ("use")
# keyword/statement - e.g. `tumia Hesabu` - and its members are then
# reached with ordinary dot notation, e.g. `Hesabu.mzizi(16)`, exactly
# like a class instance's own methods.
#
# Only one built-in module exists so far: Hesabu ("arithmetic/
# calculation"), Hamri's math module. New built-in modules are added by
# writing another plain class below (its methods are the module's
# callable members - plain Python @staticmethods, since a built-in
# module has no per-instance state, unlike a darasa) and registering it
# in BUILTIN_MODULES at the bottom.
import math


class HesabuModule:
    # Hesabu = Swahili for "arithmetic"/"calculation". Deliberately kept
    # to a small, explicitly-requested starting set of seven functions
    # rather than mirroring Python's whole math module up front - more
    # (pai/e constants, nguvu/logi/trig functions, faktoria, ...) can be
    # added the same way later.
    #
    # Every member is a @staticmethod (no `self`) since HesabuModule is
    # never instantiated - StatementParser's BuiltinModuleCallExpression
    # looks members up straight off the class itself via getattr().

    @staticmethod
    def kamili(x):
        # "kamili" ("complete/absolute") - absolute value.
        return abs(x)

    @staticmethod
    def kubwa(a,b):
        # "kubwa" ("big/large") - the larger of two values.
        return max(a,b)

    @staticmethod
    def ndogo(a,b):
        # "ndogo" ("small") - the smaller of two values.
        return min(a,b)

    @staticmethod
    def mzizi(x):
        # "mzizi" ("root") - square root.
        return math.sqrt(x)

    @staticmethod
    def juu(x):
        # "juu" ("up/above") - round up (ceiling).
        return math.ceil(x)

    @staticmethod
    def chini(x):
        # "chini" ("down/below") - round down (floor).
        return math.floor(x)

    @staticmethod
    def kadirisha(x):
        # "kadirisha" ("estimate/round") - round to the nearest whole
        # number, same tie-breaking rule as Python's own round() (banker's
        # rounding - round-half-to-even).
        return round(x)


# Maps a built-in module's Hamri-facing name (exactly as written after
# 'tumia', and exactly as written before the '.' in a member access - so
# it must stay capitalized, matching the 'Hesabu' keyword entry in
# LexicalParser.py's Tokens.keyword pattern) to the plain Python class
# that implements its members. StatementParser.py's UseModuleStatement
# and BuiltinModuleCallExpression both look a module up here by name.
BUILTIN_MODULES = {
    'Hesabu': HesabuModule,
}
