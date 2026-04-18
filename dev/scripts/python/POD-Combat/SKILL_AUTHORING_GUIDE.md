# Combat-PoD Skill Authoring Guide

This guide explains how to add new combat moves to the minigame by editing `pod_combat_skills_master.csv` and running the generator.

## Quick Start

1. Open `pod_combat_skills_master.csv` in a spreadsheet editor (Excel, LibreOffice Calc, Google Sheets)
2. Add a new row at the bottom
3. Fill in the columns (see reference below)
4. Save as CSV (UTF-8 with BOM)
5. Run `python generate_combat_files.py` from the `Combat-PoD/` directory
6. Check the output for warnings about invalid perk keys

---

## CSV Column Reference

### Identity Columns

| Column | Required | Description |
|--------|----------|-------------|
| `skill_key` | Yes | Unique internal ID. Lowercase, underscores only. Must not collide with any existing key. Example: `flame_lash` |
| `display_name` | Yes | Human-readable name shown in the skill list and combat log. Example: `Flame Lash` |
| `category` | Yes | Always `active` for usable moves |
| `config_section` | Yes | Groups moves under a header in the skill config screen. Moves in the same section share a visibility gate. Example: `Lures of Flames` |
| `discipline` | No | Leave blank. Legacy column, unused |

### Access Control

| Column | Required | Description |
|--------|----------|-------------|
| `required_trait` | No | PoD trait the character must have to equip/use this move. Leave blank for moves available to everyone. See "Trait Reference" below |
| `pod_perk_key` | No | If set, the character must also have this specific lifestyle perk. The generator validates perk keys against `POD Reference/` at build time and drops invalid ones with a warning. Use the exact perk definition name (e.g., `demon_arts_devil_fist_perk`) |

### Costs

| Column | Required | Description |
|--------|----------|-------------|
| `ap_cost` | Yes | Action Points spent when the move fires. Each turn gives 6 AP. Most attacks cost 2-3 AP; buffs/heals cost 2-3 AP |
| `energy_cost` | No | Splat-specific resource cost (blood for vampires, gnosis for fera, chi for kuei-jin, etc.). The generator picks the correct PoD spending effect based on `required_trait`. Set to 0 or leave blank for free moves |
| `stress_cost` | No | CK3 stress added to the actor. Used for WP costs. 0 = no stress |
| `gold_cost` | No | CK3 gold deducted from the actor when the move fires. Uses `remove_short_term_gold`. 0 = no gold cost |
| `prestige_cost` | No | CK3 prestige deducted from the actor. 0 = no prestige cost |
| `piety_cost` | No | CK3 piety deducted from the actor. 0 = no piety cost |

### Damage Output

| Column | Required | Description |
|--------|----------|-------------|
| `damage_source` | No | Determines the damage pipeline. See "Damage Sources" below |
| `damage_type` | No | `Superficial` or `Aggravated`. Aggravated is soaked at half effectiveness (−50% soak chance) and tracked separately for PoD health write-back. Leave blank or `Superficial` for normal damage |
| `hp_damage` | Yes | Hit points of damage dealt to the target. 0 for non-damaging moves |
| `morale_damage` | Yes | Morale damage dealt. When morale hits 0, the target is defeated. 0 for non-morale moves |
| `self_damage` | Yes | HP damage dealt to yourself when using the move. Used for reckless attacks. 0 for most moves |

### Healing

| Column | Required | Description |
|--------|----------|-------------|
| `hp_heal` | Yes | HP restored to the target (self for `targeting = self`). 0 for non-healing moves |
| `morale_heal` | Yes | Morale restored. 0 for most moves |

### Buffs and Debuffs

All buff and debuff mechanics live in the `special` column — there are no dedicated columns. Each buff/debuff flag follows the pattern:

```
{stat}_{direction}_{size}_{duration}
```

| Slot | Values |
|------|--------|
| `stat` | `soak` \| `hit` |
| `direction` | `buff` \| `debuff` |
| `size` | `small` \| `medium` \| `large` |
| `duration` | `round` \| `combat` |

