# Combat-PoD AI Logic Guide

This document describes how AI combatants select and execute moves in the combat minigame.

## Architecture Overview

The AI runs on the same move set as the player. Every `pod_combat_use_{key}_effect` generated from the CSV is available to both sides. The difference is in who picks the move:

- **Player**: clicks a button in the combat GUI
- **AI**: the generated `pod_combat_ai_csv_select_effect` runs a weighted `random_list` across all active skills, with trait gates, situational modifiers, and anti-repetition logic baked in

There is no separate AI move set or hand-tuned AI tree. The AI's behavior emerges entirely from the CSV columns and the Python generator.

---

## Turn Order: Initiative System

Combat uses a unified initiative system where all combatants (player team slots 0-4, enemy team slots 5-9) roll together and act in descending order. There are no "player phase / enemy phase" turns.

### Initiative Roll

Each alive combatant rolls:

```
initiative = prowess + random(1-30)
```

The random component is spread across 7 equal buckets (1, 5, 10, 15, 20, 25, 30) using CK3's `random_list` for uniform distribution. Higher prowess characters tend to act first, but the random factor keeps it unpredictable.

### Turn Processing

1. `pod_combat_calculate_initiative_effect` rolls initiative for all alive slots
2. `pod_combat_find_next_actor_effect` scans all 10 slots and picks the highest-initiative combatant that hasn't acted yet
3. If the next actor is the PC (slot 0), combat pauses for player input
4. If the next actor is an AI, `pod_combat_execute_ai_turn_effect` runs their full turn
5. Repeat until everyone has acted, then start a new round

The PC is never guaranteed first move. If an enemy rolls higher initiative, they act before the player sees any UI. This is handled by `pod_combat_process_pre_pc_turns_effect` which runs AI turns in a loop until it's the PC's turn.

---

## AI Turn Execution

When it's an AI combatant's turn, the system:

1. **Select a target** based on team membership:
   - Player-team AI (slots 1-4): targets an enemy (slots 5-9)
   - Enemy-team AI (slots 5-9): targets a player (slots 0-4)
   - Target selection biases toward low-HP targets (2x weight when HP <= 2)

2. **Load workspace**: copies the actor's slot data and target's slot data into the shared `pod_combat_player_*` / `pod_combat_opponent_*` workspace variables that all move effects read from

3. **Set AP to 6** (the per-turn budget)

4. **Spend AP in a loop**: calls `pod_combat_ai_try_action_effect` up to 6 times. Each call:
   - Checks AP >= 1 and combat not over
   - Calls `pod_combat_ai_csv_select_effect` to pick and execute a move
   - The move spends its AP cost from the pool

5. **Save workspace**: writes the modified HP/morale/buffs back to the actor and target slots

6. **Check victory**: if any team is fully KO'd, combat ends

---

## Move Selection: The Weighted Random List

`pod_combat_ai_csv_select_effect` is a single `random_list` block containing one entry per active skill in the CSV. The generator builds it automatically from every row with `status = implemented`.

### Entry Structure

Each entry in the random list looks like:

```
{base_weight} = {
    trigger = {
        # 1. Can the AI afford this move? (AP check)
        pod_combat_can_use_{key}_trigger = yes

        # 2. Does the AI have the required trait? (if set)
        exists = var:pod_combat_actor_char
        var:pod_combat_actor_char = {
            has_trait = {required_trait}
        }

        # 3. Is the targeting mode valid? (e.g., has allies for single-ally)
        # (targeting-specific availability gate)
    }

    # 4. Anti-repetition: halve weight if this was the last move used
    modifier = {
        factor = 0.5
        has_variable = pod_combat_ai_last_move
        var:pod_combat_ai_last_move = flag:{key}
    }

    # 5. Situational modifiers (heal when hurt, guard when low, etc.)
    # (varies by move role)

    # 6. Execute the move
    pod_combat_use_{key}_effect = yes

    # 7. Record what we just did
    set_variable = { name = pod_combat_ai_last_move value = flag:{key} }
}
```

### Base Weights by Category

The `combat_category` column determines the AI's baseline preference:

