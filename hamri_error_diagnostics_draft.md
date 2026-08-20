# Diagnostic-first error messages — a redesign sketch

This is a proposal, not an implementation — nothing in `Errors.py` has been
changed. It's a worked example of the "errors that teach, not just
translate" idea, using the real error types and call sites already in
`Errors.py` / `StatementParser.py`, so it's concrete rather than abstract.

## What's wrong with the current messages

Every exception in `Errors.py` follows the same shape: a fixed Swahili
sentence, the bare name of whatever went wrong, and a bracketed English
gloss bolted on afterward — e.g.

> `Kosa La Fahirisi: fahirisi hii katika {orodha} haipo (index out of range)`

That's a translated label, not an explanation. A learner reading it can't
tell *which* index they tried, *what the list actually contains*, or
*whether they were off by one, way out of range, or reaching for the wrong
variable entirely* — three different bugs with three different fixes, all
producing the identical message today.

The good news: at every throw site, the interpreter already *has* the data
needed to say more. Look at `ListIndexExpression` in `StatementParser.py`
(the code behind `orodha[i]`):

```python
if not isinstance(index,int) or index < 0 or index >= len(lst):
    Error.throwException('fahirisi',self.list_name)   # <- lst and index are right here, and get thrown away
    return None
```

`lst` (the actual list) and `index` (what was attempted) are sitting in
scope at the exact moment the error fires — the current code just doesn't
pass them along. That makes this a cheap win: the fix isn't "add new
tracking machinery," it's "stop discarding data you already computed."

## The design principle

Every message should answer three things, in order, using the values
actually involved:

1. **What happened** — concretely, with the real index/name/value, not a
   category label.
2. **Why** — what state made it invalid (too high? negative? the list was
   empty? wrong type entirely?), since each has a different likely cause.
3. **What to check** — a next step, not just a diagnosis.

## Before / after, across all seven error types

| Error | Today | Redesigned |
|---|---|---|
| `Kosa La Fahirisi` (index) | `fahirisi hii katika {orodha} haipo (index out of range)` | `Kosa La Fahirisi: ulijaribu kufikia orodha[7], lakini orodha ina vitu 3 tu (fahirisi 0 hadi 2). Angalia kama fahirisi yako inatokana na hesabu isiyo sahihi.` — *"You tried to reach orodha[7], but orodha only has 3 items (indices 0 to 2). Check whether your index comes from a miscalculation."* Negative index gets its own phrasing (`fahirisi haiwezi kuwa hasi` — "an index can't be negative") rather than being folded into the same sentence, since a negative index and an over-the-end index are different bugs. |
| `Kosa La Anwani` (undefined variable) | `Jina hili {umri} halijulikani` | `Kosa La Anwani: umri haijawahi kupewa thamani kabla ya mstari huu. Je, umeandika jina lake vibaya, au umesahau kuiweka thamani kwanza?` — *"umri has never been given a value before this line. Did you misspell its name, or forget to assign it a value first?"* — naming the two most common real causes (typo vs. forgot to initialize) instead of just restating that it's unknown. |
| `Kosa La Kazi` (undefined function/method) | `Kazi hii {ongeza} haijaelezwa (undefined function)` | `Kosa La Kazi: hujafafanua kazi inayoitwa ongeza kwa kutumia eleza. Angalia herufi kubwa/ndogo na jina kwa makini — Hamri haifananishi majina yasiyofanana kikamilifu.` — *"You haven't defined a function called ongeza with eleza. Check case and spelling carefully — Hamri doesn't fuzzy-match names."* — flags the single most common real cause (typo/case mismatch) rather than just confirming "it's not defined." |
| `Kosa La Mzunguko` (loop exceeded cap) | `mzunguko {} haujaisha (loop did not end - check your condition)` | `Kosa La Mzunguko: mzunguko huu umefanya zaidi ya marudio 100,000 bila sharti lake kuwa uongo. Angalia kama kigezo unachotumia kwenye sharti (mfano: i) kinabadilika ndani ya mzunguko wenyewe.` — *"This loop ran past 100,000 iterations without its condition becoming false. Check whether the variable your condition depends on (e.g. i) is actually changing inside the loop body."* — points at the single most common real cause (forgot to update the loop variable) instead of just reporting the count. |
| `Kosa La Orodha` (not a list) | `{jina} si orodha (not a list)` | `Kosa La Orodha: jina lilishikilia thamani ya aina 'namba' ('5'), si orodha. Amri hii (weka/idadi/fahirisi) inahitaji orodha.` — *"jina was holding a value of type 'number' (5), not a list. This operation (weka/idadi/indexing) needs a list."* — states the actual type and value found, not just "not a list," since knowing *what it was instead* is what tells you where the mix-up happened. |
| `Kosa La Darasa` (not an object) | `{jina} si kitu (not an object)` | Same treatment as `Kosa La Orodha` — state the actual type/value found in place of the object, since that's usually the fastest way to spot "I passed the wrong variable" versus "I never constructed this." |
| `Kosa La Leta` (import failed) | `{jina} haipatikani (import failed - check the file name, class name, or method name)` | Split into the three failure shapes it already silently conflates (see `ImportException`'s own comment: file not found vs. class not found vs. method not found) — each gets its own sentence naming which of the three actually failed, instead of one message covering all three causes. |

## What this needs, technically

Two changes, both small relative to a language rewrite:

**Cheap, no new plumbing:** change `Error.throwException` and each
exception class to accept a small context object (e.g. `{index, length,
list_name}` instead of a single bare `list_name` string) so the richer
message can be built from data the interpreter already has at every throw
site shown above. This is a signature change, not new tracking.

**One real gap:** none of the statement/expression objects in
`StatementParser.py` currently carry a source line number forward — only
the raw `TokenObj`s do (`LexicalParser.py`'s `TokenObj.line`), and that
information doesn't survive into the parsed statement tree. Quoting *which
line* the error happened on (the single most useful addition beyond the
message text itself) means threading a line number from the token stream
into each statement/expression node during parsing — a contained, one-time
plumbing task, not a redesign of the parser.

## Why this is worth doing before the C rewrite

This is exactly the kind of investment that's cheap in the current Python
tree-walker (string formatting and a bit of extra context-passing) and
would be needlessly expensive to retrofit into a C bytecode VM later,
since the VM would need the same source-position tracking built in from
the start to produce equivalent messages. Doing it now also means the
*content* of good error messages (which failure modes are common enough to
call out by name) gets validated against real learners while it's still
cheap to change a Python string, rather than being locked into hand-written
C string formatting before anyone's actually read one.
