# Case bible · Cierre de caja

> Source of truth of the example case while it was designed from `conversation.md`. Never exported, never shown to players. Generated case: `cases/cierre-de-caja/`.

## 0 · Frame ✅

| Field | Value |
|---|---|
| Title | Cierre de caja |
| Slug (folder) | cierre-de-caja |
| Case language | es |
| Locality | Pasaje Los Aromos, Rancagua, Chile. PDI (Brigada de Robos), Fiscalía Local, SML, Inspección del Trabajo. Pesos chilenos, micro con tarjeta de transporte. |
| Players | 8 adults, two teams of 4, some have played the sample case |
| Duration | Short, 45–50 min |
| Teams · tokens · players per team | 2 · 10 · 6 badges |
| Tone | Police procedural, neighbourhood scale, no gore |
| Images | None. One SVG sketch (E02). All evidence as documents, logs, chats and posts. |
| Paper | letter |
| Version · date | v1 · 2026-10-29 |
| Validated by the author on | 2026-10-29 (simulated author) |

## 1 · The truth ✅

Diego Fuentes, the shop's delivery rider, had been skimming the till for months whenever he covered the register at lunchtime (about $40.000 a time, deposited at an ATM every Monday). Renato Ibáñez blamed the cashier, Sandra Mella, and fired her on Monday 2 November. The shortages continued. His accountant pointed at who covered the register at noon; Renato activated a free 30-day cloud backup of the cameras on 3 November, and on Sunday 8 at 20:15 he watched three clips of Diego pocketing cash. At 19:30 he had already told the accountant "no era quien yo pensaba" and that he would file a complaint on Monday; at 21:30 he said so in the shopkeepers' chat. At 22:12 he phoned Diego: come now, I'm giving you the chance to return it. Diego arrived by motorbike at 22:28, opened the back door with his code at 22:30, they argued, and while Renato went back to bundling the week's cash with his back turned, Diego struck him on the right parietal with the 1 kg brass weight from the display scale (about 22:40; a neighbour heard the thud and a short cry). He then staged a robbery: took the bundles from the open safe ($1.850.000), pulled the hard disk from the DVR he himself had installed in the loft behind the drinks crates (the cloud lost the recorder at 22:44), carried the weight and the disk in a supplier's plastic bag to the rubble skip at the end of the alley (22:49), stowed the cash in his delivery box and left at 22:52. He left the register's float untouched and nothing forced.

**Cover story:** a robbery.

**Telling detail:** the thief knew there were cameras and where the recorder was hidden, took the disk, but the cloud backup kept the clips (E09) and the keypad kept his code at 22:30 (E15). Read with E08 + E11·D (the bike) and E10·D (the phone). PER1 explains it.

## 2 · Setting and time ✅

Sunday 8 November 2026, dry night, 14 °C. Pasaje Los Aromos: dead-end alley, shops at the entrance, a rubble skip from a building site at the end (30 m from the back door). The avenue with bus stops is 150 m away. Villa El Cobre (Diego) is 3 km away (8 min by bike). Población Santa Elena (Sandra) is 8 km away (20 min by bus 506). Rancagua centro (Valeria) is 4 km away. Antennas: RGA-21 covers the alley and twenty blocks around (useless to place Óscar, who lives there); RGA-33 Villa El Cobre; RGA-14 Santa Elena; RGA-09 the centre (Alameda).

## 3 · The victim ✅

| Field | Value |
|---|---|
| Name · age · occupation | Renato Ibáñez Cornejo · 54 · owner of minimarket El Trébol since 2009, widower |
| Why several people wanted them gone | Fired Sandra publicly; fought Óscar for a year and got him fined; refused his daughter money; was about to report Diego |
| What they did in their last 24 hours | 17:45 called the supplier; 19:30 called the accountant; 20:15–20:40 watched the cloud clips; 21:00 closed with Diego; 21:05 refused Valeria money by phone; 21:30 announced the complaint in the chat; 21:50–21:58 argued with Sandra at the back door and told her he knew it wasn't her; 22:10 unlocked his phone; 22:12 called Diego; from 22:30 counted the week's cash in the office |
| What they carried / what was found with them | Green apron with a pencil and a roll of green paper bands "Trébol · sem 45 · lunes" (E05) |

## 4 · Suspects ✅

Order (kit and cards): family, neighbour, employees. Culprit last.

