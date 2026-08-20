# Hamri Roadmap — from teaching interpreter to embeddable production language

This consolidates a working session mapping out where Hamri is today and
what it would take to become (a) a genuinely complete language and (b) an
embeddable runtime usable inside non-Python host programs (games, apps,
services). It's grounded in the actual code as of this session
(`LexicalParser.py`, `ExpressionParser.py`, `StatementParser.py`,
`SymbolTable.py`, `Objects.py`, `Errors.py`) — not a generic language-design
checklist.

Two companion sketches from this same session live alongside this file:
`hamri_api_draft.h` (a draft C embedding API) and
`hamri_error_diagnostics_draft.md` (a before/after redesign of the error
messages). Neither is implemented — both are design references this
roadmap builds on.

## Strategic position

A quick survey of the existing landscape (SWAP, swahili-lang, Yorlang,
Ibolang, HAWKING) found that "programming in a local African language" is
already a small, recognized category — mostly personal or educational
projects, and mostly thin keyword-translation layers sitting on top of an
existing runtime (JS or Python underneath). Hamri already differs in one
real respect: it owns its own semantics end to end (its own lexer, parser,
execution model, and error taxonomy) rather than transpiling onto another
language's engine — which is also the only reason a genuine embeddable C
runtime is even a realistic option for this project.

Given that, and given the explicit goal of being embeddable in non-Python
hosts, the recommended lane is: a small, honest, production-grade scripting
language and runtime, not a race to Python/JS feature parity. Two failure
modes to actively avoid: scope-creeping into "a full general-purpose
language" (a fight this project doesn't need to have), and treating
"translate the keywords" as sufficient differentiation on its own (several
peer projects already occupy exactly that space).

## Tier 1 — core language correctness

Do these before anything else, because later work (a real stdlib, the C
runtime) assumes the language actually behaves like a language.

1. **Real operator precedence.** `ExpressionParser.parse` currently folds
   left to right with no precedence at all — `2 + 3 * 4` evaluates to 20,
   not 14. Rewrite as a precedence-climbing (Pratt) parser. Parenthesized
   grouping, unary minus (negative literals), and chained indexing
   (`matrix[0][1]`) — all currently listed as limitations in the README —
   fall out of this rewrite rather than needing separate patches, since
   they're all really the same underlying gap (the expression grammar
   doesn't nest).

2. **Exception handling.** There is currently no way for a script to
   recover from an error — every one of the seven built-in error kinds
   (`Kosa La Anwani`, `Kosa La Fahirisi`, etc., in `Errors.py`) halts the
   whole script unconditionally via `symbolTable.exit(1)`. Add a
   `try`/`catch`-equivalent construct (something like `jaribu ... kosa ...
   kwisha`) so a script can handle a failed list access or bad import
   without crashing outright. This is arguably the single biggest gap
   between "teaching interpreter" and "production language" — more
   fundamental than raw performance.

3. **A dictionary/map type.** `orodha` is strictly an ordered list; there's
   no key-value type at all. Most real-world data (config, records,
   anything JSON-shaped) is dictionary-shaped, not sequential. Add a
   `kamusi` type with the same ergonomic verbs `orodha` already has
   (append/length/index-by-key).

4. **`break`/`continue` for loops.** Not present anywhere in `wakati`/
   `huku` today — every early-exit or skip-iteration case has to be faked
   with condition flags. Cheap relative to everything else here, high
   ergonomic payoff.

5. **First-class functions.** Functions currently live only in a global
   name table (`symbolTable.table['functions']`) and are called by name —
   they can't be stored in a variable, passed as an argument, or returned
   from another function. This blocks callback/higher-order patterns (a
   custom comparator, a generic "apply to every item" helper). Bigger lift
   than the rest of this tier, but it's what turns "a language with loops
   and lists" into something you can actually structure a program in.

## Tier 2 — maturity and discipline

Needed before "production" is a credible claim, not just a working
interpreter.

- **Automated regression suite for the language itself.** There are two
  `.ham` sample scripts but no golden-file corpus asserting expected
  output. Build this *before* the Tier 1 rewrites land, so each change can
  be made with a safety net rather than by inspection.
- **A formal grammar spec**, independent of the Python implementation
  (even a plain EBNF file) — today the "spec" is the README's prose plus
  whatever the regex lexer happens to accept. Needed so future backends
  (the C VM below) implement a defined language rather than
  reverse-engineering behavior from source.
- **Inheritance and shared/static class state** — already flagged as a
  known limitation in the README; matters once real programs want
  composition between classes.
