# Changelog

## Unreleased

### New language features

- **Inline conditionals: `<value> kama <condition> sivyo <value>`.**
  The same `kama`/`sivyo` words used for an if-block now also work
  inline, as a real conditional expression (like Python's
  `x if cond else y`) usable anywhere a value is expected - an
  assignment, a `chapa`, a function argument, and so on, e.g.
  `hali = "mtu mzima" kama umri inazidi 17 sivyo "kijana"`. Only the
  branch actually taken is ever evaluated. `sivyo` is required; writing
  `kama` without a matching `sivyo` right after it falls back to
  starting an ordinary `kama` block instead, exactly as before - so
  existing scripts that happen to have a bare `kama` following an
  expression on the same line are unaffected. Chains left to right for
  an else-if ladder: `"A" kama x sivyo "B" kama y sivyo "C"`.

### Improvements

- **Runtime errors now quote the source line they happened on** -
  every message is prefixed with `Mstari <n>:`. Previously a statement
  object never carried forward the line number of the token it started
  on, so an error deep in a long script gave no clue where to look.
  `StatementParser.parse()`'s single dispatch loop now stamps every
  parsed statement with `.line` (the 1-indexed line its first token
  came from - `TokenObj.line`, from `LexicalParser`, is 0-indexed);
  every statement-list execution loop (`kwanza`'s own, and every
  `kama`/`wakati`/`huku`/function-call body) sets
  `symbolTable.current_line` from it right before that statement
  actually runs. `Errors._report()` reads that value and prefixes it
  onto every message, so any error raised while a statement is
  executing - including one that bubbles up from deep inside a nested
  expression - is automatically attributed to the right line, with no
  per-expression-node plumbing needed. Two exceptions handled
  explicitly: `leta` (`Kosa La Leta`) fails at parse time, before
  `current_line` would even reflect it, so its own line is passed
  through directly instead; and a runaway loop (`Kosa La Mzunguko`)
  quotes the loop's own header line rather than whatever body statement
  happened to be running when the 100,000-iteration cap hit, since the
  loop itself is what's actually wrong.

## v1.0.3 — language feature expansion + interpreter fixes

This is a large update that brings the interpreter up to date with an
extended, independently-developed fork of Hamri (originally built out
alongside a web Playground). It adds several new language features,
fixes a number of pre-existing bugs, and reconciles `main.py`/`Notepad.py`
with the updated interpreter's calling conventions. Every change below
was verified with a Python test harness exercising the actual
interpreter (`LexicalParser` → `StatementParser` → `.execute()`), plus a
"docs pages" regression check that runs every code sample used to
document the language and confirms it still executes successfully.

### New language features

- **`sivyo`** — an "otherwise" (else) branch for `kama`, e.g.
  `kama ... sivyo ... kwisha`.
- **`wakati`** — a `while` loop: `wakati <condition> ... kwisha`.
- **`huku`** — a `for` loop with two forms: a counted range
  (`huku i kutoka 0 hadi 10`, exclusive end, counts down automatically if
  `hadi` is smaller than `kutoka`) and a for-each over a list
  (`huku item kwenye orodha`).
- **`rudisha`** — a real `return` statement. Properly unwinds through any
  number of nested `kama`/`wakati`/`huku` blocks up to the enclosing
  function/method call boundary (the previous `return_statement`
  attempted this via a `set_return_value` method that didn't actually
  exist anywhere in `SymbolTable`, so it could never have worked).
- **Word-form operators** — `ongeza` (+), `punguza` (-), `mara` (*),
  `gawa` (/), `sawa` (loose `==`), `kabisa`/`hakika` (strict equality,
  checks type *and* value, e.g. `1 kabisa true` is false).
- **Comments** — `# ...` to end of line, quote-aware (a `#` inside a
  string literal is left alone).