**Magnitudes** (uniform across stats): small = 10, medium = 20, large = 30.

Example flags: `soak_buff_medium_combat`, `hit_debuff_large_round`, `hit_buff_small_round`.

#### Tier Stacking Rules

A character can hold **one buff AND one debuff per (stat, duration) combination**. The can_use gate enforces this:

- Applying a higher tier **overwrites** a lower tier (small → medium → large). The live stat is rebuilt from `base_{soak,hit_chance}` plus the sum of all currently-active tier magnitudes — so overwriting medium with large cleanly yields a net +30 (new total) rather than a +10 delta, and clamping losses never accumulate.
- Applying the **same tier or lower** when a higher tier is already active is blocked — the skill button becomes unavailable and the can_use trigger returns false.
- At round end, round-duration tier variables are cleared and every slot's stats are recalculated from base + remaining combat-duration tiers.
- At combat end, all tier variables are cleared.

For **buffs**, the gate checks the actor's slot (PC = c0). For **debuffs**, it dispatches on `pod_combat_pc_target` to check the currently-targeted enemy's tier. AI bypasses the gate (AI turn logic only picks one skill per turn anyway).

Example: a skill with `soak_buff_medium_combat` is only usable by the PC when `pod_combat_c0_soak_buff_combat_tier < 2`. A skill with `soak_buff_large_combat` can always overwrite a lower-tier combat soak buff.

#### Other Buff/Debuff Flags (non-tier)

A few modifiers don't fit the tier model because they're one-shot or act outside the stat system:

| Flag | Effect |
|------|--------|
| `ap_gain_N` | Instantly grants the actor +N AP this turn. Can be reused; each use pays its own AP cost. Example: `ap_gain_2` |
| `ap_drain_N` | Reduces the target's AP pool by N on their next turn (min 1 AP). Applied once then cleared |
| `initiative_debuff_N` | Subtracts N from the target's next-round initiative roll |

These coexist with tier flags on the same skill. For example, a skill could have `special = hit_debuff_medium_round, ap_drain_2` to both halve the target's accuracy AND steal 2 AP.

### Special Mechanics

| Column | Description |
|--------|-------------|
| `special` | Comma-separated special flags. See Special Flags table below |

#### Special Flags

Flags are comma-separated in the `special` column. Multiple flags on the same skill stack — e.g. `special = bypass_guard, hit_debuff_medium_round, ap_drain_2`.

| Flag | Effect |
|------|--------|
| `bypass_guard` | Attack ignores the Guard state — always hits through guard |
| `set_guard` | Activates guard stance (blocks next physical attack). Persists until it blocks an attack or combat ends |
| `dodge` | Grants dodge state (negates next incoming attack of any type). Persists until consumed by an attack or combat ends |
| `stealth` | Grants stealth (negates next incoming attack AND +30 hit chance while active). Persists until consumed — stealth is consumed whichever happens first: the actor attacks anyone, or an attack lands against the actor. Can also be forcibly stripped by `bypass_stealth`. Stealth is checked **before** dodge in the damage pipeline, so a stealthed-and-dodging character keeps their dodge when the first incoming attack is caught by stealth |
| `retaliate_if_hit` | Sets a retaliation stance. If the actor is hit by any attack, they automatically deal `hp_damage` back to the attacker. The move itself doesn't deal direct damage — `hp_damage` is the retaliation value. Consumed on first trigger; persists until consumed or combat ends |
| `retaliate_if_missed` | Same as `retaliate_if_hit` but triggers when an attacker misses the actor. Consumed on first trigger; persists until consumed or combat ends |
| `bypass_dodge` | Attack ignores the target's dodge state. The dodge is consumed without negating the attack. Ideal for AoE/area attacks that can't be dodged |
| `bypass_stealth` | Attack breaks through stealth — strips the target's stealth state AND reverses the +30 hit chance bonus. Ideal for perception/detection abilities |
| `{stat}_{direction}_{size}_{duration}` | Tiered buff or debuff. See the **Buffs and Debuffs** section below for the full rules |
| `ap_gain_N` | Instant +N AP for the actor (not tiered; stacks across uses) |
| `ap_drain_N` | Drains N AP from target's next turn |
| `initiative_debuff_N` | -N to target's next-round initiative |