- **A baseline standard library** — string manipulation (split, trim,
  case), math beyond the four operators, date/time, basic JSON. Currently
  essentially `chapa`/`jaza`/list ops/`aina` and nothing else.
- **A versioning/backward-compatibility policy** — normal to be fluid at
  this stage (the CHANGELOG shows active semantic changes), but worth
  deciding when you commit to semver-style guarantees so an existing
  script doesn't silently break on upgrade.
- **Diagnostic-quality error messages.** See `hamri_error_diagnostics_draft.md`
  for a worked redesign of all seven error types — the short version is
  that every throw site already has the data needed (the actual index, the
  actual type found, etc.) and today discards it in favor of a bare
  translated label. Cheap fix, high value for anyone actually learning
  from the errors.

## Tier 3 — runtime architecture (the embeddability track)

This is the path to a small C runtime usable from non-Python hosts (games,
apps, services with no Python runtime alongside them) — see
`hamri_api_draft.h` for the concrete API shape this aims at.

1. **Remove the global interpreter singleton.** `symbolTable =
   SymbolTable()` is instantiated once at import time and shared via
   `from SymbolTable import symbolTable` everywhere. An embedded host needs
   multiple fully isolated interpreter instances in one process (one script
   per game NPC, one per concurrent request). `SymbolTable` is already a
   class — this is "stop sharing the instance," not a rewrite — and it's
   far cheaper to prove out in Python than to discover broken after
   porting to C.
2. **Fix recursion.** `call_flag`/`call_stack` qualify a function's locals
   by *function name*, not by a unique id per active invocation — a
   recursive or mutually-recursive call likely collides with itself. A
   host's `hamri_call` will re-enter Hamri code, including recursively, so
   this has to be solid before anything else here matters.
3. **Errors as values, not process exits.** Runtime errors already use a
   cooperative `exit_flag` checked throughout `StatementParser`'s execution
   loop (not a hard crash) — but `LexicalParser.read_source`'s file-path
   validation does call `sys.exit(1)` directly, and none of this currently
   surfaces a structured, host-readable error object. Needs to become
   "set an error on this state, return a status code" uniformly, with
   never calling `sys.exit()` from any code path a host might invoke.
4. **A small bytecode VM in C** (Hamri AST → custom bytecode → a compact C
   interpreter loop, à la Bob Nystrom's *clox*) rather than literal
   source-to-C-source transpilation — because the dynamic value model
   (numbers/strings/booleans/lists/objects interchangeably) means a real
   value representation and memory management are needed regardless of
   backend choice, and a self-contained bytecode VM is the best-scoped,
   best-documented option for a solo/small project, and doesn't require a
   C compiler present on the host at script-run time.
5. **Reference counting over tracing GC** for the value model, so a host
   holding a `HamriValue` has a simple, explicit answer for when it's
   freed, rather than needing to register GC roots (a well-known pain
   point when embedding Python or V8). Accepted trade-off: a reference
   cycle between two class instances can leak — reasonable at this
   project's scale.
6. **Host-configurable resource limits.** Generalize the existing
   100,000-iteration loop cap into constructor-time options (max
   iterations, max call depth, a memory ceiling) — an embedded script is
   usually less trusted than one you wrote and ran yourself.
7. **Host↔script bridge.** Generalize the existing `input_handler`/
   `module_loader` pluggable-callback pattern in `SymbolTable.py` into a
   real `hamri_register_function`/`hamri_call` API, so a host can expose
   native functions to `.ham` scripts and call Hamri-defined functions from
   its own side.

Deliberately out of scope: giving Hamri its own concurrency/async model.
The embedding host (the game, the service) already handles concurrent
load — Hamri scripts run as short, sandboxed units inside that. Building
Hamri its own threading model would duplicate a problem the host already
solves, at the expense of the items above.

## Suggested sequencing

1. Tier 1 (language correctness) — cheapest to get right while still in
   Python, and everything downstream assumes it's done.
2. The regression suite from Tier 2, in parallel with or just after Tier 1,
   so the rest of Tier 2 and all of Tier 3 can be validated against it.
3. Tier 3, items 1–3 (singleton, recursion, errors-as-values) — proven out
   in the existing Python interpreter first, since these are the same
   design questions regardless of target language and far cheaper to
   iterate on here.
4. The rest of Tier 2 (grammar spec, inheritance, stdlib, versioning
   policy, error-message redesign) — can happen alongside 3.
5. The C bytecode VM and embedding API (Tier 3, items 4–7) — once the
   semantics above are settled, this becomes largely mechanical porting
   rather than exploratory design.
