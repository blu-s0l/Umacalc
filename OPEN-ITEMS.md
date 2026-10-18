# Umacalc — open items

Collection manager, deck planner, Team Trials builder and resource planner for
Umamusume: Pretty Derby (Global). One `index.html` in the house style from
`../PROJECT-HANDOFF.md`, plus a generated `data.js`. Storage key `umacalc.v1`.

## To do

- **Skill links.** Trainee and card panels now link to their GameTora pages. Skill names
  aren't linked: GameTora has no page per skill, and its skills list can't be opened at a given
  skill by link. Options to put to Steve: an in-app skill pop-up (description from `skills.json`,
  plus which trainees and cards give it), or another site that has per-skill pages.
  Steve chose to leave them unlinked for now (2026-10-17). Revisit only if he raises it.
- **Aces in team building (requested 2026-10-17, for later; rules settled with Steve).**
  - **Rules.** Aces earn bonus points in Team Trials. Each race (Sprint, Mile, Medium, Long,
    Dirt) has exactly one ace, listed in that race's first slot.
  - **Who becomes ace.** The builder decides; nothing is flagged. Make as many Must include
    trainees aces as possible. Not every pin can be one: seven pins means at least two are not,
    and if none of five pins can run Dirt, only four can be aces.
  - **No point value needed.** The goal is to maximise the number of pinned aces, then build the
    best team around that.
  - **Two builds, shown side by side or switchable** (Steve, 2026-10-17):
    - **Best:** the current solve, with Must include honoured. Each race's ace is its
      highest-scoring member, whether pinned or not.
    - **Priority ace:** the two-stage solve below. Pins become aces wherever possible. A race
      without a pinned ace takes its highest-scoring member.
    In both, the ace's small bonus goes to whoever is ace, so the ace is always the race's best
    runner unless the priority rule says otherwise.
  - **Reference:** GameTora has a Team Trials scoring page (`gametora.com/umamusume/team-trials-pvp-scoring`).
    Read it before building this, to see how the ace bonus is actually scored.
  - **Not the Aces tab.** That tab is for user-entered aces in a different game mode and has
    nothing to do with this.
  - **Priority-ace build, in two stages:**
    1. Max-cardinality matching of pins to races. A pin can match a race if it has an eligible
       slot there and its own race lock allows it. Ties go to the higher slot score. Each matched
       pin is that race's ace, so fix its race.
    2. Run the usual team solve with those races fixed; unmatched pins stay free.
  - **Display:** mark aces in the team table (first in their race block, with a marker) and keep them first in
    alternatives.
  - **Why not one flow model:** pinned and unpinned runners merge at the shared style-slot
    bottleneck, so a single min-cost flow can't count pinned aces per race. That is why the
    matching runs as its own stage.


- **Check the effect interpolation against the game.** `effAt()` interpolates linearly
  between GameTora's breakpoints (Lv 1, 5, 10 … 50) and floors. Effects with no value before
  their first breakpoint count as 0. One in-game check per rarity at LB1 or LB2 would settle it.
- Conditional unique effects (types 101–122, e.g. "bonus while friendship ≥ X") are not modelled.
  They get a flat `COND_UNIQUE` score credit and an asterisk.
- Planner's Items table and the Inventory tab share `root.plan.inv`. Planner is target-based and
  Inventory is max-everything. If Planner ends up redundant, fold it into Inventory.
- Team builder ideas: weighting a race by your own priorities;
  "has this trainee's unique skill reached Lv X" (star level).
- Deck scoring ignores the deck's trainee: growth bonuses, distance and the scenario. A per-trainee
  weighting (e.g. Long trainee → stamina cards worth more) would be the next step.

## Decided

- **Star-up shard costs** are 50 / 100 / 200 / 300 per step (650 from 1★ to 5★). These came
  from JP guides, and Steve confirmed them for Global on 2026-10-17.
- **Hint-level costs** (`HINT_COST`, confirmed by Steve 2026-10-17). They apply to the 3 innate
  and 4 potential skills, max Lv3. Normal skills: Book ×4, then Book ×8, then Textbook ×6;
  Glimmer 5 / 10 / 15. Rare skills: Rare Book ×8, then ×16, then Rare Textbook ×12; Glimmer
  20 / 40 / 60.
- **Pins lock a race only** (2026-10-17). The style dropdown was removed, and older saved style
  locks are cleared on load. The ⚑ and ♡ markers sit beside the Must include and Prefer headings.