### Targeting

| Column | Description |
|--------|-------------|
| `targeting` | Who the move fires at. Options: `single-enemy` (default, one enemy), `single-ally` (one ally), `self` (caster only), `team-enemy` (all enemies), `team-ally` (all allies), `single-pc` (player character only) |

### AI Behavior

| Column | Description |
|--------|-------------|
| `ai_weight` | Override for the AI's random_list weight when selecting this move. Leave blank to use category defaults (ATK=15, PWR=12, CTL=10, DEF=8). Higher = AI picks it more often |
| `target_priority` | AI targeting hint for single-ally and single-enemy moves. Options: `wounded` (prefer lowest-HP target), `healthy` (prefer full-HP target), `round_robin` (penalize recently-picked slot to spread picks), `threat` (prefer high-prowess target). Leave blank or set to `default` for "first alive valid target" |

### Combat Role

| Column | Description |
|--------|-------------|
| `combat_category` | `ATK`, `DEF`, `CTL`, or `PWR`. Determines the equip slot. Players can equip up to 4 moves per category (16 total). ATK = damage, DEF = defense/healing, CTL = debuffs/control, PWR = buffs/power moves |

### Metadata

| Column | Description |
|--------|-------------|
| `status` | Must be `implemented` for the move to be generated. Use `future` or `planned` to skip a row |
| `priority` | Freeform label for your own tracking. `core` is conventional |
| `notes` | Freeform notes. Not used by the generator |
| `pod_move_key` | Legacy column. Leave blank |
| `log_msg_id` | Auto-assigned by rebuild scripts. For manual additions, pick any unique integer not already in use (check the highest existing value and increment). Each move needs a unique ID for the combat log display |
| `loc_name` | Display name for localization. Usually matches `display_name`. If blank, falls back to `display_name` |

---

## Damage Sources

The `damage_source` column determines which damage pipeline the move uses. Each pipeline has different interactions with guard, soak, hit chance, and creature-type vulnerabilities.

| Source | Pipeline | Notes |
|--------|----------|-------|
| `Physical` | Hit chance roll, guard check, soak check, then damage | Standard melee/ranged. Misses against high-prowess targets |
| `Supernatural` | Auto-hit, no guard, soak check, then damage | Magic/supernatural. Always hits, but can be soaked |
| `Mental` | Auto-hit, no guard, no soak, direct damage | Psychic attacks. Cannot be blocked or soaked |
| `Fire` | Physical pipeline, but aggravated vs vampires | Promotes to aggravated against vulnerable creatures |
| `Sunlight` | Physical pipeline, but aggravated vs vampires | Same as Fire for gameplay purposes |
| `Silver` | Physical pipeline, but aggravated vs werewolves and Bastet | Anti-shifter |
| `Gold` | Physical pipeline, but aggravated vs Mokole | Anti-saurian |
| `Holy` | Physical pipeline, but aggravated vs vampires, demons, kuei-jin, wraiths | Blessed/divine attacks |
| `None` | No damage pipeline. Used for pure buff/heal/debuff moves | Buff and support moves |

### Aggravated vs Superficial

- **Superficial** damage passes through the full pipeline (hit, guard, soak)
- **Aggravated** damage is soaked at half effectiveness (-50% soak chance). It also tracks separately for PoD health write-back (aggravated damage on the PoD health track is harder to heal)
- Promoted sources (Fire, Silver, Gold, Holy) check the target's creature type. If vulnerable, the damage is treated as aggravated; otherwise it uses the baseline `damage_type` from the CSV

---

