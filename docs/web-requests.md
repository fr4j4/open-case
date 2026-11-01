# Requests and the director's panel (F4b)

The teams ask for things from their phones, with a balance of tokens in view; the director answers from a queue that shows,
for each request, what the case suggests. The costs and the effect of every button are the rules of `site/play/js/rules.js`
(F4a, `web-format.md`): nothing here has a number or a code of its own.

## What travels

Only through the team room of `web-room.md` (a phone that was not approved never sees it):

| Direction | Message | What it carries |
|---|---|---|
| phone → director | `{k:'req', r}` | one request, with an `id`. Sent again every time the director connects, until it is answered |
| director → phones | `{k:'bal', t, tokens, alibi, initial, hist, open}` | the balance, and one entry per answered request (`id`, `req`, `answer`, `charged`, `note`, `at`). **Never what was handed out**: that travels as a delivery, as before |

A request is `{id, kind, code?, target?, suspect?, who?, place?, text?, detail?, evidence?, alibi?}`.
`js/requests.js` `sanitize` checks every one against `team.json` (codes, targets, kinds, lengths) before the director uses it,
and drops what it does not know. The director takes a request it already has as the same one (`receive`).

## What a team can ask

| Kind | Form (`equipo/pedir.js`) | Rules kind |
|---|---|---|
| Question | one of the menu, or another one to a suspect (a free text) | `question` |
| Follow-up | those whose `unlocked_by` it already holds; the condition is shown on the others | `follow_up` |
| Witness | name, where it appeared, question | `witness` |
| Confrontation | suspect, pieces of its folder and what each points to | `confrontation` |
| Procedure | code, target (`targets`), "what we look for and why"; `each` procedures take one objective per line, each its own request; an alibi token where `alibi: true` | `procedure` |
| Does the source exist? | button of the procedures in `free_source_procedures`, with a place | `source` (free) |

The balance (`#oc-balance`) shows what is still free: a request that waits holds back its cost (`available`, `canAsk`), and the
form does not let a team send what it cannot pay. The director checks again (`resolve` never leaves a negative balance).
The **history** tab lists every answered request and what it cost.

## The panel (`director/panel.js`)

- **Requests** tab: every team's pending requests in order of arrival. Each card has the suggestion (for example
  `DG3 · B → E15·B · 1 ficha`), the conditions with a ✓ or ✗ (`H2+` needs `E13b`; a witness appears in…), the team's balance,
  and the buttons of `rules.requests[kind].answers` with their cost; the suggested one is highlighted, the ones that cannot be
  given are disabled and say why.
- The director's choices: for a **witness**, which one (the typed name is matched against `who`, `name` and `aliases`); for a
  **confrontation**, which of the suspect's cards (the card list and the `guide_note`). When the case writes `opens_with`, the panel already marks the card the evidence opens, and says so; if the evidence opens several cards equally it lists them and leaves the choice (the guide says to ask what they point at); for a procedure of an open request
  (`material`), which sheets; the alibi tokens used; and what is handed out (the suggestion can be edited by taking
  something out; the answer is charged anyway). A message to the team can go with any answer; it is the **free answer**
  (`give` or `obvious` with a text, for questions off the menu).
- **Register** tab: every request with its answer, cost, what was handed out and seconds to answer, and the median. It replaces
  the printed control sheet.

Answering charges the team's rules state (`game.play.states[team]`, in the director's IndexedDB), hands out the items with the
same delivery as the *Give* tab (phones online get them; otherwise the QR) and sends the balance. What the *Give* tab hands out
is also held in that state, so the rules see it.

## Files

| File | What it does |
|---|---|
| `js/requests.js` | pure: `sanitize`, `canAsk`, `receive`, `suggest`, `answer`, `balanceFor`, `medianSeconds` |
| `equipo/pedir.js` | the "Ask" and "Tokens" tabs of the team's page |
| `director/panel.js` | the "Requests" and "Register" tabs |
| `js/room.js` | `DirectorRoom.sendTeam`, `DeviceRoom.sendToDirector`, `onData`/`onDirector` |

Words: `web.requests` in `opencase/strings/es.yaml` and `en.yaml`. A case adds nothing.

## Tests and closing

- `tests/web/test_requests.py` (node): checking of requests, tokens held back, the scripted game, suggestions, an edited handout.
- `tests/web/test_requests_ui.py`: the pages. The scripted game is `tests/web/partidas/v8_tres_equipos.json`, rounds 1 to 3 of the
  v8 simulation (3 teams, 21 requests), made in the forms and answered with the buttons, over the real `relay` transport; it ends
  with the folders and tokens of the simulation (A 7 + 2 alibi, B 4 + 2, C 6). A second test: a request made while the director is
  away waits, keeps its token held back and arrives when the director returns.

**Technical closing:** the above, in the CI. **Field closing (for fr4j4, it blocks only phase I):** a table with 2 or 3 teams in
the preview: the director answers each request in under 15 s (median, read in the Register) and no team reports a wrong charge.
