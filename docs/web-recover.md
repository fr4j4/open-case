# Recovering a game that lost its director (F6a)

If the director's device dies in the middle of a game (battery, a closed tab with the storage cleared, a new phone), the game must
not die with it. There are two ways back, and both are in the app: **the backup file** and **the teams' phones**.

## Backup file

*Back up* (top bar of the director) downloads `<case>-<date>.opencase.json`: the whole saved game (what was handed out, the requests
and the balances, the clock, the notices and hints, the sheets the teams handed in, **the marks of the score sheet**, and the room: PIN,
team rooms and approved phones). The *Room* tab shows when the last copy was made. On a new device, *Recover a game → Load a
backup* (also in the *Room* tab) reads it; the room opens again with the same PIN and the phones, which were in the team rooms
all along, reconnect by themselves. The file holds the PIN and the names of the team rooms, so it is as private as the game itself.

`readBackup` checks the file against fixed patterns (case, language, version, the files of a delivery, the PIN, the room names) and
`cleanPlay` checks the book against the rules of the case (a request is sanitized like one that arrives from the network, a balance that
does not make sense goes back to the start): a forged file cannot make the app fetch something else or break the account.

The backup is as old as the last download. What happened after it is not in it; recovering from the teams below covers that.

## Recovering from the teams

Each phone keeps what it was told: its folder in the order of the deliveries, every answered request with its cost, the requests
still waiting, the sheets and the clock. The team's *Room* tab has *If the director lost their device*: a link
`…/play/director/#recuperar.oc1r.<code>` (with its QR) that carries the PIN and the name of **the team's room**, nothing else.

1. On the new device: `play/director/` → *Recover a game*. Paste the link of each team (or open one: it fills the box; or scan the QR).
   The codes must agree on the case and the PIN; each team once.
2. The device makes the game with that PIN and those rooms and opens the team rooms **quietly**: a phone that comes in is taken as
   the team's (it knows the room name, which is the credential) and is asked for its registro (`{k:'recover'}` → `{k:'reg', rid, i, n, d}`,
   the registro cut in messages of 7000 characters). **Nothing else is sent to a phone** (no sync, no balance, no clock) until the
   director has chosen, because what a phone holds is what the new game is made of. Requests and sheets that arrive meanwhile wait.
3. For each team the screen lists the phones that answered, with what each has (handed out, answered, waiting, tokens). If they
   **differ**, it says so and shows what only each one has; the best one (most answers, then most items) is proposed, and the director
   picks. The registros are **never merged**.
4. *Recover with this selection* rebuilds (`recover.js`, `rebuild`) and the phones get their folder, balance and clock.
   A team with no registro starts from scratch (the screen says so).

What `rebuild` makes: per team the rules state (`newState` + envelope 1 + what it was handed + the tokens spent by the answered
requests, so the account adds up: `checkState` is clean), `asked` (witnesses), the register (answered and waiting), the sheets
handed in, the hints (the hint cards the team holds), the notices (those that reached any team), the clock (the phone furthest along),
and the log of what was handed out (one entry per team, so the original delivery numbers are not kept).

What the phones do **not** know, and is therefore lost without a backup file: the marks of the score sheet; which phone answered
which request; what each answer handed out (it is in the folder, not in the register); the exact moment of each delivery. The screen
warns about the marks.

## Why it is safe

- The room name is the credential of a team room (`web-room.md`). Adopting the phones that come in with it is as safe as the team room
  itself; the teams recovered keep adopting for the rest of the game (the phones that arrive late are still theirs), and *Remove from the
  room* still rotates the name.
- A registro is checked like everything that comes from the network (`checkRegistro`): the device id must be the sender, the files
  must be pages of the case, every request goes through `sanitize`, texts are cut, numbers are bounded.
- Nothing about the game travels in the link: only the PIN, the room name and the case/version.

## Files

| File | What it does |
|---|---|
| `js/recover.js` | pure: backup (`makeBackup`, `readBackup`, `cleanPlay`), codes (`recoveryCode`, `parseCodes`, `gameFromCodes`), registro (`buildRegistro`, `splitRegistro`, `Assembler`, `checkRegistro`, `differences`, `rebuild`) |
| `director/recuperar.js` | the backup card, the form of the setup screen and the `Recovery` screen |
| `js/room.js` | `DirectorRoom.recover`/`endRecovery` (quiet teams, adopted phones), `recover` message on the phone |
| `equipo/app.js` | sends the registro, shows the recovery link and QR |
| `director/app.js` | wiring: `startRecovery`, `loadBackup`, `downloadBackup`, the messages held meanwhile |

Words: `web.recover` in `opencase/strings/es.yaml` and `en.yaml`.

## Tests and closing

- `tests/web/test_recover.py` (node, `recover.test.mjs`): the scripted game of the v8 simulation (3 teams, 21 requests) is played, the
  phones' registros are built, cut, shuffled and put together, and the rebuilt game has the same tokens, held sheets and cards, witnesses
  asked and register, a clean account, and charges the next request the same; forged registros and backups are refused; two phones that
  differ are shown as different; the codes.
- `tests/web/test_recover_ui.py`: a director and two phones over the real `relay` transport. **From the teams:** in the middle of a game
  (answers, a waiting request, a hint) the director's context is closed; a new one recovers from the phones' links, nothing is sent
  to them before the choice, the queue, the register, the clock, the balances and the folders are the ones before, the waiting request
  is answered and charged, and the score comes out of the figures. **From the backup:** same room and PIN, phones back by themselves,
  balances untouched, the waiting request and the marks there.

**Technical closing:** the above, in the CI. **Field closing (for fr4j4, it blocks only phase I):** in a real game with three phones,
close the director's browser (or lose its storage), recover from a second device with the real transport and see that the phones
reconnect, the balances do not move and the game ends with the same score; and the camera scan of the recovery QR on iOS and Android.
