/*
 * hamri_api_draft.h
 * -----------------
 * DESIGN SKETCH — not implemented yet, nothing here compiles against real
 * code. This is a first draft of what an embeddable C API for Hamri could
 * look like, written to think through the shape of the problem before any
 * C is actually written. It deliberately mirrors the pattern used by Lua,
 * SQLite, and similar "small language/engine embedded via a C ABI" designs,
 * since that's the lowest common denominator every other language's FFI
 * (ctypes/cffi, JNI, P/Invoke, cgo, Rust's bindgen, etc.) can call into
 * directly without needing a Python (or any other) runtime alongside it.
 *
 * Everything below traces back to a specific gap in the current Python
 * implementation (LexicalParser.py / StatementParser.py / SymbolTable.py /
 * Objects.py) — see the comments inline. The intent is that once the
 * *semantics* implied here (real per-call frames, no global singleton,
 * errors-as-values instead of exit()) are proven out in the existing
 * Python interpreter, porting to a real C bytecode VM behind this header
 * is mostly mechanical rather than exploratory.
 */

#ifndef HAMRI_H
#define HAMRI_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ------------------------------------------------------------------ *
 * Interpreter state
 * ------------------------------------------------------------------ *
 * Opaque handle to one isolated Hamri interpreter instance — the C
 * analogue of Lua's `lua_State*`.
 *
 * This is the single most important structural change from today's
 * Python code: SymbolTable.py currently instantiates one
 * `symbolTable = SymbolTable()` at module-import time and every other
 * file does `from SymbolTable import symbolTable`, so there can only
 * ever be one live interpreter per process. A host embedding Hamri —
 * a game running one script per NPC, a server handling concurrent
 * requests — needs to create and destroy as many of these as it wants,
 * fully isolated from one another. SymbolTable is already written as a
 * class, so this is a "stop sharing the instance" refactor more than a
 * rewrite, and it's worth proving out in Python before it's ported.
 * ------------------------------------------------------------------ */
typedef struct HamriState HamriState;

/* Create a fresh, isolated interpreter. Never fails silently — returns
 * NULL only on allocation failure, so a caller can always tell "no
 * interpreter" apart from "interpreter with an error pending" (see
 * hamri_last_error below). */
HamriState *hamri_new(void);

/* Tear down an interpreter and release everything it owns (globals,
 * loaded modules, any values the host hasn't separately retained —
 * see hamri_retain/hamri_release). Safe to call on a state that has a
 * pending error. */
void hamri_free(HamriState *state);

/* ------------------------------------------------------------------ *
 * Resource limits
 * ------------------------------------------------------------------ *
 * The existing 100,000-iteration safety cap on wakati/huku loops
 * (StatementParser.py) is exactly the right instinct for an embedded
 * engine, just hard-coded today. A script run by its own author via
 * main.py and a script handed to an embedding host are very different
 * trust levels — the host should get to decide these, the same way
 * you'd sandbox any third-party plugin.
 *
 * All limits below apply to hamri_run_string/hamri_run_file and any
 * hamri_call made afterwards on this state. 0 means "use the current
 * built-in default" rather than "unlimited" — an embedder has to opt
 * into removing a guard rail, not discover it missing.
 * ------------------------------------------------------------------ */
void hamri_set_max_loop_iterations(HamriState *state, uint64_t max_iterations);
void hamri_set_max_call_depth(HamriState *state, uint32_t max_depth);
void hamri_set_memory_limit_bytes(HamriState *state, size_t max_bytes);

/* ------------------------------------------------------------------ *
 * Running scripts
 * ------------------------------------------------------------------ *
 * Both return 0 on success, non-zero on failure — never terminates the
 * host process. Errors.py today throws/exits on a bad script (Kosa La
 * Anwani, Kosa La Kazi, etc.); for an embedded engine that has to
 * become "set an error on this HamriState and return", with the host
 * deciding what happens next (retry, log, kill just this one script).
 * ------------------------------------------------------------------ */
int hamri_run_string(HamriState *state, const char *source, size_t length);
int hamri_run_file(HamriState *state, const char *path);

/* NULL if the last operation on this state succeeded. Otherwise a
 * human-readable message — for a first pass this can just be the
 * existing Swahili error strings (Kosa La Anwani, Kosa La Fahirisi,
 * ...) verbatim, unless you want a stable machine-readable code too
 * (see HamriErrorCode below) for hosts that want to branch on error
 * kind rather than parse text. */
const char *hamri_last_error(HamriState *state);

typedef enum {
    HAMRI_OK = 0,
    HAMRI_ERR_ANWANI,      /* Kosa La Anwani   - undefined variable */
    HAMRI_ERR_KAZI,        /* Kosa La Kazi     - undefined function/method */
    HAMRI_ERR_MZUNGUKO,    /* Kosa La Mzunguko - loop exceeded its cap */
    HAMRI_ERR_ORODHA,      /* Kosa La Orodha   - not a list */
    HAMRI_ERR_FAHIRISI,    /* Kosa La Fahirisi - list index out of range */
    HAMRI_ERR_DARASA,      /* Kosa La Darasa   - not an object */
    HAMRI_ERR_LETA,        /* Kosa La Leta     - import failed */
    HAMRI_ERR_SYNTAX,      /* parse/lex failure before execution even starts */
    HAMRI_ERR_LIMIT        /* hit a host-configured resource limit */
} HamriErrorCode;

