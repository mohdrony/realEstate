# Outreach — the channels only Rony can work

The scout never contacts anyone (DRIVER.md §3). These templates are for Rony to send himself.
Log every contact and every tip in `tracker.csv`; the scout reads it each run, scores any tipped flat and
reminds Rony of follow-ups older than 3 weeks.

| File | Channel | Send to |
|---|---|---|
| `01_hausverwaltung.md` | Property managers (Hausverwaltungen) | 10–20 managers in Brühl, Hürth, Erftstadt, Wesseling, Köln-Süd, Bonn, Kerpen, Bergheim |
| `02_suchauftrag_makler.md` | Search mandate for agents | 3–5 small local agents, plus Sparkasse/Volksbank property advisers |
| `03_gesuch_anzeige.md` | Wanted ad | Kleinanzeigen (Gesuche), local Facebook groups, notice boards |
| `04_bank.md` | Own bank | Your Sparkasse/Volksbank adviser: pre-approval + Verwertung list |

**Before you send anything:** get the bank pre-approval (`04_bank.md`) first — "financing confirmed" is the
sentence that makes sellers call you back. Fill `[…]` placeholders; numbers come from the v4 screen
(`python metric/deal_v4.py data/listings.csv`).

`tracker.csv` columns: `date, channel, contact, town, what_sent, reply, tip_listing_id, follow_up_date, note`.