## Trait Reference

The `required_trait` column gates who can equip the move. The generator maps these to the correct PoD check automatically.

### Vampire Disciplines
Use the trait name directly: `celeritydiscipline`, `celerityadvanced`, `potencediscipline`, `potenceadvanced`, `fortitudediscipline`, `fortitudeadvanced`, `presencediscipline`, `presenceadvanced`, `auspexdiscipline`, `auspexadvanced`, `dominatediscipline`, `dominateadvanced`, `obfuscatediscipline`, `obfuscateadvanced`, `obtenebrationdiscipline`, `obtenebrationadvanced`, `proteandiscipline`, `proteanadvanced`, `animalismdiscipline`, `animalismadvanced`, `serpentisdiscipline`, `serpentisadvanced`, `vicissitudediscipline`, `vicissitudeadvanced`, `valerendiscipline`, `valerenadvanced`, `quietusdiscipline`, `quietusadvanced`, `daimoniondiscipline`, `daimonionadvanced`, `dementationdiscipline`, `dementationadvanced`, `temporisdiscipline`, `temporisadvanced`, `abombwediscipline`, `abombweadvanced`, `kaidiscipline`, `necromancydiscipline`, `necromancyadvanced`, `bloodsorcerydiscipline`, `bloodsorceryadvanced`

Basic discipline traits (`*discipline`) are prerequisites for advanced (`*advanced`). A section mixing both will show for players with basic; advanced moves auto-hide until the player has the advanced trait.

### Vampire Generic
`vampire` - any vampire can equip

### Fera (Shifters)
- `fera` - any werewolf, bastet, or mokole (uses `pod_combat_is_fera_trigger` which ORs werewolf/bastet/mokole)
- `werewolf` - garou only
- `bastet` - feline shifters only
- `mokole` - saurian shifters only

### Fera Auspices (Garou)
`ahroun`, `galliard`, `philodox`, `ragabash`, `theurge`

### Fera Breeds (Bastet)
`bagheera`, `bubasti`, `ceilican`, `khan`, `simba`, `swara` (mapped to PoD faiths)

### Fera Streams (Mokole)
`rising_sun`, `noonday_sun`, `setting_sun`, `midnight_sun`, `shrouded_sun`, `decorated_sun`, `eclipsed_sun`

### Werewolf Tribes
`werewolf_blackfury`, `werewolf_bonegnawer`, `werewolf_childofgaia`, `werewolf_fianna`, `werewolf_getoffenris`, `werewolf_hakken`, `werewolf_redtalon`, `werewolf_shadowlord`, `werewolf_silentstrider`, `werewolf_silverfang`, `werewolf_stargazer`, `werewolf_warderofmen`, `werewolf_blackspiraldancer`, `werewolf_whitehowler` (mapped to PoD faiths)

### Other Splats
- `hunter` - mapped to `POD_is_supehunter_trigger`
- `truefaith` - True Faith characters
- `sorcerer` - mortal sorcerers 
- `demon` - Fallen/demons
- `mummy` - Amenti mummies
- `kueijin` - Kuei-jin 

### Energy Cost by Splat

The generator automatically calls the correct PoD energy-spend effect based on `required_trait`:

| Splat | Effect Called | Resource |
|-------|-------------|----------|
| Vampire (all discipline traits, `vampire`) | `POD_discipline_cost_effect` | Blood |
| Fera (all fera/werewolf/bastet/mokole/auspice/breed traits) | `POD_gift_cost_effect` | Gnosis |
| Sorcerer | `POD_sorcery_cost_effect` | Mana (splat-agnostic) |
| Mummy | `POD_hekau_cost_effect` | Sekhem |
| Demon | `POD_lore_energy_cost_effect` | Faith/Resolve |
| Kuei-jin | `POD_kj_art_cost_effect` | Willpower |
| Hunter/Truefaith | None | No energy system |

---

## Section Naming Conventions

