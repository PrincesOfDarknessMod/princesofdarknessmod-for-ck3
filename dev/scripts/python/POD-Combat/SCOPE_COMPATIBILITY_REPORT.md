# Combat-PoD Scope Compatibility Report

When the combat minigame replaces a PoD/vanilla duel, the follow-up event (`OUTPUT_EVENT`) needs to read scopes that were set by the original event chain. The minigame breaks the scope chain — all scopes must be reconstructed from stashed character variables.

## Scopes Reconstructed by the Dispatcher

These scopes are available in follow-up events after a minigame-driven duel:

| Scope Name | Source | Notes |
|------------|--------|-------|
| `scope:sc_initiator` | SC_INITIATOR param | Who started the duel |
| `scope:sc_attacker` | SC_ATTACKER param | Attacker |
| `scope:sc_defender` | SC_DEFENDER param | Defender |
| `scope:sc_victor` | Minigame winner | Set from pod_combat_winner |
| `scope:sc_loser` | Minigame loser | Set from pod_combat_loser |
| `scope:defender` | = SC_DEFENDER | Alias |
| `scope:attacker` | = SC_ATTACKER | Alias |
| `scope:challenger` | = SC_ATTACKER | Alias |
| `scope:fatality` | FATALITY param | Flag value |
| `scope:fixed` | FIXED param | Flag value |
| `scope:locale` | hardcoded battlefield | Not reconstructed from param |
| `scope:sc_finished` | always yes | Flag value |
| `scope:victory_type` | always flag:skill | Flag value |

## Missing Scopes That Will Cause Errors

Any follow-up event reading a scope NOT in the above list will get "Undefined event target" errors. The two most common missing scopes are:

- **`scope:actor`** — used by 34 callers (most character interactions). Maps to SC_ATTACKER.
- **`scope:recipient`** — used by 33 callers (most character interactions). Maps to SC_DEFENDER.

These could be added to the dispatcher to fix the majority of callers.

## Follow-Up Events by Risk Level

### HIGH RISK — Widely Used, Simple Fix (add scope:actor + scope:recipient)

These events only need `scope:actor` and/or `scope:recipient` which map directly to the attacker/defender:

| Output Event | Caller File | Missing Scopes |
|---|---|---|
| `single_combat.1006` | `00_trait_interactions.txt`, character interactions | `scope:actor`, `scope:recipient` |
| `perk_interaction.0101` | `00_perk_interactions.txt`, `00_trait_interactions.txt` | `scope:actor`, `scope:recipient` |
| `trait_specific_interactions.0151` | `00_trait_interactions.txt` | `scope:actor`, `scope:recipient` |
| `trait_specific_interactions.0153` | `00_trait_interactions.txt` | `scope:actor`, `scope:recipient` |
| `trait_specific_interactions.0155` | `00_trait_interactions.txt` | `scope:actor`, `scope:recipient` |
| `culture_tradition_events.0001` | `00_tradition_interactions.txt` | `scope:actor`, `scope:recipient` |
| `POD_temporis.101` | `POD_canon_chars_interactions.txt` | `scope:actor`, `scope:recipient` |
| `POD_fae_interactions.100` | `POD_fae_interactions.txt` | `scope:actor`, `scope:recipient` |
| `kueijin_scheme.201` | PoD kueijin scheme events | `scope:actor`, `scope:recipient` |

### HIGH RISK — PoD-Specific, Need Custom Scope Names

These events read event-chain-specific scope names that can't be generically mapped:

| Output Event | Caller | Missing Scopes | Maps To |
|---|---|---|---|
| `POD_web_of_knives.1010` | `POD_web_of_knives_events.txt` | `scope:victim` | SC_DEFENDER — **FIXED by submod override** |
| `POD_vamphunt.31` | PoD vampire hunt events | `scope:target`, `scope:victim` | SC_DEFENDER |
| `POD_camarilla.3000` | `POD_canon_chars_interactions.txt` | `scope:alastor` | SC_ATTACKER (custom char) |
| `POD_heists.201` | PoD heist events | `scope:adversary` | SC_DEFENDER |
| `POD_heists.204` | PoD heist events | `scope:adversary` | SC_DEFENDER |
| `POD_wyrm.510` | PoD Wyrm events | `scope:shadowflame`, `scope:wyrm_champion` | Custom chars |

