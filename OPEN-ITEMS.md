# Umacalc — open items

Collection manager, deck planner, Team Trials builder and resource planner for
Umamusume: Pretty Derby (Global). One `index.html` in the house style from
`../PROJECT-HANDOFF.md`, plus a generated `data.js`. Storage key `umacalc.v1`.

## To do

- **Check the effect interpolation against the game.** `effAt()` interpolates linearly
  between GameTora's breakpoints (Lv 1, 5, 10 … 50) and floors. Effects with no value before
  their first breakpoint count as 0. One in-game check per rarity at LB1 or LB2 would settle it.
- **Check the star-up shard costs in the Global client.** `STAR_SHARDS` is 50 / 100 / 200 / 300
  per step (650 from 1★ to 5★), taken from JP guides.
- Conditional unique effects (types 101–122, e.g. "bonus while friendship ≥ X") are not modelled.
  They get a flat `COND_UNIQUE` score credit and an asterisk.
- Coin costs for potential levels aren't in the data, so the planner shows items only.
- Team builder ideas: an ace pick per race; weighting a race by your own priorities;
  "has this trainee's unique skill reached Lv X" (star level).
- Deck scoring ignores the deck's trainee: growth bonuses, distance and the scenario. A per-trainee
  weighting (e.g. Long trainee → stamina cards worth more) would be the next step.

## Decided

- **Data comes from GameTora's public JSON** (`tools/build_data.py`). The app filters on
  `release_en <= today` at runtime, so new Global releases show up without editing code. Rebuild
  `data.js` only when GameTora adds new trainees or cards.
  `py -I tools/build_data.py <some-empty-download-dir>`
- **JP-only trainees** (JP release ≤ today, not yet on Global) are listed on Trainees so they
  can be targeted. They can't be owned unless Data → Include JP-only is on.
- **Estimated Global release** (`estGlobal`) is a least-squares line of Global date against JP
  date. It is fitted on the last 365 days of Global releases, trainees and cards together, and is
  never earlier than tomorrow. Global covers about 1.35 JP days per day, so the gap shrinks. On
  2026-10-17 it agreed with GameTora's own forecasts to within days near term and about a month
  three years out.
- **Team Trials model:** 5 races (Sprint, Mile, Medium, Long, Dirt = dirt mile) × 3 runners,
  one character once across the whole team, and no style repeated within a race.
- **Slot score** = 100 × product of three aptitude multipliers (surface, distance, style:
  S 1.03, A 1, B 0.85, C 0.6, D 0.3), plus a small tiebreak from base stats at the owned star
  level and growth bonuses weighted per race. Aptitude dominates; stats only break ties.
  "Sparks" = grade steps short of A, summed (B = 1, C = 2).
- **Solver:** exact min-cost flow (character → race/style slot → race, capacity 3 per race).
  Pinned trainees get +1000 and may take any grade. Alternatives are re-solves with one
  best-team member banned, then a second round on the three strongest; ranked by size, then score.
- **Support score** is a rough per-unit weighting (`W`) of effects at the card's current
  level. It ranks cards and fills decks. It is not a simulation.
- Unowned cards are shown at LB4. A card with no stored level is at its LB's max level.
  The planner stores a lower current level if one is entered.
- The friend slot draws from every available SSR, friend and group card at a chosen LB.
- Duplicate characters in a deck, including the trainee, are flagged, not blocked.

## Ruled out

- Images from GameTora: an external dependency and a hotlinking concern. The app uses names only.
