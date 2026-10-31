# The live room (F3)

The director opens a **room**; phones come in with a **PIN** or a link; the director **approves** each one and assigns it to a
team; from then on the deliveries go over the network. The QR of F2 stays as the backup (Teams tab of the director) and is
what opens when a team has no phone connected.

## Flow

1. Director: *Room* tab → *Create room*. It shows a 6-character PIN (no `0 O 1 I L`), a link `…/play/equipo/#sala.<PIN>` and a QR of that link.
2. A phone types the PIN (or opens the link or scans the QR) in the team app. It appears under *Waiting for approval* with its name.
3. The director taps *To team X* (or *Refuse*). The phone opens X's folder by itself (kit, envelope 1, suspects) and everything already handed out to X.
4. *Deliver* sends to the team's connected phones. The ones that were offline get the rest when they reconnect (the director sends a `sync` with everything the team has so far). Several phones of one team see the same.
5. A phone can be moved to another team (its folder is replaced) or taken out. The team's room name then changes, so the one that left cannot keep listening.

## Rooms and what travels

| Room | Name | Who knows it | What goes through it |
|---|---|---|---|
| Vestibule | `oc-v-<PIN>` | anybody with the PIN | `join`, `wait`, `approved`, `denied`: nothing about the game |
| Team | `oc-t-<20 random chars>` | the director and the phones it approved for that team | `sync`, `deliver` (the same message as the QR: only codes), `room`, `out` |

The `relay` transport encrypts every frame with a key made from the room name, so a phone that was not approved cannot read
a team room even though the relays are public. The PIN is **not** a secret that protects the game from a determined player
(it is short, the site is public); what it guarantees is that a device nobody approved receives nothing the director hands
out, and that a team never gets another team's messages. The director also ignores any message from a device that is not
approved for the room it comes through.

## Reliability

- `js/transport/` (F0) numbers, acknowledges, repeats and orders every message; here, `js/canal.js` joins the transport in
  `transport/config.js` (`primary`) with the backup (`fallback`). The director listens on both; a phone opens the main one and
  adds the backup if nobody answers in `connectTimeoutMs` (10 s). Deciding the transport from field data changes only `config.js`.
- The director's game (room, PIN, approved devices) is in IndexedDB: a reload reopens the same room. A phone keeps its id and its
  session, so a reload goes straight to its team room.
- `js/log.js` keeps an event log (joins, approvals, moves, deliveries, connections) in IndexedDB.
- `js/room.js` asks for a Wake Lock on both sides (the screen stays on while the room is open).
- Tests and the network lab can force a transport with `?transport=broadcast|relay|…` and the relays with `?relays=wss://…`.

## Files

| File | What it does |
|---|---|
| `js/canal.js` | main transport + backup behind the `Transporte` interface |
| `js/room.js` | PIN, rooms, `DirectorRoom` and `DeviceRoom`, Wake Lock |
| `js/log.js` | event log in IndexedDB |
| `director/app.js`, `equipo/app.js` | *Room* tab, approval, delivery over the network; PIN form, status, folder replaced on a move |

Requests and the balance travel through the same team rooms (`web-requests.md`); the clock, the sheets handed in and the score, in `web-game.md`.

Words: `web.room` in `opencase/strings/es.yaml` and `en.yaml`.

## Tests and closing

`tests/web/test_room.py` runs the real `relay` transport against a Nostr relay written in Python (Playwright's `route_web_socket`),
with every phone in its own browser context: 1 director and 4 phones in 2 teams plus a device with the PIN that is never approved;
50 deliveries (20 to A, 15 to B, 15 to both) arrive complete, in order, once and only to their team; the intruder receives
nothing; a phone that was off gets what it missed; a reloaded director recovers the room and the phones come back in under 15 s;
refusing and moving phones. The WebRTC transport needs real networks, so it is **not** covered here.

**Technical closing:** everything above, in the CI. **Field closing (for fr4j4, it blocks only phase I):** with the real
transport (`trystero-nostr` + `relay`) and at least 3 phones on different networks, the success rates F0 decided; a cut of 60 s
and back with nothing lost (here only the closed-page case is tested); iOS with the screen locked (Wake Lock and reconnect).