The `config_section` value becomes:
1. A header in the skill equip screen (shown in UPPERCASE)
2. A visibility group (all moves in a section share the same trait gate)

Choose descriptive names that group thematically related moves. Examples:
- Discipline sections: `Celerity`, `Potence`, `Obtenebration`
- Path sections: `Path of Blood`, `Lures of Flames`, `Way of Fire`
- Fera sections: `Tribe Silver Fang`, `Auspice Ahroun`, `Fera Common`
- Generic: `Base Physical`, `Base Tactical`, `Innate Vampire`

If moves in the same section have different `required_trait` values (e.g., basic + advanced discipline), the section header shows when the player has ANY of those traits, and individual moves hide when the player lacks their specific trait.

---

## Example: Adding a New Vampire Discipline Move

```csv
skill_key,display_name,category,config_section,discipline,required_trait,ap_cost,energy_cost,stress_cost,gold_cost,prestige_cost,piety_cost,damage_source,damage_type,hp_damage,morale_damage,self_damage,hp_heal,morale_heal,special,pod_perk_key,pod_move_key,status,priority,notes,combat_category,ai_weight,target_priority,log_msg_id,targeting,loc_name
eyes_of_the_beast,Eyes of the Beast,active,Animalism,,animalismdiscipline,2,1,0,0,0,0,None,,0,0,0,0,0,"hit_buff_medium_combat",,,implemented,core,Sharpen senses for the rest of combat,DEF,,,9001,self,Eyes of the Beast
```

This creates:
- A DEF move called "Eyes of the Beast"
- In the "Animalism" section (visible only to characters with `animalismdiscipline`)
- Costs 2 AP + 1 Blood
- Grants +20 hit chance for the rest of combat (medium tier, combat duration)
- Targets self (the caster)
- Can't be reused unless overwritten by a `large` hit_buff

---

## Regenerating After Edits

```bash
cd Combat-PoD/
python generate_combat_files.py
```

The generator:
- Reads the CSV
- Validates all `pod_perk_key` values against `POD Reference/`
- Prints warnings for invalid perks (they're dropped, not fatal)
- Writes 9 output files (effects, triggers, GUIs, values, localization, etc.)
- Reports total skill counts

After regenerating, launch CK3 and check the error log for any issues. Common problems:
- Duplicate `skill_key` values (each must be unique)
- Missing traits (the trait must exist in PoD's trait database)
- Unbalanced braces (the generator handles this, but hand-edits to other files can cause issues)

---

## Balance Guidelines

These are suggestions, not hard rules:

- **AP costs**: 1-2 for weak moves, 2-3 for standard, 3-4 for powerful. 6 AP per turn means 2-3 actions
- **HP damage**: 1-2 (light), 3 (standard), 4 (heavy), 5+ (exceptional, should have high costs)
- **Morale damage**: Similar scale to HP. Morale defeat is an alternative win condition
- **Energy costs**: 1 for standard supernatural moves, 2 for powerful ones. 0 for purely physical
- **Buff/debuff tiers**: Magnitudes are fixed — small = 10, medium = 20, large = 30. Tune AP cost to match tier, not the other way around: small tiers on 1-2 AP moves, medium on 2-3 AP, large on 3-4 AP (often with an energy cost)
- **Tier duration**: `round` is a cheap tactical boost that expires at round end; `combat` is a significant investment that lasts the whole fight. Combat-duration large tiers should feel expensive
- **AP drain**: 1-2 is moderate (target loses 1-2 actions next turn), 3+ is devastating (costs should reflect this)
- **Initiative debuff**: `initiative_debuff_5` is subtle, `_10` is noticeable, `_15` is a near-guaranteed turn order shift. Combine with `ap_drain_N` for powerful tempo control
- **Bypass guard**: Reserve for high-cost signature moves (3+ AP, often 2 energy)
- **Aggravated damage**: Should cost more (energy, AP, or stress) since it ignores soak
- **Self-damage**: 1-2 for blood magic style moves that trade HP for power