- **Data comes from GameTora's public JSON** (`tools/build_data.py`). The app filters on
  `release_en <= today` at runtime, so new Global releases show up without editing code. Rebuild
  `data.js` only when GameTora adds new trainees or cards.
  `py -I tools/build_data.py <some-empty-download-dir>`
- **Inventory = what it takes to max every switched-on trainee:** 5★, P5, and Lv3 hints on
  all seven hint-able skills (3 innate, 4 potential). Owned trainees are on by default and unowned ones off
  (`root.inv.on`). Shards are per trainee, so the still-needed count sums each trainee's own
  shortfall; one trainee's surplus never covers another. Hint levels are stored on the owned
  trainee as `root.umas[id].h = {skillId: level}`, covering the 3 innate and 4 potential skills.
  A potential skill stays locked until its potential level is reached.
- **Planner Filter** (`root.plan.show`): owned trainees are shown by default; trainees marked Target are
  hidden until ticked. An unowned target plans from a fresh pull: base stars, P1, no hints, no
  shards owned. This replaced the "Targets only" checkbox on 2026-10-17.
- **JP-only trainees** (JP release ≤ today, not yet on Global) are listed on Trainees so they
  can be targeted. They can't be owned unless Data → Include JP-only is on.
- **Estimated Global release** (`estGlobal`) is a least-squares line of Global date against JP
  date. It is fitted on the last 365 days of Global releases, trainees and cards together, and is
  never earlier than tomorrow. Global covers about 1.35 JP days per day, so the gap shrinks. On
  2026-10-17 it agreed with GameTora's own forecasts to within days near term and about a month
  three years out.
- **Team Trials model:** 5 races (Sprint, Mile, Medium, Long, Dirt = dirt mile) × 3 runners,
  one character once across the whole team, and no style repeated within a race.
- **Slot score** = 100 × the product of three aptitude multipliers (surface, distance, style:
  S 1.03, A 1, B 0.93, C 0.6, D 0.3) × 0.85 for each additional aptitude below A. A single B
  is cheap (one common spark), but several fixes compound: two Bs ≈ 0.74, three ≈ 0.58,
  B + C ≈ 0.47. This was Steve's call on 2026-10-17. Stats add to that, weighted per race
  (stamina counts 0 in Sprint and 1.2 in Long; wit gets +0.2 in every race, 2026-10-17, because skill activation runs on wit and Team Trials points come mostly from skills). Base stats at the owned star level add
  (weighted average − 85) / 4, a light tiebreak. Growth adds weighted average % × 0.6, so a
  fitting 20% bonus is worth about one B. It was doubled from 0.3 on 2026-10-17 because growth
  multiplies every training gain, while base stats are a one-time head start. Aptitude dominates; stats
  only break ties. "Sparks" = grade steps short of A, summed (B = 1, C = 2).
- **Prefer list:** +8 to that card's slots, about one B, so it wins any slot it is within
  8 points of. Teams are ranked by score plus that bonus. The displayed score never includes
  it, so totals stay comparable. Marked ♡ in the team table. Pins (⚑) stay at +1000.
- **Solver:** exact min-cost flow (character → race/style slot → race, capacity 3 per race).
  Pinned trainees get +1000 and may take any grade. Alternatives are re-solves with one
  best-team member banned, then a second round on the three strongest; ranked by size, then score.
- **Support score** is a rough per-unit weighting (`W`) of effects at the card's current
  level. It ranks cards and fills decks. It is not a simulation.
- Unowned cards are shown at LB4. A card with no stored level is at its LB's max level.
  The planner stores a lower current level if one is entered.
- The friend slot draws from every available SSR, friend and group card at a chosen LB.
- Duplicate characters in a deck, including the trainee, are flagged, not blocked.

- **Trainee portraits are copied into `img/umas/<card_id>.png`.** They are GameTora's 128px
  thumbnails, about 6 KB each and about 1.7 MB in all, and the build script fetches only new ones.
  They are self-hosted rather than hotlinked so the app doesn't use GameTora's bandwidth or break
  when its paths change. The art is Cygames'; the footer credits both. If a takedown ever comes,
  delete `img/` and the panel drops the picture (`onerror` removes it).

## Ruled out

- Monies (coin) costs for potential and hint levels: Steve chose to leave them out (2026-10-17).
- Hotlinking images from GameTora: it uses their bandwidth and makes the app depend on their paths.
