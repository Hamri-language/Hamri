# Hamri

Hamri is a small, Swahili-keyword programming language, written in pure
Python for ease of readability by contributors. We are however
transpiling the code base to C/C++ soon.

This README is a full language reference in addition to run
instructions — everything below runs directly with the interpreter in
this repo, no external dependencies beyond the Python standard library
(Tkinter is only needed for the optional desktop IDE).

## Running Hamri

1. Clone the repository:

        git clone https://github.com/Hamri-language/Hamri.git

2. Run the built-in demo script, or your own `.ham` file, straight from
   the console:

        python3 main.py                       # runs the sample bundled in main.py
        python3 main.py path/to/script.ham    # runs a script file of your own

3. Or use the provided desktop IDE (Tkinter):

        python3 Notepad.py

   Write or open a script in the text area, then use the "Run ▶" button
   (or `Cmd+R` / `Ctrl+R`, or File > Execute) to run it — output appears
   in the console pane below. "Clear Editor" and "Clear Console" (also
   in the File menu) reset either pane. A line-number gutter runs down
   the left edge of the editor, and a status bar just below it shows
   the text cursor's current line and column — handy for matching up
   an error message's `Mstari <n>, Nafasi <m>:` prefix with the exact
   spot in your script.

   Tkinter isn't part of the Python standard install on every platform.
   If `python3 Notepad.py` fails with `ModuleNotFoundError: No module
   named '_tkinter'`, install your platform's Tk bindings (e.g. on
   macOS with Homebrew Python: `brew install python-tk@<your version>`).

See CHANGELOG.md for the full history of language features and fixes on
top of the original implementation.

## Getting started

Every Hamri program needs a `kwanza ... kwisha` block — this is the
required entry point. Code written outside it (such as function or
class definitions) is parsed but never runs on its own; only what's
inside `kwanza` executes.

```
kwanza
    chapa "Habari, Dunia!"
kwisha
```

## Keywords

Every reserved word in Hamri is Swahili. Some are structural (they mark
the start or end of a block); a few are word forms of an operator, so a
condition or assignment can read like a sentence instead of leaning on
symbols.

| Keyword | Swahili meaning | What it does in Hamri |
|---|---|---|
| `kwanza` | first | Opens the required main block — only code inside `kwanza ... kwisha` runs automatically |
| `kwisha` | finished, the end | Closes any open block: `kwanza`, `kama`, `eleza`, `wakati`, `huku`, or `darasa` |
| `chapa` | print, stamp | Prints a value to the console |
| `jaza` | fill | Prompts for input (via the terminal) and stores it into a variable |
| `eleza` | explain | Defines a function or class method |
| `kama` | if, like | Starts a conditional block |
| `sivyo` | otherwise, not so | Else branch of a `kama` block |
| `wakati` | while, time | Starts a loop that repeats while its condition is true |
| `huku` | during, while | Starts a counted for-loop (`huku i kutoka 0 hadi 5`) or a for-each loop (`huku item kwenye orodha`) |
| `kutoka` | from | Marks the starting value in a `huku` range, or the source file in a `leta` import |
| `hadi` | to, until | Marks the (exclusive) ending value in a `huku` range |
| `rudisha` | return, give back | Returns a value to the caller and exits the function immediately |
| `ni` | is | Word form of `=` — e.g. `umri ni 20` |
| `inazidi` | exceeds | Word form of `>` |
| `haizidi` | does not exceed | Word form of `<` |
| `sawa na` | equal to | Word form of `==` (loose equality) |
| `kabisa` / `hakika` | completely / certainly | Strict equality — true only if both value *and* type match |
| `ongeza` | add, increase | Word form of `+` |
| `punguza` | reduce, decrease | Word form of `-` |
| `mara` | times | Word form of `*` |
| `gawa` | divide, share | Word form of `/` |
| `weka` | put, place | Appends a value to a list — `weka <value> kwenye <list>` |
| `kwenye` | into, at | Marks the target list for `weka`, or the list being looped over in a for-each `huku` |
| `idadi` | count, number | Length of a list — `n = idadi orodha` |
| `ondoa` | remove | Removes an item from a list by position — `ondoa <index> kutoka <list>` |
| `futa` | erase, delete | Removes an item from a list by value — `futa <value> kutoka <list>` |
| `darasa` | class | Defines a class — `darasa Jina ... kwisha`, optionally `darasa Jina inarithi Mzazi ... kwisha` to inherit from another class |
| `inarithi` | inherit | Marks the parent class a `darasa` extends — `darasa Mtoto inarithi Mzazi` |
| `msingi` | base | Declares a shared/static class variable inside a `darasa` body — `msingi jina = <value>` |
| `leta` | bring | Imports a class, or one of its methods, from another file |
| `aina` | kind, type | Prints what kind of value an expression holds — `aina umri` |
| `tumia` | use | Activates a built-in module — `tumia Hesabu` |
| `Hesabu` | (arithmetic) | Hamri's built-in math module — see [Built-in modules](#built-in-modules-tumia) |