### MEDIUM RISK — Vanilla DLC Events, Complex Scope Requirements

These events read multiple custom scopes including third-party characters, artifacts, and other non-combatant data that CANNOT be reconstructed from duel parameters:

| Output Event | Missing Scopes (sample) | Issue |
|---|---|---|
| `tribal.1021` | `scope:liege_to_challenge`, `scope:liege_champion` | Third-party scopes |
| `artifact.2001` | `scope:artifact`, `scope:antiquarian`, `scope:this_artifact` | Non-character scopes |
| `hold_court.6101` | `scope:6100_vassal_1`, `scope:6100_vassal_2`, `scope:6100_lord` | Multiple third parties |
| `hold_court.8211` | `scope:aggressor_vassal`, `scope:vassal_claim`, `scope:vassal_faction` | Complex political scopes |
| `fp1_tbc.0011` | `scope:tbc_gold`, `scope:tbc_humiliation`, `scope:champion` | Trial by combat scopes |
| `fp2_struggle.2022` | `scope:fp2_2009_garduna_guild_master` | Unique character scope (x10 callers) |
| `jason_locale_events.201` | `scope:drunk_knight`, tournament scopes | Tournament-specific |
| `diarchy.9028` | `scope:usurper`, `scope:liege` | Diarchy-specific |
| `ep3_contract_event.0571` | `scope:task_contract`, `scope:task_contract_employer` | Contract scopes |
| `ep3_laamps.6002` | `scope:frederick` (x6 callers) | Named character scope |

### LOW RISK — Vanilla Events Unlikely to Fire for PoD Players

| Output Event | Context |
|---|---|
| `bp1_yearly.5710` through `.5729` | Vanilla rivalry yearly events |
| `bp1_yearly.6001` | Henrik events (DLC-specific) |
| `bp1_yearly.3203` | Chad yearly events |
| `bp2_yearly.7022` | Teen tribal events |
| `court.8162`, `court.9003` | Court events |
| `fp1_yearly.2001`, `.2101`, `.2201` | FP1 yearly events |
| `fp3_yearly.8005` | FP3 yearly events |
| `mpo_nomad_events.1021` | Nomad DLC events |
| `tgp_japan_yearly_events.1121` | Japan DLC events |

### LOW RISK — PoD Spirit/Umbra Events

| Output Event | Missing Scopes |
|---|---|
| `POD_fera_spirit_quest.29` | `scope:spawned_spirit` |
| `POD_umbra_crisis.111` | `scope:spirit` |
| `POD_umbra_expedition.100` | `scope:spirit` |
| `POD_umbra_expedition.304` | `scope:great_fenris` |

These involve umbra/spirit combat which may need separate handling regardless.

## Recommended Fixes

### Priority 1 — Add scope:actor and scope:recipient to Dispatcher

Adding these two aliases to the post-combat dispatch event (`pod_combat.9999`) would fix the majority of callers (9+ high-risk events):

```
var:pod_combat_sc_attacker = { save_scope_as = actor }
var:pod_combat_sc_defender = { save_scope_as = recipient }
```

**Caveat:** `scope:actor` in an interaction context is the interaction's built-in actor scope. Overwriting it in an event context should be fine since the follow-up event doesn't have an interaction actor.

### Priority 2 — Override Specific PoD Events

For PoD events with custom scope names (victim, alastor, adversary), create submod overrides that rewrite them to use `scope:defender`/`scope:attacker` — same approach as the `z_Combat-PoD_web_of_knives_override.txt` fix.

### Priority 3 — Accept Vanilla DLC Limitations

Events with complex third-party scopes (hold_court vassals, artifacts, trial by combat champions, tournament contestants) fundamentally cannot be fixed by scope reconstruction alone. These events depend on characters/objects that aren't the attacker or defender and were saved by parent events that no longer exist in the scope chain.

Options:
- Accept cosmetic errors (the duel outcome still applies via wounds/death)
- Override these events to gracefully handle missing scopes (null checks)
- Skip the minigame for specific OUTPUT_EVENTs that are known-broken (whitelist)