| Letter | Name · age | Role / relation | Apparent motive | Secret | The lie | True alibi | Discard evidence |
|---|---|---|---|---|---|---|---|
| V | Valeria Ibáñez · 27 | daughter, nursing student | debts, fought for money, called him that night (E04, E07) | $1.9M loan from an informal lender; pawned her mother's ring | "No hablé con mi papá ese día" | Camila Toro's birthday, centre, 20:30–01:00 | E10·V (antenna) + E16/A1 (Camila, one source) + E13·V (delivery to the flat 23:48) |
| O | Óscar Peralta · 61 | owner of the bottle shop next door | parking war, Renato's complaint got him fined, "te vas a arrepentir" in the chat (E03) | sells alcohol after 22:00 | "Cerré a las diez" | at his counter until 23:35 | E08 (his camera) + R1 (Marta sees him smoking with the shop open at 23:05) + E11·X |
| S | Sandra Mella · 38 | fired cashier | fired for theft, no severance, Instagram post, seen arguing at 21:50 (E04, AVISO 1) | went that night to demand her severance; Renato told her he knew it wasn't her | "Desde ese lunes no volví a pisar el local" | left 21:58, bus 22:03, home 22:41 | E08/E15 (left 21:58) + E17·S (bus 22:03) + E10·S (route 22:08, Santa Elena 22:41) |
| D | Diego Fuentes · 29 | delivery rider, found the body | none visible; has the door code (E01) | the culprit; skimmed the till for months | "Llegué a mi casa a las 21:20 y no salí más"; "Renato no me llamó" | none: alone at home, partner on night shift | — |

Culprit: D. Main red herring: S (secondary: O, V, "a robbery").

Card facts: in `suspects.yaml`.

## 5 · Timeline of the night ✅

Crime window: 22:28–22:52. Key minute: 22:40.

| Time | Renato | V | O | S | D | Environment | Recorded by |
|---|---|---|---|---|---|---|---|
| 19:30 | calls accountant 12 min | at home, centre | serving | at home, Santa Elena | at the shop | | E07, CT1 |
| 20:15–20:40 | watches cloud clips | 20:35 at Camila's | serving | | | | E09, E10·V, E16 |
| 21:00–21:04 | closes with Diego | | | | leaves on bike 21:04 | | E08, E11·D, E15 (21:02) |
| 21:05 | call with Valeria 6 min | on the balcony | | | | | E07, E10·V, E16 (21:09) |
| 21:17–21:19 | | | | 21:24 bus from Santa Elena | bike off at El Cobre; antenna El Cobre | | E11·D, E10·D, E17·S |
| 21:30–21:36 | chat: complaint tomorrow | | 21:33 replies | | | | E03, E07 |
| 21:44–21:58 | lets Sandra in 21:50, argues, lets her out 21:58 | | 21:30 serving | arrives 21:44, in 21:50, out 21:58 | at home | Marta hears shouting | E08, E15, E10·S, R1 |
| 22:03–22:08 | | | 22:05 sells beer | bus 22:03, route 22:08 | 21:50 data at El Cobre | | E17·S, E10·S, E08, E10·D |
| 22:10–22:12 | unlocks phone, calls Diego 1:40 | | | | takes the call at El Cobre | | E07, E10·D |
| 22:19–22:30 | opens the safe, counts | 22:35 group photo | 22:20–22:24 smokes outside | | bike on 22:19, antenna 22:24, parks 22:27, code 22:30 | | E11·D, E10·D, E08, E15, E16 |
| 22:38–22:44 | **killed** | | | 22:41 home | strikes; removes disk | 22:40 thud and cry; 22:44 recorder offline | R1, E01, E09, E10·S |
| 22:45–22:52 | | | 22:45 sells to two youths | | 22:49 bag to the skip; 22:52 leaves | | E08, E15, E11·D |
| 22:56–23:10 | | 23:10 karaoke | 23:05 smokes, looks at El Trébol | | antenna 22:56, bike off El Cobre 23:04, antenna 23:10 | Marta looks out ~22:45, sees the bike | E10·D, E11·D, R1, R2, E16 |
| 23:35–23:48 | | 23:48 delivery order | closes 23:35, lights off 23:40 | | washes jacket | | E08, E13·V, E12·D |
| 06:26–07:14 Mon | | | | | bike on 06:26, antenna 06:35, parks 06:39, code 07:12, calls 133 07:14 | | E11·D, E10·D, E15, E01 |

Checks done: 3 km in 8 min by bike; 8 km in 20 min by bus; the 13:05 Saturday clip against the 12:55 keypad entry; the Monday 07:12 entry; the 21:02 exit on Sunday; weekdays of all dates in 2026.