`nafsi` ("self", used inside a method to refer to the current object) is
**not** a reserved keyword the way the others above are — it's an
ordinary variable name that Hamri automatically binds to the current
instance before a method runs. See [Classes](#classes-darasa) below.

Word operators and symbol operators can be mixed freely in the same
script — `umri ni 20` and `umri = 20` do exactly the same thing.

> Every word in the table above is reserved everywhere in a script, not
> just where you'd expect it — so a variable or property that happens
> to share a name with one of the newer additions (`tumia`, `Hesabu`,
> `futa`, `inarithi`, `msingi`) stops working as a plain identifier.
> Keyword matching is case-sensitive, so a lowercase `hesabu` (as
> opposed to capitalized `Hesabu`) is unaffected — but a variable
> literally named `futa`, `inarithi`, `msingi`, or `tumia` will need
> renaming.

## Numbers

Whole numbers (`10`, `-3`) and decimals (`3.14`, `-0.5`) can both be
written directly as literals. A leading `-` always means negation, not
subtraction, when it sits where a value is expected — `x = -5`,
`chapa -3.14`, and `chapa 10 - -5` (ten minus negative five, i.e. `15`)
all read the way you'd expect. `--5` (a double negative) is also valid
and evaluates to `5`.

```
kwanza
    chapa 3.14
    chapa -5
    x = -2.5
    chapa x
kwisha
```

Parentheses `(...)` group part of an expression so it's evaluated as
one unit before anything outside the parentheses touches it — the one
way to override Hamri's own left-to-right evaluation order (see
[Operators](#operators) below for what that means without grouping):

```
kwanza
    chapa (2 + 3) * 4    # 20 - the group is evaluated first
    chapa 2 + (3 * 4)    # 14 - forces normal math order instead
kwisha
```

## Variables & types

Assign with `=`. There's no keyword needed to declare a variable — just
assign it.

```
kwanza
    name = "Amara"
    age = 25
    is_member = true
kwisha
```

| Type | Example | Notes |
|---|---|---|
| Text | `"hello"` or `'hello'` | Double or single quotes |
| Whole number | `10`, `-10` | See [Numbers](#numbers) below for negative literals |
| Decimal | `3.14`, `-0.5` | See [Numbers](#numbers) below |
| Boolean | `true` / `false` | Lowercase only |

Check what kind of value something is with `aina` ("kind/type") —
prints `namba` (number), `neno` (text), `boolean`, `orodha` (list), or
the class name itself for an object:

```
kwanza
    age = 25
    aina age

    name = "Amara"
    aina name
kwisha
```

## Printing: `chapa`

`chapa` prints a value or expression, including numbers, text,
booleans, and variables.

```
kwanza
    chapa "Hello world"
    x = 5
    chapa x
    chapa "x is: " + x
kwisha
```

## Input: `jaza`

`jaza` asks the user for input and stores the result in a variable.
Separate the prompt text and the variable name with a comma. When run
via `main.py` (console mode), the prompt appears as a normal terminal
input; when run through the desktop Notepad IDE, it pops up a dialog
box in the GUI itself instead.

```
kwanza
    jaza "Enter your name: ", jina
    chapa "Habari, " + jina
kwisha
```

> If the typed input is a plain whole number (e.g. `25`, or a negative
> like `-3`), it's automatically stored as a number so it can be used
> directly in comparisons and arithmetic. Anything else — including a
> decimal like `3.5` — is stored as text.

## Conditionals: `kama`

Runs a block only if the condition is true. Add `sivyo` ("otherwise")
for what should happen when it's false — still just one `kwisha` closes
the whole thing.

```
kwanza
    umri = 20
    kama umri > 17
        chapa "Mtu mzima (adult)"
    sivyo
        chapa "Kijana (minor)"
    kwisha
kwisha
```

| Operator | Word form | Meaning |
|---|---|---|
| `==` | | equal to |
| `!=` | | not equal to |
| `<` | `haizidi` | less than |
| `>` | `inazidi` | greater than |
| `<=` | | less than or equal to |
| `>=` | | greater than or equal to |
| | `kabisa` / `hakika` | strict equality — value *and* type must match |

`kama` blocks can be nested inside functions, inside loops, and inside
each other.

## Inline conditionals: `kama ... sivyo`

The same `kama`/`sivyo` words also work inline, as a value rather than
a whole block — pick one of two values based on a condition, right
inside an assignment, a `chapa`, or anywhere else a value is expected.
It reads left to right: `<value if true> kama <condition> sivyo <value
if false>`.

```
kwanza
    umri = 20
    hali = "mtu mzima" kama umri inazidi 17 sivyo "kijana"
    chapa hali
kwisha
```

Only the branch actually picked is ever evaluated, so it's safe to
reach for something that would otherwise error out (like an unset
property) on the branch that never runs. `sivyo` is required — unlike
the block form, there's no "no-op if false" version of this. Chain
several together for an else-if ladder:

```
kwanza
    alama = 72
    daraja = "A" kama alama inazidi 89 sivyo "B" kama alama inazidi 79 sivyo "C"
    chapa daraja
kwisha
```

> Writing `kama` without a matching `sivyo` right after it isn't
> treated as an inline conditional at all — it falls back to starting
> a brand new `kama` block instead, same as if it were on its own line.

## Loops: `wakati`

`wakati` ("while") repeats its block for as long as the condition stays
true, re-checking it before every pass. Remember to change something
inside the loop that will eventually make the condition false.

```
kwanza
    i = 0
    wakati i < 5
        chapa i
        i = i + 1
    kwisha
kwisha
```

> If a loop's condition never becomes false, it stops itself
> automatically after 100,000 passes with a `Kosa La Mzunguko` error,
> rather than hanging forever. If you see that error, double-check that
> your loop is actually updating the variable the condition depends on.

## For loops: `huku`

`huku` ("during/while") counts a variable through a range, no
parentheses needed: `huku <var> kutoka <start> hadi <end>`. `kutoka`
means "from" and `hadi` means "to/until" — the loop variable is created
for you and runs from `start` up to, but not including, `end` (just
like Python's `range()`).

```
kwanza
    huku i kutoka 0 hadi 5
        chapa i
    kwisha
kwisha
```

If `end` is smaller than `start`, `huku` counts down instead:

```
kwanza
    huku i kutoka 5 hadi 0
        chapa i
    kwisha
kwisha
```

The `start` and `end` bounds can be any expression, not just literal
numbers — variables, arithmetic, or a mix. `huku` shares the same
100,000-iteration safety cap (`Kosa La Mzunguko`) as `wakati`, and can
be nested inside `kama`, `wakati`, functions, or other `huku` loops.

## Functions: `eleza`

Define a function with `eleza name(params) ... kwisha`. Parentheses are
required even with no parameters. Functions can be defined either
inside or outside the `kwanza` block; call them with
`name(arguments)`.

```
eleza add(a, b)
    chapa a + b
kwisha

kwanza
    add(3, 4)
kwisha
```

> Calling a function that was never defined with `eleza` produces a
> clear error (`Kosa La Kazi`) rather than crashing.

## Returning values: `rudisha`

`rudisha` ("return") hands a value back to whatever called the function
and stops the function immediately — nothing after it in that function
runs, even if it's nested inside a `kama`, `wakati`, or `huku`. A bare
`rudisha` with no value is useful on its own as an early exit (a guard
clause).

```
eleza square(x)
    rudisha x mara x
kwisha

eleza safe_divide(a, b)
    kama b sawa na 0
        chapa "Can't divide by zero"
        rudisha
    kwisha
    rudisha a gawa b
kwisha

kwanza
    result = square(5)
    chapa result

    chapa safe_divide(10, 2)
kwisha
```

> A function's return value can be captured with `x = name(args)`,
> printed directly with `chapa name(args)`, or combined inline with an
> operator (`chapa square(2) + 1`) anywhere in a larger expression. If a
> function never hits a `rudisha`, calling it this way gives back
> nothing meaningful.

## Operators

| Operator | Word form | Meaning | Notes |
|---|---|---|---|
| `=` | `ni` | Assignment | `umri = 20` and `umri ni 20` are identical |
| `+` | `ongeza` | Addition, or joining text | `"age: " + 5` works — text and numbers are joined automatically |
| `-` | `punguza` | Subtraction | |
| `*` | `mara` | Multiplication | |
| `/` | `gawa` | Division | Returns a whole number when it divides evenly (`10/2` → `5`), otherwise a decimal (`7/2` → `3.5`) |
| `==` | `sawa na` | Loose equality | `1 == true` is true — numbers and booleans compare loosely |
| | `kabisa` / `hakika` | Strict equality | True only if value *and* type match — `1 kabisa true` is false, unlike `==`/`sawa na` |

> Expressions are evaluated strictly left to right, with no operator
> precedence — `2 + 3 * 4` is `(2 + 3) * 4` (`20`), not the `14` you'd
> get from ordinary math notation. Use parentheses (see
> [Numbers](#numbers) above) to force a different order:
> `2 + (3 * 4)` gives `14`.

## Comments

Anything after a `#` on a line is ignored — use it for notes to
yourself or to explain what the code does. A `#` inside a text string
is left alone.

```
kwanza
    # this line is ignored entirely
    chapa "Price: #1"  # this trailing note is stripped, the string isn't
kwisha
```

## Lists: `orodha`

A list holds an ordered collection of values, written with square
brackets and commas: `[1, 2, 3]`. Items can be any mix of text,
numbers, or booleans, and are numbered starting at `0`.

```
kwanza
    orodha = [10, 20, 30]
    chapa orodha
    chapa orodha[0]
kwisha
```

Update an existing item in place by assigning to its position:

```
kwanza
    orodha = [10, 20, 30]
    orodha[1] = 99
    chapa orodha
kwisha
```

Add an item to the end of a list with `weka <value> kwenye <list>`
("put value into list"), and find out how many items a list has with
`idadi <list>` ("count/number of list"):

```
kwanza
    orodha = [10, 20, 30]
    weka 40 kwenye orodha
    chapa idadi orodha
kwisha
```

Loop over every item in a list directly with
`huku <var> kwenye <list>` ("for var in list") — no index bookkeeping
needed. This is a separate form of `huku` from the counted
`kutoka`/`hadi` range covered earlier; `idadi` also pairs naturally with
the counted form if you need the index itself:

```
kwanza
    orodha = ["chai", "kahawa", "maji"]

    huku kinywaji kwenye orodha
        chapa kinywaji
    kwisha

    huku i kutoka 0 hadi idadi orodha
        chapa orodha[i]
    kwisha
kwisha
```

Remove an item by position with `ondoa <i> kutoka <list>` ("remove i
from list") — the remaining items shift down to fill the gap:

```
kwanza
    orodha = [10, 20, 30]
    ondoa 1 kutoka orodha
    chapa orodha
kwisha
```

To remove an item by its *value* instead of its position — wherever it
happens to be in the list — use `futa <value> kutoka <list>` ("erase
value from list"). It removes the first matching element, the same way
Python's `list.remove()` does, and reports `Kosa La Futa` if nothing in
the list matches:

```
kwanza
    orodha = ["chai", "kahawa", "maji", "kahawa"]
    futa "kahawa" kutoka orodha
    chapa orodha    # [chai, maji, kahawa] - only the first "kahawa" is removed
kwisha
```

Lists can nest — an item inside `[...]` can be another list literal, to
any depth — and a nested list can be indexed into directly, one level
per `[...]`, without an intermediate variable:

```
kwanza
    matrix = [[1, 2], [3, 4]]
    chapa matrix
    chapa matrix[0][1]      # 2 - reaches straight into the nested list

    matrix[1][0] = 99       # chained indexing works for assignment too
    chapa matrix
kwisha
```

> A list variable can also come from a function's return value
> (`orodha = make_list()`) or be built from other variables
> (`[a, b, c]`), and an element itself can now be any expression Hamri
> already supports — a negative literal, a parenthesized group, a
> property/method/index read, and so on (`[1, -2, (1 + 1), mtu1.jina]`).
> Indexing, appending, removing, and length all check that the variable
> is actually a list first, and that an index is in range, reporting
> `Kosa La Orodha` or `Kosa La Fahirisi` instead of crashing.

## Classes: `darasa`

`darasa` ("class") groups methods (functions) that belong together and
can be instantiated as objects. Properties are usually set on an
instance from inside a method, using `nafsi` ("self"), which Hamri
automatically binds to the current object every time a method runs.

```
darasa Mtu
    eleza jenga(jina)
        nafsi.jina = jina
    kwisha

    eleza salamu()
        chapa "Habari, mimi ni " + nafsi.jina
    kwisha
kwisha

kwanza
    mtu1 = Mtu("Amara")
    mtu1.salamu()
kwisha
```

A class body can also declare a property by name alone, with no
assignment, so it exists (defaulting to nothing set — reading it prints
as `None` until something assigns it) even before a constructor ever
runs:

```
darasa Mtu
    umri

    eleza jenga(jina)
        nafsi.jina = jina
    kwisha
kwisha

kwanza
    mtu1 = Mtu("Amara")
    chapa mtu1.umri    # None - declared, but never assigned
    mtu1.umri = 30
    chapa mtu1.umri
kwisha
```

A method named `jenga` ("build") is treated as the constructor — if a
class defines one, it runs automatically as soon as the class is
instantiated (`Mtu("Amara")`), with whatever arguments were passed to
the call. A class doesn't need a `jenga` at all; without one, `Mtu()`
just creates a bare instance with no properties set yet.

From outside the class, dot notation reads a property or calls a
method on an instance. Each instance keeps its own separate set of
properties — two objects made from the same class never share state. A
method can also call another method on the same object via `nafsi`:

```
darasa Counter
    eleza jenga()
        nafsi.count = 0
    kwisha

    eleza increment()
        nafsi.count = nafsi.count ongeza 1
        rudisha nafsi.count
    kwisha
kwisha

kwanza
    counter1 = Counter()
    chapa counter1.increment()
    chapa counter1.increment()
    chapa counter1.count
kwisha
```

Instances work like any other value — they can be stored in a list,
including a list built directly from constructor calls, and looped over
with `huku ... kwenye`:

```
darasa Mnyama
    eleza jenga(jina, sauti)
        nafsi.jina = jina
        nafsi.sauti = sauti
    kwisha

    eleza tangaza()
        rudisha nafsi.jina + " anasema " + nafsi.sauti
    kwisha
kwisha

kwanza
    wanyama = [Mnyama("Simba", "Ngurumo"), Mnyama("Paka", "Meow")]
    huku mnyama kwenye wanyama
        chapa mnyama.tangaza()
    kwisha
kwisha
```

> Property reads and method calls can be combined inline with an
> operator, just like a function call or an indexed read —
> `chapa "Habari, " + nafsi.jina` and
> `nafsi.count = nafsi.count ongeza 1` both work as written, no
> intermediate variable needed.

### Inheritance: `inarithi`

A class can extend another with `inarithi` ("inherit") —
`darasa Mtoto inarithi Mzazi ... kwisha`. `Mtoto` gets every method,
`msingi` variable, and bare property declaration `Mzazi` has, for free;
it only needs to define `eleza`/`msingi`/properties of its own for
whatever it wants to override or add:

```
darasa Mnyama
    eleza jenga(jina)
        nafsi.jina = jina
    kwisha

    eleza tangaza()
        rudisha nafsi.jina + " anasema " + nafsi.sauti
    kwisha
kwisha

darasa Mbwa inarithi Mnyama
    eleza jenga(jina)
        nafsi.jina = jina
        nafsi.sauti = "Woof"
    kwisha
kwisha

kwanza
    rex = Mbwa("Rex")
    chapa rex.tangaza()    # inherited from Mnyama - Mbwa never defines tangaza itself
kwisha
```

A subclass that defines its own `jenga` overrides the parent's
constructor completely; one that doesn't define `jenga` at all
transparently uses the parent's instead, the same way any other
inherited method works.

### Shared/static class variables: `msingi`

`msingi` ("base") declares a variable that belongs to the *class*
itself, not to any one instance — every object made from the class (and
every subclass, unless it declares its own `msingi` variable of the same
name) sees the same single value. Reach it from outside `nafsi`, with
the class's own name:

```
darasa Mnyama
    msingi idadi_ya_wanyama = 0

    eleza jenga(jina)
        nafsi.jina = jina
        Mnyama.idadi_ya_wanyama = Mnyama.idadi_ya_wanyama + 1
    kwisha
kwisha

kwanza
    simba = Mnyama("Simba")
    paka = Mnyama("Paka")
    chapa Mnyama.idadi_ya_wanyama    # 2 - shared across both instances
kwisha
```

## Modules: `leta`

`leta` ("bring") imports a class — or one specific method of a class —
from another `.ham` file on disk.

```
# mtu.ham
darasa Mtu
    eleza jenga(jina)
        nafsi.jina = jina
    kwisha

    eleza salamu()
        rudisha "Habari, mimi ni " + nafsi.jina
    kwisha

    eleza mraba(n)
        rudisha n mara n
    kwisha
kwisha
```

From another file, bring the whole class in with `kutoka` ("from"):

```
leta Mtu kutoka "mtu.ham"

kwanza
    mtu1 = Mtu("Amara")
    chapa mtu1.salamu()
kwisha
```

Import more than one class from the same file in a single statement
with a comma list: `leta Mtu, Mnyama kutoka "mtu.ham"`.

You can also import just one specific method of a class, without
pulling in the whole thing, by naming the class as well:
`leta <method> kutoka <Class> kutoka "<faili>"`. This works standalone
(no instance needed) as long as the method never reaches for `nafsi`:

```
leta mraba kutoka Mtu kutoka "mtu.ham"

kwanza
    chapa mraba(5)
kwisha
```

> A method imported this way still has access to its own parameters as
> normal, but has no instance to bind `nafsi` to — calling it if its
> body still uses `nafsi.anything` fails with `Kosa La Anwani`, the
> same as referencing any other undefined variable. Also worth knowing:
> importing a file that happens to have its own `kwanza` block (e.g.
> one written to be run standalone too) never executes that block as a
> side effect — only its `darasa`/`eleza` definitions come along.
> There's no renaming on import (a class or method always keeps the
> name it was defined with) and no per-scope isolation — once imported,
> a class is available everywhere in the rest of the file, not just
> after the `leta` line.

## Built-in modules: `tumia`

`tumia` ("use") activates one of Hamri's built-in modules — functionality
that ships with the interpreter itself, reached with the same dot
notation as an object's own methods, but without writing or importing
any `.ham` file for it. Write `tumia <ModuleName>` once (typically near
the top of your `kwanza` block) before using anything from that module;
reaching for a module's member before activating it fails with
`Kosa La Tumia`.

Hamri ships one built-in module so far — `Hesabu` ("arithmetic"), a
small math toolbox:

| Function | Equivalent | Meaning |
|---|---|---|
| `Hesabu.kamili(x)` | `abs(x)` | Absolute value |
| `Hesabu.kubwa(a, b)` | `max(a, b)` | The larger of two values |
| `Hesabu.ndogo(a, b)` | `min(a, b)` | The smaller of two values |
| `Hesabu.mzizi(x)` | `math.sqrt(x)` | Square root |
| `Hesabu.juu(x)` | `math.ceil(x)` | Round up |
| `Hesabu.chini(x)` | `math.floor(x)` | Round down |
| `Hesabu.kadirisha(x)` | `round(x)` | Round to the nearest whole number |

```
kwanza
    tumia Hesabu

    chapa Hesabu.kamili(-5)        # 5
    chapa Hesabu.kubwa(3, 7)       # 7
    chapa Hesabu.mzizi(16)         # 4.0
    chapa Hesabu.juu(4.3)          # 5
    chapa Hesabu.chini(4.7)        # 4
    chapa Hesabu.kadirisha(4.5)    # 4 - banker's rounding, same as Python's round()
kwisha
```

> A call with an argument the underlying function can't handle (e.g.
> `Hesabu.mzizi(-1)`, a negative square root) reports `Kosa La Hoja`
> instead of crashing. `Hesabu` doesn't cover every one of Python's
> math functions yet (no constants like π, no trigonometry, no
> logarithms/exponents, no factorial) — just this starting set.

## Error messages

Hamri reports runtime errors in Swahili and stops the script (exit code
1) rather than continuing silently. Every message is prefixed with
`Mstari <n>, Nafasi <m>:` ("Line n, Position m") — the source line the
failing statement started on, and how many characters into that line
it starts — so you don't have to guess which part of a long script (or
which of several statements crammed onto one line) actually went
wrong:

```
Mstari 4, Nafasi 5: Kosa La Anwani: Jina hili {umri} halijulikani
```

The quoted position is always the *statement* that was running when
the error happened — the `chapa`/`kama`/`wakati`/function-call itself,
not some internal detail of how the expression inside it was built.
That's true even when the failure comes from deep inside a nested
expression (e.g. an undefined property read as part of a larger
`chapa`), from inside a loop or function body, or from a `leta` import
that couldn't find its file (reported at parse time, before the script
even starts running, since `leta` has no runtime step of its own). A
runaway `wakati`/`huku` loop (`Kosa La Mzunguko`) is the one exception
worth calling out — it quotes the loop's own header position, not
whatever body statement happened to be running on the iteration that
tripped the 100,000-iteration cap, since the loop itself (not that
particular statement) is what's actually wrong.

| Message | Cause |
|---|---|
| `Kosa La Anwani` (Address Error) | Referenced a variable that was never assigned |
| `Kosa La Kazi` (Function Error) | Called a function that was never defined with `eleza`, or a method that doesn't exist on a class |
| `Kosa La Mzunguko` (Loop Error) | A `wakati`/`huku` loop ran past 100,000 iterations without its condition becoming false |
| `Kosa La Orodha` (List Error) | Tried to index, update, append to, loop over, or measure the length of a variable that isn't a list |
| `Kosa La Fahirisi` (Index Error) | Used a list position that's negative or past the end of the list |
| `Kosa La Darasa` (Class Error) | Tried to read a property or call a method on a variable that isn't an object (an instance of a `darasa`) |
| `Kosa La Leta` (Import Error) | `leta` couldn't find the file, or the requested class/method doesn't exist in it |
| `Kosa La Tumia` (Module-Not-In-Use Error) | Reached for a built-in module's member before activating it with `tumia` |
| `Kosa La Hoja` (Argument Error) | A built-in module call was given an argument it can't work with (e.g. a negative square root) |
| `Kosa La Futa` (Value Error) | `futa <value> kutoka <list>` didn't find a matching value anywhere in the list |

## Current limitations

Hamri is a young, evolving language. A few things it doesn't support
yet:

| Limitation | Details |
|---|---|
| No operator precedence | Expressions are evaluated strictly left to right (`2 + 3 * 4` is `20`, not `14`) — use parentheses to force a different order, see [Numbers](#numbers). |
| No renaming or scoping on `leta` | An imported class/method always keeps its original name, and becomes available everywhere in the file once imported. |
| `Hesabu` covers only a starting set of functions | No π/e constants, trigonometry, logarithms/exponents, or factorial yet — see [Built-in modules](#built-in-modules-tumia). |
| No explicit "call the parent's version" (`super`) | A subclass method that overrides a parent's can't explicitly call the overridden version — only *not* defining an override falls back to the parent's. |
| New reserved keywords can collide with existing identifiers | `tumia`, `Hesabu`, `futa`, `inarithi`, and `msingi` are all reserved now — a variable or property already using one of those exact names (case-sensitively) needs renaming. |

## Full example

Putting it all together — a small program that greets the user,
classifies their age, counts down, and returns a value from a function:

```
eleza greet(name)
    chapa "Habari, " + name
kwisha

eleza square(x)
    rudisha x mara x
kwisha

kwanza
    jaza "Enter your name: ", jina
    jaza "Enter your age: ", umri

    greet(jina)

    kama umri > 17
        chapa "Wewe ni mtu mzima (you are an adult)"
    sivyo
        chapa "Wewe ni kijana (you are a minor)"
    kwisha

    # count down from 3
    hesabu = 3
    wakati hesabu > 0
        chapa hesabu
        hesabu = hesabu - 1
    kwisha

    # then count back up
    huku n kutoka 1 hadi 4
        chapa n
    kwisha

    chapa square(4)
kwisha
```

The code is properly commented and annotated. Happy coding!

## Follow us on our socials

Instagram — https://www.instagram.com/hamri.lang

Facebook — https://www.facebook.com/hamri.lang

LinkedIn — https://www.linkedin.com/company/hamri-foundation

Email — hello@hamri.org