HamriErrorCode hamri_last_error_code(HamriState *state);

/* ------------------------------------------------------------------ *
 * Values crossing the ABI boundary
 * ------------------------------------------------------------------ *
 * A tagged union mirroring what Objects.py already represents
 * dynamically in Python (Int/Str/Bool/Literal, plus lists and darasa
 * instances) — every embedding language will convert its own native
 * types to/from this shape, so it needs to stay small and stable.
 *
 * Strings and lists are reference-counted (see the memory-management
 * note in the .list/.string branches below) rather than GC-traced, on
 * purpose: a host holding a HamriValue needs a simple, explicit answer
 * to "when is this actually freed", and refcounting gives it one
 * (hamri_retain/hamri_release) without requiring the host to register
 * GC roots the way embedding a tracing collector (e.g. embedding
 * Python or V8) typically does. The accepted trade-off is that a
 * reference cycle between two darasa instances can leak — acceptable
 * at this project's current scale, and consistent with the "good
 * enough, not exhaustively rigorous" engineering already used for the
 * loop-iteration cap.
 * ------------------------------------------------------------------ */
typedef enum {
    HAMRI_NIL,
    HAMRI_BOOL,
    HAMRI_INT,
    HAMRI_FLOAT,   /* division already produces these (see
                      ExpressionParser.DivisionExpression) even though
                      Hamri has no float *literal* syntax yet */
    HAMRI_STRING,
    HAMRI_LIST,
    HAMRI_OBJECT,  /* a darasa instance */
} HamriValueType;

typedef struct HamriValue HamriValue;

HamriValueType hamri_value_type(const HamriValue *v);

/* Constructors — all return an owned value with refcount 1. */
HamriValue *hamri_nil(void);
HamriValue *hamri_bool(int b);
HamriValue *hamri_int(int64_t i);
HamriValue *hamri_float(double d);
HamriValue *hamri_string(const char *utf8, size_t length);

/* Lists: built up incrementally so a host doesn't need to know the
 * length up front (mirrors `weka <value> kwenye <list>`). */
HamriValue *hamri_list_new(void);
int         hamri_list_push(HamriValue *list, HamriValue *item);
size_t      hamri_list_len(const HamriValue *list);
HamriValue *hamri_list_get(const HamriValue *list, size_t index); /* borrowed */

/* Accessors — undefined behavior if hamri_value_type() doesn't match;
 * a debug build should assert, a release build can just return a
 * zeroed/empty value rather than crash the host. */
int64_t     hamri_as_int(const HamriValue *v);
double      hamri_as_float(const HamriValue *v);
int         hamri_as_bool(const HamriValue *v);
const char *hamri_as_cstring(const HamriValue *v); /* NUL-terminated, owned by v */

/* Reference counting, since HamriValue lifetimes cross the ABI
 * boundary in both directions (host -> Hamri as arguments, Hamri ->
 * host as return values). */
void hamri_retain(HamriValue *v);
void hamri_release(HamriValue *v);

/* ------------------------------------------------------------------ *
 * Host <-> script bridge
 * ------------------------------------------------------------------ *
 * This is the part that makes "embeddable" actually mean something
 * beyond "runs in-process": a host registers native functions that
 * .ham scripts can call by name, and can call named Hamri functions
 * from its own side and get a value back.
 *
 * Notably, chapa/jaza already have a proto version of this in
 * SymbolTable.py — `input_handler` and `module_loader` are pluggable
 * callables the host (today: the Tkinter Notepad IDE) can override
 * instead of hitting a hardcoded input()/open(). The design here is
 * that same idea generalized: chapa and jaza become the first two
 * built-in consumers of hamri_register_function, rather than special
 * cases in the interpreter.
 * ------------------------------------------------------------------ */
typedef HamriValue *(*HamriNativeFn)(HamriState *state,
                                      HamriValue **args,
                                      size_t argc,
                                      void *userdata);

/* Make `name` callable from Hamri scripts running on this state, e.g.
 * so a game can expose `mnyama_toa_sauti()` to .ham scripts, or so the
 * host can supply its own chapa/jaza backends (matching
 * SymbolTable.console/input_handler/module_loader today). */
int hamri_register_function(HamriState *state,
                             const char *name,
                             HamriNativeFn fn,
                             void *userdata);

/* Call a Hamri-defined function/method by name from host code, e.g.
 * after hamri_run_string has defined `eleza` functions or `darasa`
 * classes the host now wants to drive. Returns an owned HamriValue
 * (release it when done), or NULL on error — check
 * hamri_last_error/hamri_last_error_code. */
HamriValue *hamri_call(HamriState *state,
                        const char *function_name,
                        HamriValue **args,
                        size_t argc);

#ifdef __cplusplus
}
#endif

#endif /* HAMRI_H */