## 6 · Deduction paths ✅

| Path | Type | Sheets (how obtained) | ◆ card | Tokens from zero | Visible from the menu? |
|---|---|---|---|---|---|
| A | movement | E08 (O3 or DG3 botillería) + E11·D (DG6 Diego) | D5 | 3 | yes: O3 is in the menu, DG6 names a person |
| B | alibi / access | E15 (DG3 teclado) + E10·D (DG5 Diego) | D6 | 3 | yes: E01 names the keypad; DG5 names a person |
| C | physical | E12·D (DG7 Diego), or E14 (DG9 contenedor) + E11·D or E12·D | D7 | 2 | yes: DG7 names a person; E02 shows the skip |
| K | knowledge (bonus, not required) | E09 (DG4) | D8 | 2 | yes: E07 calendar and E01 point to the cameras |
| M (motive) | motive | E09 (DG4), or E13·D (DG8 Diego), or CT1 (after E06/E07), or S4+ | D9 | 1–2 | yes |

Minimum route to the confession: O3 → E08, DG6 D → E11·D, D◆ → D5, DG7 D → E12·D, D◆ → D7, DG4 → E09 = 6 tokens of 10 (60 %).
Cost to discard every innocent: V: DG5 V + TESTIGO Camila = 2; O: O3 + R1 = 2; S: E08 (already) + DG3 transporte = 1 → 5 tokens (50 %).
Cost to sweep one procedure across all suspects: 4 tokens (40 %).
Free material alone: suggests an inside job (nothing forced, the register's float untouched, the DVR disk gone, the apron bands) and that Diego has a code, but also that Renato, the supplier and until 2-11 Sandra had codes; it does not name him.

## 7 · Red herrings ✅

| Red herring | Who or what pushes it | Points at | Sheets that explain it | Points |
|---|---|---|---|---|
| A robbery from outside | E01 (safe open and empty), E03 ("entraron a robar"), PRENSA | nobody | E01 (nothing forced, float untouched), E15 (code), E14 (disk dumped), PER1 | 1 |
| Sandra (main) | E03, E04, DEC·O, DEC·D, AVISO 1, AVISO 2, R1 (shouting with a woman) | S | E06 (shortages after she left), E08, E15, E17·S, E10·S, S4, CT1 | 1 |
| Óscar | E03 (threat), DEC·V, E13·O (fine) | O | E08, R1, O4, E11·X | 1 |
| Valeria | E04 (post), E07 (call), AVISO 2 (debt) | V | E10·V, E16/A1, E13·V, V4, V5 | 1 |

## 8 · Evidence ✅

| Code | Title | Kind | How obtained | Provided by | What it shows | Truth / chosen-to-show | Serves | Spoiler risk |
|---|---|---|---|---|---|---|---|---|
| E01 | Parte policial | report | free, envelope 1 | PDI | body, safe, register, keypad door, DVR without disk, missing weight, Marta heard a thud | true | all | names Diego as finder; acceptable |
| E02 | Croquis | sketch (SVG) | free, envelope 1 | PDI | layout, camera of the bottle shop, back doors, skip | true | A, C | low |
| E03 | Grupo Locatarios | chat | free, envelope 1 | shopkeepers | Óscar's threat, Sandra's firing, "denuncia seria" Sunday 21:30, Óscar "cerré a las diez" | true chat; Óscar's lie | M, red herrings | low |
| E04 | Redes sociales | posts | free, envelope 1 | open source | Renato "ya sé cómo lo hace", Sandra's post, Óscar "hasta tarde", Valeria's post, Diego's comment | chosen to show | red herrings | low |
| DEC · V/O/S/D | Statements | statement | free, envelope 1 | suspects | one lie each | lies | all | DEC·D: at most the "no supe más" slip, worth a contradiction point with E07 |
| E05 | Autopsia | report | free, envelope 2 | SML | blow with brass object, 22:00–00:00, no defence, apron bands | true | C | low |
| E06 | Contabilidad | ledger | DG1 | PDI + accountant | $1.850.000 missing in banded bundles, float intact, shortages continue on Sandra's days off, Diego covers at noon | true | M, S herring | names Patricio Lillo (witness) |
| E07 | Celular de la víctima | log | DG2 | lab | 22:12 call to Diego, 21:05 Valeria, 19:30 accountant, calendar (cloud, complaint, deposit) | true | M, contradiction, V | medium (the 22:12 call) |
| E08 | Cámaras botillería | camera log | O3 or DG3 | Óscar | Sandra in/out, bike 22:28/22:49/22:52, Óscar serving to 23:35 | true | A, discards O and S | medium |
| E09 | Respaldo en la nube | account log | DG4 | lab | Diego secondary admin, Renato watched clips, recorder offline 22:44, clips of the rider pocketing cash | true | K, M | high (paid) |
| E10·V/O/S/D | Antenas | tower | DG5 | telco | each suspect's sector by hour; coverage notes | true | B, discards | medium |
| E11·D / E11·X | Vehículos | inspection | DG6 | PDI | bike GPS log, washed box, bronze dust; others nothing | true | A, C | high (paid) |
| E12·D / E12·S / E12·X | Pertenencias | search | DG7 | PDI | $1.240.000 with sem 45 bands, washed jacket, bronze dust; Sandra's complaint folder; Valeria's pawn receipt | true | C, V5 | high (paid) |
| E13·V/O/S/D | Cartolas | bank | DG8 | bank | Valeria's loan; Óscar's fine; Sandra clean; Diego's Monday cash deposits | true | M, V5, discards | medium |
| E14 | Contenedor | find | DG9 | PDI | weight with blood, DVR disk, supplier bag, no prints | true | C, robbery herring | medium |
| E15 | Teclado puerta trasera | log | DG3 | PDI | code 2 at 22:30, exits 21:58 and 22:52, Monday 07:12 | true | B | high (paid) |
| E16 | Historias de Camila | posts log | with A1 | Camila | Valeria at the party 20:40–01:05 | true | discard V | low |
| E17·S / E17·X | Transporte | log | DG3 | transit | Sandra's bus 21:24 and 22:03; others | true | discard S | low |
| AVISO 1, AVISO 2 | Avisos | notice | read at minute 7 and 14 | Fiscalía | push S and V | chosen to show | herrings | none (no codes) |

Dossier sections: start (envelope 1): E01–E04; statements (envelope 1): DEC-V, DEC-O, DEC-S, DEC-D; investigation (envelope 2): E05; with-answer: E16; procedures: E06–E15, E17; notices: AVISO1, AVISO2.

## 9 · Questions and cards ✅

In `cases/cierre-de-caja/languages/es/cards.yaml` (43 cards). Summary:

| Suspect | Menu | Confrontations (trigger → card) | Failed | Follow-ups |
|---|---|---|---|---|
| V | V1 where (unlocks A1) · V2 spoke? (lie) · V3 money | call (E07/E10·V/E16) → V4 · loan (E13·V/E12·X/AVISO 2) → V5 | V✕ | — |
| O | O1 where (lie) · O2 the feud · O3 camera (+E08) | E08/R1 → O4 | O✕ | — |
| S | S1 where (lie) · S2 why fired · S3 who had access (key: Diego) | E08/E15/E10·S/E17·S/R1 → S4 | S✕ | S4+ (motive) |
| D | D1 where (lie) · D2 shortages · D3 spoke after closing? (lie) | E07 alone → D4 · E08/R2 + E11·D → D5 (A) · E15 + E10·D → D6 (B) · E12·D or E14 + E11·D/E12·D → D7 (C) · E09 → D8 (K) · E13·D / E06 + S4+ or CT1 / D8 → D9 (M) | D✕ (single sheets) | D1+ |

Witnesses: R1, R2 (Marta, free), CT1 (Patricio Lillo), A1 (Camila + E16), PER1. Wildcards: ◆ ✕, TESTIGO, NADA. Notices: AVISO 1, AVISO 2, PRENSA. Hints: PISTA 1–3. Closing: CIERRE.

## 10 · Procedures and witnesses ✅

| Code | Procedure | Cost | Targets → sheet |
|---|---|---|---|
| DG1 | Contabilidad del local | 1 | E06 |
| DG2 | Celular de la víctima | 1 | E07 |
| DG3 | Cámaras o registros de un lugar o servicio | 1 | botillería → E08 · teclado → E15 · transporte S → E17·S · transporte otros → E17·X · cámaras del minimarket → "sin disco", free · otras cámaras → sin hallazgos |
| DG4 | Cuentas y respaldos digitales de la víctima | 1 | E09 |
| DG5 | Antenas de una persona | 1 | E10·V/O/S/D |
| DG6 | Vehículo de una persona | 1 | D → E11·D · otros → E11·X |
| DG7 | Pertenencias de una persona | 1 | D → E12·D · S → E12·S · otros → E12·X |
| DG8 | Cartola de una persona | 1 | E13·V/O/S/D |
| DG9 | Rastrear un lugar | 1 | pasaje o contenedor → E14 · otro → sin hallazgos |
| DG10 | Otra | 1–2 | recuperar el disco → "20 días" · otra → director decides |

| Code | Witness | Appears in | Delivers |
|---|---|---|---|
| R1, R2 | Marta Soto | E01 (free) | cards |
| CT1 | Patricio Lillo | E06, E07 | card |
| A1 | Camila Toro | DEC·V, E04, V1 | card + E16 |
| PER1 | perito informático | after E09 or E15 | card |

Named people with "Nada que aportar": Carmen (peluquería), Tito (ferretería), Distribuidora Marcel, Diego's partner, Dr. Villalobos, Subcomisario Quintana.

## 11 · Notices, press, hints ✅

| When | What is read | Pushes |
|---|---|---|
| Notice 1 · minute 7 | a neighbour heard the victim arguing with a woman near ten; Sandra did not answer the summons | S |
| Notice 2 · minute 14 | Sandra's labour complaint; Valeria's debt with an informal lender | S, V |
| Press · with notice 2 | "¿Quién sigue?", robbery wave, "una persona de interés" | robbery |

Hints: 1. how did the thief get in, what does the back door record (−1) · 2. who knew about the cameras and the recorder; why the disk but not the float (−1) · 3. the 22:12 call: where was that person twenty minutes later (−2).

## 12 · Economy and scoring ✅

Tokens 10; timing 8 / 22 / 15; free: does X own a vehicle, where does X live, what does X do, were there cameras (yes, no disk), "eso ya lo tienen".

Scoring: culprit with sheet 5 (2 without) · how 2 · why 2 · window 1 (any range containing 22:40 within 22:00–23:30) · bonus shortages 2 · contradiction 1 · each innocent discarded 2 (1 with one sheet) · each innocent blank −1 · each red herring explained 1 · each token left 0.25 · hints −1, −1, −2 · wrong accusation −5 and cannot win; both wrong: no winner · no accusation: tokens only. Tie-break: fewer tokens, then clearer presentation.

Confession: two of paths A, B, C with their ◆ card (D5, D6, D7) + motive (E09, E13·D, CT1, S4+, D8 or D9) + name on the sheet. Confession scores nothing.

## 13 · Director's script ✅

In `guide/03-guion.md` (opening, notices, press, hints) and `guide/07-confesion.md` (confession, closing). Opening in the voice of Subcomisario Quintana; confession in Diego's voice, 150 words, no codes.

## 14 · Graphics ✅

| Image or drawing | For sheet | Constraints | Status |
|---|---|---|---|
| Sketch of El Trébol, the bottle shop and the alley (SVG, 760 × 420) | E02 | not to scale, legend with three colours, no measurement | done: `diagrams/e02.svg` |

No photos. Suspect cards show the folder silhouette.

## 15 · Decisions, problems and changes ✅

| Date | Kind | What | Severity | Fix | Status |
|---|---|---|---|---|---|
| 2026-10-29 | decision | Short case, no photos, Rancagua, Spanish | — | — | done |
| 2026-10-29 | decision | Culprit last in the suspects list; order family → neighbour → employees | — | — | done |
| 2026-10-29 | problem | E13·V had a bar purchase at 23:48 in the centre while Valeria "never left the flat" | unfair | delivery order to the flat's street | fixed |
| 2026-10-29 | problem | Cloud clip of Saturday 13:05 vs keypad entry 13:31 | cosmetic | keypad entry 12:55 | fixed |
| 2026-10-29 | problem | Bottle-shop camera covers the end of the alley: it must see the trip to the skip | consistency | E08 row 22:49 added; E14 alone is a failed confrontation | fixed |
| 2026-10-29 | problem | AVISO 2 said "deuda vencida"; E13·V shows the instalment paid | cosmetic | removed "vencida" | fixed |
| 2026-10-29 | problem | Diego opened with his code on Monday 07:12 (E01): E15 had no such row; Sunday 21:02 exit was missing too | consistency | rows added | fixed |
| 2026-10-29 | change after validation | R2 said "pensé que era el Diego": named the culprit for one token | breaks (cheap route) | "de esas con caja atrás, no sé de quién" | fixed, author told |
| 2026-10-29 | audit (self, desk) | Consistency pass on all 33 sheets; difficulty: minimum route 6/10, discards 5/10, sweep 4/10; spoilers: kit, envelopes and suspect cards read as a player | — | — | passed |
| 2026-10-29 | simulation | Not run for the example | — | run with `templates/audit-prompts.md` before a real table | pending |