- **Lists (`orodha`)** — bracket literals (`[1, 2, 3]`), including
  nested lists (`[[1, 2], [3, 4]]`); indexed read/write (`orodha[i]`,
  `orodha[i] = x`); `weka <value> kwenye <list>` (append); `idadi <list>`
  (length); `ondoa <index> kutoka <list>` (remove by position); and
  `huku item kwenye orodha` for-each iteration.
- **Classes (`darasa`)** — full basic OOP: `darasa Jina ... kwisha`
  containing `eleza` method definitions; `nafsi` as an automatically
  bound "self" (not a reserved keyword — it's just a variable name that
  happens to get bound to the current instance before a method runs);
  a `jenga` method name convention that's auto-invoked as the
  constructor; dot notation for both properties and method calls
  (`mtu1.jina`, `mtu1.sema()`); instances work like any other value
  (can live in a list, be looped over, etc).
- **`leta`** — imports from another file. Whole-class form:
  `leta Mtu, Mnyama kutoka "faili"`. Selective method form (pulls out one
  method as a standalone callable, without importing the whole class):
  `leta salamu kutoka Mtu kutoka "faili"`. A library file's own `kwanza`
  block (if it has one) is never executed as a side effect of importing
  from it.
- **`aina`** — prints what kind of value an expression holds (`namba`,
  `neno`, `boolean`, `orodha`, or the class name for an object). This
  keyword already existed in the original codebase (referenced in the
  sample script in `main.py`) but its implementation was effectively
  dead code — it dispatched to an `Object.return_type()` method that was
  only ever overridden on `Var`, and even then returned a hardcoded,
  malformed string. Reimplemented from scratch as a proper statement
  (`aina <expr>`, matching `chapa`'s own bare-expression style, rather
  than the original's function-call-style `aina(x)`).

### Bug fixes

- **`kama` (if) now actually does something.** Previously `kama` was
  recognized by the lexer but had no corresponding branch in
  `StatementParser.parseStatement` at all — it silently fell through to
  a no-op. There were also no comparison operators (`==`, `!=`, `<`,
  `>`, `<=`, `>=`) defined anywhere, so there was nothing to build a
  condition with even if it had been wired up. Both are now fully
  implemented, including `sivyo`/else branches and nesting inside
  functions/loops/each other.
- **Square brackets were never tokenized.** `divider` was written as
  `r'(\\[|\\]|\(|\))'` — in a raw string that matches a literal
  backslash followed by a bracket character, not the bracket itself, so
  `[`/`]` silently never matched anything. Fixed to `r'(\[|\]|\(|\)|\.)'`
  (the trailing `.` is new too, for property/method access).
- **Token matching used substring search instead of a full match.**
  `find_token_match` used `pattern.findall(...)`, so e.g. a string
  containing a stray `(` could be misclassified as a divider. Switched
  to `pattern.fullmatch(...)`.
- **Boolean literals always evaluated true.** `Bool.evaluate()` did
  `bool(self.token.capitalize())`, which is `True` for *any* non-empty
  string, including the literal text `"false"`. Fixed to compare the
  lowercased string against `'true'`.
- **Self-referential assignment (`i = i + 1`) was broken.**
  `Var.evaluate()`'s assignment path stored the *unevaluated* expression
  object directly, so a variable's own stored value could reference
  itself and recurse forever on read. Now evaluates immediately and
  stores the plain result.
- **Undefined function calls crashed with a raw Python `KeyError`**
  instead of a clean Hamri-level error message. Now reports
  `Kosa La Kazi` and stops the script gracefully.
- **Local variables weren't isolated per function/method call.** Any
  variable assigned inside a function body that wasn't one of its
  declared parameters was stored under a single flat, shared key — so
  once *any* function had assigned to (say) a local named `x`, every
  other variable named `x` anywhere else in the program (including an
  unrelated global) would permanently read back that function's last
  value. Fixed by giving the interpreter a real call stack: locals,
  `huku` loop variables, and `jaza` input variables are now isolated to
  whichever call is actually executing.
- **A "special value" (a function call, list index, `idadi`, or a
  property/method read) could only ever be an entire expression on its
  own**, e.g. `chapa square(2) + 1` or `chapa nafsi.jina + "!"` would
  silently drop everything after the call/property. These now compose
  normally with a trailing operator anywhere they appear — including as
  a `kama`/`wakati` condition, a `huku` bound, or a function-call
  argument. This also covers a second special value appearing *later* in
  the same chain (e.g. `nafsi.jina + " anasema " + nafsi.sauti` — the
  second property read used to silently fall back to printing the raw
  object instead of its value).
- **Running a script with no console/GUI attached (e.g. `main.py`,
  run directly) produced no visible output at all.** `chapa`, `aina`,
  and the run-start/success/failure banners only ever wrote to a
  console object if one was supplied, with no fallback. All of them now
  fall back to a plain `print()` when no console is attached, matching
  how error messages already behaved.

### Desktop IDE (`Notepad.py`)

- **Added a "Run ▶" button** directly in the window, alongside "Clear
  Editor" and "Clear Console" buttons - all three are also available from
  the File menu (Execute / Clear Editor / Clear Console). On macOS, a
  Tk app's menu bar renders in the system menu bar at the top of the
  screen rather than inside the window, and a script launched straight
  from a terminal (rather than a real `.app` bundle) doesn't always
  grab menu focus reliably - so these buttons (plus a `Cmd+R`/`Ctrl+R`
  keyboard shortcut bound directly to the root window) guarantee there's
  always a way to run the script and clear either pane without depending
  on the system menu bar working.
- **Fixed a crash when pasting into the editor with nothing selected.**
  `CustomText._proxy` (used to detect edits for syntax highlighting)
  called straight into the underlying Tcl widget command with no error
  handling. A `<<Paste>>` internally issues `delete sel.first sel.last`
  even when there's no selection, which Tcl reports as an error ("text
  doesn't contain any characters tagged with sel") instead of a no-op -
  uncaught, that exception escaped straight out of Tk's mainloop and
  silently killed the whole application. Now caught and treated as a
  no-op, matching what a real no-op delete should do.

### Repository cleanup

- Removed everything not related to the actual Hamri language/interpreter:
  the old PHP-based website shell (`index.php`, `lib/`, `data/`, `tmp/`),
  the `ui/` folder (an HTML/JS Playground prototype), and local
  dev-environment scaffolding (`.lando.yml`, `.venv/`). The repository is
  now a plain, dependency-free Python codebase: clone it, run `main.py`
  or `Notepad.py`, nothing else required.
- **Still flagged, not yet removed**: `run.py` at the repo root calls
  into `pyscript` (a browser-Python bridge) and isn't used by anything
  else here, and `Logger.py.testcopy` is a leftover test artifact -
  both are untracked and safe to delete whenever convenient; neither
  will get committed by the commands below since they're never `git
  add`-ed.

### Other changes

- `main.py` and `Notepad.py` updated for the new `LexicalParser`
  constructor signature — pass `from_text=True` to parse literal source
  text (as both files now do for in-memory/text-widget content); leaving
  it out (the default) still treats the first argument as a file path,
  same as before.
- `main.py` now also accepts a script path as a command-line argument
  (`python3 main.py path/to/script.ham`) and runs that instead of the
  built-in sample when one is given.
- `LexicalParser.read_source` (the file-path branch, `from_text=False`)
  now checks the path exists and ends in `.ham` first, printing a clear
  message and exiting instead of raising a raw traceback.
- `Notepad.py`'s `__execute()` now resets interpreter state
  (`symbolTable.reset()`) before each run, and passes the console Text
  widget straight into `StatementParser.parse(...)` instead of routing
  through `Console.py`'s `console.use_console(...)` singleton.
  `Console.py` itself is left in place but is no longer imported
  anywhere — same treatment as `Stack.py`/`Symbols.py`, which were
  already unused, unimported prototypes before this change (a generic
  stack class and a second, parallel `SymbolTable`/`Scope`
  implementation, neither ever wired into anything).
- Added `.gitignore` for local dev-environment/cache files that were
  previously untracked-but-present locally (`data/`, `lib/`, `tmp/`,
  `.ddev/`, `.lando.yml`, `index.php`, `.htaccess`, `.DS_Store`) and the
  stale duplicate `modules/` folder (an older, pre-feature copy of the
  same interpreter files now at the repo root).

### Known pre-existing limitations (documented, not fixed here)

- No parenthesized grouping in expressions, no decimal or negative
  number literals, no inheritance or static/shared class variables, no
  chained list indexing (`matrix[0][1]` — index into an intermediate
  variable instead), and `ondoa` removes by position, not by value.

### Desktop IDE follow-up fixes

Two rough edges called out (but deliberately left unfixed) earlier in
this same release are now actually fixed too, along with a related
lexer bug the highlighting fix surfaced along the way.

- **`jaza` no longer silently blocks on the terminal when run through
  the desktop Notepad.** Previously `InputStatement.execute()` always
  called Python's built-in `input()` directly, so a script using `jaza`
  and run via `Notepad.py` would appear to hang — it was actually
  waiting on stdin in whatever terminal launched the IDE, easy to miss
  entirely. `SymbolTable` now has a pluggable `input_handler` hook
  (mirroring the existing `module_loader` hook `leta` uses) - `jaza`
  calls `symbolTable.read_input(prompt)`, which uses the hook if one's
  set, and falls back to plain `input()` otherwise (so `main.py` is
  unaffected). `Notepad.py` wires this to a proper
  `tkinter.simpledialog.askstring` dialog.
- **Fixed `Notepad.py`'s live syntax highlighting (`__generateTags`),**
  previously entirely non-functional: it compared `token.type` — a
  *method* on `TokenObj`, not the token's type string (`token.token_type`
  is the actual attribute) — against capitalized category names
  (`"Keyword"`, `"Identifier"`, etc.) that don't match any of the
  lexer's real, lowercase token types (`keyword`, `variable`, `operator`,
  `boolean`, `integer`, `string`) at all, so no branch ever matched and
  no token was ever colored. It also passed raw character offsets
  straight to `tag_add()`, which expects Tkinter's own `"line.column"`
  index strings, not plain offsets. Both are now fixed: correct type
  comparison, correct index conversion, and tags are re-applied (not
  recreated) on every edit.
- **Fixed a related lexer bug the above surfaced**: a `string` token's
  `value` has its surrounding quote characters stripped off (so the
  interpreter sees the bare text, not the quotes) — but `TokenObj`
  computed its length from that same already-stripped value, so it came
  out 2 characters short of the token's actual span in the source. This
  didn't affect execution (nothing on the interpretation path reads a
  token's length or span), but it meant highlighting a string literal
  stopped 2 characters early. `TokenObj` now takes an explicit
  `raw_length` (the un-stripped match length), so `.size()`/`.span()`
  reflect the real source position for every token type.
- **Added a light/dark background toggle for the code editor.** A new
  "Dark Mode" toolbar button (mirrored by a matching View menu, for the
  same reason the Run/Clear buttons exist) switches the editor between
  its original light background and a dark one. Syntax highlighting
  colors switch with it - `Token.Identifier` was previously hardcoded to
  plain black, which would have been invisible against a dark
  background, so it (and every other token color) now comes from a
  small per-theme color table instead. Scoped to the editor only - the
  console pane already has its own fixed black background and isn't
  affected.

## v1.0.2 — initial commit

The starting point this changelog's v1.0.3 entry above is measured
against: the original interpreter (`LexicalParser` → `StatementParser` →
`Objects`/`ExpressionParser`/`SymbolTable`/`Errors`), `main.py`, and the
`Notepad.py` desktop IDE, supporting `kwanza`/`kwisha`, `chapa`, `jaza`,
`eleza`, and a partially-wired `kama`/`aina`, tagged retroactively as a
version marker for the baseline this project started from.