| Category | Base Weight | Role |
|----------|------------|------|
| ATK | 15 | Offensive — AI favors dealing damage |
| PWR | 12 | Power moves — buffs, transformations |
| CTL | 10 | Control — debuffs, crowd control |
| DEF | 8 | Defensive — guards, heals, dodge |

A skill's `ai_weight` CSV column overrides this. Leave it blank to use the category default. Set a specific number to increase or decrease that skill's selection frequency relative to other moves.

---

## Anti-Repetition

Every move entry includes a modifier that checks `var:pod_combat_ai_last_move`. If the AI used this exact move on its previous action, the weight is multiplied by 0.5 (halved). This:

- Prevents the AI from spamming a single high-weight move
- Forces tactical variety
- Only affects the immediately previous move (two moves ago is fair game)

On the first action of combat, `pod_combat_ai_last_move` doesn't exist yet, so the modifier's `has_variable` guard prevents it from firing.

---

## Energy Attrition (AI-Only Soft Resource Drain)

AI combatants do not actually pay Blood / Gnosis / Willpower / other energy costs — those costs only deduct when the PC fires a skill (the `var:pod_combat_current_actor = 0` gate in each skill effect). Without a counterweight, a fera NPC could fire 3-Gnosis gifts every turn forever.

The solution: a per-slot counter `pod_combat_c{N}_energy_used` increments on every energy-cost skill the combatant fires (counts PC usage too, but it's cosmetic for them since they pay real energy). The AI random_list emits **4 stacking 0.75 multipliers** for every skill with `energy_cost > 0`:

```
modifier = { factor = 0.75  has_variable = ...energy_used  var:...energy_used >= 1 }
modifier = { factor = 0.75  has_variable = ...energy_used  var:...energy_used >= 2 }
modifier = { factor = 0.75  has_variable = ...energy_used  var:...energy_used >= 3 }
modifier = { factor = 0.75  has_variable = ...energy_used  var:...energy_used >= 4 }
```

Effective penalty stack:

| Energy skills used so far | Multiplier |
|---|---|
| 0 | 1.0× |
| 1 | 0.75× |
| 2 | ~0.56× |
| 3 | ~0.42× |
| 4+ | ~0.32× (capped at 4 stacks) |

Non-energy skills (physical strikes, guard, feint, dodge) are unaffected, so an AI that's burned through its gifts naturally drifts toward mundane attacks over time.

The counter resets per combat via `pod_combat_c{N}_energy_used value = 0` in `pod_combat_init_slot_from_character_effect`.

---

## Situational Modifiers

The generator automatically adds context-aware weight modifiers based on the move's role. These are not configurable per-skill in the CSV — they're inferred from the move's stats:

### Heal Moves (hp_heal > 0, no "drain" in special)

```
modifier = {
    factor = 3
    pod_combat_player_hp < pod_combat_player_max_hp
}
```

When the AI is wounded, healing moves become 3x more likely.

### Morale Heal Moves (morale_heal > 0)

```
modifier = {
    factor = 3
    var:pod_combat_player_morale < 10
}
```

When morale is critically low (below 10), rally/morale-restore moves spike in priority.

### Guard

```
modifier = {
    factor = 2
    pod_combat_player_hp < pod_combat_player_max_hp
}
```

Guard becomes 2x more likely when the AI is hurt — plays defensively when losing.

### Feint / Remove-Guard (special contains "remove_guard")

```
modifier = {
    factor = 3
    has_variable = pod_combat_opponent_is_guarding
}
```

When the target is guarding, feint-like moves become 3x more likely. The AI will actively try to break defenses.

### Combined Example

An AI at half HP facing a guarding opponent would see:
- Strike (ATK): weight 15 (base)
- Guard (DEF): weight 16 (8 base x 2 wounded)
- Heal (DEF): weight 24 (8 base x 3 wounded)
- Feint (CTL): weight 30 (10 base x 3 opponent guarding)

The feint would be most likely, followed by healing.

---

## Tiered Buffs / Debuffs and AI

The tiered buff/debuff system (see `SKILL_AUTHORING_GUIDE.md` for full rules) applies a per-slot tier gate to prevent a single buff skill from stacking with itself. **The gate is PC-turn-only** — AI bypasses it entirely.

This is intentional:

- The AI already picks one skill per turn through the weighted random list, so "spam the same buff three times in a row" isn't a failure mode it naturally produces.
- Gating the AI by tier would require rebuilding the gate inside every `trigger = {}` block in `pod_combat_ai_csv_select_effect` and expanding target-slot dispatching per move — a lot of generated noise for little behavioral benefit.
- AI usage of a tier skill still **applies the tier correctly**. If an enemy uses `soak_buff_medium_combat`, their `pod_combat_c{slot}_soak_buff_combat_tier` is set to 2 and the recalc-from-base pass rebuilds their live `_soak` from `_base_soak` plus the sum of active tier magnitudes.

Practical consequence: a patient AI can cycle through small → medium → large versions of the same stat buff across rounds, upgrading itself over time. If this becomes a design problem for a specific AI encounter, add an anti-repetition tag or lower the skill's `ai_weight` rather than duplicating the gate logic.

The player-side gate still works whenever the PC is the actor (including when the PC uses the move against an AI-held tier on the target). Only AI actors are ungated.

---

## Trait Gating

Moves with a `required_trait` in the CSV are only available to AI combatants that have that trait. The generator emits a trigger block that checks `var:pod_combat_actor_char`:

```
trigger = {
    exists = var:pod_combat_actor_char
    var:pod_combat_actor_char = {
        has_trait = celeritydiscipline
    }
}
```

`var:pod_combat_actor_char` is set at the start of each AI turn to the acting combatant's character reference. This means:

- A vampire NPC with `celeritydiscipline` can use Celerity moves
- A mortal NPC cannot, even though the moves exist in the random list
- All moves the AI doesn't qualify for are simply gated out by the trigger and never selected

The `TRAIT_CHECK_OVERRIDES` mapping handles special cases (tribes as faiths, `fera` as werewolf/bastet/mokole OR, `hunter` as supehunter, etc.) — the same mapping used for player-side checks.

---

## Targeting System

### Turn-Start Target

At the beginning of each AI turn, a target is selected based on team:

- **Player-team AI** (slots 1-4 allies): picks from enemy slots 5-9
- **Enemy-team AI** (slots 5-9 enemies): picks from player slots 0-4

Target selection uses a weighted random list:
- Base weight: 1 for all slots
- +50 for alive, valid-team targets
- x2 for targets with HP <= 2 (finishing blow bias)

### Mid-Turn Target Swapping

Some moves target allies (heals, buffs) or have specific target preferences. The `targeting` and `target_priority` CSV columns control this:

**Targeting modes:**

| Value | Behavior |
|-------|----------|
| `single-enemy` | Default. Hits the turn-start enemy target |
| `single-ally` | Swap to an ally, execute, restore enemy target |
| `single-pc` | Always targets the PC (slot 0) |
| `self` | Targets the caster. No swap needed |
| `team-enemy` | Hits all enemies (AoE) |
| `team-ally` | Hits all allies (AoE) |

**Target priority modes** (for single-ally and single-enemy):

| Priority | Behavior |
|----------|----------|
| `default` | First alive valid target found |
| `wounded` | Prefer lowest-HP target (+100 weight when HP < max) |
| `healthy` | Prefer full-HP target (+100 weight when HP >= max) |
| `round_robin` | Penalize recently-picked target (x0.2 weight), distributes attention |
| `threat` | Prefer high-prowess target (+100 if prowess >= 5, +200 more if >= 8) |

### The Swap Dance

For `single-ally` with a priority, the AI does a three-step sequence:

1. **Swap**: save current enemy target, pick ally target, load ally into workspace
2. **Execute**: run the move effect (heals/buffs the ally)
3. **Restore**: put the enemy target back into workspace

This ensures buff/heal moves affect the right character while the AI's main damage target isn't lost.

---

## Slot System

The combat minigame uses 10 numbered slots:

| Slots | Team | Description |
|-------|------|-------------|
| 0 | Player | Always the PC. Only slot that pauses for human input |
| 1-4 | Player | Coterie allies (filled in NvN modes) |
| 5 | Enemy | Primary opponent |
| 6-9 | Enemy | Additional enemies (filled in NvN modes) |

In a 1v1 duel, only slots 0 and 5 are populated. The AI system treats this identically to a group fight — it's just a degenerate NvN with 8 empty slots.

---

## Workspace Bridge

The combat system uses a shared "workspace" that move effects read from and write to. Before each action, the workspace is loaded from the acting slot's variables:

- `pod_combat_player_*` = the **actor's** stats (HP, morale, soak, prowess, buffs)
- `pod_combat_opponent_*` = the **target's** stats

After the action, the workspace is saved back to the respective slots. This workspace indirection is what allows the same `pod_combat_use_{key}_effect` to work for both player and AI — the effect doesn't need to know which slot it's operating on.

---

## Tuning Guide

### Make a move more/less likely for AI

Set the `ai_weight` column in the CSV:
- Higher than the category default = AI picks it more
- Lower = AI picks it less
- 0 or blank = use category default

### Add a new situational modifier

Edit `_ai_situational_modifiers()` in `generate_combat_files.py`. The function receives a skill dict and returns a list of modifier block strings. Add new conditions based on any workspace variable or skill property.

### Change category base weights

Edit `AI_BASE_WEIGHTS` in `generate_combat_files.py`:
```python
AI_BASE_WEIGHTS = {
    "ATK": 15,
    "CTL": 10,
    "DEF": 8,
    "PWR": 12,
}
```

### Adjust anti-repetition strength

The `0.5` factor in the anti-repetition modifier can be changed in `generate_ai_select_effect()`. Lower values (e.g., 0.2) make the AI strongly avoid repeats; higher values (e.g., 0.8) let it repeat more freely.

### Adjust energy-attrition strength

Each stacking energy-use penalty is `0.75` by default (4 stacks → ~0.32× at 4+ energy skills). Change the `0.75` literal in `generate_ai_select_effect()` to tighten (e.g., `0.6`) or loosen (e.g., `0.85`) the curve. Raising the stack count from 4 further rewards patient AI; lowering it caps drain earlier.

### Change target-selection bias

The low-HP bias (x2 when HP <= 2) is in the hand-maintained `pod_combat_ai_select_enemy_target_effect` and `pod_combat_ai_select_player_target_effect` in `common/scripted_effects/POD_combat/pod_combat_ai_effects.txt`.

### Adjust initiative variance

The initiative random range (1-30 across 7 buckets) is in `pod_combat_calculate_initiative_effect` in `common/scripted_effects/POD_combat/pod_combat_group_effects.txt`. A wider range makes turn order more random; a narrower range makes prowess more deterministic.

---

## File Map

All scripted-effect files live in `common/scripted_effects/POD_combat/`. The GUI window files live in `gui/POD_windows/`. The table below lists just the filename for readability.

| File | Content | Maintained by |
|------|---------|--------------|
| `pod_combat_ai_effects.txt` | Turn execution, target selection, workspace bridge, swap dance | Hand-maintained |
| `pod_combat_ai_generated_effects.txt` | `pod_combat_ai_csv_select_effect` — the move picker | Generated from CSV |
| `pod_combat_group_effects.txt` | Initiative, turn order, victory check, round management, workspace load/save, shapeshift pre-pass | Hand-maintained |
| `pod_combat_effects.txt` | Damage pipelines, auto-resolve, cleanup, stealth consumption | Hand-maintained |
| `pod_combat_tier_effects.txt` | Tier recalc (soak/hit buff/debuff) and round/combat-end revert | Hand-maintained |
| `pod_combat_control_guis.txt` | End Turn / Auto-Resolve / Help / Forfeit / Target Selection handlers (under `common/scripted_guis/`) | Hand-maintained |
| `pod_combat_static_l_english.yml` | Window labels, help event, debug interaction text, toasts (under `localization/english/`) | Hand-maintained |
| `generate_combat_files.py` | Generator — reads CSV, emits the 9 per-skill output files | Python script |
| `pod_combat_skills_master.csv` | Source of truth for all moves, weights, traits, targeting | Designer-edited |
