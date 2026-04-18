#!/usr/bin/env python3
"""
generate_combat_files.py — CK3 PoD Combat System Code Generator

Reads pod_combat_skills_master.csv (sitting next to this script) and
writes 9 mod files into the devpod/ folder alongside the scripts/
tree. All paths are resolved from this file's own location, so the
script works regardless of the caller's working directory.

Expected repository layout:
    POD-Integration/
    ├── devpod/                          ← mod files land here
    │   ├── common/
    │   ├── events/
    │   ├── gui/
    │   └── localization/
    └── scripts/python/POD-Combat/
        ├── generate_combat_files.py     ← this script
        ├── pod_combat_skills_master.csv
        └── *.md (design docs)

Generated files (per-skill, rebuilt on every CSV change):
  1. devpod/common/scripted_effects/POD_combat/pod_combat_move_effects.txt
  2. devpod/common/scripted_triggers/pod_combat_triggers.txt
  3. devpod/common/scripted_guis/pod_combat_guis.txt
  4. devpod/common/scripted_guis/pod_combat_skill_guis.txt
  5. devpod/common/script_values/pod_combat_values.txt
  6. devpod/gui/POD_windows/pod_combat_window.gui
  7. devpod/gui/POD_windows/pod_combat_skills_window.gui
  8. devpod/localization/english/pod_combat_l_english.yml
  9. devpod/common/scripted_effects/POD_combat/pod_combat_ai_generated_effects.txt

Hand-maintained static infrastructure (NOT regenerated), all under devpod/:
  - common/scripted_effects/POD_combat/pod_combat_effects.txt
  - common/scripted_effects/POD_combat/pod_combat_group_effects.txt
  - common/scripted_effects/POD_combat/pod_combat_tier_effects.txt
  - common/scripted_effects/POD_combat/pod_combat_ai_effects.txt
  - common/scripted_effects/POD_combat/pod_combat_loadout_effects.txt
  - common/scripted_effects/POD_combat/z_Combat-PoD_override_single_combat_effects.txt
  - common/scripted_guis/pod_combat_control_guis.txt
  - common/character_interactions/pod_combat_debug_interaction.txt
  - events/pod_combat_events.txt
  - localization/english/pod_combat_static_l_english.yml

Run:
    python POD-Integration/scripts/python/POD-Combat/generate_combat_files.py
"""

import csv
import os
import re
from collections import OrderedDict

# ──────────────────────────────────────────────────────────────────────
# PATH RESOLUTION
# ──────────────────────────────────────────────────────────────────────
# Every path the script reads or writes is resolved from this file's
# location, not the caller's cwd. The layout is:
#
#     POD-Integration/
#     ├── devpod/                         ← DEVPOD_DIR (mod output)
#     └── scripts/python/POD-Combat/      ← SCRIPT_DIR
#         └── generate_combat_files.py
#
# To bootstrap in a new checkout (or a different path), only these
# constants need adjusting.

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# devpod/ sits three levels above SCRIPT_DIR:
#   POD-Combat/  →  python/  →  scripts/  →  POD-Integration/  →  devpod/
DEVPOD_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..", "..", "devpod")
)

# The CSV and helper .md docs live next to the script itself.
CSV_PATH = os.path.join(SCRIPT_DIR, "pod_combat_skills_master.csv")


def devpod_path(rel):
    """Join `rel` under DEVPOD_DIR. `rel` uses forward slashes for
    readability; os.path.join normalizes the separator per platform."""
    parts = rel.split("/")
    return os.path.join(DEVPOD_DIR, *parts)


# ──────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────

BOM = "\ufeff"

FERA_TRAITS = {"fera", "werewolf", "bastet", "mokole", "ahroun", "galliard", "philodox", "ragabash", "theurge"}

# Map CSV required_trait values to the scope-local check that actually works
# in PoD. Entries here REPLACE the default `has_trait = <value>` emission
# everywhere trait checks are written — scripted GUIs, script values, AI
# gates, etc. Keep the replacement as a single scope-local statement so it
# drops in wherever a has_trait line would go.
#
#   - hunter            → PoD uses `supehunter` as the splat trait
#   - werewolf_<tribe>  → tribes are modeled as faiths, not traits
#   - <bastet_breed>    → breeds are also faiths (bagheera, simba, etc.)
#   - werewolf_whitehowler → extinct tribe with no faith; gate on the tree root
TRAIT_CHECK_OVERRIDES = {
    "hunter":                     "POD_is_supehunter_trigger = yes",
    # PoD has no `fera` trait — dispatch to the combat-local trigger that
    # OR's werewolf/bastet/mokole. Defined in pod_combat_triggers.txt.
    "fera":                       "pod_combat_is_fera_trigger = yes",
    "werewolf_blackfury":         "faith = faith:blackfury",
    "werewolf_blackspiraldancer": "faith = faith:blackspiraldancer",
    "werewolf_bonegnawer":        "faith = faith:bonegnawer",
    "werewolf_childofgaia":       "faith = faith:childofgaia",
    "werewolf_fianna":            "faith = faith:fianna",
    "werewolf_getoffenris":       "faith = faith:getoffenris",
    "werewolf_hakken":            "faith = faith:hakken",
    "werewolf_redtalon":          "faith = faith:redtalon",
    "werewolf_shadowlord":        "faith = faith:shadowlord",
    "werewolf_silentstrider":     "faith = faith:silentstrider",
    "werewolf_silverfang":        "faith = faith:silverfang",
    "werewolf_stargazer":         "faith = faith:stargazer",
    "werewolf_warderofmen":       "faith = faith:warderofmen",
    "werewolf_whitehowler":       "has_perk = waking_the_dead_perk",
    "bagheera":                   "faith = faith:bagheera",
    "bubasti":                    "faith = faith:bubasti",
    "ceilican":                   "faith = faith:ceilican",
    "khan":                       "faith = faith:khan",
    "simba":                      "faith = faith:simba",
    "swara":                      "faith = faith:swara",
}


def _trait_check_line(trait):
    """Return the scope-local check for a CSV required_trait value.

    Defaults to `has_trait = <trait>`. Overridden entries come from
    TRAIT_CHECK_OVERRIDES for traits that don't exist in PoD's trait database
    (e.g. tribes and breeds modeled as faiths)."""
    return TRAIT_CHECK_OVERRIDES.get(trait, f"has_trait = {trait}")


# ──────────────────────────────────────────────────────────────────────
# PoD PERK VALIDATION
# ──────────────────────────────────────────────────────────────────────

_VALID_POD_PERKS_CACHE = None

# Populated during generation by resolve_perk(). Dict of perk_key -> list of
# skill_keys that referenced the missing perk. Printed as a summary warning
# at the end of the generator run.
_INVALID_PERKS_SEEN = {}


def load_valid_pod_perks():
    """Scan the PoD Reference lifestyle_perks directory for every defined
    perk key. Result is cached so we only do this once per run.

    Returns an empty set if the reference directory cannot be found — the
    generator will then skip validation and pass perk keys through as-is."""
    global _VALID_POD_PERKS_CACHE
    if _VALID_POD_PERKS_CACHE is not None:
        return _VALID_POD_PERKS_CACHE

    valid = set()
    # Look in several candidate locations relative to this script. Once
    # the mod is integrated into PoD directly, the perk definitions will
    # live inside devpod/; for the dev workspace they still live in a
    # sibling "POD Reference" folder two levels above POD-Integration.
    candidate_roots = [
        # Integrated into PoD: perks live inside devpod itself
        os.path.join(DEVPOD_DIR, "common", "lifestyle_perks"),
        # Dev workspace: "POD Reference" is a sibling of POD-Integration
        os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", "POD Reference", "common", "lifestyle_perks")),
        # Legacy fallbacks (running from an older layout)
        os.path.join("..", "POD Reference", "common", "lifestyle_perks"),
        os.path.join("POD Reference", "common", "lifestyle_perks"),
    ]
    root = next((r for r in candidate_roots if os.path.isdir(r)), None)
    if root is None:
        _VALID_POD_PERKS_CACHE = frozenset()
        return _VALID_POD_PERKS_CACHE

    perk_pattern = re.compile(r"^([a-z][a-z0-9_]*_perk)\s*=\s*{", re.MULTILINE)
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not fname.endswith(".txt"):
                continue
            try:
                with open(os.path.join(dirpath, fname), "r",
                          encoding="utf-8-sig", errors="replace") as f:
                    txt = f.read()
            except OSError:
                continue
            for m in perk_pattern.finditer(txt):
                valid.add(m.group(1))

    _VALID_POD_PERKS_CACHE = frozenset(valid)
    return _VALID_POD_PERKS_CACHE


def resolve_perk(perk_key, skill_key=None, invalid_tracker=None):
    """Return `perk_key` if it exists in PoD, otherwise None.

    When an invalid perk is found, the skill key is recorded in
    `invalid_tracker` (a dict) so the generator can print a summary warning
    at the end. Skills whose perk is dropped still work at runtime — the
    required_trait gate handles access control, we just lose the finer-grained
    perk check."""
    if not perk_key:
        return None
    valid = load_valid_pod_perks()
    if not valid:
        return perk_key  # no reference available, trust the CSV
    if perk_key in valid:
        return perk_key
    if invalid_tracker is not None:
        invalid_tracker.setdefault(perk_key, []).append(skill_key)
    return None


# ──────────────────────────────────────────────────────────────────────
# ENERGY COST DISPATCH
# ──────────────────────────────────────────────────────────────────────
# Maps a required_trait to the PoD energy-spend effect call string.
# The string uses "COUNT" as a placeholder — the caller replaces it
# with the numeric value from the CSV's energy_cost column.
#
# Traits not listed (e.g. truefaith, hunter) have no energy system in
# PoD and return None — those skills should not have energy_cost in the
# CSV (or it silently has no game effect, which is fine for balance).
_VAMPIRE_TRAITS = {
    "vampire",
    "celeritydiscipline", "celerityadvanced",
    "fortitudediscipline", "fortitudeadvanced",
    "potencediscipline", "potenceadvanced",
    "presencediscipline", "presenceadvanced",
    "auspexdiscipline", "auspexadvanced",
    "dominatediscipline", "dominateadvanced",
    "obfuscatediscipline", "obfuscateadvanced",
    "obtenebrationdiscipline", "obtenebrationadvanced",
    "proteandiscipline", "proteanadvanced",
    "animalismdiscipline", "animalismadvanced",
    "serpentisdiscipline", "serpentisadvanced",
    "vicissitudediscipline", "vicissitudeadvanced",
    "valerendiscipline", "valerenadvanced",
    "quietusdiscipline", "quietusadvanced",
    "daimoniondiscipline", "daimonionadvanced",
    "dementationdiscipline", "dementationadvanced",
    "temporisdiscipline", "temporisadvanced",
    "abombwediscipline", "abombweadvanced",
    "kaidiscipline", "kaiadvanced",
    "necromancydiscipline", "necromancyadvanced",
    "bloodsorcerydiscipline", "bloodsorceryadvanced",
}


def _get_energy_cost_effect(required_trait):
    """Return the PoD effect call string for spending energy, or None.

    The returned string contains the placeholder '__EC__' which the
    caller replaces with the numeric energy_cost value from the CSV."""
    if not required_trait:
        return None
    if required_trait in _VAMPIRE_TRAITS:
        return "POD_discipline_cost_effect = { COUNT = __EC__ }"
    if required_trait in FERA_TRAITS or required_trait.startswith("werewolf_"):
        return "POD_gift_cost_effect = { COUNT = __EC__ }"
    # Bastet breed faiths are fera
    if required_trait in ("bagheera", "bubasti", "ceilican", "khan", "simba", "swara"):
        return "POD_gift_cost_effect = { COUNT = __EC__ }"
    if required_trait == "sorcerer":
        return "POD_sorcery_cost_effect = { COUNT = __EC__ }"
    if required_trait == "mummy":
        return "POD_hekau_cost_effect = { COUNT = __EC__ }"
    if required_trait == "demon":
        return "POD_lore_energy_cost_effect = { COUNT = __EC__ }"
    if required_trait == "kueijin":
        return "POD_kj_art_cost_effect = { COUNT = __EC__ }"
    if required_trait == "mage":
        return "POD_sorcery_cost_effect = { COUNT = __EC__ }"
    # hunter, truefaith — no PoD energy system
    return None


# Map config_section -> (sv_name_suffix, trait_to_check)
# Built dynamically from CSV data in build_section_sv_map()


def _skill_visibility_sv(required_trait):
    """Map a skill's required_trait string to the script value name that checks it.
    Returns None if the skill should always be visible (no trait gate)."""
    if not required_trait or required_trait == "None":
        return None
    if required_trait == "is_vampire":
        return "pod_combat_is_vampire_sv"
    if required_trait in FERA_TRAITS:
        if required_trait == "fera":
            return "pod_combat_is_fera_sv"
        return f"pod_combat_has_{required_trait}_sv"
    if required_trait.endswith("advanced"):
        base = required_trait[:-8]
        return f"pod_combat_has_{base}_adv_sv"
    if required_trait.endswith("discipline"):
        base = required_trait[:-10]
        return f"pod_combat_has_{base}_sv"
    return f"pod_combat_has_{required_trait}_sv"


def _sv_greater_than_zero(sv_name):
    """Build a GUI expression that checks if the given SV is > 0."""
    return f"GreaterThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue('{sv_name}'), '(CFixedPoint)0')"


def _build_or_expr(sv_names):
    """Build a chained Or() expression for a list of SV names.
    For a single SV, returns the bare GreaterThan check.
    For multiple SVs, chains Or(a, Or(b, c, ...))."""
    if not sv_names:
        return None
    if len(sv_names) == 1:
        return _sv_greater_than_zero(sv_names[0])
    head = _sv_greater_than_zero(sv_names[0])
    tail = _build_or_expr(sv_names[1:])
    return f"Or({head}, {tail})"


# ──────────────────────────────────────────────────────────────────────
# DATA MODEL
# ──────────────────────────────────────────────────────────────────────

def parse_csv(path):
    """Read the CSV and return list of skill dicts."""
    skills = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize fields
            row["ap_cost"] = int(row["ap_cost"])
            # energy_cost (formerly blood_cost) — covers vampire Blood, Fera
            # Gnosis, mage Quintessence, etc. The consuming effect depends on
            # the skill's required_trait (Fera uses POD_gift_cost_effect, etc).
            # Accept the legacy column name "blood_cost" for backwards compat.
            if "energy_cost" in row:
                row["energy_cost"] = int(row["energy_cost"])
            elif "blood_cost" in row:
                row["energy_cost"] = int(row["blood_cost"])
            else:
                row["energy_cost"] = 0
            # stress_cost — adds CK3 stress to the actor when the skill fires.
            # Useful for moves that strain sanity (e.g. invoking demons,
            # forbidden magic, breaking the Masquerade). Emitted as
            # `add_stress = N` in the generated move effect.
            row["stress_cost"] = int(row.get("stress_cost", "0") or "0")
            # Currency costs — CK3 gold/prestige/piety deducted when skill fires.
            row["gold_cost"] = int(row.get("gold_cost", "0") or "0")
            row["prestige_cost"] = int(row.get("prestige_cost", "0") or "0")
            row["piety_cost"] = int(row.get("piety_cost", "0") or "0")
            row["hp_damage"] = int(row["hp_damage"])
            row["morale_damage"] = int(row["morale_damage"])
            row["self_damage"] = int(row["self_damage"])
            row["hp_heal"] = int(row["hp_heal"])
            row["morale_heal"] = int(row["morale_heal"])
            row["log_msg_id"] = int(row["log_msg_id"])
            # ai_weight — per-skill override for the AI random_list weight.
            # Blank / 0 / missing means "use the category-derived default"
            # (ATK=15, PWR=12, CTL=10, DEF=8, fallback=5). Designers can
            # populate this to tune individual skill preference without
            # editing Python. The override is read by _ai_base_weight().
            ai_weight_raw = (row.get("ai_weight") or "").strip()
            if ai_weight_raw == "":
                row["ai_weight"] = 0
            else:
                try:
                    row["ai_weight"] = int(ai_weight_raw)
                except ValueError:
                    print(f"  WARNING: invalid ai_weight {ai_weight_raw!r} for {row['skill_key']}, defaulting to 0 (category fallback)")
                    row["ai_weight"] = 0
            # target_priority — per-skill hint for AI target selection.
            # Consulted by single-{ally,enemy} skills via the swap effects in
            # pod_combat_ai_effects.txt. single-pc, team-*, and self all
            # ignore this hint (their selection is fixed). Valid values:
            #   blank / "default" — legacy behavior:
            #     • single-ally  → first alive non-self same-team ally
            #     • single-enemy → use the AI's turn-start enemy target
            #   "wounded"     — prefer the lowest-HP candidate
            #   "healthy"     — prefer a full-HP candidate
            #   "round_robin" — penalize the most recently round-robin-picked
            #                   slot to distribute picks across candidates
            #   "threat"      — prefer high-prowess slots (+100 if prowess>=5,
            #                   +200 if prowess>=8). Useful for "buff the
            #                   strongest ally" or "shut down the main DPS".
            # Unknown values warn and fall through to default.
            tp_raw = (row.get("target_priority") or "").strip().lower()
            if tp_raw in ("", "default", "none"):
                row["target_priority"] = "default"
            elif tp_raw in ("wounded", "healthy", "round_robin", "threat"):
                row["target_priority"] = tp_raw
            else:
                print(f"  WARNING: unknown target_priority {tp_raw!r} for {row['skill_key']}, defaulting")
                row["target_priority"] = "default"
            # Normalize None-like strings
            for field in ["required_trait", "damage_source", "damage_type",
                          "special",
                          "pod_perk_key", "pod_move_key", "combat_category"]:
                val = row[field].strip()
                if val.lower() in ("none", ""):
                    row[field] = None
                else:
                    row[field] = val
            # Targeting mode — hyphenated scheme.
            #
            # Valid values:
            #   single-enemy — hit the currently selected target, which must be
            #                  on the opposing team. Default for attack skills.
            #   single-ally  — apply to the currently selected target, which
            #                  must be on the actor's team. Used for targeted
            #                  ally buffs. Healing components always fall on
            #                  the attacker regardless (see generate_damage_call).
            #   single-pc    — always targets slot 0 (the PC), regardless of the
            #                  actor's team. Enemy AIs use this for "focus the
            #                  Prince" moves; the PC themselves can use it as a
            #                  self-targeting variant. Body shape is identical
            #                  to single-enemy/single-ally — the target swap
            #                  happens in the move GUI / AI entry pre-body.
            #   team-enemy   — AoE: iterate every alive slot on the opposing
            #                  team and apply the body to each.
            #   team-ally    — AoE: iterate every alive slot on the actor's
            #                  team (buffs/heals) and apply the body to each.
            #   self         — apply only to the actor, no target lookup.
            #
            # Legacy aliases accepted for backwards-compatibility with older
            # CSVs: single -> single-enemy, all_enemies -> team-enemy,
            # all_allies -> team-ally.
            _TARGETING_ALIASES = {
                "": "single-enemy",
                "none": "single-enemy",
                "single": "single-enemy",
                "all_enemies": "team-enemy",
                "all_allies": "team-ally",
            }
            _TARGETING_VALID = {
                "single-enemy", "single-ally", "single-pc",
                "team-enemy", "team-ally",
                "self",
            }
            targeting_raw = (row.get("targeting") or "").strip().lower()
            if targeting_raw in _TARGETING_ALIASES:
                row["targeting"] = _TARGETING_ALIASES[targeting_raw]
            elif targeting_raw in _TARGETING_VALID:
                row["targeting"] = targeting_raw
            else:
                # Unknown value — fall back to single-enemy and warn.
                print(f"  WARNING: unknown targeting '{targeting_raw}' for {row['skill_key']}, defaulting to 'single-enemy'")
                row["targeting"] = "single-enemy"
            # Localization content columns — each skill's button label and
            # Localization: loc_name stores the base display name for the
            # button label. The " (N AP)" suffix is appended at emission time.
            # Tooltip descriptions are auto-generated from CSV stats by
            # _build_skill_description() — no loc_desc column needed.
            loc_name_raw = (row.get("loc_name") or "").strip()
            row["loc_name"] = loc_name_raw if loc_name_raw else row["display_name"]
            skills.append(row)
    return skills


def is_fera_skill(skill):
    """Return True if the skill uses Gnosis (Fera resource) instead of Blood."""
    rt = skill["required_trait"]
    if rt is None:
        return False
    traits = [t.strip() for t in rt.split("|")]
    return any(t in FERA_TRAITS for t in traits)


def is_passive(skill):
    """Return True if the skill is passive (no effect/trigger/button)."""
    cat = skill["category"]
    return cat in ("passive", "passive_fera")


def is_active(skill):
    """Return True if the skill is active (non-passive, implemented)."""
    return skill["status"] == "implemented" and not is_passive(skill)


# ──────────────────────────────────────────────────────────────────────
# TIERED BUFF / DEBUFF SYSTEM
# ──────────────────────────────────────────────────────────────────────
# Buffs and debuffs are expressed as flags in the `special` column:
#   {stat}_{direction}_{size}_{duration}
#     stat:      soak | hit
#     direction: buff | debuff
#     size:      small (tier 1) | medium (tier 2) | large (tier 3)
#     duration:  round | combat
# Magnitude is uniform across stats (per user choice):
#     small  = 10   medium = 20   large  = 30
#
# Stacking: a character can hold at most ONE buff AND ONE debuff per
# (stat, duration) pair. Applying a higher tier overwrites a lower one;
# reapplying the same or lower tier is blocked by the can_use gate.

TIER_STATS = ["soak", "hit"]
TIER_DIRECTIONS = ["buff", "debuff"]
TIER_SIZES = ["small", "medium", "large"]
TIER_DURATIONS = ["round", "combat"]
TIER_ORDER = {"small": 1, "medium": 2, "large": 3}
TIER_MAGNITUDE = {"small": 10, "medium": 20, "large": 30}


def parse_tier_flags(special):
    """Extract (stat, direction, size, duration) tuples from the special column.

    Returns a list of tuples. Silently ignores flags that don't match the
    tier naming convention so unrelated flags like `bypass_guard`, `stealth`,
    `ap_gain_2`, etc. pass through untouched.
    """
    out = []
    if not special:
        return out
    for flag in special.split(","):
        flag = flag.strip()
        parts = flag.split("_")
        if len(parts) != 4:
            continue
        stat, direction, size, duration = parts
        if (stat in TIER_STATS and direction in TIER_DIRECTIONS
                and size in TIER_SIZES and duration in TIER_DURATIONS):
            out.append((stat, direction, size, duration))
    return out


def tier_var_stem(stat, direction, duration):
    """Name stem used for tier variables across workspace and per-slot vars.
    Example: ('soak', 'buff', 'round') -> 'soak_buff_round'"""
    return f"{stat}_{direction}_{duration}"


def is_implemented(skill):
    """Return True if status == implemented."""
    return skill["status"] == "implemented"





def generate_damage_call(skill):
    """Generate the primary damage/heal call line(s).

    Handles the five targeting modes (per skill["targeting"]):
      single-enemy — direct body, applied to pod_combat_opponent_* workspace.
                     The selected target must be on the opposing team (this is
                     enforced by the target selector, not the effect body).
      single-ally  — same body shape as single-enemy (manipulates the target
                     workspace) but the selected target must be on the actor's
                     team. Used for targeted ally buffs.
      team-enemy   — body is wrapped in a loop that iterates alive enemy slots
                     and applies the body to each.
      team-ally    — body is wrapped in a loop that iterates alive ally slots
                     and applies the body to each.
      self         — body is applied as-is (acts on pod_combat_player_*, no
                     target lookup).

    Healing assumption (user-confirmed): hp_heal and morale_heal always apply
    to the attacker (pod_combat_player_* workspace), regardless of targeting.
    This lets a `single-ally` buff-and-heal skill restore the caster rather
    than the ally, and keeps drain heals working the same way they always did.
    """
    lines = []
    ds = skill["damage_source"]
    dt = skill["damage_type"]
    hp_dmg = skill["hp_damage"]
    morale_dmg = skill["morale_damage"]
    hp_heal = skill["hp_heal"]
    morale_heal = skill["morale_heal"]
    special = skill["special"] or ""

    # Retaliation moves don't deal direct damage — hp_damage is the
    # retaliation value, handled in the special-flags section of the
    # effect block. Return empty body so the damage pipeline is skipped.
    if "retaliate_if_hit" in special or "retaliate_if_missed" in special:
        return lines
    targeting = skill.get("targeting", "single-enemy")

    has_damage = False

    # Guard special case
    if skill["skill_key"] == "guard":
        lines.append("\tset_variable = { name = pod_combat_player_is_guarding value = yes }")
        lines.append("\tset_variable = { name = pod_combat_last_damage value = 0 }")
        return lines

    # HP damage
    #
    # Damage source/type dispatch table
    # ---------------------------------
    # Physical     — standard hit → guard → soak → damage pipeline
    # Supernatural — auto-hit, no guard, dodge → soak → damage
    # Mental       — no HP damage, routes through morale damage below
    # Fire         — Physical pipeline, ALWAYS aggravated vs vampires
    # Sunlight     — Physical pipeline, ALWAYS aggravated vs vampires
    # Silver       — Physical pipeline, ALWAYS aggravated vs werewolves/Bastet
    # Gold         — Physical pipeline, ALWAYS aggravated vs Mokole
    # Holy         — Physical pipeline, ALWAYS aggravated vs vampires, demons,
    #                Kuei-jin, and wraiths
    #
    # For the elemental/metal/holy sources:
    #   - Baseline Superficial routes to pod_combat_deal_{source}_hp_damage_effect
    #     which contains the promotion-vs-vulnerable check.
    #   - Baseline Aggravated is already aggravated for everyone, so it skips the
    #     wrapper and calls pod_combat_deal_physical_aggravated_hp_damage_effect
    #     directly.
    ELEMENTAL_SOURCES = ("Fire", "Sunlight", "Silver", "Gold", "Holy")
    if hp_dmg > 0 and ds is not None:
        has_damage = True
        if "bypass_guard" in special:
            if ds in ELEMENTAL_SOURCES and dt == "Superficial":
                src = ds.lower()
                lines.append(f"\tpod_combat_deal_{src}_bypass_guard_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")
            elif ds in ELEMENTAL_SOURCES and dt == "Aggravated":
                lines.append(f"\tpod_combat_deal_physical_aggravated_bypass_guard_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")
            elif ds == "Physical" and dt == "Aggravated":
                lines.append(f"\tpod_combat_deal_physical_aggravated_bypass_guard_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")
            else:
                lines.append(f"\tpod_combat_deal_physical_bypass_guard_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")
        elif ds in ELEMENTAL_SOURCES and dt == "Superficial":
            src = ds.lower()
            lines.append(f"\tpod_combat_deal_{src}_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")
        elif ds in ELEMENTAL_SOURCES and dt == "Aggravated":
            # Already aggravated for everyone — no promotion needed.
            lines.append(f"\tpod_combat_deal_physical_aggravated_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")
        elif ds == "Physical" and dt == "Superficial":
            lines.append(f"\tpod_combat_deal_physical_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")
        elif ds == "Physical" and dt == "Aggravated":
            lines.append(f"\tpod_combat_deal_physical_aggravated_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")
        elif ds == "Supernatural" and dt == "Superficial":
            lines.append(f"\tpod_combat_deal_supernatural_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")
        elif ds == "Supernatural" and dt == "Aggravated":
            lines.append(f"\tpod_combat_deal_supernatural_aggravated_hp_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {hp_dmg} }}")

    # Morale damage (mental)
    if morale_dmg > 0 and ds == "Mental":
        if has_damage:
            # Combo HP+morale: wrap morale in not-over check
            lines.append("")
            lines.append("\t# Morale damage (only if combat not over)")
            lines.append("\tif = {")
            lines.append("\t\tlimit = {")
            lines.append("\t\t\tNOT = { has_variable = pod_combat_is_over }")
            lines.append("\t\t}")
            lines.append(f"\t\tpod_combat_deal_morale_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {morale_dmg} }}")
            lines.append("\t}")
        else:
            has_damage = True
            lines.append(f"\tpod_combat_deal_morale_damage_effect = {{ TARGET_SIDE = opponent AMOUNT = {morale_dmg} }}")

    # ── HEAL TYPE DISPATCH ─────────────────────────────────────────
    # damage_type now doubles as the heal-type selector:
    #   Superficial — heals only up to (max_hp - agg_damage). Aggravated
    #                 wounds remain. Most in-combat healing uses this.
    #   Aggravated  — heals HP and reduces the agg_damage counter by the
    #                 same amount. Rare / high-tier healing. For drain
    #                 skills that deal aggravated damage, the drained life
    #                 force also restores aggravated wounds on the attacker.
    #   None/blank  — legacy unconditional heal with no agg interaction.
    heal_effect = "pod_combat_restore_hp_effect"
    if dt == "Superficial":
        heal_effect = "pod_combat_restore_hp_superficial_effect"
    elif dt == "Aggravated":
        heal_effect = "pod_combat_restore_hp_aggravated_effect"

    # Drain heal (after damage)
    if "drain" in special and hp_heal > 0:
        if ds == "Supernatural":
            # Supernatural drain: only check soaked (no miss/block for supernatural)
            lines.append("")
            lines.append("\t# Drain heal (only if the attack landed — not soaked)")
            lines.append("\tif = {")
            lines.append("\t\tlimit = {")
            lines.append("\t\t\tNOT = { has_variable = pod_combat_last_was_soaked }")
            lines.append("\t\t}")
            lines.append(f"\t\t{heal_effect} = {{ SIDE = player AMOUNT = {hp_heal} }}")
            lines.append("\t}")
        else:
            lines.append("")
            lines.append("\t# Drain heal (only if the attack landed)")
            lines.append("\tif = {")
            lines.append("\t\tlimit = {")
            lines.append("\t\t\tNOT = { has_variable = pod_combat_last_was_missed }")
            lines.append("\t\t\tNOT = { has_variable = pod_combat_last_was_blocked }")
            lines.append("\t\t\tNOT = { has_variable = pod_combat_last_was_soaked }")
            lines.append("\t\t}")
            lines.append(f"\t\t{heal_effect} = {{ SIDE = player AMOUNT = {hp_heal} }}")
            lines.append("\t}")
    elif hp_heal > 0 and "drain" not in special:
        # Pure heal (non-drain)
        lines.append(f"\t{heal_effect} = {{ SIDE = player AMOUNT = {hp_heal} }}")
        if not has_damage:
            lines.append("\tset_variable = { name = pod_combat_last_damage value = 0 }")

    # Self damage — triggered by the self_damage CSV column (no special flag needed)
    if skill["self_damage"] > 0:
        sd = skill["self_damage"]
        lines.append("")
        lines.append("\t# Self-damage (always hits, no guard, no soak)")
        lines.append("\t# Victory is checked at save_workspace time; no in-pipeline call needed.")
        lines.append("\tsave_scope_value_as = {")
        lines.append("\t\tname = new_hp")
        lines.append("\t\tvalue = {")
        lines.append("\t\t\tvalue = var:pod_combat_player_hp")
        lines.append(f"\t\t\tsubtract = {sd}")
        lines.append("\t\t\tmin = 0")
        lines.append("\t\t}")
        lines.append("\t}")
        lines.append("\tset_variable = { name = pod_combat_player_hp value = scope:new_hp }")

    # Remove guard (feint-like)
    if "remove_guard" in special:
        if not has_damage:
            # Pure remove_guard (like feint)
            lines.append("\tset_variable = { name = pod_combat_opponent_feinted value = yes }")
            lines.append("\tremove_variable = pod_combat_opponent_is_guarding")
            lines.append("\tset_variable = { name = pod_combat_last_damage value = 0 }")
        else:
            # Combo: damage + remove guard (like falling_touch)
            lines.append("\tremove_variable = pod_combat_opponent_is_guarding")
            lines.append("\tset_variable = { name = pod_combat_opponent_feinted value = yes }")

    # ── Tiered buffs / debuffs (from `special` column) ──
    # Flag format: {stat}_{direction}_{size}_{duration}
    #   stat ∈ {soak, hit}   direction ∈ {buff, debuff}
    #   size ∈ {small, medium, large}   duration ∈ {round, combat}
    #
    # Recalc-from-base model: the skill sets its tier var, then calls the
    # appropriate workspace recalc effect. The recalc rebuilds the live
    # stat from base + sum of active tier magnitudes (clamped). Because
    # every application starts from the pristine base, clamping losses
    # DO NOT accumulate — reverting a tier always restores the correct
    # prior value.
    #
    # base_soak / base_hit_chance are never touched by skills; they only
    # change when a character is initialized or when hit chance is
    # recomputed against a new target's prowess.
    tier_flags = parse_tier_flags(special)
    recalcs_needed = set()  # (stat, side) pairs
    for stat, direction, size, duration in tier_flags:
        tier_int = TIER_ORDER[size]
        side_var = "player" if direction == "buff" else "opponent"
        stem = tier_var_stem(stat, direction, duration)
        tier_var = f"pod_combat_{side_var}_{stem}_tier"
        dur_label = "combat" if duration == "combat" else "round"

        lines.append("")
        lines.append(f"	# {stat.capitalize()} {direction} {size} ({dur_label}) via tier system")
        lines.append(f"	set_variable = {{ name = {tier_var} value = {tier_int} }}")
        recalcs_needed.add((stat, side_var))

    # Call each required recalc exactly once (even if the skill applies
    # both a round and combat tier of the same stat — both land in the
    # same recalc pass).
    for stat, side in sorted(recalcs_needed):
        stat_effect = "soak" if stat == "soak" else "hit"
        lines.append(f"	pod_combat_recalc_{stat_effect}_{side}_effect = yes")

    if tier_flags and not has_damage and hp_heal == 0 and morale_dmg == 0:
        lines.append("	set_variable = { name = pod_combat_last_damage value = 0 }")

    # ── Non-tier special modifiers (ap_gain_N, ap_drain_N, initiative_debuff_N) ──
    # These stay as inline flag handling — they are either one-shot or do
    # not fit the small/medium/large tier model.
    if special:
        for flag in special.split(","):
            flag = flag.strip()
            if flag.startswith("ap_gain_"):
                try:
                    n = int(flag.split("_", 2)[2])
                except (IndexError, ValueError):
                    continue
                if n > 0:
                    lines.append("")
                    lines.append(f"	# Instant AP gain +{n}")
                    lines.append(f"	change_variable = {{ name = pod_combat_current_ap add = {n} }}")
                    if not has_damage and hp_heal == 0 and morale_dmg == 0:
                        lines.append("	set_variable = { name = pod_combat_last_damage value = 0 }")
            elif flag.startswith("ap_drain_"):
                try:
                    n = int(flag.split("_", 2)[2])
                except (IndexError, ValueError):
                    continue
                if n > 0:
                    lines.append("")
                    lines.append(f"	# Debuff: drain {n} AP from target's next turn")
                    lines.append(f"	change_variable = {{ name = pod_combat_opponent_ap_drain add = {n} }}")
                    if not has_damage and hp_heal == 0 and morale_dmg == 0:
                        lines.append("	set_variable = { name = pod_combat_last_damage value = 0 }")
            elif flag.startswith("initiative_debuff_"):
                try:
                    n = int(flag.rsplit("_", 1)[1])
                except (IndexError, ValueError):
                    continue
                if n > 0:
                    lines.append("")
                    lines.append(f"	# Debuff: reduce target initiative by {n} next round")
                    lines.append(f"	change_variable = {{ name = pod_combat_opponent_init_bonus add = -{n} }}")
                    if not has_damage and hp_heal == 0 and morale_dmg == 0:
                        lines.append("	set_variable = { name = pod_combat_last_damage value = 0 }")

        # Dodge flag
    if "dodge" in (special or ""):
        lines.append("\tset_variable = { name = pod_combat_player_is_dodging value = yes }")
        if not has_damage:
            lines.append("\tset_variable = { name = pod_combat_last_damage value = 0 }")

    # Stealth — separate from dodge. Negates next incoming attack AND
    # grants +30 hit chance. Uses _is_stealthed (not _is_dodging) so the
    # GUI can show distinct icons and bypass_stealth works independently.
    if "stealth" in (special or ""):
        lines.append("\t# Stealth: negate next attack + hit chance bonus for next strike")
        lines.append("\tset_variable = { name = pod_combat_player_is_stealthed value = yes }")
        lines.append("\tchange_variable = { name = pod_combat_player_hit_chance add = 30 }")
        lines.append("\tset_variable = { name = pod_combat_last_damage value = 0 }")

    # Retaliation stances — set a one-shot counter that fires when the
    # actor is attacked. The hp_damage value becomes the retaliation
    # damage. The stance is consumed on first trigger or cleared at round end.
    if "retaliate_if_hit" in (special or "") and hp_dmg > 0:
        is_agg = (skill["damage_type"] or "").lower() == "aggravated"
        agg_label = f" ({ds}/Aggravated — bypasses soak)" if is_agg else f" ({ds}/Superficial — soakable)"
        lines.append(f"\t# Retaliation stance: deal {hp_dmg} HP back if hit{agg_label}")
        lines.append(f"\tset_variable = {{ name = pod_combat_player_retaliate_hit value = {hp_dmg} }}")
        if is_agg:
            lines.append("\tset_variable = { name = pod_combat_player_retaliate_hit_agg value = yes }")
        lines.append("\tset_variable = { name = pod_combat_last_damage value = 0 }")

    if "retaliate_if_missed" in (special or "") and hp_dmg > 0:
        is_agg = (skill["damage_type"] or "").lower() == "aggravated"
        agg_label = f" ({ds}/Aggravated — bypasses soak)" if is_agg else f" ({ds}/Superficial — soakable)"
        lines.append(f"\t# Retaliation stance: deal {hp_dmg} HP back if attacker misses{agg_label}")
        lines.append(f"\tset_variable = {{ name = pod_combat_player_retaliate_miss value = {hp_dmg} }}")
        if is_agg:
            lines.append("\tset_variable = { name = pod_combat_player_retaliate_miss_agg value = yes }")
        lines.append("\tset_variable = { name = pod_combat_last_damage value = 0 }")

    # Morale heal (standalone, not in combo)
    if morale_heal > 0 and morale_dmg == 0 and hp_heal == 0 and hp_dmg == 0:
        lines.append(f"\tpod_combat_restore_morale_effect = {{ SIDE = player AMOUNT = {morale_heal} }}")
    elif morale_heal > 0 and (morale_dmg > 0 or hp_dmg > 0):
        # Combo: morale heal after damage
        lines.append(f"\tpod_combat_restore_morale_effect = {{ SIDE = player AMOUNT = {morale_heal} }}")

    # Wrap the single-target body in a slot-iteration loop if this is an AoE move.
    # single-enemy / single-ally / self leave the body alone — they already
    # target the right workspace pair from the caller's perspective (the target
    # loaded into pod_combat_opponent_*, or the actor in pod_combat_player_*).
    if targeting == "team-enemy":
        lines = _wrap_all_enemies(lines)
        # After the AoE loop, opponent_* has the LAST iterated slot's data.
        # Reload the original selected_target so pod_combat_save_workspace_effect
        # (called by the GUI/AI handler after the move) writes the correct data
        # back instead of clobbering the original target with a different slot's state.
        lines.append("\t# Reload original target after AoE to prevent workspace scramble")
        lines.append("\tpod_combat_load_workspace_effect = yes")
    elif targeting == "team-ally":
        lines = _wrap_all_allies(lines)
        lines.append("\t# Reload original target after AoE to prevent workspace scramble")
        lines.append("\tpod_combat_load_workspace_effect = yes")

    return lines


def _wrap_all_enemies(body_lines):
    """Wrap body_lines in a loop over all alive enemy slots."""
    lines = []
    lines.append("\t# AoE: apply to every alive opposing-team slot (actor-aware).")
    for slot in range(5, 10):
        lines.append(f"\tif = {{")
        lines.append(f"\t\tlimit = {{ has_variable = pod_combat_c{slot}_char var:pod_combat_c{slot}_alive = 1 }}")
        lines.append(f"\t\tpod_combat_load_target_from_slot_effect = {{ SLOT = {slot} }}")
        for bl in body_lines:
            lines.append("\t\t" + bl.lstrip("\t"))
        lines.append(f"\t\tpod_combat_save_target_to_slot_effect = {{ SLOT = {slot} }}")
        # KO check: if this slot's HP or morale dropped to 0, mark as dead
        lines.append(f"\t\tif = {{ limit = {{ OR = {{ var:pod_combat_c{slot}_hp <= 0 var:pod_combat_c{slot}_morale <= 0 }} }} set_variable = {{ name = pod_combat_c{slot}_alive value = 0 }} }}")
        lines.append("\t}")
    return lines


def _wrap_all_allies(body_lines):
    """Wrap body_lines in a loop over all alive ally slots."""
    lines = []
    lines.append("\t# AoE ally: apply to every alive same-team slot.")
    for slot in range(0, 5):
        lines.append(f"\tif = {{")
        lines.append(f"\t\tlimit = {{ has_variable = pod_combat_c{slot}_char var:pod_combat_c{slot}_alive = 1 }}")
        lines.append(f"\t\tpod_combat_load_target_from_slot_effect = {{ SLOT = {slot} }}")
        for bl in body_lines:
            lines.append("\t\t" + bl.lstrip("\t"))
        lines.append(f"\t\tpod_combat_save_target_to_slot_effect = {{ SLOT = {slot} }}")
        # KO check for ally AoE (e.g., AoE damage-all or sacrifice effects)
        lines.append(f"\t\tif = {{ limit = {{ OR = {{ var:pod_combat_c{slot}_hp <= 0 var:pod_combat_c{slot}_morale <= 0 }} }} set_variable = {{ name = pod_combat_c{slot}_alive value = 0 }} }}")
        lines.append("\t}")
    return lines


def generate_effect_block(skill, skill_number):
    """Generate a complete effect block for one active skill."""
    key = skill["skill_key"]
    display = skill["display_name"]
    ds = skill["damage_source"] or "None"
    dt = skill["damage_type"] or "None"
    ap = skill["ap_cost"]
    ec = skill["energy_cost"]
    stress = skill.get("stress_cost", 0)
    special = skill.get("special") or ""
    is_fera = is_fera_skill(skill)
    resource_name = "Gnosis" if is_fera else "Blood"
    log_id = skill["log_msg_id"]

    lines = []
    lines.append(f"# \u2500\u2500 {skill_number}. {display} " + "\u2500" * max(1, 60 - len(display) - len(str(skill_number)) - 6))
    lines.append(f"pod_combat_use_{key}_effect = {{")
    # Cost summary in header comment
    cost_bits = [f"{ap} AP"]
    if ec > 0:
        cost_bits.append(f"{ec} {resource_name}")
    if stress > 0:
        cost_bits.append(f"{stress} Stress")
    if skill.get("gold_cost", 0) > 0:
        cost_bits.append(f"{skill['gold_cost']} Gold")
    if skill.get("prestige_cost", 0) > 0:
        cost_bits.append(f"{skill['prestige_cost']} Prestige")
    if skill.get("piety_cost", 0) > 0:
        cost_bits.append(f"{skill['piety_cost']} Piety")
    lines.append(f"\t# {display} \u2014 {ds}/{dt} \u2014 " + ", ".join(cost_bits))

    # Spend AP
    lines.append(f"\tpod_combat_spend_ap_effect = {{ AMOUNT = {ap} }}")

    # Energy, stress, and currency costs only apply when the PC (slot 0) is
    # acting. All move effects run in the PC's scope (root), so without this
    # guard an AI combatant's skill would deduct from the PC's blood/gnosis/
    # gold/stress instead of the AI's.
    has_real_costs = (ec > 0 or stress > 0
                      or skill.get("gold_cost", 0) > 0
                      or skill.get("prestige_cost", 0) > 0
                      or skill.get("piety_cost", 0) > 0)
    if has_real_costs:
        lines.append("\tif = {")
        lines.append("\t\tlimit = { has_variable = pod_combat_current_actor var:pod_combat_current_actor = 0 }")

        # Energy cost
        if ec > 0:
            energy_effect = _get_energy_cost_effect(skill["required_trait"])
            if energy_effect:
                lines.append(f"\t\t{energy_effect.replace('__EC__', str(ec))}")

        # Stress cost
        if stress > 0:
            lines.append(f"\t\tadd_stress = {stress}")

        # Currency costs
        gold_cost = skill.get("gold_cost", 0)
        prestige_cost = skill.get("prestige_cost", 0)
        piety_cost = skill.get("piety_cost", 0)
        if gold_cost > 0:
            lines.append(f"\t\tremove_short_term_gold = {gold_cost}")
        if prestige_cost > 0:
            lines.append(f"\t\tadd_prestige = -{prestige_cost}")
        if piety_cost > 0:
            lines.append(f"\t\tadd_piety = -{piety_cost}")

        lines.append("\t}")

    # AI energy-use counter — increments on every energy-cost skill the
    # current actor fires, regardless of whether the actor is the PC or
    # an AI combatant. The AI select random_list applies a stacking 0.75
    # weight modifier based on this counter (caps at 4 stacks), simulating
    # energy attrition for AI combatants without them actually spending
    # Blood / Gnosis / Willpower. The PC gets the counter incremented too
    # but they already pay real energy so it's cosmetic for them.
    # The counter lives on the workspace (pod_combat_player_energy_used),
    # is initialized to 0 per slot, and is synced back to the slot via
    # pod_combat_save_workspace_effect.
    if ec > 0:
        lines.append("\tif = {")
        lines.append("\t\tlimit = { has_variable = pod_combat_player_energy_used }")
        lines.append("\t\tchange_variable = { name = pod_combat_player_energy_used add = 1 }")
        lines.append("\t}")

    # Clear result flags from previous action so the log push reads clean state.
    lines.append("\tremove_variable = pod_combat_last_was_blocked")
    lines.append("\tremove_variable = pod_combat_last_was_soaked")
    lines.append("\tremove_variable = pod_combat_last_was_missed")
    lines.append("\tremove_variable = pod_combat_last_was_dodged")
    lines.append("\tremove_variable = pod_combat_last_was_retaliated")
    lines.append("\tremove_variable = pod_combat_last_was_retaliate_soaked")
    lines.append("\tremove_variable = pod_combat_last_was_morale_damage")
    lines.append("\tremove_variable = pod_combat_last_was_heal")
    lines.append("\tremove_variable = pod_combat_last_was_morale_heal")

    # Log metadata
    lines.append(f"\tset_variable = {{ name = pod_combat_log_msg_id value = {log_id} }}")
    lines.append("\tset_variable = { name = pod_combat_last_actor_side value = var:pod_combat_current_turn_side }")
    lines.append(f"\tset_variable = {{ name = pod_combat_last_action value = flag:{key} }}")

    # Bypass flags — strip target's defensive states before damage.
    # bypass_dodge: removes the target's dodge flag (attack is undodgeable).
    # bypass_stealth: removes dodge flag AND reverses the +30 hit bonus
    #   stealth granted (you see through their concealment entirely).
    if "bypass_stealth" in (special or ""):
        lines.append("\t# Bypass stealth: strip stealth state and reverse hit bonus")
        lines.append("\tremove_variable = pod_combat_opponent_is_stealthed")
        lines.append("\tsave_scope_value_as = {")
        lines.append("\t\tname = reduced_hit")
        lines.append("\t\tvalue = { value = var:pod_combat_opponent_hit_chance subtract = 30 min = 20 }")
        lines.append("\t}")
        lines.append("\tset_variable = { name = pod_combat_opponent_hit_chance value = scope:reduced_hit }")
    elif "bypass_dodge" in (special or ""):
        lines.append("\t# Bypass dodge: attack is undodgeable")
        lines.append("\tremove_variable = pod_combat_opponent_is_dodging")

    # Generate skill body
    body_lines = generate_damage_call(skill)
    lines.append("")
    lines.extend(body_lines)

    # Retaliation check — after every damage-dealing move, check if the
    # target has a retaliation stance that should fire back at the actor.
    # Only emitted for moves that actually deal damage (not pure buffs/heals).
    if skill["hp_damage"] > 0 or skill["morale_damage"] > 0:
        special_str = skill.get("special") or ""
        if "retaliate_if_hit" not in special_str and "retaliate_if_missed" not in special_str:
            lines.append("\tpod_combat_check_retaliation_effect = { TARGET_SIDE = opponent ACTOR_SIDE = player }")

    lines.append("")
    lines.append("\tpod_combat_push_log_effect = yes")
    lines.append("}")
    return lines


def generate_effects_file(active_skills):
    """Generate File 1: pod_combat_move_effects.txt"""
    out = []
    out.append("##########################################")
    out.append("######   POD COMBAT MOVE EFFECTS   ######")
    out.append("##########################################")
    out.append(f"# Individual scripted effects for all {len(active_skills)} active (non-passive) combat moves.")
    out.append("# Each effect spends AP, clears result flags, sets log metadata, applies")
    out.append("# damage / healing / buffs / debuffs, then pushes the combat log entry.")
    out.append("#")
    out.append("# Damage functions (defined in pod_combat_effects.txt):")
    out.append("#   pod_combat_deal_physical_hp_damage_effect          \u2014 hit roll -> guard -> soak -> HP")
    out.append("#   pod_combat_deal_supernatural_hp_damage_effect      \u2014 auto-hit, no guard, soak -> HP")
    out.append("#   pod_combat_deal_physical_bypass_guard_hp_damage_effect \u2014 hit roll, skip guard, soak -> HP")
    out.append("#   pod_combat_deal_physical_aggravated_hp_damage_effect        \u2014 like physical, soak halved")
    out.append("#   pod_combat_deal_supernatural_aggravated_hp_damage_effect    \u2014 like supernatural, soak halved")
    out.append("#   pod_combat_deal_physical_aggravated_bypass_guard_hp_damage_effect \u2014 physical agg + bypass guard")
    out.append("#   pod_combat_deal_morale_damage_effect               \u2014 direct morale damage")
    out.append("#   pod_combat_restore_hp_effect                       \u2014 heal HP")
    out.append("#   pod_combat_restore_morale_effect                   \u2014 heal morale")
    out.append("#   pod_combat_spend_ap_effect                         \u2014 spend AP")

    # Group by config_section
    current_section = None
    section_counts = {}
    for s in active_skills:
        sec = s["config_section"]
        section_counts[sec] = section_counts.get(sec, 0) + 1

    skill_num = 0
    for s in active_skills:
        sec = s["config_section"]
        if sec != current_section:
            current_section = sec
            count = section_counts[sec]
            out.append("")
            out.append("")
            out.append(f"###### {sec.upper()} ({count}) ######")

        skill_num += 1
        out.append("")
        block = generate_effect_block(s, skill_num)
        out.extend(block)

    # Tier revert/cleanup effects live in the hand-maintained file
    # common/scripted_effects/POD_combat/pod_combat_tier_effects.txt. They
    # are static infrastructure (do not regenerate on skill changes).

    return BOM + "\n".join(out) + "\n"


# ──────────────────────────────────────────────────────────────────────
# FILE 2: SCRIPTED TRIGGERS
# ──────────────────────────────────────────────────────────────────────

def generate_triggers_file(active_skills, all_implemented):
    """Generate File 2: pod_combat_triggers.txt"""
    out = []
    out.append("##########################################")
    out.append("######   POD COMBAT TRIGGERS   ######")
    out.append("##########################################")

    # Core triggers
    out.append("")
    out.append("###### CORE COMBAT STATE TRIGGERS ######")
    out.append("")
    out.append("pod_combat_is_active_trigger = {")
    out.append("\thas_variable = pod_combat_active")
    out.append("}")
    out.append("")
    out.append("pod_combat_is_over_trigger = {")
    out.append("\t# The pod_combat_is_over flag is set by pod_combat_check_group_victory_effect")
    out.append("\t# when an entire team is wiped. All combats (including 1v1) go through the")
    out.append("\t# same victory check, so this single flag is authoritative.")
    out.append("\thas_variable = pod_combat_is_over")
    out.append("}")
    out.append("")
    out.append("pod_combat_is_player_turn_trigger = {")
    out.append("\thas_variable = pod_combat_current_turn_side")
    out.append("\tvar:pod_combat_current_turn_side = 0")
    out.append("}")
    out.append("")
    out.append("###### AP AFFORDABILITY TRIGGER ######")
    out.append("")
    out.append("pod_combat_can_afford_ap_trigger = {")
    out.append("\tpod_combat_current_ap_value >= $COST$")
    out.append("}")
    out.append("")
    out.append("###### GUARD / FEINT STATE TRIGGERS ######")
    out.append("")
    out.append("pod_combat_target_is_guarding_trigger = {")
    out.append('\t# $TARGET_SIDE$ = "player" or "opponent"')
    out.append("\thas_variable = pod_combat_$TARGET_SIDE$_is_guarding")
    out.append("}")
    out.append("")
    out.append("pod_combat_target_is_feinted_trigger = {")
    out.append('\t# $TARGET_SIDE$ = "player" or "opponent"')
    out.append("\thas_variable = pod_combat_$TARGET_SIDE$_feinted")
    out.append("}")

    # Splat aggregate triggers — PoD has no literal `fera` trait, so we
    # check the three shifter splat traits directly. Used anywhere the CSV
    # has required_trait=fera.
    out.append("")
    out.append("###### SPLAT AGGREGATE TRIGGERS ######")
    out.append("")
    out.append("pod_combat_is_fera_trigger = {")
    out.append("\tOR = {")
    out.append("\t\thas_trait = werewolf")
    out.append("\t\thas_trait = bastet")
    out.append("\t\thas_trait = mokole")
    out.append("\t}")
    out.append("}")

    # NOR block
    out.append("")
    out.append("###### LOADOUT TRIGGERS ######")
    out.append("")
    out.append("pod_combat_no_moves_equipped_trigger = {")
    out.append("\tNOR = {")
    for s in active_skills:
        out.append(f"\t\thas_variable = pod_combat_equipped_{s['skill_key']}")
    out.append("\t}")
    out.append("}")

    # Team-alive triggers — used by the can_use target-type gates. Both are
    # PC-perspective (slots 1-4 = allies, slots 5-9 = enemies). Only consulted
    # during the PC's turn via a trigger_if gate, so enemy AIs skip these
    # checks and their own target-selection logic stays authoritative.
    out.append("")
    out.append("###### TEAM-ALIVE TRIGGERS ######")
    out.append("")
    out.append("pod_combat_has_alive_ally_trigger = {")
    out.append("\t# True if at least one non-PC ally slot (1-4) is populated and alive.")
    out.append("\tOR = {")
    for slot in range(1, 5):
        out.append("\t\tAND = {")
        out.append(f"\t\t\thas_variable = pod_combat_c{slot}_char")
        out.append(f"\t\t\tvar:pod_combat_c{slot}_alive = 1")
        out.append("\t\t}")
    out.append("\t}")
    out.append("}")
    out.append("")
    out.append("pod_combat_has_alive_enemy_trigger = {")
    out.append("\t# True if at least one enemy slot (5-9) is populated and alive.")
    out.append("\tOR = {")
    for slot in range(5, 10):
        out.append("\t\tAND = {")
        out.append(f"\t\t\thas_variable = pod_combat_c{slot}_char")
        out.append(f"\t\t\tvar:pod_combat_c{slot}_alive = 1")
        out.append("\t\t}")
    out.append("\t}")
    out.append("}")

    # Actor-aware version used by the AI select effect — gates single-ally
    # skills on "at least one alive non-self same-team ally exists". Teams
    # are determined by slot index: slots 0-4 are team 0, 5-9 are team 1.
    # Each slot branch checks both team membership (via actor side gate)
    # and that the actor is not the slot itself (otherwise a PC with no
    # coterie would have itself as the only same-team candidate).
    out.append("")
    out.append("pod_combat_ai_has_available_ally_trigger = {")
    out.append("\t# True if the current actor has at least one alive non-self")
    out.append("\t# same-team ally available as a single-ally target.")
    out.append("\tOR = {")
    for slot in range(0, 10):
        actor_gate = "var:pod_combat_current_actor <= 4" if slot < 5 else "var:pod_combat_current_actor >= 5"
        out.append("\t\tAND = {")
        out.append(f"\t\t\thas_variable = pod_combat_c{slot}_char")
        out.append(f"\t\t\tvar:pod_combat_c{slot}_alive = 1")
        out.append(f"\t\t\t{actor_gate}")
        out.append(f"\t\t\tNOT = {{ var:pod_combat_current_actor = {slot} }}")
        out.append("\t\t}")
    out.append("\t}")
    out.append("}")

    # Mirror trigger for opposing-team availability — used by single-enemy
    # skills with target_priority hints. The AI's turn-start enemy target
    # picker already guarantees a primary enemy exists, but the swap-to-X
    # effects need a defensive gate so a degenerate state (no alive enemies)
    # doesn't fire a no-op random_list.
    out.append("")
    out.append("pod_combat_ai_has_available_enemy_trigger = {")
    out.append("\t# True if the current actor has at least one alive opposing-team")
    out.append("\t# slot. (Opposite of pod_combat_ai_has_available_ally_trigger —")
    out.append("\t# slots 0-4 only count when the actor is on team 1, and vice versa.)")
    out.append("\tOR = {")
    for slot in range(0, 10):
        # Slot N's gate fires only when the actor is on the OPPOSING team.
        actor_gate = "var:pod_combat_current_actor >= 5" if slot < 5 else "var:pod_combat_current_actor <= 4"
        out.append("\t\tAND = {")
        out.append(f"\t\t\thas_variable = pod_combat_c{slot}_char")
        out.append(f"\t\t\tvar:pod_combat_c{slot}_alive = 1")
        out.append(f"\t\t\t{actor_gate}")
        out.append("\t\t}")
    out.append("\t}")
    out.append("}")

    # Per-skill can_use triggers
    out.append("")
    out.append("###### PER-MOVE AVAILABILITY TRIGGERS ######")
    out.append("# Each checks AP cost + move-specific restrictions")
    out.append("# All evaluate in player scope during player turn")

    # Separate vampire and fera for section headers
    fera_started = False
    for s in active_skills:
        key = s["skill_key"]
        ap = s["ap_cost"]
        ec = s["energy_cost"]
        is_fera_s = is_fera_skill(s)

        if is_fera_s and not fera_started:
            out.append("")
            out.append("###### FERA PER-MOVE AVAILABILITY TRIGGERS ######")
            fera_started = True

        out.append("")
        out.append(f"pod_combat_can_use_{key}_trigger = {{")
        out.append(f"\tpod_combat_can_afford_ap_trigger = {{ COST = {ap} }}")
        out.append("\tNOT = { pod_combat_is_over_trigger = yes }")

        # Guard: can't guard if already guarding
        if key == "guard":
            out.append("\tNOT = { has_variable = pod_combat_player_is_guarding }")

        # Rally: can't if at max morale
        if key == "rally":
            out.append("\tNOT = { pod_combat_player_morale_value >= pod_combat_max_morale }")

        # HP heal (non-drain): require being wounded. The gate shape depends
        # on damage_type since different heal variants have different notions
        # of "would this actually help":
        #   Superficial heal — only restores HP below the aggravated ceiling
        #     (max_hp - agg_damage), so it's wasted if HP is already at/above
        #     that threshold. Gate on hp < sup_ceiling_value.
        #   Aggravated heal  — restores HP AND clears agg_damage, so it's
        #     useful any time the player is wounded OR carrying aggravated
        #     damage. Gate on an OR of those conditions.
        #   Legacy/unspecified (damage_type blank) — simple wounded check
        #     (hp < max_hp) matching the unconditional restore behavior.
        # Drain heals are exempt — their "does this help" check is already
        # the attack landing, not the actor's prior HP state.
        special = s["special"] or ""
        dt = s["damage_type"]
        if s["hp_heal"] > 0 and "drain" not in special:
            if dt == "Aggravated":
                out.append("\tOR = {")
                out.append("\t\tpod_combat_player_hp_value < pod_combat_player_max_hp_value")
                out.append("\t\tpod_combat_player_agg_damage_value > 0")
                out.append("\t}")
            elif dt == "Superficial":
                out.append("\tpod_combat_player_hp_value < pod_combat_player_sup_ceiling_value")
            else:
                out.append("\tpod_combat_player_hp_value < pod_combat_player_max_hp_value")

        # Fera with gnosis cost
        if is_fera_s and ec > 0:
            out.append(f"\tPOD_has_enough_gnosis_for_gift = {{ COUNT = {ec} }}")

        # Target-type gate — wrapped in trigger_if so it only runs during
        # the PC's turn (var:pod_combat_current_turn_side = 0). Enemy AIs
        # bypass this check because their own target-selection logic (via
        # pod_combat_ai_select_{enemy,player}_target_effect) already
        # guarantees a valid workspace target before the move fires.
        targeting = s.get("targeting", "single-enemy")
        gate_lines = _target_type_gate_lines(targeting)
        if gate_lines:
            out.append("\ttrigger_if = {")
            out.append("\t\tlimit = {")
            out.append("\t\t\thas_variable = pod_combat_current_turn_side")
            out.append("\t\t\tvar:pod_combat_current_turn_side = 0")
            out.append("\t\t}")
            for gl in gate_lines:
                out.append(gl)
            out.append("\t}")

        # Tier gate — each tiered buff/debuff flag on this skill requires
        # that the actor/target does NOT already have a tier equal to or
        # higher than this one for the same (stat, direction, duration).
        # For BUFFS the tier lives on the actor (PC → slot 0).
        # For DEBUFFS the tier lives on the target (pc_target slot 5-9).
        # Gate is PC-turn only; AI's own selection logic avoids spamming.
        tier_flags_for_gate = parse_tier_flags(s.get("special"))
        if tier_flags_for_gate:
            out.append("\ttrigger_if = {")
            out.append("\t\tlimit = {")
            out.append("\t\t\thas_variable = pod_combat_current_turn_side")
            out.append("\t\t\tvar:pod_combat_current_turn_side = 0")
            out.append("\t\t}")
            for stat, direction, size, duration in tier_flags_for_gate:
                tier_int = TIER_ORDER[size]
                stem = tier_var_stem(stat, direction, duration)
                if direction == "buff":
                    # PC = slot 0 — check c0's tier directly
                    tv = f"pod_combat_c0_{stem}_tier"
                    out.append("\t\tOR = {")
                    out.append(f"\t\t\tNOT = {{ has_variable = {tv} }}")
                    out.append(f"\t\t\tvar:{tv} < {tier_int}")
                    out.append("\t\t}")
                else:
                    # Debuff — dispatch on pc_target (slot 5-9). If no
                    # target is selected, allow (skill's target gate will
                    # fail separately). For each candidate slot, require
                    # that slot's tier is below this one.
                    out.append("\t\ttrigger_if = {")
                    out.append("\t\t\tlimit = { has_variable = pod_combat_pc_target }")
                    for slot in range(5, 10):
                        tv = f"pod_combat_c{slot}_{stem}_tier"
                        out.append("\t\t\ttrigger_if = {")
                        out.append(f"\t\t\t\tlimit = {{ var:pod_combat_pc_target = {slot} }}")
                        out.append("\t\t\t\tOR = {")
                        out.append(f"\t\t\t\t\tNOT = {{ has_variable = {tv} }}")
                        out.append(f"\t\t\t\t\tvar:{tv} < {tier_int}")
                        out.append("\t\t\t\t}")
                        out.append("\t\t\t}")
                    out.append("\t\t}")
            out.append("\t}")

        out.append("}")

    return BOM + "\n".join(out) + "\n"


def _target_type_gate_lines(targeting):
    """Return the PC-turn target-type gate lines for a given targeting mode.

    The gate is wrapped in a trigger_if (limit: PC turn), so these lines are
    only enforced when the player clicks or hovers a move button.

      single-enemy — pc_target must be an alive enemy slot (5-9)
      single-ally  — pc_target must be an alive ally slot (1-4, not self)
      single-pc    — always valid during PC turn (PC is slot 0, always alive
                     on their own turn by definition); the move GUI swaps to
                     slot 0 before firing the body
      team-enemy   — at least one enemy must be alive (has_alive_enemy)
      team-ally    — always valid during PC turn (PC is alive → at least one
                     same-team member), so no extra gate needed
      self         — no target check (acts on actor workspace)
    """
    if targeting == "single-enemy":
        lines = [
            "\t\thas_variable = pod_combat_pc_target",
            "\t\tOR = {",
        ]
        for slot in range(5, 10):
            lines.append("\t\t\tAND = {")
            lines.append(f"\t\t\t\tvar:pod_combat_pc_target = {slot}")
            lines.append(f"\t\t\t\thas_variable = pod_combat_c{slot}_char")
            lines.append(f"\t\t\t\tvar:pod_combat_c{slot}_alive = 1")
            lines.append("\t\t\t}")
        lines.append("\t\t}")
        return lines
    if targeting == "single-ally":
        lines = [
            "\t\thas_variable = pod_combat_pc_target",
            "\t\tOR = {",
        ]
        for slot in range(1, 5):
            lines.append("\t\t\tAND = {")
            lines.append(f"\t\t\t\tvar:pod_combat_pc_target = {slot}")
            lines.append(f"\t\t\t\thas_variable = pod_combat_c{slot}_char")
            lines.append(f"\t\t\t\tvar:pod_combat_c{slot}_alive = 1")
            lines.append("\t\t\t}")
        lines.append("\t\t}")
        return lines
    if targeting == "team-enemy":
        return ["\t\tpod_combat_has_alive_enemy_trigger = yes"]
    # team-ally and self: no PC-turn gate needed
    return []


# ──────────────────────────────────────────────────────────────────────
# FILE 3: SCRIPTED GUIS (MOVE BUTTONS)
# ──────────────────────────────────────────────────────────────────────

def generate_combat_guis_file(active_skills):
    """Generate File 3: pod_combat_guis.txt"""
    out = []
    out.append("##########################################")
    out.append("######   POD COMBAT SCRIPTED GUIS   ######")
    out.append("##########################################")
    out.append("")
    out.append("# Each scripted GUI handles a button click in the combat window.")
    out.append("# Scope: ROOT = player character (via GuiScope.SetRoot(GetPlayer.MakeScope).End)")
    out.append("")
    out.append("###### MOVE BUTTONS ######")

    fera_started = False
    for s in active_skills:
        key = s["skill_key"]
        is_fera_s = is_fera_skill(s)
        is_single_pc = s.get("targeting") == "single-pc"
        if is_fera_s and not fera_started:
            out.append("")
            out.append("###### FERA MOVE GUIS ######")
            fera_started = True

        out.append("")
        out.append(f"pod_combat_move_{key} = {{")
        out.append("\tis_valid = {")
        out.append("\t\tpod_combat_is_active_trigger = yes")
        out.append("\t\tpod_combat_is_player_turn_trigger = yes")
        out.append(f"\t\tpod_combat_can_use_{key}_trigger = yes")
        out.append("\t}")
        out.append("\teffect = {")
        if is_single_pc:
            # single-pc: temporarily swap selected_target to slot 0 (the PC)
            # so the move body applies to the PC. The persistent pc_target
            # variable is untouched, so pod_combat_restore_pc_target_effect
            # after the move automatically reloads whatever slot the player
            # had selected. The PC acting on themselves via single-pc is
            # uncommon (self is cleaner for pure self-buffs), but the PC
            # can still fire single-pc skills and they work correctly.
            out.append("\t\t# single-pc: swap the opponent workspace to slot 0 (the PC)")
            out.append("\t\tset_variable = { name = pod_combat_selected_target value = 0 }")
            out.append("\t\tpod_combat_load_target_from_slot_effect = { SLOT = 0 }")
        # The unified target is already loaded into the opponent workspace
        # by the last pod_combat_restore_pc_target_effect call (at PC turn
        # start or after the previous move). All targeting modes — single-
        # enemy, single-ally, team-*, self — read and write the same
        # workspace slots, so no ally-specific load/restore dance is needed.
        # (single-pc swapped above; all others already loaded correctly.)
        out.append(f"\t\tpod_combat_use_{key}_effect = yes")
        out.append("\t\t# Flush workspace changes back to slot variables so the character")
        out.append("\t\t# cards reflect the new HP / morale / soak / damage state immediately.")
        out.append("\t\tpod_combat_save_workspace_effect = yes")
        out.append("\t\t# If the current target was knocked out (or is no longer valid),")
        out.append("\t\t# auto-retarget to the next living non-PC slot and reload it.")
        out.append("\t\t# For single-pc, this also restores the player's previously")
        out.append("\t\t# selected enemy/ally target since pc_target was never changed.")
        out.append("\t\tif = {")
        out.append("\t\t\tlimit = { NOT = { pod_combat_is_over_trigger = yes } }")
        out.append("\t\t\tpod_combat_restore_pc_target_effect = yes")
        out.append("\t\t}")
        out.append("\t\tif = {")
        out.append("\t\t\tlimit = {")
        out.append("\t\t\t\tNOT = { pod_combat_is_over_trigger = yes }")
        out.append("\t\t\t\tpod_combat_current_ap_value < 1")
        out.append("\t\t\t}")
        out.append("\t\t\tpod_combat_end_player_turn_effect = yes")
        out.append("\t\t}")
        out.append("\t}")
        out.append("}")

    # Static control handlers (End Turn, Auto-Resolve, Help, Forfeit,
    # Target Selection 1-9) live in the hand-maintained file
    # common/scripted_guis/pod_combat_control_guis.txt. They are not
    # regenerated on skill changes.

    return BOM + "\n".join(out) + "\n"


# ──────────────────────────────────────────────────────────────────────
# FILE 4: SKILL TOGGLE GUIS
# ──────────────────────────────────────────────────────────────────────

def generate_skill_guis_file(active_skills, all_implemented):
    """Generate File 4: pod_combat_skill_guis.txt"""
    out = []
    out.append("##########################################")
    out.append("######   POD COMBAT SKILL GUIS   ######")
    out.append("##########################################")
    out.append("")
    out.append("# Scripted GUIs for the skill configuration window.")
    out.append("# Each toggle equips/unequips a single combat move.")
    out.append("# Equipping is blocked when the category is at pod_combat_max_per_category (4).")
    out.append("# Full loadout: 16 skills (4 ATK + 4 CTL + 4 DEF + 4 PWR).")
    out.append(f"# {len(active_skills)} active skills: 8 base + 3 innate vampire + {len(active_skills) - 11} discipline.")
    out.append("")
    out.append("###### WINDOW CONTROLS ######")
    out.append("")
    out.append("pod_combat_close_skills = {")
    out.append("\tis_valid = {")
    out.append("\t\thas_variable = pod_combat_config_open")
    out.append("\t}")
    out.append("\teffect = {")
    out.append("\t\tremove_variable = pod_combat_config_open")
    out.append("\t}")
    out.append("}")

    current_section = None
    for s in active_skills:
        key = s["skill_key"]
        sec = s["config_section"]
        cat = s.get("combat_category")
        cat_lower = cat.lower() if cat else "atk"
        rt = s["required_trait"]
        perk = s["pod_perk_key"]

        if sec != current_section:
            current_section = sec
            out.append("")
            out.append(f"###### {sec.upper()} TOGGLES ######")
            if rt is None:
                out.append("# Available to all characters. Equip blocked at max cap. Remove always allowed.")

        out.append("")
        out.append(f"pod_combat_toggle_{key} = {{")
        out.append("\tis_valid = {")
        out.append("\t\thas_variable = pod_combat_config_open")
        out.append("\t\ttrigger_if = {")
        out.append(f"\t\t\tlimit = {{ NOT = {{ has_variable = pod_combat_equipped_{key} }} }}")
        out.append(f"\t\t\tpod_combat_{cat_lower}_count < pod_combat_max_per_category")

        # Trait checks (uses TRAIT_CHECK_OVERRIDES for tribes/breeds/hunter)
        if rt is not None:
            traits = [t.strip() for t in rt.split("|")]
            for t in traits:
                out.append(f"\t\t\t{_trait_check_line(t)}")

        # Perk checks — skip perks that do not exist in PoD Reference.
        # The required_trait gate above is sufficient for access control;
        # dropping invalid perks prevents runtime "Invalid database object"
        # errors without blocking the skill.
        resolved_perk = resolve_perk(perk, skill_key=key,
                                     invalid_tracker=_INVALID_PERKS_SEEN)
        if resolved_perk is not None:
            out.append(f"\t\t\thas_perk = {resolved_perk}")

        out.append("\t\t}")
        out.append("\t}")
        out.append("\teffect = {")
        out.append("\t\tif = {")
        out.append(f"\t\t\tlimit = {{ has_variable = pod_combat_equipped_{key} }}")
        out.append(f"\t\t\tremove_variable = pod_combat_equipped_{key}")
        out.append("\t\t}")
        out.append("\t\telse = {")
        out.append(f"\t\t\tset_variable = {{ name = pod_combat_equipped_{key} value = yes }}")
        out.append("\t\t}")
        out.append("\t}")
        out.append("}")

    return BOM + "\n".join(out) + "\n"


# ──────────────────────────────────────────────────────────────────────
# FILE 5: SCRIPT VALUES
# ──────────────────────────────────────────────────────────────────────

def build_section_sv_map(all_implemented):
    """Build unique discipline/trait SVs from config_section data.
    Returns ordered list of (sv_name, trait_name) tuples."""
    seen = OrderedDict()
    for s in all_implemented:
        if is_passive(s):
            continue
        rt = s["required_trait"]
        if rt is None:
            continue
        traits = [t.strip() for t in rt.split("|")]
        for t in traits:
            if t in FERA_TRAITS:
                continue  # Fera handled separately
            if t == "is_vampire":
                continue  # Handled separately
            # Determine SV name from trait
            # e.g., potencediscipline -> pod_combat_has_potence_sv
            # potenceadvanced -> pod_combat_has_potence_adv_sv
            if t.endswith("advanced"):
                base = t[:-8]  # strip "advanced"
                sv_name = f"pod_combat_has_{base}_adv_sv"
            elif t.endswith("discipline"):
                base = t[:-10]  # strip "discipline"
                sv_name = f"pod_combat_has_{base}_sv"
            else:
                sv_name = f"pod_combat_has_{t}_sv"

            if sv_name not in seen:
                seen[sv_name] = t
    return list(seen.items())


def generate_values_file(active_skills, all_implemented):
    """Generate File 5: pod_combat_values.txt"""
    out = []
    out.append("######################################")
    out.append("######   POD COMBAT VALUES   ######")
    out.append("######################################")

    # Variable reference comment
    out.append("")
    out.append("# \u2500\u2500\u2500 COMBAT VARIABLE REFERENCE " + "\u2500" * 45)
    out.append("#")
    out.append("# All combat state is stored as character variables on the PLAYER character.")
    out.append("# Group combat uses a 10-slot system (slots 0-4 = player team, 5-9 = enemy")
    out.append("# team). A shared WORKSPACE (pod_combat_player_* / pod_combat_opponent_*)")
    out.append("# holds whichever combatant is acting and whichever one is the current")
    out.append("# target; the workspace is loaded from / saved back to the appropriate")
    out.append("# slot at each action boundary by pod_combat_{load,save}_workspace_effect.")
    out.append("# Skill effects read and write only the workspace, so the same generated")
    out.append("# code runs for the PC, AI coterie, the primary opponent, and knights.")
    out.append("#")
    out.append("# \u2500\u2500 Core state \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    out.append("#   pod_combat_active                 \u2014 flag: combat is in progress")
    out.append("#   pod_combat_is_over                \u2014 flag: combat is over (re-entry guard)")
    out.append("#   pod_combat_mode                   \u2014 0=1v1, 1=1vN, 2=Nv1, 3=NvN")
    out.append("#   pod_combat_round                  \u2014 current round number")
    out.append("#   pod_combat_current_actor          \u2014 slot index of the acting combatant (0-9)")
    out.append("#   pod_combat_current_ap             \u2014 AP remaining this turn")
    out.append("#   pod_combat_current_turn_side      \u2014 0 = player-team turn, 1 = enemy-team turn")
    out.append("#   pod_combat_player_team_size       \u2014 number of occupied ally slots (0-4)")
    out.append("#   pod_combat_enemy_team_size        \u2014 number of occupied enemy slots (5-9)")
    out.append("#   pod_combat_pc_target              \u2014 the PC's persistent target slot (1-9)")
    out.append("#   pod_combat_selected_target        \u2014 slot loaded into opponent workspace")
    out.append("#")
    out.append("# \u2500\u2500 Per-slot stats (N = 0-9) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    out.append("#   pod_combat_c{N}_char              \u2014 character ref occupying the slot")
    out.append("#   pod_combat_c{N}_alive             \u2014 1 if slot is active, 0 if KO'd")
    out.append("#   pod_combat_c{N}_team              \u2014 0 = player team, 1 = enemy team")
    out.append("#   pod_combat_c{N}_hp / _max_hp      \u2014 current HP / health track length")
    out.append("#   pod_combat_c{N}_initial_hp        \u2014 HP at combat start (for write-back)")
    out.append("#   pod_combat_c{N}_agg_damage        \u2014 aggravated HP taken (round-scoped)")
    out.append("#   pod_combat_c{N}_agg_total         \u2014 aggravated HP taken (combat total)")
    out.append("#   pod_combat_c{N}_morale            \u2014 current Morale")
    out.append("#   pod_combat_c{N}_prowess           \u2014 current prowess")
    out.append("#   pod_combat_c{N}_soak              \u2014 live soak chance (0-100)")
    out.append("#   pod_combat_c{N}_base_soak         \u2014 soak before any tier effects")
    out.append("#   pod_combat_c{N}_hit_chance        \u2014 live hit chance (20-95)")
    out.append("#   pod_combat_c{N}_base_hit_chance   \u2014 hit chance before any tier effects")
    out.append("#   pod_combat_c{N}_initiative        \u2014 initiative roll this round")
    out.append("#   pod_combat_c{N}_init_bonus        \u2014 next-round initiative modifier")
    out.append("#   pod_combat_c{N}_ap_drain          \u2014 AP drained from next turn")
    out.append("#   pod_combat_c{N}_energy_used       \u2014 counter for AI energy-attrition weighting")
    out.append("#")
    out.append("# \u2500\u2500 Per-slot stance flags (N = 0-9) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    out.append("# All persist across rounds; only cleared when consumed or at combat end.")
    out.append("#   pod_combat_c{N}_is_guarding       \u2014 Guard stance active")
    out.append("#   pod_combat_c{N}_is_dodging        \u2014 Dodge stance active")
    out.append("#   pod_combat_c{N}_is_stealthed      \u2014 Stealth active (includes +30 hit)")
    out.append("#   pod_combat_c{N}_feinted           \u2014 feint marker (round-scoped)")
    out.append("#   pod_combat_c{N}_retaliate_hit     \u2014 retaliation damage if hit")
    out.append("#   pod_combat_c{N}_retaliate_miss    \u2014 retaliation damage if missed")
    out.append("#   pod_combat_c{N}_retaliate_{hit,miss}_agg  \u2014 aggravated variants")
    out.append("#")
    out.append("# \u2500\u2500 Tier variables (per slot) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    out.append("# Tier = 1 (small, \u00b110), 2 (medium, \u00b120), 3 (large, \u00b130). Live stats are")
    out.append("# rebuilt from base + sum of active tier magnitudes. See pod_combat_tier_effects.txt.")
    out.append("#   pod_combat_c{N}_{stat}_{direction}_{duration}_tier")
    out.append("#     stat:      soak | hit")
    out.append("#     direction: buff | debuff")
    out.append("#     duration:  round (cleared at round end) | combat (lasts the fight)")
    out.append("#")
    out.append("# \u2500\u2500 Workspace (acting combatant + current target) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    out.append("# Mirrors the per-slot fields for whoever is currently acting / targeted.")
    out.append("#   pod_combat_player_*               \u2014 actor's stats (loaded from current_actor slot)")
    out.append("#   pod_combat_opponent_*             \u2014 target's stats (loaded from selected_target slot)")
    out.append("# The same tier, stance, retaliation, and base_* fields exist on both sides.")
    out.append("#   pod_combat_current_hit_chance     \u2014 active attacker's hit chance this attack")
    out.append("#")
    out.append("# \u2500\u2500 Result / display \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    out.append("#   pod_combat_winner                 \u2014 character ref: who won (or team leader)")
    out.append("#   pod_combat_loser                  \u2014 character ref: who lost")
    out.append("#   pod_combat_last_action            \u2014 flag: last skill key (for log display)")
    out.append("#   pod_combat_last_damage            \u2014 last damage amount dealt")
    out.append("#   pod_combat_last_actor_side        \u2014 0 = player-team acted, 1 = enemy-team acted")
    out.append("#   pod_combat_last_was_blocked       \u2014 flag: last attack was guard-blocked")
    out.append("#   pod_combat_last_was_soaked        \u2014 flag: last attack was soaked")
    out.append("#   pod_combat_last_was_missed        \u2014 flag: last attack missed the hit roll")
    out.append("#   pod_combat_last_was_dodged        \u2014 flag: last attack dodged or caught by stealth")
    out.append("#   pod_combat_last_was_retaliated    \u2014 flag: target fired a retaliation stance")
    out.append("#   pod_combat_last_was_heal          \u2014 flag: last action was a heal")
    out.append("#   pod_combat_last_was_morale_*      \u2014 flags: morale damage / heal variants")
    out.append("#   pod_combat_ai_last_move           \u2014 flag: AI's last move (for anti-repetition)")
    out.append("#")
    out.append("# Hit chance formula: 60 + (own prowess \u2212 target prowess) / 2, clamped 20-95.")
    out.append("# " + "\u2500" * 68)

    # Constants
    out.append("")
    out.append("###### BASE CONSTANTS ######")
    out.append("")
    out.append("pod_combat_base_ap = 6")
    out.append("")
    out.append("# Legacy 1v1-era constants. Max HP is per-slot now (c{N}_max_hp, set from")
    out.append("# the character's PoD health track at init) and hit chance is computed by")
    out.append("# pod_combat_calculate_all_hit_chances_effect / recalc_player_hit_chance,")
    out.append("# so nothing reads these three. Kept as defined symbols so any external")
    out.append("# reference doesn't error out; candidates for removal in a future pass.")
    out.append("pod_combat_max_hp = 20")
    out.append("")
    out.append("pod_combat_initiative_value = {")
    out.append("\tvalue = prowess")
    out.append("}")
    out.append("")
    out.append("pod_combat_hit_chance_base = 60")
    out.append("")
    out.append("# Morale is still shared across all slots (fixed 20 cap).")
    out.append("pod_combat_max_morale = 20")
    out.append("")
    out.append("pod_combat_morale_from_hp_ratio = {")
    out.append("\tvalue = 2")
    out.append("}")

    # Value accessors
    out.append("")
    out.append("###### CURRENT VALUE ACCESSORS ######")
    out.append("# Used by GUI and triggers to read combat state.")
    out.append("# Guarded with has_variable so CK3 doesn't log errors when the GUI")
    out.append("# evaluates these script values outside an active combat.")
    for name in ["current_ap", "round", "player_hp", "player_max_hp", "player_soak",
                 "player_morale", "opponent_hp", "opponent_max_hp", "opponent_soak",
                 "opponent_morale", "player_prowess", "opponent_prowess",
                 "player_hit_chance", "opponent_hit_chance"]:
        out.append("")
        out.append(f"pod_combat_{name}_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_{name} }} value = var:pod_combat_{name} }}")
        out.append("}")

    # Group combat actor/target tracking
    out.append("")
    out.append("###### GROUP COMBAT ACTOR / TARGET ######")
    out.append("# Used by GUI to highlight the current actor and selected target")
    out.append("")
    out.append("pod_combat_current_actor_value = {")
    out.append("\tif = { limit = { has_variable = pod_combat_current_actor } value = var:pod_combat_current_actor }")
    out.append("}")
    out.append("")
    out.append("pod_combat_selected_target_value = {")
    out.append("\tif = { limit = { has_variable = pod_combat_selected_target } value = var:pod_combat_selected_target }")
    out.append("}")
    out.append("")
    out.append("pod_combat_pc_target_value = {")
    out.append("\t# Drives the TARGETED badge on combat cards. Reads from the PC's")
    out.append("\t# persistent target choice (not the transient selected_target, which can")
    out.append("\t# be clobbered during AI turns). Defaults to -1 when unset so nothing")
    out.append("\t# highlights before combat starts.")
    out.append("\tvalue = -1")
    out.append("\tif = { limit = { has_variable = pod_combat_pc_target } value = var:pod_combat_pc_target }")
    out.append("}")
    out.append("")
    out.append("pod_combat_player_agg_damage_value = {")
    out.append("\t# Aggravated HP damage the player has taken this combat (workspace var).")
    out.append("\t# Used by heal-availability gates to decide whether an aggravated heal would")
    out.append("\t# actually accomplish anything. Falls back to 0 when the workspace is unset.")
    out.append("\tif = { limit = { has_variable = pod_combat_player_agg_damage } value = var:pod_combat_player_agg_damage }")
    out.append("}")
    out.append("")
    out.append("pod_combat_player_sup_ceiling_value = {")
    out.append("\t# The effective ceiling for SUPERFICIAL HP healing on the player workspace:")
    out.append("\t#   max_hp - agg_damage")
    out.append("\t# Aggravated damage blocks the top of the HP track, so only the space below")
    out.append("\t# this ceiling can be refilled by pod_combat_restore_hp_superficial_effect.")
    out.append("\t# The heal-availability trigger uses this to grey out superficial-heal buttons")
    out.append("\t# when the player has nothing left to heal (e.g., 5/10 HP with 5 aggravated).")
    out.append("\tif = { limit = { has_variable = pod_combat_player_max_hp } value = var:pod_combat_player_max_hp }")
    out.append("\tif = { limit = { has_variable = pod_combat_player_agg_damage } subtract = var:pod_combat_player_agg_damage }")
    out.append("\tmin = 0")
    out.append("}")

    # Percentage values
    out.append("")
    out.append("###### GUI PERCENTAGE VALUES ######")
    out.append("# Return 0\u2013100 for progressbar_standard (max = 100)")
    for who, hp_max_sv in [("player", "pod_combat_player_max_hp_value"),
                           ("opponent", "pod_combat_opponent_max_hp_value")]:
        out.append("")
        out.append(f"pod_combat_{who}_hp_pct = {{")
        out.append(f"\tvalue = var:pod_combat_{who}_hp")
        out.append("\tmultiply = 100")
        out.append(f"\tdivide = {hp_max_sv}")
        out.append("\tmin = 0")
        out.append("\tmax = 100")
        out.append("}")
        out.append("")
        out.append(f"pod_combat_{who}_morale_pct = {{")
        out.append(f"\tvalue = var:pod_combat_{who}_morale")
        out.append("\tmultiply = 100")
        out.append("\tdivide = pod_combat_max_morale")
        out.append("\tmin = 0")
        out.append("\tmax = 100")
        out.append("}")
        out.append("")
        out.append(f"pod_combat_{who}_total_damage_sv = {{")
        out.append(f"\tvalue = var:pod_combat_{who}_max_hp")
        out.append(f"\tsubtract = var:pod_combat_{who}_hp")
        out.append("\tmin = 0")
        out.append("}")
        out.append("")
        out.append(f"pod_combat_{who}_agg_damage_sv = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_{who}_agg_total }} add = var:pod_combat_{who}_agg_total }}")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_{who}_agg_damage }} add = var:pod_combat_{who}_agg_damage }}")
        out.append(f"\tmax = pod_combat_{who}_total_damage_sv")
        out.append("}")

    # Per-slot script values for group combat GUI
    out.append("")
    out.append("###### PER-SLOT COMBAT VALUES (GROUP COMBAT) ######")
    out.append("# Generated accessors for combatant slots 0-9")
    out.append("# Slots 0-4 = player team, slots 5-9 = enemy team")
    out.append("")
    for i in range(10):
        out.append(f"pod_combat_c{i}_hp_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_hp }} value = var:pod_combat_c{i}_hp }}")
        out.append("}")
        out.append(f"pod_combat_c{i}_max_hp_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_max_hp }} value = var:pod_combat_c{i}_max_hp }}")
        out.append("}")
        out.append(f"pod_combat_c{i}_morale_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_morale }} value = var:pod_combat_c{i}_morale }}")
        out.append("}")
        out.append(f"pod_combat_c{i}_morale_pct = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_morale }}")
        out.append(f"\t\tvalue = var:pod_combat_c{i}_morale")
        out.append("\t\tmultiply = 100")
        out.append("\t\tdivide = pod_combat_max_morale")
        out.append("\t}")
        out.append("\tmin = 0")
        out.append("\tmax = 100")
        out.append("}")
        out.append(f"pod_combat_c{i}_total_damage_sv = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_max_hp }}")
        out.append(f"\t\tvalue = var:pod_combat_c{i}_max_hp")
        out.append(f"\t\tsubtract = var:pod_combat_c{i}_hp")
        out.append("\t\tmin = 0")
        out.append("\t}")
        out.append("}")
        out.append(f"pod_combat_c{i}_agg_damage_sv = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_agg_total }} add = var:pod_combat_c{i}_agg_total }}")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_agg_damage }} add = var:pod_combat_c{i}_agg_damage }}")
        out.append(f"\tmax = pod_combat_c{i}_total_damage_sv")
        out.append("}")
        out.append(f"pod_combat_c{i}_soak_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_soak }} value = var:pod_combat_c{i}_soak }}")
        out.append("\tmin = 0")
        out.append("\tmax = 100")
        out.append("}")
        # Hit chance display: read the stored pod_combat_c{N}_hit_chance
        # variable directly. This variable is:
        #   - Initialized to 60 + (own prowess - primary enemy prowess) / 2
        #     by pod_combat_calculate_all_hit_chances_effect
        #   - Kept up-to-date by save_workspace_effect whenever a skill
        #     modifies pod_combat_player_hit_chance or pod_combat_opponent_hit_chance
        # so buffs and debuffs show up on the character card automatically.
        # Fallback: if the variable is unset (outside combat / preview),
        # compute from prowess so tooltips have a sensible value.
        out.append(f"pod_combat_c{i}_hit_chance_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_hit_chance }}")
        out.append(f"\t\tvalue = var:pod_combat_c{i}_hit_chance")
        out.append("\t}")
        out.append(f"\tif = {{ limit = {{ NOT = {{ has_variable = pod_combat_c{i}_hit_chance }} has_variable = pod_combat_c{i}_prowess }}")
        out.append("\t\tvalue = 60")
        out.append("\t\tadd = {")
        out.append(f"\t\t\tvalue = var:pod_combat_c{i}_prowess")
        if i <= 4:
            # Ally slot: subtract pc_target's prowess (falls back to slot 5 when pc_target unset)
            out.append("\t\t\t# Subtract currently targeted enemy's prowess")
            for target in range(5, 10):
                out.append(f"\t\t\tif = {{ limit = {{ has_variable = pod_combat_pc_target var:pod_combat_pc_target = {target} has_variable = pod_combat_c{target}_prowess }} subtract = var:pod_combat_c{target}_prowess }}")
            out.append("\t\t\tif = {")
            out.append("\t\t\t\tlimit = {")
            out.append("\t\t\t\t\tNOT = { has_variable = pod_combat_pc_target }")
            out.append("\t\t\t\t\thas_variable = pod_combat_c5_prowess")
            out.append("\t\t\t\t}")
            out.append("\t\t\t\tsubtract = var:pod_combat_c5_prowess")
            out.append("\t\t\t}")
        else:
            out.append("\t\t\tif = { limit = { has_variable = pod_combat_c0_prowess } subtract = var:pod_combat_c0_prowess }")
        out.append("\t\t\tdivide = 2")
        out.append("\t\t}")
        out.append("\t}")
        # Clamp at the script-value level so both branches (stored variable
        # read and prowess-based fallback) stay within 20-95%.
        out.append("\tmin = 20")
        out.append("\tmax = 95")
        out.append("}")
        out.append(f"pod_combat_c{i}_prowess_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_prowess }} value = var:pod_combat_c{i}_prowess }}")
        out.append("}")
        out.append(f"pod_combat_c{i}_alive_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_alive }} value = var:pod_combat_c{i}_alive }}")
        out.append("}")
        out.append(f"pod_combat_c{i}_is_guarding_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_is_guarding }} value = 1 }}")
        out.append("}")
        out.append(f"pod_combat_c{i}_is_dodging_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_is_dodging }} value = 1 }}")
        out.append("}")
        out.append(f"pod_combat_c{i}_is_stealthed_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_is_stealthed }} value = 1 }}")
        out.append("}")
        out.append(f"pod_combat_c{i}_initiative_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_initiative }} value = var:pod_combat_c{i}_initiative }}")
        out.append("}")
        # Tier magnitude script values — one per (stat, direction, duration).
        # Returns 0 if no tier is active, else the tier's magnitude
        # (small=10, medium=20, large=30). Used by the combat-card effects
        # row to show the magnitude and gate visibility on >0.
        for stat in TIER_STATS:
            for direction in TIER_DIRECTIONS:
                for duration in TIER_DURATIONS:
                    stem = tier_var_stem(stat, direction, duration)
                    tv = f"pod_combat_c{i}_{stem}_tier"
                    out.append(f"pod_combat_c{i}_{stem}_mag_sv = {{")
                    for s, m in TIER_MAGNITUDE.items():
                        t_int = TIER_ORDER[s]
                        out.append(f"\tif = {{ limit = {{ has_variable = {tv} var:{tv} = {t_int} }} value = {m} }}")
                    out.append("}")
        # Turn-order rank: 1 + count of other alive combatants with higher initiative
        # (ties broken by lower slot index going first)
        out.append(f"pod_combat_c{i}_turn_order_value = {{")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_c{i}_initiative var:pod_combat_c{i}_alive = 1 }}")
        out.append("\t\tvalue = 1")
        for j in range(10):
            if j == i:
                continue
            if j < i:
                # Lower slot index wins ties: count j if initiative >= ours
                out.append(f"\t\tif = {{ limit = {{ has_variable = pod_combat_c{j}_initiative var:pod_combat_c{j}_alive = 1 var:pod_combat_c{j}_initiative >= var:pod_combat_c{i}_initiative }} add = 1 }}")
            else:
                # Higher slot index loses ties: count j only if strictly greater
                out.append(f"\t\tif = {{ limit = {{ has_variable = pod_combat_c{j}_initiative var:pod_combat_c{j}_alive = 1 var:pod_combat_c{j}_initiative > var:pod_combat_c{i}_initiative }} add = 1 }}")
        out.append("\t}")
        out.append("}")
        out.append("")

    # Equipped count
    out.append("")
    out.append("###### EQUIPPED MOVE COUNT ######")
    out.append(f"# Counts how many combat moves are currently equipped")
    out.append(f"# One line per active non-passive skill ({len(active_skills)} skills from master CSV)")
    out.append("")
    out.append("pod_combat_equipped_count = {")
    out.append("\tvalue = 0")

    current_section = None
    for s in active_skills:
        sec = s["config_section"]
        if sec != current_section:
            current_section = sec
            out.append(f"\t# {sec}")
        out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_equipped_{s['skill_key']} }} add = 1 }}")
    out.append("}")

    # Max equipped — deprecated total cap, kept as alias for compatibility.
    # The real constraint is pod_combat_max_per_category = 4, enforced per ATK/CTL/DEF/PWR.
    # A full loadout is 16 skills (4 per category).
    out.append("")
    out.append("###### MAX EQUIPPED LIMIT ######")
    out.append("# Maximum total equipped is 16 (4 per category * 4 categories)")
    out.append("")
    out.append("pod_combat_max_equipped = 16")

    # Discipline trait SVs
    out.append("")
    out.append("###### DISCIPLINE TRAIT CHECKS ######")
    out.append("# Used by GUI to show/hide discipline skill rows.")
    out.append("# Returns 1 if trait present, 0 if not.")

    sv_map = build_section_sv_map(all_implemented)
    current_discipline = None
    for sv_name, trait_name in sv_map:
        # Group by discipline base
        if trait_name.endswith("advanced"):
            base = trait_name[:-8]
        elif trait_name.endswith("discipline"):
            base = trait_name[:-10]
        else:
            base = trait_name

        if base != current_discipline:
            current_discipline = base
            out.append("")
            out.append(f"# --- {base.title()} ---")

        out.append(f"{sv_name} = {{")
        out.append("\tvalue = 0")
        # TRAIT_CHECK_OVERRIDES covers fake traits (tribes/breeds/hunter)
        # so the SV returns 1 when the real PoD condition is satisfied.
        out.append(f"\tif = {{ limit = {{ {_trait_check_line(trait_name)} }} add = 1 }}")
        out.append("}")
        out.append("")

    # Any discipline SV
    out.append("# --- Any discipline (checks all 20 basic discipline traits) ---")
    out.append("pod_combat_has_any_discipline_sv = {")
    out.append("\tvalue = 0")
    basic_disciplines = [
        "potencediscipline", "celeritydiscipline", "fortitudediscipline",
        "proteandiscipline", "dominatediscipline", "presencediscipline",
        "obfuscatediscipline", "obtenebrationdiscipline", "serpentisdiscipline",
        "daimoniondiscipline", "necromancydiscipline", "vicissitudediscipline",
        "valerendiscipline", "quietusdiscipline", "kaidiscipline",
        "animalismdiscipline", "dementationdiscipline", "abombwediscipline",
        "temporisdiscipline", "auspexdiscipline",
    ]
    for d in basic_disciplines:
        out.append(f"\tif = {{ limit = {{ has_trait = {d} }} add = 1 }}")
    out.append("}")

    # Vampire trait check
    out.append("")
    out.append("###### VAMPIRE TRAIT CHECK ######")
    out.append("# Returns 1 if character is a vampire, 0 if not")
    out.append("")
    out.append("pod_combat_is_vampire_sv = {")
    out.append("\tvalue = 0")
    out.append("\tif = { limit = { POD_is_vampire_trigger = yes } add = 1 }")
    out.append("}")

    # Combat log SVs
    out.append("")
    out.append("###### COMBAT LOG VALUES ######")
    out.append("# Each log entry (1-30, 1=newest) has: msg ID, actor slot (0-9), target slot (0-9 or -1), damage, blocked")
    for i in range(1, 31):
        out.append("")
        out.append(f"pod_combat_log_{i}_sv = {{ value = var:pod_combat_log_{i} }}")
        out.append(f"pod_combat_log_{i}_actor_sv = {{ value = var:pod_combat_log_{i}_actor }}")
        out.append(f"pod_combat_log_{i}_target_sv = {{ value = var:pod_combat_log_{i}_target }}")
        out.append(f"pod_combat_log_{i}_damage_sv = {{ value = var:pod_combat_log_{i}_damage }}")
        out.append(f"pod_combat_log_{i}_blocked_sv = {{ value = var:pod_combat_log_{i}_blocked }}")

    # Turn-change detection
    out.append("")
    out.append("# Turn-change detection: nonzero = actors differ between adjacent entries")
    for i in range(1, 30):
        j = i + 1
        out.append(f"pod_combat_log_turn_change_{i}_{j} = {{")
        out.append(f"\tvalue = var:pod_combat_log_{i}_actor")
        out.append(f"\tsubtract = var:pod_combat_log_{j}_actor")
        out.append("}")

    # Aggravated damage tracking comment
    out.append("")
    out.append("###### AGGRAVATED DAMAGE TRACKING ######")
    out.append("# Track aggravated damage separately for health write-back. Workspace")
    out.append("# vars hold this-round accumulation; once the round ends the count is")
    out.append("# rolled into each slot's _agg_total and the per-round counter resets.")
    out.append("#   pod_combat_player_agg_damage    \u2014 aggravated HP taken by the actor this round")
    out.append("#   pod_combat_opponent_agg_damage  \u2014 aggravated HP taken by the current target this round")
    out.append("# Per-slot versions (pod_combat_c{N}_agg_damage, pod_combat_c{N}_agg_total)")
    out.append("# are synced through the workspace bridge.")

    # Fera trait SVs
    out.append("")
    out.append("###### FERA TRAIT SVS ######")
    # PoD has no literal `fera` trait — the splat is represented by the three
    # shifter traits (werewolf, bastet, mokole). pod_combat_is_fera_sv routes
    # through pod_combat_is_fera_trigger so the OR lives in exactly one
    # place. Auspice/breed traits use their own direct has_trait checks.
    out.append("")
    out.append("pod_combat_is_fera_sv = {")
    out.append("\tvalue = 0")
    out.append(f"\tif = {{ limit = {{ {_trait_check_line('fera')} }} add = 1 }}")
    out.append("}")
    # Splat-level and auspice traits for all three shifter types. Werewolf,
    # bastet, and mokole are the three real fera splats; the rest are garou
    # auspices. Each emits `pod_combat_has_{trait}_sv`.
    for trait in ["werewolf", "bastet", "mokole",
                  "ahroun", "galliard", "philodox", "ragabash", "theurge"]:
        sv = f"pod_combat_has_{trait}_sv"
        out.append("")
        out.append(f"{sv} = {{")
        out.append("\tvalue = 0")
        out.append(f"\tif = {{ limit = {{ has_trait = {trait} }} add = 1 }}")
        out.append("}")

    # Fera perk gifts SV
    out.append("")
    out.append("pod_combat_has_fera_perk_gifts_sv = {")
    out.append("\tvalue = 0")
    # Collect perk skills from Perk Gifts config section — only valid PoD
    # perks; invalid ones would cause "Invalid database object" runtime errors.
    for s in all_implemented:
        if s["config_section"] == "Perk Gifts" and s["pod_perk_key"]:
            rp = resolve_perk(s["pod_perk_key"], skill_key=s["skill_key"],
                              invalid_tracker=_INVALID_PERKS_SEEN)
            if rp is not None:
                out.append(f"\tif = {{ limit = {{ has_perk = {rp} }} add = 1 }}")
    out.append("}")

    # Category count SVs
    out.append("")
    out.append("###### COMBAT SKILL CATEGORY COUNTS ######")
    out.append("")
    out.append("pod_combat_max_per_category = { value = 4 }")

    for cat in ["atk", "ctl", "def", "pwr"]:
        out.append("")
        out.append(f"pod_combat_{cat}_count = {{")
        out.append("\tvalue = 0")
        cat_upper = cat.upper()
        # Collect skills for this category with section comments
        current_section = None
        for s in active_skills:
            if s.get("combat_category") == cat_upper:
                sec = s["config_section"]
                if sec != current_section:
                    current_section = sec
                    if "Base" in sec:
                        out.append(f"\t# {sec}")
                    elif "Innate" in sec and "Fera" not in sec:
                        out.append(f"\t# Vampire attacks" if cat == "atk" else f"\t# {sec}")
                    elif "Fera" in sec or is_fera_skill(s):
                        out.append(f"\t# Fera {'attacks' if cat == 'atk' else sec.lower()}")
                out.append(f"\tif = {{ limit = {{ has_variable = pod_combat_equipped_{s['skill_key']} }} add = 1 }}")
        out.append("}")

    return BOM + "\n".join(out) + "\n"


# ──────────────────────────────────────────────────────────────────────
# FILE 6: COMBAT WINDOW GUI
# ──────────────────────────────────────────────────────────────────────

def generate_combat_window_gui(active_skills):
    """Generate File 6: gui/POD_windows/pod_combat_window.gui

    Three-panel group combat layout:
      Left (220px):  Ally team (slots 0-4, slot 0 = PC)
      Center (expanding): Header, AP, skill buttons, action buttons, combat log
      Right (220px): Enemy team (slots 5-9, clickable for target selection)
    """
    # Classify skills by combat_category
    atk = [s for s in active_skills if s.get("combat_category") == "ATK"]
    ctl = [s for s in active_skills if s.get("combat_category") == "CTL"]
    def_ = [s for s in active_skills if s.get("combat_category") == "DEF"]
    pwr = [s for s in active_skills if s.get("combat_category") == "PWR"]

    # Collect log entries: all active skills with log_msg_id > 0
    log_skills = [(s["log_msg_id"], s["display_name"]) for s in active_skills if s["log_msg_id"] > 0]
    log_skills.sort(key=lambda x: x[0])

    # ── Helper: single move button ──

    def button_block(key, indent="\t\t\t\t\t\t"):
        """Generate a single move button."""
        lines = []
        lines.append(f"{indent}button_standard = {{")
        lines.append(f'{indent}\tvisible = "[GetPlayer.MakeScope.Var(\'pod_combat_equipped_{key}\').IsSet]"')
        lines.append(f"{indent}\tsize = {{ 170 33 }}")
        lines.append(f'{indent}\tonclick = "[GetScriptedGui(\'pod_combat_move_{key}\').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"')
        lines.append(f'{indent}\tenabled = "[GetScriptedGui(\'pod_combat_move_{key}\').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"')
        lines.append(f'{indent}\ttooltip = "pod_combat_move_{key}_desc"')
        lines.append(f'{indent}\ttext = "pod_combat_move_{key}"')
        lines.append(f"{indent}}}")
        return "\n".join(lines)

    # ── Helper: category row (ATK/CTL/DEF/PWR) ──

    def category_row(label, skills_list):
        """Generate a category row (label + flowcontainer with buttons)."""
        lines = []
        lines.append(f"\t\t\t\t# \u2500\u2500 {label} \u2500\u2500")
        lines.append("\t\t\t\thbox = {")
        lines.append("\t\t\t\t\tlayoutpolicy_horizontal = expanding")
        lines.append("\t\t\t\t\tmargin = { 0 1 }")
        lines.append("\t\t\t\t")
        lines.append("\t\t\t\t\twidget = {")
        lines.append("\t\t\t\t\t\tsize = { 42 33 }")
        lines.append("\t\t\t\t\t\ttext_single = {")
        lines.append("\t\t\t\t\t\t\tparentanchor = vcenter")
        lines.append(f'\t\t\t\t\t\t\traw_text = "#bold {label}#!"')
        lines.append('\t\t\t\t\t\t\tdefault_format = "#weak"')
        lines.append("\t\t\t\t\t\t\tmargin_left = 2")
        lines.append("\t\t\t\t\t\t}")
        lines.append("\t\t\t\t\t}")
        lines.append("\t\t\t\t")
        lines.append("\t\t\t\t\tflowcontainer = {")
        lines.append("\t\t\t\t\t\tdirection = horizontal")
        lines.append("\t\t\t\t\t\tspacing = 4")
        lines.append("\t\t\t\t\t\tignoreinvisible = yes")
        for s in skills_list:
            lines.append("\t\t\t\t\t")
            lines.append(button_block(s["skill_key"]))
        lines.append("\t\t\t\t\t}")
        lines.append("\t\t\t\t\texpand = {}")
        lines.append("\t\t\t\t}")
        return "\n".join(lines)

    # ── Helper: combat log entry ──

    def log_entry(entry_num):
        """Generate a single combat log entry block."""
        sv = f"pod_combat_log_{entry_num}_sv"
        actor_sv = f"pod_combat_log_{entry_num}_actor_sv"
        target_sv = f"pod_combat_log_{entry_num}_target_sv"
        damage_sv = f"pod_combat_log_{entry_num}_damage_sv"
        blocked_sv = f"pod_combat_log_{entry_num}_blocked_sv"
        var_name = f"pod_combat_log_{entry_num}"

        lines = []
        if entry_num > 1:
            lines.append("")
            lines.append(f"\t\t\t\t\t# \u2500\u2500 Divider between entries {entry_num-1} and {entry_num} \u2500\u2500")
            lines.append(f"\t\t\t\t\tdivider_light = {{")
            lines.append(f'\t\t\t\t\t\tvisible = "[GetPlayer.MakeScope.Var(\'{var_name}\').IsSet]"')
            lines.append(f"\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
            lines.append(f"\t\t\t\t\t}}")

        lines.append("")
        lines.append(f"\t\t\t\t\t# \u2500\u2500 Entry {entry_num}" + (" (newest)" if entry_num == 1 else "") + " \u2500\u2500")
        lines.append(f"\t\t\t\t\thbox = {{")
        lines.append(f'\t\t\t\t\t\tvisible = "[GetPlayer.MakeScope.Var(\'{var_name}\').IsSet]"')
        lines.append(f"\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
        lines.append(f"\t\t\t\t\t\tmargin = {{ 5 2 }}")

        # Who column — character name based on actor slot (0-9)
        lines.append(f"\t\t\t\t\t\twidget = {{")
        lines.append(f"\t\t\t\t\t\t\tsize = {{ 180 20 }}")
        # Slot 0 — PC (always valid, no datacontext guard needed)
        lines.append(f"\t\t\t\t\t\t\twidget = {{")
        lines.append(f"\t\t\t\t\t\t\t\tvisible = \"[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue('{actor_sv}'), '(CFixedPoint)0')]\"")
        lines.append(f'\t\t\t\t\t\t\t\tdatacontext = "[GetPlayer]"')
        lines.append(f"\t\t\t\t\t\t\t\tsize = {{ 180 20 }}")
        lines.append(f"\t\t\t\t\t\t\t\ttext_single = {{")
        lines.append(f'\t\t\t\t\t\t\t\t\traw_text = "#bold [Character.GetFirstNameNoTooltip]#!"')
        lines.append(f"\t\t\t\t\t\t\t\t\talign = center")
        lines.append(f"\t\t\t\t\t\t\t\t}}")
        lines.append(f"\t\t\t\t\t\t\t}}")
        # Slots 1-9 — other combatants (need visible+datacontext on same widget)
        for slot in range(1, 10):
            lines.append(f"\t\t\t\t\t\t\twidget = {{")
            lines.append(f"\t\t\t\t\t\t\t\tvisible = \"[And(EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue('{actor_sv}'), '(CFixedPoint){slot}'), GetPlayer.MakeScope.Var('pod_combat_c{slot}_char').IsSet)]\"")
            lines.append(f'\t\t\t\t\t\t\t\tdatacontext = "[GetPlayer.MakeScope.Var(\'pod_combat_c{slot}_char\').GetCharacter]"')
            lines.append(f"\t\t\t\t\t\t\t\tsize = {{ 180 20 }}")
            lines.append(f"\t\t\t\t\t\t\t\ttext_single = {{")
            lines.append(f'\t\t\t\t\t\t\t\t\traw_text = "#bold [Character.GetFirstNameNoTooltip]#!"')
            lines.append(f"\t\t\t\t\t\t\t\t\talign = center")
            lines.append(f"\t\t\t\t\t\t\t\t}}")
            lines.append(f"\t\t\t\t\t\t\t}}")
        lines.append(f"\t\t\t\t\t\t}}")

        # Action column
        lines.append(f"\t\t\t\t\t\twidget = {{")
        lines.append(f"\t\t\t\t\t\t\tsize = {{ 200 20 }}")
        for msg_id, display_name in log_skills:
            lines.append(f"\t\t\t\t\t\t\ttext_single = {{ visible = \"[EqualTo_CFixedPoint( GetPlayer.MakeScope.ScriptValue('{sv}'), '(CFixedPoint){msg_id}' )]\" raw_text = \"{display_name}\" }}")
        lines.append(f"\t\t\t\t\t\t}}")

        # Target column — character name based on target slot (0-9); -1 = no target (self-cast)
        lines.append(f"\t\t\t\t\t\twidget = {{")
        lines.append(f"\t\t\t\t\t\t\tsize = {{ 180 20 }}")
        # Slot 0 — PC
        lines.append(f"\t\t\t\t\t\t\twidget = {{")
        lines.append(f"\t\t\t\t\t\t\t\tvisible = \"[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue('{target_sv}'), '(CFixedPoint)0')]\"")
        lines.append(f'\t\t\t\t\t\t\t\tdatacontext = "[GetPlayer]"')
        lines.append(f"\t\t\t\t\t\t\t\tsize = {{ 180 20 }}")
        lines.append(f"\t\t\t\t\t\t\t\ttext_single = {{")
        lines.append(f'\t\t\t\t\t\t\t\t\traw_text = "[Character.GetFirstNameNoTooltip]"')
        lines.append(f"\t\t\t\t\t\t\t\t\talign = center")
        lines.append(f"\t\t\t\t\t\t\t\t}}")
        lines.append(f"\t\t\t\t\t\t\t}}")
        # Slots 1-9 — other combatants
        for slot in range(1, 10):
            lines.append(f"\t\t\t\t\t\t\twidget = {{")
            lines.append(f"\t\t\t\t\t\t\t\tvisible = \"[And(EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue('{target_sv}'), '(CFixedPoint){slot}'), GetPlayer.MakeScope.Var('pod_combat_c{slot}_char').IsSet)]\"")
            lines.append(f'\t\t\t\t\t\t\t\tdatacontext = "[GetPlayer.MakeScope.Var(\'pod_combat_c{slot}_char\').GetCharacter]"')
            lines.append(f"\t\t\t\t\t\t\t\tsize = {{ 180 20 }}")
            lines.append(f"\t\t\t\t\t\t\t\ttext_single = {{")
            lines.append(f'\t\t\t\t\t\t\t\t\traw_text = "[Character.GetFirstNameNoTooltip]"')
            lines.append(f"\t\t\t\t\t\t\t\t\talign = center")
            lines.append(f"\t\t\t\t\t\t\t\t}}")
            lines.append(f"\t\t\t\t\t\t\t}}")
        # No target (-1) — show em-dash for self-cast / untargeted moves
        lines.append(f"\t\t\t\t\t\t\ttext_single = {{")
        lines.append(f"\t\t\t\t\t\t\t\tvisible = \"[LessThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue('{target_sv}'), '(CFixedPoint)0')]\"")
        lines.append(f'\t\t\t\t\t\t\t\traw_text = "#weak \u2014#!"')
        lines.append(f"\t\t\t\t\t\t\t\talign = center")
        lines.append(f"\t\t\t\t\t\t\t}}")
        lines.append(f"\t\t\t\t\t\t}}")

        # Result column
        lines.append(f"\t\t\t\t\t\twidget = {{")
        lines.append(f"\t\t\t\t\t\t\tsize = {{ 160 20 }}")
        lines.append(f"\t\t\t\t\t\t\ttext_single = {{ visible = \"[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue('{blocked_sv}'), '(CFixedPoint)0')]\" raw_text = \"[GetPlayer.MakeScope.ScriptValue('{damage_sv}')|0] HP\" }}")
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)1\')]" raw_text = "#italic Blocked!#!" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)2\')]" raw_text = "#italic Soaked!#!" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)3\')]" raw_text = "#italic Missed!#!" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)4\')]" raw_text = "#italic Countered!#!" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)5\')]" raw_text = "#italic Dodged!#!" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)6\')]" raw_text = "[GetPlayer.MakeScope.ScriptValue(\'{damage_sv}\')|0] HP #italic Retaliated!#!" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)7\')]" raw_text = "[GetPlayer.MakeScope.ScriptValue(\'{damage_sv}\')|0] HP #italic Counter Soaked#!" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)8\')]" raw_text = "#italic Applied#!" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)9\')]" raw_text = "[GetPlayer.MakeScope.ScriptValue(\'{damage_sv}\')|0] Morale" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)10\')]" raw_text = "#G +[GetPlayer.MakeScope.ScriptValue(\'{damage_sv}\')|0] HP#!" }}')
        lines.append(f'\t\t\t\t\t\t\ttext_single = {{ visible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{blocked_sv}\'), \'(CFixedPoint)11\')]" raw_text = "#G +[GetPlayer.MakeScope.ScriptValue(\'{damage_sv}\')|0] Morale#!" }}')
        lines.append(f"\t\t\t\t\t\t}}")
        lines.append(f"\t\t\t\t\t\texpand = {{}}")

        lines.append(f"\t\t\t\t\t}}")
        return "\n".join(lines)

    # ── Helper: character card (used for both allies and enemies) ──
    # No portrait_head_small — CK3 crashes when datacontext references a nonexistent variable

    def hp_flowcontainer(i, indent, box_size=12):
        """Emit a flowcontainer of 10 HP track boxes for slot i at the given indent."""
        out = []
        out.append(f"{indent}flowcontainer = {{")
        out.append(f"{indent}\tdirection = horizontal")
        out.append(f"{indent}\tspacing = 0")
        out.append(f"{indent}\tignoreinvisible = yes")
        for b in range(1, 11):
            out.append(f"{indent}\twidget = {{")
            out.append(f'{indent}\t\tvisible = "[GreaterThanOrEqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_max_hp_value\'), \'(CFixedPoint){b}\')]"')
            out.append(f"{indent}\t\tsize = {{ {box_size} {box_size} }}")
            out.append(f"{indent}\t\ticon = {{")
            out.append(f'{indent}\t\t\tvisible = "[LessThanOrEqualTo_CFixedPoint(\'(CFixedPoint){b}\', GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_agg_damage_sv\'))]"')
            out.append(f'{indent}\t\t\ttexture = "gfx/interface/icons/text_icons/aggravateddamagehealthtrack.dds"')
            out.append(f"{indent}\t\t\tsize = {{ {box_size} {box_size} }}")
            out.append(f"{indent}\t\t}}")
            out.append(f"{indent}\t\ticon = {{")
            out.append(f'{indent}\t\t\tvisible = "[And(GreaterThan_CFixedPoint(\'(CFixedPoint){b}\', GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_agg_damage_sv\')), LessThanOrEqualTo_CFixedPoint(\'(CFixedPoint){b}\', GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_total_damage_sv\')))]"')
            out.append(f'{indent}\t\t\ttexture = "gfx/interface/icons/text_icons/normaldamagehealthtrack.dds"')
            out.append(f"{indent}\t\t\tsize = {{ {box_size} {box_size} }}")
            out.append(f"{indent}\t\t}}")
            out.append(f"{indent}\t\ticon = {{")
            out.append(f'{indent}\t\t\tvisible = "[GreaterThan_CFixedPoint(\'(CFixedPoint){b}\', GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_total_damage_sv\'))]"')
            out.append(f'{indent}\t\t\ttexture = "gfx/interface/icons/text_icons/emptyhealthtrack.dds"')
            out.append(f"{indent}\t\t\tsize = {{ {box_size} {box_size} }}")
            out.append(f"{indent}\t\t}}")
            out.append(f"{indent}\t}}")
        out.append(f"{indent}}}")
        return "\n".join(out)

    def portrait_stats_block(i, indent):
        """Emit the Name + HP + Morale vbox that sits to the right of the portrait,
        plus a vertical status-icon strip on the far right showing active stances
        (guard, dodge, stealth).
        Returns a block of lines ready to be appended inside an hbox.
        """
        out = []
        # Stats column
        out.append(f"{indent}vbox = {{")
        out.append(f"{indent}\tmargin_left = 4")
        out.append(f"{indent}\tspacing = 1")
        # Character name
        out.append(f"{indent}\ttext_single = {{")
        out.append(f'{indent}\t\traw_text = "[Character.GetFirstNameNoTooltip]"')
        out.append(f'{indent}\t\tdefault_format = "#bold"')
        out.append(f"{indent}\t}}")
        # HP label
        out.append(f"{indent}\ttext_single = {{")
        out.append(f'{indent}\t\traw_text = "#bold HP#!"')
        out.append(f'{indent}\t\tdefault_format = "#weak"')
        out.append(f"{indent}\t}}")
        # HP boxes
        out.append(hp_flowcontainer(i, f"{indent}\t", box_size=12))
        # Morale label
        out.append(f"{indent}\ttext_single = {{")
        out.append(f'{indent}\t\traw_text = "#bold Morale#!"')
        out.append(f'{indent}\t\tdefault_format = "#weak"')
        out.append(f"{indent}\t}}")
        # Morale bar
        out.append(f"{indent}\tprogressbar_standard = {{")
        out.append(f"{indent}\t\tsize = {{ 150 10 }}")
        out.append(f'{indent}\t\tvalue = "[GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_morale_pct\')]"')
        out.append(f"{indent}\t}}")
        out.append(f"{indent}}}")

        return "\n".join(out)

    def status_icons_overlay(i, indent):
        """Emit absolutely-positioned status icons that float over the
        top-right corner of a character card's widget. The widget uses
        fixed size (245x90) so absolute positioning works."""
        guard_sv = f"pod_combat_c{i}_is_guarding_value"
        dodge_sv = f"pod_combat_c{i}_is_dodging_value"
        stealth_sv = f"pod_combat_c{i}_is_stealthed_value"
        out = []
        # Guard icon — top-right
        out.append(f"{indent}icon = {{")
        out.append(f'{indent}\tvisible = "[GreaterThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{guard_sv}\'), \'(CFixedPoint)0\')]"')
        out.append(f'{indent}\ttexture = "gfx/interface/icon/combat/guard.dds"')
        out.append(f"{indent}\tsize = {{ 24 24 }}")
        out.append(f"{indent}\tposition = {{ 210 2 }}")
        out.append(f'{indent}\ttooltip = "pod_combat_status_guard_tt"')
        out.append(f"{indent}}}")
        # Dodge icon — below guard (only for dodge, NOT stealth)
        out.append(f"{indent}icon = {{")
        out.append(f'{indent}\tvisible = "[GreaterThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{dodge_sv}\'), \'(CFixedPoint)0\')]"')
        out.append(f'{indent}\ttexture = "gfx/interface/icon/combat/dodge.dds"')
        out.append(f"{indent}\tsize = {{ 24 24 }}")
        out.append(f"{indent}\tposition = {{ 210 28 }}")
        out.append(f'{indent}\ttooltip = "pod_combat_status_dodge_tt"')
        out.append(f"{indent}}}")
        # Stealth icon — below dodge
        out.append(f"{indent}icon = {{")
        out.append(f'{indent}\tvisible = "[GreaterThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'{stealth_sv}\'), \'(CFixedPoint)0\')]"')
        out.append(f'{indent}\ttexture = "gfx/interface/icon/combat/stealth.dds"')
        out.append(f"{indent}\tsize = {{ 24 24 }}")
        out.append(f"{indent}\tposition = {{ 210 54 }}")
        out.append(f'{indent}\ttooltip = "pod_combat_status_stealth_tt"')
        out.append(f"{indent}}}")
        return "\n".join(out)

    def effects_row(slot_num, indent):
        """Generate the tier buff/debuff summary row for a character card.
        Shows compact text like '+20 Soak (R)' in green for active buffs and
        '-20 Hit (C)' in red for active debuffs. Each of the 8 possible tier
        slots is a separate text_single gated on its magnitude > 0, so the
        row is visually empty when no effects are active.
        """
        i = slot_num
        lines = []
        lines.append(f"{indent}flowcontainer = {{")
        lines.append(f"{indent}\tmargin = {{ 4 1 }}")
        lines.append(f"{indent}\tignoreinvisible = yes")
        lines.append(f"{indent}\tspacing = 6")
        for stat in TIER_STATS:
            for direction in TIER_DIRECTIONS:
                for duration in TIER_DURATIONS:
                    stem = tier_var_stem(stat, direction, duration)
                    sv = f"pod_combat_c{i}_{stem}_mag_sv"
                    sign = "+" if direction == "buff" else "-"
                    # CK3 standard format codes: #P = green (positive), #N = red (negative)
                    color = "#P" if direction == "buff" else "#N"
                    stat_label = "Soak" if stat == "soak" else "Hit"
                    dur_label = "R" if duration == "round" else "C"
                    lines.append(f"{indent}\ttext_single = {{")
                    lines.append(f"{indent}\t\tvisible = \"[GreaterThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue('{sv}'), '(CFixedPoint)0')]\"")
                    lines.append(f"{indent}\t\traw_text = \"{color} {sign}[GetPlayer.MakeScope.ScriptValue('{sv}')|0] {stat_label} ({dur_label})#!\"")
                    # Match the Prowess/Init lines' base font style (weak); the
                    # #P / #N inline color tag only re-colors, leaving the
                    # weak size and weight intact.
                    lines.append(f"{indent}\t\tdefault_format = \"#weak\"")
                    lines.append(f"{indent}\t}}")
        lines.append(f"{indent}}}")
        return "\n".join(lines)

    def ally_card(slot_num, indent):
        """Generate a character card for an ally slot.

        Slot 0 is always the PC and has no Target button — self-only skills
        use targeting = self. Slots 1-4 get a unified Target button that
        sets pod_combat_pc_target (the single, unified target variable used
        by every combat card regardless of team).
        """
        i = slot_num
        lines = []
        lines.append(f"{indent}# Slot {i}")
        lines.append(f"{indent}vbox = {{")
        lines.append(f'{indent}\tvisible = "[GreaterThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_max_hp_value\'), \'(CFixedPoint)0\')]"')
        lines.append(f"{indent}\tminimumsize = {{ 240 -1 }}")
        lines.append(f"{indent}\tmaximumsize = {{ 240 -1 }}")
        lines.append(f"{indent}\tmargin = {{ 2 2 }}")
        lines.append(f"{indent}\tbackground = {{ using = Background_Area }}")
        # Portrait + Name + HP + Morale row — all compact side-by-side
        if i == 0:
            # Slot 0 is always the PC — use GetPlayer directly
            lines.append(f"{indent}\twidget = {{")
            lines.append(f'{indent}\t\tdatacontext = "[GetPlayer]"')
            lines.append(f"{indent}\t\tsize = {{ 240 90 }}")
            lines.append(f"{indent}\t\thbox = {{")
            lines.append(f"{indent}\t\t\tmargin = {{ 3 2 }}")
            lines.append(f"{indent}\t\t\tportrait_head_small = {{}}")
            lines.append(portrait_stats_block(i, f"{indent}\t\t\t"))
            lines.append(f"{indent}\t\t}}")
            # Status icons overlaid on the card
            lines.append(status_icons_overlay(i, f"{indent}\t\t"))
            lines.append(f"{indent}\t}}")
        else:
            lines.append(f"{indent}\twidget = {{")
            lines.append(f'{indent}\t\tvisible = "[GetPlayer.MakeScope.Var(\'pod_combat_c{i}_char\').IsSet]"')
            lines.append(f'{indent}\t\tdatacontext = "[GetPlayer.MakeScope.Var(\'pod_combat_c{i}_char\').GetCharacter]"')
            lines.append(f"{indent}\t\tsize = {{ 240 90 }}")
            lines.append(f"{indent}\t\thbox = {{")
            lines.append(f"{indent}\t\t\tmargin = {{ 3 2 }}")
            lines.append(f"{indent}\t\t\tportrait_head_small = {{}}")
            lines.append(portrait_stats_block(i, f"{indent}\t\t\t"))
            lines.append(f"{indent}\t\t}}")
            # Status icons overlaid on the card
            lines.append(status_icons_overlay(i, f"{indent}\t\t"))
            lines.append(f"{indent}\t}}")
        # KO status bar — only appears when the ally is down.
        # When alive, the widget is hidden and its space collapses so the rest of
        # the card packs tighter. The vbox parent's layout naturally recovers the
        # 22px that was reserved for this row.
        #
        # For slots 1-4, this slot is ALSO the ally-target button (three states:
        # KNOCKED OUT / TARGETED / Target). Slot 0 (PC) has no Target button —
        # only the KO row — since self-buffs use targeting = self.
        if i == 0:
            # hbox (not widget) so the parent vbox can collapse this row via
            # ignoreinvisible when the PC is alive. widget does not support
            # ignoreinvisible and cannot be positioned inside a layout.
            lines.append(f"{indent}\thbox = {{")
            lines.append(f'{indent}\t\tvisible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_alive_value\'), \'(CFixedPoint)0\')]"')
            lines.append(f"{indent}\t\tminimumsize = {{ 240 22 }}")
            lines.append(f"{indent}\t\ttext_single = {{")
            lines.append(f'{indent}\t\t\traw_text = "#bold KNOCKED OUT#!"')
            lines.append(f"{indent}\t\t}}")
            lines.append(f"{indent}\t}}")
        else:
            # Unified target selection button. Same shape as the enemy card
            # button — clicking it sets pod_combat_pc_target to this slot.
            # Three visual states (priority order):
            #   1. KNOCKED OUT — combatant is dead, button is disabled via is_valid
            #   2. TARGETED   — this slot is the PC's current target
            #   3. Target     — selectable living ally
            lines.append(f"{indent}\tbutton_standard = {{")
            lines.append(f"{indent}\t\tsize = {{ 240 22 }}")
            # parentanchor is not valid on a widget inside a layout container
            # (triggers "Widget cannot have a position in a layout"). The
            # parent slot vbox is 250 wide, so a symmetric 5px horizontal
            # margin centers the 240-wide button without using parentanchor.
            lines.append(f"{indent}\t\tmargin = {{ 5 0 }}")
            lines.append(f'{indent}\t\tvisible = "[GetPlayer.MakeScope.Var(\'pod_combat_c{i}_char\').IsSet]"')
            lines.append(f'{indent}\t\tonclick = "[GetScriptedGui(\'pod_combat_select_target_{i}\').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"')
            lines.append(f'{indent}\t\tenabled = "[GetScriptedGui(\'pod_combat_select_target_{i}\').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"')
            lines.append(f'{indent}\t\ttooltip = "pod_combat_select_target_tooltip"')
            # KNOCKED OUT (dead) — highest priority
            lines.append(f"{indent}\t\ttext_single = {{")
            lines.append(f'{indent}\t\t\tvisible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_alive_value\'), \'(CFixedPoint)0\')]"')
            lines.append(f'{indent}\t\t\traw_text = "#bold KNOCKED OUT#!"')
            lines.append(f"{indent}\t\t\tparentanchor = center")
            lines.append(f"{indent}\t\t}}")
            # TARGETED (alive + this is current target)
            lines.append(f"{indent}\t\ttext_single = {{")
            lines.append(f'{indent}\t\t\tvisible = "[And(EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_alive_value\'), \'(CFixedPoint)1\'), EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_pc_target_value\'), \'(CFixedPoint){i}\'))]"')
            lines.append(f'{indent}\t\t\traw_text = "#bold TARGETED#!"')
            lines.append(f"{indent}\t\t\tparentanchor = center")
            lines.append(f"{indent}\t\t}}")
            # Target (alive + not current target)
            lines.append(f"{indent}\t\ttext_single = {{")
            lines.append(f'{indent}\t\t\tvisible = "[And(EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_alive_value\'), \'(CFixedPoint)1\'), Not(EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_pc_target_value\'), \'(CFixedPoint){i}\')))]"')
            lines.append(f'{indent}\t\t\traw_text = "Target"')
            lines.append(f"{indent}\t\t\tparentanchor = center")
            lines.append(f"{indent}\t\t}}")
            lines.append(f"{indent}\t}}")
        # Stats text
        lines.append(f"{indent}\ttext_single = {{")
        lines.append(f"{indent}\t\tmargin = {{ 4 1 }}")
        lines.append(f'{indent}\t\traw_text = "Prowess: [GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_prowess_value\')|0]  Hit: [GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_hit_chance_value\')|0]%  Soak: [GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_soak_value\')|0]%"')
        lines.append(f'{indent}\t\tdefault_format = "#weak"')
        lines.append(f"{indent}\t}}")
        # Initiative + turn order text (hidden if initiative not yet calculated)
        lines.append(f"{indent}\ttext_single = {{")
        lines.append(f"{indent}\t\tmargin = {{ 4 1 }}")
        lines.append(f'{indent}\t\tvisible = "[GreaterThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_initiative_value\'), \'(CFixedPoint)0\')]"')
        lines.append(f'{indent}\t\traw_text = "Init:[GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_initiative_value\')|0] Turn:[GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_turn_order_value\')|0]"')
        lines.append(f'{indent}\t\tdefault_format = "#weak"')
        lines.append(f"{indent}\t}}")
        # Tier buff/debuff effects row
        lines.append(effects_row(i, indent + "\t"))
        # Active actor highlight
        lines.append(f"{indent}\tbackground = {{")
        lines.append(f'{indent}\t\tvisible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_current_actor_value\'), \'(CFixedPoint){i}\')]"')
        lines.append(f"{indent}\t\tusing = Background_Area_Dark")
        lines.append(f"{indent}\t\tmargin = {{ -2 -2 }}")
        lines.append(f"{indent}\t}}")
        lines.append(f"{indent}}}")
        return "\n".join(lines)

    def enemy_card(slot_num, indent):
        """Generate a character card for an enemy slot with target selection."""
        i = slot_num
        lines = []
        lines.append(f"{indent}# Slot {i}")
        lines.append(f"{indent}vbox = {{")
        lines.append(f'{indent}\tvisible = "[GreaterThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_max_hp_value\'), \'(CFixedPoint)0\')]"')
        lines.append(f"{indent}\tminimumsize = {{ 240 -1 }}")
        lines.append(f"{indent}\tmaximumsize = {{ 240 -1 }}")
        lines.append(f"{indent}\tmargin = {{ 2 2 }}")
        lines.append(f"{indent}\tbackground = {{ using = Background_Area }}")
        # Portrait + Name + HP + Morale row (compact, all side-by-side)
        lines.append(f"{indent}\twidget = {{")
        lines.append(f'{indent}\t\tvisible = "[GetPlayer.MakeScope.Var(\'pod_combat_c{i}_char\').IsSet]"')
        lines.append(f'{indent}\t\tdatacontext = "[GetPlayer.MakeScope.Var(\'pod_combat_c{i}_char\').GetCharacter]"')
        lines.append(f"{indent}\t\tsize = {{ 240 90 }}")
        lines.append(f"{indent}\t\thbox = {{")
        lines.append(f"{indent}\t\t\tmargin = {{ 3 2 }}")
        lines.append(f"{indent}\t\t\tportrait_head_small = {{}}")
        lines.append(portrait_stats_block(i, f"{indent}\t\t\t"))
        lines.append(f"{indent}\t\t}}")
        # Status icons overlaid on the card
        lines.append(status_icons_overlay(i, f"{indent}\t\t"))
        lines.append(f"{indent}\t}}")
        # Target selection button (full width of card)
        # Three visual states (priority order):
        #   1. KNOCKED OUT — combatant is dead, button is disabled via is_valid
        #   2. TARGETED   — this slot is the PC's current target
        #   3. Target     — selectable living enemy
        lines.append(f"{indent}\tbutton_standard = {{")
        lines.append(f"{indent}\t\tsize = {{ 240 22 }}")
        # Symmetric 5px horizontal margin centers the 240-wide button in the
        # 250-wide enemy slot vbox without needing parentanchor (invalid on
        # a widget inside a layout container).
        lines.append(f"{indent}\t\tmargin = {{ 5 0 }}")
        lines.append(f'{indent}\t\tonclick = "[GetScriptedGui(\'pod_combat_select_target_{i}\').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"')
        lines.append(f'{indent}\t\tenabled = "[GetScriptedGui(\'pod_combat_select_target_{i}\').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"')
        lines.append(f'{indent}\t\ttooltip = "pod_combat_select_target_tooltip"')
        # KNOCKED OUT (dead) — highest priority, shown regardless of target state
        lines.append(f"{indent}\t\ttext_single = {{")
        lines.append(f'{indent}\t\t\tvisible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_alive_value\'), \'(CFixedPoint)0\')]"')
        lines.append(f'{indent}\t\t\traw_text = "#bold KNOCKED OUT#!"')
        lines.append(f"{indent}\t\t\tparentanchor = center")
        lines.append(f"{indent}\t\t}}")
        # TARGETED (alive + current target)
        lines.append(f"{indent}\t\ttext_single = {{")
        lines.append(f'{indent}\t\t\tvisible = "[And(EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_alive_value\'), \'(CFixedPoint)1\'), EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_pc_target_value\'), \'(CFixedPoint){i}\'))]"')
        lines.append(f'{indent}\t\t\traw_text = "#bold TARGETED#!"')
        lines.append(f"{indent}\t\t\tparentanchor = center")
        lines.append(f"{indent}\t\t}}")
        # Target (alive + not current target)
        lines.append(f"{indent}\t\ttext_single = {{")
        lines.append(f'{indent}\t\t\tvisible = "[And(EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_alive_value\'), \'(CFixedPoint)1\'), Not(EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_pc_target_value\'), \'(CFixedPoint){i}\')))]"')
        lines.append(f'{indent}\t\t\traw_text = "Target"')
        lines.append(f"{indent}\t\t\tparentanchor = center")
        lines.append(f"{indent}\t\t}}")
        lines.append(f"{indent}\t}}")
        # Stats text
        lines.append(f"{indent}\ttext_single = {{")
        lines.append(f"{indent}\t\tmargin = {{ 4 1 }}")
        lines.append(f'{indent}\t\traw_text = "Prowess: [GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_prowess_value\')|0]  Hit: [GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_hit_chance_value\')|0]%  Soak: [GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_soak_value\')|0]%"')
        lines.append(f'{indent}\t\tdefault_format = "#weak"')
        lines.append(f"{indent}\t}}")
        # Initiative + turn order text (hidden if initiative not yet calculated)
        lines.append(f"{indent}\ttext_single = {{")
        lines.append(f"{indent}\t\tmargin = {{ 4 1 }}")
        lines.append(f'{indent}\t\tvisible = "[GreaterThan_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_initiative_value\'), \'(CFixedPoint)0\')]"')
        lines.append(f'{indent}\t\traw_text = "Init:[GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_initiative_value\')|0] Turn:[GetPlayer.MakeScope.ScriptValue(\'pod_combat_c{i}_turn_order_value\')|0]"')
        lines.append(f'{indent}\t\tdefault_format = "#weak"')
        lines.append(f"{indent}\t}}")
        # Tier buff/debuff effects row
        lines.append(effects_row(i, indent + "\t"))
        # Active actor highlight
        lines.append(f"{indent}\tbackground = {{")
        lines.append(f'{indent}\t\tvisible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_current_actor_value\'), \'(CFixedPoint){i}\')]"')
        lines.append(f"{indent}\t\tusing = Background_Area_Dark")
        lines.append(f"{indent}\t\tmargin = {{ -2 -2 }}")
        lines.append(f"{indent}\t}}")
        # Selected target highlight (PC's persistent target, not the transient
        # workspace dispatch variable — pc_target_value stays stable during
        # AI turns so the highlight doesn't flicker).
        lines.append(f"{indent}\tbackground = {{")
        lines.append(f'{indent}\t\tvisible = "[EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'pod_combat_pc_target_value\'), \'(CFixedPoint){i}\')]"')
        lines.append(f"{indent}\t\tusing = Background_Area_Dark")
        lines.append(f"{indent}\t\tmargin = {{ -2 -2 }}")
        lines.append(f"{indent}\t}}")
        lines.append(f"{indent}}}")
        return "\n".join(lines)

    # ────────────────────────────────────────────────
    # Build the full three-panel GUI
    # ────────────────────────────────────────────────

    out = []
    out.append("######################################")
    out.append("######   POD COMBAT WINDOW   ######")
    out.append("######################################")
    out.append("")
    out.append("# Three-panel group combat layout.")
    out.append("# Left: Ally team (slots 0-4).  Center: Controls + log.  Right: Enemy team (slots 5-9).")
    out.append("# Visible when pod_combat_active variable is set on the player.")
    out.append("")
    out.append("widget = {")
    out.append('\tname = "pod_combat_window"')
    out.append('\tvisible = "[And(And(Not(IsPauseMenuShown), IsDefaultGUIMode), GetPlayer.IsValid)]"')
    out.append("\tlayer = royal_court")
    out.append("\tsize = { 100% 100% }")
    out.append("")
    out.append("\twindow = {")
    out.append("\t\tparentanchor = center")
    out.append("\t\tsize = { 1410 940 }")
    out.append("\t\tusing = Window_Background")
    out.append("\t\tusing = Window_Decoration")
    out.append("")
    out.append("\t\tvisible = \"[And(GetPlayer.MakeScope.Var('pod_combat_active').IsSet, Not(GetPlayer.MakeScope.Var('pod_combat_config_open').IsSet))]\"")
    out.append("")

    # ── Outer hbox: padding | content column | padding ──
    # The empty side widgets give the content area breathing room so it doesn't
    # overflow the window. The header bar sits above the three-panel hbox INSIDE
    # the content column, so it only spans the content area (not the padding).
    out.append("\t\thbox = {")
    out.append("\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\tlayoutpolicy_vertical = expanding")
    out.append("")
    out.append("\t\t\t# Left padding (empty)")
    out.append("\t\t\twidget = {")
    out.append("\t\t\t\tminimumsize = { 30 -1 }")
    out.append("\t\t\t\tmaximumsize = { 30 -1 }")
    out.append("\t\t\t}")
    out.append("")
    out.append("\t\t\t# Content column: top buffer, header, middle buffer, three-panel hbox, bottom buffer")
    out.append("\t\t\tvbox = {")
    out.append("\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append("")
    out.append("\t\t\t\t# Top buffer row (20px empty space above the Combat header)")
    out.append("\t\t\t\twidget = {")
    out.append("\t\t\t\t\tminimumsize = { -1 20 }")
    out.append("\t\t\t\t\tmaximumsize = { -1 20 }")
    out.append("\t\t\t\t}")
    out.append("")
    out.append("\t\t\t\t##############################")
    out.append("\t\t\t\t###### HEADER (content width)")
    out.append("\t\t\t\t##############################")
    out.append("")
    out.append("\t\t\t\theader_pattern = {")
    out.append("\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("")
    out.append('\t\t\t\t\tblockoverride "header_text" {')
    out.append('\t\t\t\t\t\ttext = "pod_combat_window_title"')
    out.append("\t\t\t\t\t}")
    out.append("")
    out.append('\t\t\t\t\tblockoverride "button_close" {')
    out.append("\t\t\t\t\t\tonclick = \"[GetScriptedGui('pod_combat_forfeit').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append('\t\t\t\t\t\ttooltip = "pod_combat_forfeit_tooltip"')
    out.append("\t\t\t\t\t}")
    out.append("\t\t\t\t}")
    out.append("")

    # ── Three-panel hbox: allies | center | enemies ──
    # Uses expanding layout so it fills all remaining vertical space below the header
    out.append("\t\t\thbox = {")
    out.append("\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append("\t\t\t\tmargin = { 5 5 }")

    # ══════════════════════════════════════════════
    # LEFT PANEL: Ally team
    # ══════════════════════════════════════════════
    out.append("")
    out.append("\t\t\t##############################")
    out.append("\t\t\t###### LEFT PANEL: ALLIES")
    out.append("\t\t\t##############################")
    out.append("")
    out.append("\t\t\t\tvbox = {")
    out.append("\t\t\t\t\tminimumsize = { 280 -1 }")
    out.append("\t\t\t\t\tmaximumsize = { 280 -1 }")
    out.append("\t\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append("\t\t\t\t\tmargin = { 5 2 }")
    out.append("")
    out.append("\t\t\t\t\ttext_single = {")
    out.append('\t\t\t\t\t\traw_text = "#bold ALLIES#!"')
    out.append('\t\t\t\t\t\tdefault_format = "#weak"')
    out.append("\t\t\t\t\t\talign = center")
    out.append("\t\t\t\t\t}")
    out.append("")

    # Ally cards go inside a scrollbox so long rows (many buffs / debuffs)
    # don't push cards off the panel. The scrollbox expands vertically to
    # fill the left column; its inner vbox holds all 5 cards plus a trailing
    # expand to keep empty slots from leaving visual gaps.
    out.append("\t\t\t\t\tscrollbox = {")
    out.append("\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append('\t\t\t\t\t\tblockoverride "scrollbox_content"')
    out.append("\t\t\t\t\t\t{")
    out.append("\t\t\t\t\t\t\tvbox = {")
    out.append("\t\t\t\t\t\t\t\tmargin = { 0 2 }")
    ally_indent = "\t\t\t\t\t\t\t\t"
    for slot in range(0, 5):
        out.append("")
        out.append(ally_card(slot, ally_indent))
    out.append("")
    out.append(f"{ally_indent}expand = {{}}")
    out.append("\t\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t}")
    out.append("\t\t\t}")  # close left panel vbox

    # ══════════════════════════════════════════════
    # CENTER PANEL: Header + Skills + Log
    # ══════════════════════════════════════════════
    out.append("")
    out.append("\t\t\t##############################")
    out.append("\t\t\t###### CENTER PANEL")
    out.append("\t\t\t##############################")
    out.append("")
    out.append("\t\t\tvbox = {")
    out.append("\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append("")

    # Round + AP on a single row to save vertical space
    out.append("")
    out.append("\t\t\t\t# Round counter + Action Points on a single line")
    out.append("\t\t\t\thbox = {")
    out.append("\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\tmargin = { 10 4 }")
    out.append("\t\t\t\t\tspacing = 24")
    out.append("\t\t\t\t\ttext_single = {")
    out.append("\t\t\t\t\t\traw_text = \"[Localize('pod_combat_round')]\"")
    out.append('\t\t\t\t\t\tdefault_format = "#bold"')
    out.append("\t\t\t\t\t}")
    out.append("\t\t\t\t\ttext_single = {")
    out.append("\t\t\t\t\t\traw_text = \"[Localize('pod_combat_ap_label')]: [GetPlayer.MakeScope.ScriptValue('pod_combat_current_ap_value')|0] / [GetPlayer.MakeScope.ScriptValue('pod_combat_base_ap')|0]\"")
    out.append('\t\t\t\t\t\tdefault_format = "#bold"')
    out.append("\t\t\t\t\t}")
    out.append("\t\t\t\t\texpand = {}")
    out.append("\t\t\t\t}")

    # Move buttons
    out.append("")
    out.append("\t\t\t\t##############################")
    out.append("\t\t\t\t###### MOVE BUTTONS")
    out.append("\t\t\t\t##############################")
    out.append("")
    out.append("\t\t\t\tvbox = {")
    out.append("\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\tmargin = { 5 0 }")
    out.append("\t\t\t\t\tspacing = 2")
    out.append("")
    out.append(category_row("ATK", atk))
    out.append("")
    out.append(category_row("CTL", ctl))
    out.append("")
    out.append(category_row("DEF", def_))
    out.append("")
    out.append(category_row("PWR", pwr))
    out.append("\t\t\t\t}")

    # Action buttons
    out.append("")
    out.append("\t\t\t\t##############################")
    out.append("\t\t\t\t###### ACTION BUTTONS")
    out.append("\t\t\t\t##############################")
    out.append("")
    out.append("\t\t\t\thbox = {")
    out.append("\t\t\t\t\tmargin = { 10 4 }")
    out.append("\t\t\t\t\tspacing = 20")
    out.append("")
    # End Turn button — visible during combat, hidden when over
    out.append("\t\t\t\t\tbutton_standard = {")
    out.append('\t\t\t\t\t\tvisible = "[Not(GetPlayer.MakeScope.Var(\'pod_combat_is_over\').IsSet)]"')
    out.append("\t\t\t\t\t\tsize = { 170 33 }")
    out.append('\t\t\t\t\t\ttext = "pod_combat_end_turn"')
    out.append("\t\t\t\t\t\tonclick = \"[GetScriptedGui('pod_combat_end_turn').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append("\t\t\t\t\t\tenabled = \"[GetScriptedGui('pod_combat_end_turn').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append('\t\t\t\t\t\ttooltip = "pod_combat_end_turn_desc"')
    out.append("\t\t\t\t\t}")
    out.append("")
    # Auto-resolve — hidden when combat is over
    out.append("\t\t\t\t\tbutton_standard = {")
    out.append('\t\t\t\t\t\tvisible = "[Not(GetPlayer.MakeScope.Var(\'pod_combat_is_over\').IsSet)]"')
    out.append("\t\t\t\t\t\tsize = { 170 33 }")
    out.append('\t\t\t\t\t\ttext = "pod_combat_auto_resolve"')
    out.append("\t\t\t\t\t\tonclick = \"[GetScriptedGui('pod_combat_auto_resolve').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append("\t\t\t\t\t\tenabled = \"[GetScriptedGui('pod_combat_auto_resolve').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append('\t\t\t\t\t\ttooltip = "pod_combat_auto_resolve_desc"')
    out.append("\t\t\t\t\t}")
    out.append("")
    # End Combat button — visible only when combat is over
    out.append("\t\t\t\t\tbutton_standard = {")
    out.append('\t\t\t\t\t\tvisible = "[GetPlayer.MakeScope.Var(\'pod_combat_is_over\').IsSet]"')
    out.append("\t\t\t\t\t\tsize = { 170 33 }")
    out.append('\t\t\t\t\t\ttext = "pod_combat_end_combat"')
    out.append("\t\t\t\t\t\tonclick = \"[GetScriptedGui('pod_combat_end_turn').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append("\t\t\t\t\t\tenabled = \"[GetScriptedGui('pod_combat_end_turn').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append("\t\t\t\t\t}")
    out.append("")
    # Help / Overview button — always visible during combat
    out.append("\t\t\t\t\tbutton_standard = {")
    out.append("\t\t\t\t\t\tsize = { 80 33 }")
    out.append('\t\t\t\t\t\ttext = "pod_combat_help_button"')
    out.append("\t\t\t\t\t\tonclick = \"[GetScriptedGui('pod_combat_help').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append("\t\t\t\t\t\tenabled = \"[GetScriptedGui('pod_combat_help').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append('\t\t\t\t\t\ttooltip = "pod_combat_help_tooltip"')
    out.append("\t\t\t\t\t}")
    out.append("\t\t\t\t}")

    # Combat log — scrollable, last 30 actions
    out.append("")
    out.append("\t\t\t\t##############################")
    out.append("\t\t\t\t###### COMBAT LOG")
    out.append("\t\t\t\t##############################")
    out.append("")
    out.append("\t\t\t\tvbox = {")
    out.append("\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append("\t\t\t\t\tmargin = { 10 5 }")
    out.append("")
    out.append("\t\t\t\t\tbackground = {")
    out.append("\t\t\t\t\t\tusing = Background_Area")
    out.append("\t\t\t\t\t}")
    out.append("")
    out.append("\t\t\t\t\t# Column headers")
    out.append("\t\t\t\t\thbox = {")
    out.append("\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\t\tmargin = { 5 2 }")
    out.append("\t\t\t\t\t\twidget = {")
    out.append("\t\t\t\t\t\t\tsize = { 180 20 }")
    out.append('\t\t\t\t\t\t\ttext_single = { raw_text = "#bold Attacker#!" align = center }')
    out.append("\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t\twidget = {")
    out.append("\t\t\t\t\t\t\tsize = { 200 20 }")
    out.append('\t\t\t\t\t\t\ttext_single = { raw_text = "#bold Action#!" }')
    out.append("\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t\twidget = {")
    out.append("\t\t\t\t\t\t\tsize = { 180 20 }")
    out.append('\t\t\t\t\t\t\ttext_single = { raw_text = "#bold Target#!" align = center }')
    out.append("\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t\twidget = {")
    out.append("\t\t\t\t\t\t\tsize = { 160 20 }")
    out.append('\t\t\t\t\t\t\ttext_single = { raw_text = "#bold Result#!" }')
    out.append("\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t\texpand = {}")
    out.append("\t\t\t\t\t}")
    out.append("")
    out.append("\t\t\t\t\tdivider_light = {")
    out.append("\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\t}")
    out.append("")
    # Scrollable log body — 30 entries in a vertical scrollbox
    out.append("\t\t\t\t\tscrollbox = {")
    out.append("\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append("")
    out.append('\t\t\t\t\t\tblockoverride "scrollbox_content"')
    out.append("\t\t\t\t\t\t{")
    out.append("\t\t\t\t\t\t\tvbox = {")
    out.append("\t\t\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\t\t\t\tmargin = { 0 2 }")

    # 30 log entries (nested one extra level inside scrollbox → need +1 tab on each line)
    def reindent(block: str, extra_tabs: int = 1) -> str:
        prefix = "\t" * extra_tabs
        return "\n".join((prefix + ln) if ln else ln for ln in block.split("\n"))

    for i in range(1, 31):
        out.append(reindent(log_entry(i), 1))

    out.append("")
    out.append("\t\t\t\t\t\t\t\t# Empty state")
    out.append("\t\t\t\t\t\t\t\ttext_single = {")
    out.append("\t\t\t\t\t\t\t\t\tvisible = \"[Not(GetPlayer.MakeScope.Var('pod_combat_log_1').IsSet)]\"")
    out.append('\t\t\t\t\t\t\t\t\traw_text = "#italic Awaiting your command.#!"')
    out.append("\t\t\t\t\t\t\t\t\tmargin = { 5 4 }")
    out.append("\t\t\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t}")
    out.append("\t\t\t\t}")
    out.append("\t\t\t}")  # close center panel vbox

    # ══════════════════════════════════════════════
    # RIGHT PANEL: Enemy team
    # ══════════════════════════════════════════════
    out.append("")
    out.append("\t\t\t##############################")
    out.append("\t\t\t###### RIGHT PANEL: ENEMIES")
    out.append("\t\t\t##############################")
    out.append("")
    out.append("\t\t\t\tvbox = {")
    out.append("\t\t\t\t\tminimumsize = { 280 -1 }")
    out.append("\t\t\t\t\tmaximumsize = { 280 -1 }")
    out.append("\t\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append("\t\t\t\t\tmargin = { 5 2 }")
    out.append("")
    out.append("\t\t\t\t\ttext_single = {")
    out.append('\t\t\t\t\t\traw_text = "#bold ENEMIES#!"')
    out.append('\t\t\t\t\t\tdefault_format = "#weak"')
    out.append("\t\t\t\t\t\talign = center")
    out.append("\t\t\t\t\t}")
    out.append("")

    # Enemy cards — same scrollbox pattern as the ally panel.
    out.append("\t\t\t\t\tscrollbox = {")
    out.append("\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append('\t\t\t\t\t\tblockoverride "scrollbox_content"')
    out.append("\t\t\t\t\t\t{")
    out.append("\t\t\t\t\t\t\tvbox = {")
    out.append("\t\t\t\t\t\t\t\tmargin = { 0 2 }")
    enemy_indent = "\t\t\t\t\t\t\t\t"
    for slot in range(5, 10):
        out.append("")
        out.append(enemy_card(slot, enemy_indent))
    out.append("")
    out.append(f"{enemy_indent}expand = {{}}")
    out.append("\t\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t}")
    out.append("\t\t\t\t}")  # close right panel vbox

    out.append("\t\t\t}")  # close three-panel hbox
    out.append("")
    out.append("\t\t\t\t# Bottom buffer row (20px empty space)")
    out.append("\t\t\t\twidget = {")
    out.append("\t\t\t\t\tminimumsize = { -1 20 }")
    out.append("\t\t\t\t\tmaximumsize = { -1 20 }")
    out.append("\t\t\t\t}")
    out.append("\t\t\t}")  # close content vbox

    # Right padding (empty)
    out.append("")
    out.append("\t\t\t# Right padding (empty)")
    out.append("\t\t\twidget = {")
    out.append("\t\t\t\tminimumsize = { 30 -1 }")
    out.append("\t\t\t\tmaximumsize = { 30 -1 }")
    out.append("\t\t\t}")

    out.append("\t\t}")  # close outer hbox
    out.append("\t}")  # close window
    out.append("}")  # close widget

    # No BOM for .gui files
    return "\n".join(out) + "\n"


# ──────────────────────────────────────────────────────────────────────
# FILE 7: SKILLS CONFIG WINDOW GUI
# ──────────────────────────────────────────────────────────────────────

def generate_skills_window_gui(active_skills, passive_skills, all_implemented):
    """Generate File 7: gui/POD_windows/pod_combat_skills_window.gui"""

    # Group all implemented skills by config_section (preserve order)
    sections = OrderedDict()
    for s in all_implemented:
        sec = s["config_section"]
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(s)

    # Build section visibility expression map.
    # Value is either:
    #   None                 — always visible (no gate)
    #   str (sv name)        — single-SV check, emitted as GreaterThan(..)
    #   list[str] (sv names) — multi-SV check, emitted as chained Or(GreaterThan(..), ..)
    section_sv = {}
    for sec, skills_in_sec in sections.items():
        # Fixed special cases that bypass the per-skill trait scan
        if sec in ("Base Physical", "Base Tactical"):
            section_sv[sec] = None
            continue
        if sec == "Innate Vampire":
            section_sv[sec] = "pod_combat_is_vampire_sv"
            continue
        if sec == "Innate Fera":
            section_sv[sec] = "pod_combat_is_fera_sv"
            continue
        if sec == "Perk Gifts":
            section_sv[sec] = "pod_combat_has_fera_perk_gifts_sv"
            continue

        # Collect unique SVs from every skill in this section.
        # If any skill is always-visible (no trait), the whole section is
        # always visible. Otherwise we OR all distinct trait SVs so the
        # section header shows whenever the player can use ANY skill in it.
        svs = []
        seen = set()
        has_none = False
        for s in skills_in_sec:
            sv = _skill_visibility_sv(s["required_trait"])
            if sv is None:
                has_none = True
                break
            if sv not in seen:
                svs.append(sv)
                seen.add(sv)

        if has_none or not svs:
            section_sv[sec] = None
        elif len(svs) == 1:
            section_sv[sec] = svs[0]
        else:
            section_sv[sec] = svs

    def skill_row(s, indent="\t\t\t\t\t\t\t\t"):
        """Generate one skill row in the config window.
        Each row self-hides when the player lacks the skill's required_trait,
        so the list only shows moves the player can actually equip."""
        key = s["skill_key"]
        is_pass = is_passive(s)
        lines = []
        lines.append(f"{indent}# {s['display_name']}")
        lines.append(f"{indent}hbox = {{")
        lines.append(f"{indent}\tlayoutpolicy_horizontal = expanding")
        lines.append(f"{indent}\tmargin = {{ 8 2 }}")

        # Per-skill visibility: hide rows the player cannot equip.
        # Innate Vampire and Perk Gifts rows use their own section-level gates
        # (they aren't in this row's hbox because they don't depend on a
        # discipline trait — just vampire-ness or a specific perk).
        sec_name = s.get("config_section", "")
        if sec_name not in ("Innate Vampire", "Perk Gifts"):
            skill_sv = _skill_visibility_sv(s["required_trait"])
            if skill_sv is not None:
                lines.append(f'{indent}\tvisible = "[{_sv_greater_than_zero(skill_sv)}]"')
        lines.append(f"")
        lines.append(f"{indent}\tbackground = {{")
        lines.append(f"{indent}\t\tusing = Background_Area")
        lines.append(f"{indent}\t}}")
        lines.append(f"")
        lines.append(f"{indent}\tvbox = {{")
        lines.append(f"{indent}\t\tlayoutpolicy_horizontal = expanding")
        lines.append(f"{indent}\t\tmargin = {{ 8 4 }}")
        lines.append(f"")
        lines.append(f'{indent}\t\ttext_single = {{')
        lines.append(f'{indent}\t\t\ttext = "pod_combat_move_{key}"')
        lines.append(f'{indent}\t\t\tdefault_format = "#bold"')
        lines.append(f'{indent}\t\t}}')
        lines.append(f'{indent}\t\ttext_multi = {{')
        lines.append(f'{indent}\t\t\ttext = "pod_combat_move_{key}_desc"')
        lines.append(f'{indent}\t\t\tdefault_format = "#weak"')
        lines.append(f'{indent}\t\t\tautoresize = yes')
        lines.append(f'{indent}\t\t\tmaximumsize = {{ 440 -1 }}')
        lines.append(f'{indent}\t\t\talign = center')
        lines.append(f'{indent}\t\t}}')
        lines.append(f"{indent}\t}}")

        if is_pass:
            # Passive: display-only label
            lines.append(f"")
            lines.append(f"{indent}\ttext_single = {{")
            lines.append(f'{indent}\t\traw_text = "#italic Passive#!"')
            lines.append(f'{indent}\t\tdefault_format = "#weak"')
            lines.append(f"{indent}\t\tmargin_right = 8")
            lines.append(f"{indent}\t}}")
        else:
            # Equip button
            lines.append(f"")
            lines.append(f"{indent}\tbutton_standard = {{")
            lines.append(f"{indent}\t\tsize = {{ 90 35 }}")
            lines.append(f'{indent}\t\tvisible = "[Not(GetPlayer.MakeScope.Var(\'pod_combat_equipped_{key}\').IsSet)]"')
            lines.append(f'{indent}\t\ttext = "pod_combat_equip_btn"')
            lines.append(f'{indent}\t\tonclick = "[GetScriptedGui(\'pod_combat_toggle_{key}\').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"')
            lines.append(f'{indent}\t\tenabled = "[GetScriptedGui(\'pod_combat_toggle_{key}\').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"')
            lines.append(f"{indent}\t\tmargin_right = 8")
            lines.append(f"{indent}\t}}")
            # Remove button
            lines.append(f"{indent}\tbutton_standard = {{")
            lines.append(f"{indent}\t\tsize = {{ 90 35 }}")
            lines.append(f'{indent}\t\tvisible = "[GetPlayer.MakeScope.Var(\'pod_combat_equipped_{key}\').IsSet]"')
            lines.append(f'{indent}\t\ttext = "pod_combat_remove_btn"')
            lines.append(f'{indent}\t\tonclick = "[GetScriptedGui(\'pod_combat_toggle_{key}\').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"')
            lines.append(f"{indent}\t\tmargin_right = 8")
            lines.append(f"{indent}\t}}")

        lines.append(f"{indent}}}")
        return "\n".join(lines)

    out = []
    out.append("############################################")
    out.append("######   POD COMBAT SKILLS WINDOW   ######")
    out.append("############################################")
    out.append("")
    out.append("# Skill configuration window \u2014 visible outside combat when opened via decision.")
    out.append("# Players equip/unequip combat moves here. Loadout persists between fights.")
    out.append("")
    out.append("widget = {")
    out.append('\tname = "pod_combat_skills_window"')
    out.append('\tvisible = "[And(And(Not(IsPauseMenuShown), IsDefaultGUIMode), And(GetPlayer.IsValid, And(GetPlayer.MakeScope.Var(\'pod_combat_config_open\').IsSet, Not(GetPlayer.MakeScope.Var(\'pod_combat_active\').IsSet))))]"')
    out.append("\tlayer = royal_court")
    out.append("\tsize = { 100% 100% }")
    out.append("")
    out.append("\twindow = {")
    out.append("\t\tparentanchor = center")
    out.append("\t\tsize = { 800 1050 }")
    out.append("\t\tusing = Window_Background")
    out.append("\t\tusing = Window_Decoration")
    out.append("\t\tallow_outside = yes")
    out.append("")
    out.append("\t\tvbox = {")
    out.append("\t\t\tlayoutpolicy_vertical = expanding")
    out.append("\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\tusing = Window_Margins")

    # Header
    out.append("")
    out.append("\t\t\t##############################")
    out.append("\t\t\t###### HEADER")
    out.append("\t\t\t##############################")
    out.append("")
    out.append("\t\t\theader_pattern = {")
    out.append("\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("")
    out.append('\t\t\t\tblockoverride "header_text" {')
    out.append('\t\t\t\t\ttext = "pod_combat_skills_title"')
    out.append("\t\t\t\t}")
    out.append("")
    out.append('\t\t\t\tblockoverride "button_close" {')
    out.append("\t\t\t\t\tonclick = \"[GetScriptedGui('pod_combat_close_skills').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"")
    out.append("\t\t\t\t}")
    out.append("\t\t\t}")
    out.append("")
    out.append("\t\t\t# Equipped count per category")
    out.append("\t\t\thbox = {")
    out.append("\t\t\t\tmargin = { 0 5 }")
    out.append("\t\t\t\tspacing = 20")
    out.append("\t\t\t\ttext_single = {")
    out.append("\t\t\t\t\traw_text = \"[Localize('pod_combat_equipped_label')]\"")
    out.append('\t\t\t\t\tdefault_format = "#bold"')
    out.append("\t\t\t\t}")
    out.append("\t\t\t\ttext_single = {")
    out.append("\t\t\t\t\traw_text = \"ATK: [GetPlayer.MakeScope.ScriptValue('pod_combat_atk_count')|0] / [GetPlayer.MakeScope.ScriptValue('pod_combat_max_per_category')|0]\"")
    out.append("\t\t\t\t}")
    out.append("\t\t\t\ttext_single = {")
    out.append("\t\t\t\t\traw_text = \"CTL: [GetPlayer.MakeScope.ScriptValue('pod_combat_ctl_count')|0] / [GetPlayer.MakeScope.ScriptValue('pod_combat_max_per_category')|0]\"")
    out.append("\t\t\t\t}")
    out.append("\t\t\t\ttext_single = {")
    out.append("\t\t\t\t\traw_text = \"DEF: [GetPlayer.MakeScope.ScriptValue('pod_combat_def_count')|0] / [GetPlayer.MakeScope.ScriptValue('pod_combat_max_per_category')|0]\"")
    out.append("\t\t\t\t}")
    out.append("\t\t\t\ttext_single = {")
    out.append("\t\t\t\t\traw_text = \"PWR: [GetPlayer.MakeScope.ScriptValue('pod_combat_pwr_count')|0] / [GetPlayer.MakeScope.ScriptValue('pod_combat_max_per_category')|0]\"")
    out.append("\t\t\t\t}")
    out.append("\t\t\t\ttext_single = {")
    out.append("\t\t\t\t\traw_text = \"Total: [GetPlayer.MakeScope.ScriptValue('pod_combat_equipped_count')|0] / [GetPlayer.MakeScope.ScriptValue('pod_combat_max_equipped')|0]\"")
    out.append('\t\t\t\t\tdefault_format = "#weak"')
    out.append("\t\t\t\t}")
    out.append("\t\t\t}")
    out.append("")
    out.append("\t\t\tdivider_light = {")
    out.append("\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t}")

    # Skill list
    out.append("")
    out.append("\t\t\t##############################")
    out.append("\t\t\t###### SKILL LIST")
    out.append("\t\t\t##############################")
    out.append("")
    out.append("\t\t\tscrollarea = {")
    out.append("\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\tlayoutpolicy_vertical = expanding")
    out.append("")
    out.append("\t\t\t\tscrollbarpolicy_horizontal = always_off")
    out.append("\t\t\t\tscrollbarpolicy_vertical = as_needed")
    out.append("")
    out.append("\t\t\t\tscrollbar_vertical = {")
    out.append("\t\t\t\t\tusing = Scrollbar_Vertical")
    out.append("\t\t\t\t}")
    out.append("")
    out.append("\t\t\t\tscrollwidget = {")
    out.append("")
    out.append("\t\t\t\t\tvbox = {")
    out.append("\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    out.append("\t\t\t\t\t\tignoreinvisible = yes")
    out.append("\t\t\t\t\t\tmargin = { 5 5 }")
    out.append("\t\t\t\t\t\tmargin_right = 22")

    for sec, skills_in_sec in sections.items():
        sv = section_sv.get(sec)
        sec_label = sec.upper()

        out.append("")
        out.append(f"\t\t\t\t\t\t##############################")
        out.append(f"\t\t\t\t\t\t###### {sec_label}")
        out.append(f"\t\t\t\t\t\t##############################")
        out.append("")
        out.append(f"\t\t\t\t\t\tvbox = {{")
        out.append(f"\t\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
        # ignoreinvisible collapses hidden child rows so the section doesn't
        # leave gaps when only some skills are available.
        out.append(f"\t\t\t\t\t\t\tignoreinvisible = yes")
        if sv is not None:
            if isinstance(sv, list):
                expr = _build_or_expr(sv)
            else:
                expr = _sv_greater_than_zero(sv)
            out.append(f"\t\t\t\t\t\t\tvisible = \"[{expr}]\"")
        out.append("")
        out.append(f"\t\t\t\t\t\t\thbox = {{")
        out.append(f"\t\t\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
        out.append(f"\t\t\t\t\t\t\t\tmargin = {{ 5 4 }}")
        out.append(f"\t\t\t\t\t\t\t\ttext_single = {{")
        out.append(f'\t\t\t\t\t\t\t\t\traw_text = "#bold {sec_label}#!"')
        out.append(f'\t\t\t\t\t\t\t\t\tdefault_format = "#weak"')
        out.append(f"\t\t\t\t\t\t\t\t}}")
        out.append(f"\t\t\t\t\t\t\t}}")

        for s in skills_in_sec:
            out.append("")
            out.append(skill_row(s))

        out.append(f"\t\t\t\t\t\t}}")

    out.append("\t\t\t\t\t}")
    out.append("\t\t\t\t}")
    out.append("\t\t\t}")
    out.append("\t\t}")
    out.append("\t}")
    out.append("}")

    # No BOM for .gui files
    return "\n".join(out) + "\n"


# ──────────────────────────────────────────────────────────────────────
# FILE 8: LOCALIZATION
# ──────────────────────────────────────────────────────────────────────

def _build_skill_description(skill):
    """Build an auto-generated tooltip description from CSV columns.

    Format:
      #bold ATK#! — single-enemy
      Physical / Aggravated
      3 HP damage | 2 Morale damage
      Costs: 2 AP, 1 Blood, 15 Gold
      Debuff: -10 Hit Chance
      Special: bypass_guard
      <notes from CSV if present>
    """
    parts = []
    cat = skill.get("combat_category", "")
    targeting = skill.get("targeting", "single-enemy")
    special = skill.get("special") or ""

    # Line 1: Category + targeting
    cat_label = {"ATK": "Attack", "DEF": "Defense", "CTL": "Control", "PWR": "Power"}.get(cat, cat)
    target_labels = {
        "single-enemy": "single enemy",
        "single-ally": "single ally",
        "self": "self",
        "team-enemy": "all enemies",
        "team-ally": "all allies",
        "single-pc": "player character",
    }
    target_label = target_labels.get(targeting, targeting)
    parts.append(f"#bold {cat_label}#! - {target_label}")

    # Line 2: Damage source / type
    ds = skill.get("damage_source") or ""
    dt = skill.get("damage_type") or ""
    if ds and ds != "None":
        type_str = f" / {dt}" if dt and dt != "None" and dt != "Superficial" else ""
        parts.append(f"{ds}{type_str}")

    # Line 3: Damage / healing numbers
    hp_dmg = skill["hp_damage"]
    mor_dmg = skill["morale_damage"]
    self_dmg = skill["self_damage"]
    hp_heal = skill["hp_heal"]
    mor_heal = skill["morale_heal"]
    dmg_bits = []

    if "retaliate_if_hit" in special:
        dmg_bits.append(f"{hp_dmg} HP retaliation if hit")
    elif "retaliate_if_missed" in special:
        dmg_bits.append(f"{hp_dmg} HP retaliation if missed")
    else:
        if hp_dmg > 0:
            dmg_bits.append(f"{hp_dmg} HP damage")
        if mor_dmg > 0:
            dmg_bits.append(f"{mor_dmg} Morale damage")
    if self_dmg > 0:
        dmg_bits.append(f"{self_dmg} self-damage")
    if hp_heal > 0:
        dmg_bits.append(f"+{hp_heal} HP heal")
    if mor_heal > 0:
        dmg_bits.append(f"+{mor_heal} Morale heal")
    if dmg_bits:
        parts.append(" | ".join(dmg_bits))

    # Line 4: Extra costs (AP is already shown in the button label)
    cost_bits = []
    ec = skill.get("energy_cost", 0)
    stress = skill.get("stress_cost", 0)
    gold = skill.get("gold_cost", 0)
    prestige = skill.get("prestige_cost", 0)
    piety = skill.get("piety_cost", 0)
    if ec > 0:
        resource = "Gnosis" if is_fera_skill(skill) else "Chi" if skill.get("required_trait") == "kueijin" else "Blood"
        cost_bits.append(f"{ec} {resource}")
    if stress > 0:
        cost_bits.append(f"{stress} Stress")
    if gold > 0:
        cost_bits.append(f"{gold} Gold")
    if prestige > 0:
        cost_bits.append(f"{prestige} Prestige")
    if piety > 0:
        cost_bits.append(f"{piety} Piety")
    if cost_bits:
        parts.append("Cost: " + ", ".join(cost_bits))

    # Line 5: Tiered buffs / debuffs (small/medium/large, round/combat)
    tier_flags_tip = parse_tier_flags(skill.get("special"))
    for stat, direction, size, duration in tier_flags_tip:
        mag = TIER_MAGNITUDE[size]
        stat_label = "Soak" if stat == "soak" else "Hit Chance"
        unit = "%" if stat == "soak" else ""
        sign = "+" if direction == "buff" else "-"
        kind = "Buff" if direction == "buff" else "Debuff"
        parts.append(f"{kind}: {sign}{mag}{unit} {stat_label} ({size}, {duration})")

    # Line 6: Non-tier special modifiers
    if special:
        for flag in [f.strip() for f in special.split(",")]:
            if flag.startswith("ap_gain_"):
                try:
                    n = int(flag.split("_", 2)[2])
                    parts.append(f"Buff: +{n} AP")
                except (IndexError, ValueError):
                    pass
            elif flag.startswith("ap_drain_"):
                try:
                    n = int(flag.split("_", 2)[2])
                    parts.append(f"Debuff: -{n} AP (next turn)")
                except (IndexError, ValueError):
                    pass
            elif flag.startswith("initiative_debuff_"):
                try:
                    n = int(flag.rsplit("_", 1)[1])
                    parts.append(f"Debuff: -{n} Initiative (next round)")
                except (IndexError, ValueError):
                    pass

    # Line 7: Special flags (human-readable)
    # Split special flags for exact matching (avoid "dodge" matching "bypass_dodge")
    special_flags = {f.strip() for f in special.split(",") if f.strip() and f.strip() != "None"}
    special_labels = []
    if "bypass_guard" in special_flags:
        special_labels.append("Bypasses Guard")
    if "set_guard" in special_flags:
        special_labels.append("Sets Guard")
    if "dodge" in special_flags:
        special_labels.append("Dodge (negates next attack)")
    if "stealth" in special_flags:
        special_labels.append("Stealth (negates next attack, +30 Hit Chance)")
    if "bypass_dodge" in special_flags:
        special_labels.append("Undodgeable")
    if "bypass_stealth" in special_flags:
        special_labels.append("Breaks Stealth")
    if "retaliate_if_hit" in special_flags:
        agg = "Aggravated" if (dt or "").lower() == "aggravated" else "Soakable"
        special_labels.append(f"Counter-stance ({agg})")
    if "retaliate_if_missed" in special_flags:
        agg = "Aggravated" if (dt or "").lower() == "aggravated" else "Soakable"
        special_labels.append(f"Miss-counter ({agg})")
    if special_labels:
        parts.append(" | ".join(special_labels))

    # Line 8: Notes from CSV (flavor text)
    notes = (skill.get("notes") or "").strip()
    if notes:
        parts.append(f"#italic {notes}#!")

    # Join with literal \n for CK3 localization newlines
    result = "\\n".join(parts)
    # Escape quotes for YML
    result = result.replace('"', '\\"')
    return result


def generate_localization_file(all_implemented):
    """Generate File 8: localization/english/pod_combat_l_english.yml"""
    out = []
    out.append("l_english:")

    # Static content (labels, help event, debug interaction text, toasts,
    # game rule, group combat labels) now lives in
    # localization/english/pod_combat_static_l_english.yml and is NOT
    # regenerated here. See that file for edits to those strings.

        # Skills by section. The button label gets an " (N AP)" suffix.
    # The _desc key gets an auto-generated stat block built from the CSV
    # columns, providing a consistent tooltip across all skills.
    current_section = None
    for s in all_implemented:
        sec = s["config_section"]
        if sec != current_section:
            current_section = sec
            out.append("")
            out.append(f" ##############################")
            out.append(f" ###### {sec.upper()}")
            out.append(f" ##############################")
            out.append("")

        key = s["skill_key"]
        ap = s["ap_cost"]
        loc_name_base = s["loc_name"].replace('"', '\\"')
        if is_passive(s):
            out.append(f' pod_combat_move_{key}:0 "{loc_name_base}"')
        else:
            out.append(f' pod_combat_move_{key}:0 "{loc_name_base} ({ap} AP)"')

        # Auto-generated description from CSV stats
        desc = _build_skill_description(s)
        out.append(f' pod_combat_move_{key}_desc:0 "{desc}"')

    return BOM + "\n".join(out) + "\n"


# ──────────────────────────────────────────────────────────────────────
# FILE 9: AI SELECTION EFFECT (GROUP MODE)
# ──────────────────────────────────────────────────────────────────────
#
# Produces pod_combat_ai_csv_select_effect, the random_list body that the
# AI uses to pick a move each action in group mode. Every active skill gets
# a random_list entry, gated on:
#
#   pod_combat_can_use_{key}_trigger = yes   — AP / state affordability
#   (trait check if required_trait is set)   — actor must qualify
#
# The body of each entry calls pod_combat_use_{key}_effect = yes, which is
# the same move effect the player uses. This works because the group-mode
# workspace bridge loads the current actor into the pod_combat_player_*
# workspace and their chosen target into pod_combat_opponent_*, so the
# hard-coded TARGET_SIDE = opponent / SIDE = player in the generated move
# effect always resolves to "do this to my target / myself" regardless of
# which slot is acting.
#
# Base weight is derived from the combat_category column:
#   ATK=15  CTL=10  DEF=8  PWR=12  (no category fallback = 5)
#
# Anti-repetition: each entry halves its weight if the AI's last move on
# the same side was this skill (matches the legacy AI behavior).
#
# Situational modifiers:
#   - Heal/rally-style skills boost at low HP / low morale
#   - Feint boosts against a guarding target
#   - Guard boosts when HP is hurt
#
# Targeting filter: modes the AI can safely pick.
#   single-enemy — works directly (the workspace bridge loaded the target).
#   self         — works directly (body acts on the actor workspace).
#   single-ally  — works via a swap/restore dance. Before the move fires,
#                  pod_combat_ai_swap_to_ally_target_effect saves the AI's
#                  enemy target, picks the first alive non-self same-team
#                  ally, and loads them into the opponent workspace. After
#                  the move fires, pod_combat_ai_restore_enemy_target_effect
#                  puts the enemy target back. Each single-ally entry is
#                  gated on pod_combat_ai_has_available_ally_trigger so
#                  the random_list only proposes it when a valid ally exists.
#   single-pc    — like single-ally but the swap always targets slot 0 (the
#                  PC). Enemy AIs use this for "focus the Prince" skills
#                  like debuffs / domination attempts specifically targeted
#                  at the main character. The same restore_enemy_target
#                  effect puts the AI's original target back afterwards.
#                  Slot 0 is always populated during combat so no
#                  availability trigger is needed.
#   team-enemy   — works via the actor-aware AoE wrap. Enemy AIs iterate
#                  slots 0-4 (PC team); PC-team AIs iterate 5-9.
#   team-ally    — works via the actor-aware AoE wrap. Enemy AIs iterate
#                  slots 5-9 (enemy team); PC-team AIs iterate 0-4. Each
#                  iteration includes the caster, matching standard AoE
#                  buff semantics.
#
# Every targeting mode is now AI-usable. Only "self" is universally valid;
# the others have their own presence/liveness gates.
_AI_ALLOWED_TARGETING = {
    "single-enemy", "single-ally", "single-pc",
    "self", "team-enemy", "team-ally",
}

# Base weights by combat category — ATK is most common, PWR is specialized.
AI_BASE_WEIGHTS = {
    "ATK": 15,
    "CTL": 10,
    "DEF": 8,
    "PWR": 12,
}
AI_FALLBACK_WEIGHT = 5

def _ai_trait_gate_lines(required_trait):
    """Return trigger lines that gate the actor on a required_trait value.

    required_trait may be pipe-separated ("celerityadvanced|auspexdiscipline")
    meaning ALL traits are required. Emits one line per trait, wrapped in
    a scope into var:pod_combat_actor_char so the check runs against the
    acting character rather than the root (PC).

    Uses _trait_check_line() for all trait lookups, which handles PoD-specific
    overrides (tribes as faiths, fera as werewolf/bastet/mokole OR, hunter
    as supehunter, etc.) via TRAIT_CHECK_OVERRIDES.

    Lines are indented at 4 tabs (inside the trigger block which is 3 tabs
    deep within the random_list entry). Returns an empty list if
    required_trait is None.
    """
    if not required_trait:
        return []
    traits = [t.strip() for t in required_trait.split("|") if t.strip()]
    if not traits:
        return []
    lines = []
    lines.append("\t\t\t\texists = var:pod_combat_actor_char")
    lines.append("\t\t\t\tvar:pod_combat_actor_char = {")
    for t in traits:
        lines.append(f"\t\t\t\t\t{_trait_check_line(t)}")
    lines.append("\t\t\t\t}")
    return lines


def _ai_base_weight(skill):
    """Return the base weight for this skill's AI random_list entry.

    Priority order:
      1. Per-skill override: skill["ai_weight"] if > 0 (blank cells and
         explicit 0 both fall through to category)
      2. combat_category default: ATK=15, PWR=12, CTL=10, DEF=8
      3. Fallback: AI_FALLBACK_WEIGHT (5) for skills with no category

    Designers populate the ai_weight CSV column to tune individual skills
    without touching Python. Leave the cell blank to accept the category
    default.
    """
    override = skill.get("ai_weight") or 0
    if isinstance(override, int) and override > 0:
        return override
    cat = (skill.get("combat_category") or "").strip().upper()
    return AI_BASE_WEIGHTS.get(cat, AI_FALLBACK_WEIGHT)


# Map a target_priority value to the matching swap-effect name. Two helper
# functions, one per target side. Default falls back to the legacy
# first-match swap (ally) or no-swap (enemy — handled by single_enemy_with_priority).
_ALLY_SWAP_BY_PRIORITY = {
    "default":     "pod_combat_ai_swap_to_ally_target_effect",
    "wounded":     "pod_combat_ai_swap_to_wounded_ally_target_effect",
    "healthy":     "pod_combat_ai_swap_to_healthy_ally_target_effect",
    "round_robin": "pod_combat_ai_swap_to_round_robin_ally_target_effect",
    "threat":      "pod_combat_ai_swap_to_threat_ally_target_effect",
}
_ENEMY_SWAP_BY_PRIORITY = {
    "wounded":     "pod_combat_ai_swap_to_wounded_enemy_target_effect",
    "healthy":     "pod_combat_ai_swap_to_healthy_enemy_target_effect",
    "round_robin": "pod_combat_ai_swap_to_round_robin_enemy_target_effect",
    "threat":      "pod_combat_ai_swap_to_threat_enemy_target_effect",
}


def _ally_swap_for_priority(priority):
    return _ALLY_SWAP_BY_PRIORITY.get(priority, _ALLY_SWAP_BY_PRIORITY["default"])


def _enemy_swap_for_priority(priority):
    return _ENEMY_SWAP_BY_PRIORITY.get(priority, _ENEMY_SWAP_BY_PRIORITY["wounded"])


def _priority_comment(priority):
    """Return a short bracketed comment string for a target_priority value."""
    if priority and priority != "default":
        return f"(target priority: {priority})"
    return ""


def _ai_situational_modifiers(skill):
    """Return a list of modifier blocks (as line lists) for situational
    weight adjustments based on the skill's role.

    These fire in addition to the anti-repetition modifier. Each block
    should be a list of lines already tab-indented for the random_list
    entry body (starting with "\t\t").
    """
    mods = []
    key = skill["skill_key"]
    hp_heal = skill["hp_heal"] or 0
    morale_heal = skill["morale_heal"] or 0
    special = skill["special"] or ""

    # Pure heal → boost when actor is wounded
    if hp_heal > 0 and "drain" not in special:
        mods.append([
            "\t\tmodifier = {",
            "\t\t\tfactor = 3",
            "\t\t\tpod_combat_player_hp_value < pod_combat_player_max_hp_value",
            "\t\t}",
        ])

    # Morale heal (rally) → boost when morale is low
    if morale_heal > 0:
        mods.append([
            "\t\tmodifier = {",
            "\t\t\tfactor = 3",
            "\t\t\tpod_combat_player_morale_value < 10",
            "\t\t}",
        ])

    # Guard → boost when hurt so the AI plays defensively as HP drops
    if key == "guard":
        mods.append([
            "\t\tmodifier = {",
            "\t\t\tfactor = 2",
            "\t\t\tpod_combat_player_hp_value < pod_combat_player_max_hp_value",
            "\t\t}",
        ])

    # Feint / remove_guard → much more useful when target is guarding
    if "remove_guard" in special:
        mods.append([
            "\t\tmodifier = {",
            "\t\t\tfactor = 3",
            "\t\t\thas_variable = pod_combat_opponent_is_guarding",
            "\t\t}",
        ])

    return mods


def generate_ai_select_effect(active_skills):
    """Generate the CSV-driven AI select effect.

    Emits pod_combat_ai_csv_select_effect containing one random_list entry
    per active skill. The hand-maintained pod_combat_ai_effects.txt wires
    this up as the sole AI move picker for every combat (1v1 and NvN share
    the same workspace-bridge code path).
    """
    out = []
    out.append("##########################################")
    out.append("######   POD COMBAT AI SELECT (CSV)   ######")
    out.append("##########################################")
    out.append("")
    out.append("# GENERATED BY generate_combat_files.py — DO NOT EDIT BY HAND")
    out.append("#")
    out.append("# pod_combat_ai_csv_select_effect is the sole AI move picker for all")
    out.append("# combats (1v1 and NvN alike). It reuses the standard player move")
    out.append("# effects (pod_combat_use_{key}_effect), which work for any actor")
    out.append("# because the workspace bridge loads the current actor into")
    out.append("# pod_combat_player_* and their target into pod_combat_opponent_*.")
    out.append("#")
    out.append("# Trait gates check var:pod_combat_actor_char, which is set in")
    out.append("# pod_combat_load_actor_from_slot_effect.")
    out.append("")
    out.append("pod_combat_ai_csv_select_effect = {")
    out.append("\trandom_list = {")
    out.append("")

    # Separate fera section for readability
    fera_started = False
    for s in active_skills:
        # Skip targeting modes the AI can't safely emit. With the unified
        # target system and the single-ally swap/restore dance, every mode
        # is supported — this filter is kept as a defensive guard in case
        # a future targeting value is added to the CSV before the generator
        # and runtime support land.
        if s.get("targeting", "single-enemy") not in _AI_ALLOWED_TARGETING:
            continue

        key = s["skill_key"]
        display = s["display_name"]
        weight = _ai_base_weight(s)
        rt = s["required_trait"]
        targeting = s.get("targeting", "single-enemy")
        is_single_ally = (targeting == "single-ally")
        is_single_pc = (targeting == "single-pc")
        is_single_enemy = (targeting == "single-enemy")
        # Per-skill enemy preference is only meaningful for single-enemy skills
        # with a non-default target_priority. When set, the generator emits a
        # mid-move swap to a priority-matched opposing-team slot, fires the
        # move, and restores the AI's turn-start enemy target.
        target_priority = s.get("target_priority", "default")
        single_enemy_with_priority = (
            is_single_enemy and target_priority in ("wounded", "healthy", "round_robin", "threat")
        )
        is_fera_s = is_fera_skill(s)

        if is_fera_s and not fera_started:
            out.append("\t\t###### FERA MOVES ######")
            out.append("")
            fera_started = True

        out.append(f"\t\t###### {display.upper()} \u2014 weight {weight} ######")
        out.append(f"\t\t{weight} = {{")
        out.append("\t\t\ttrigger = {")
        out.append(f"\t\t\t\tpod_combat_can_use_{key}_trigger = yes")
        # Trait gate
        trait_lines = _ai_trait_gate_lines(rt)
        for tl in trait_lines:
            out.append(tl)
        # single-ally: gate on having at least one alive non-self ally
        # so the random_list only proposes this entry when the swap
        # effect has a valid slot to pick.
        if is_single_ally:
            out.append("\t\t\t\tpod_combat_ai_has_available_ally_trigger = yes")
        # single-enemy with target_priority: defensive gate so the swap
        # variant has at least one valid opposing-team slot to pick from.
        # Default single-enemy skills don't need this — the AI's turn-start
        # target picker already guarantees an enemy was selected.
        if single_enemy_with_priority:
            out.append("\t\t\t\tpod_combat_ai_has_available_enemy_trigger = yes")
        # single-pc: gate on slot 0 being alive. Usually always true during
        # combat (PC death ends combat), but this is a defensive guard
        # against edge cases where check_group_victory hasn't fired yet.
        if is_single_pc:
            out.append("\t\t\t\thas_variable = pod_combat_c0_char")
            out.append("\t\t\t\tvar:pod_combat_c0_alive = 1")
        out.append("\t\t\t}")

        # Anti-repetition modifier
        out.append("\t\t\tmodifier = {")
        out.append("\t\t\t\tfactor = 0.5")
        out.append("\t\t\t\thas_variable = pod_combat_ai_last_move")
        out.append(f"\t\t\t\tvar:pod_combat_ai_last_move = flag:{key}")
        out.append("\t\t\t}")

        # Energy-attrition penalty for AI combatants. AI doesn't actually
        # spend Blood / Gnosis / Willpower, so without this penalty a fera
        # NPC could spam 3-Gnosis moves all combat without cost. Each
        # energy-cost skill the actor has already fired this combat
        # stacks another 0.75 multiplier on THIS selection weight, up to
        # 4 stacks (0.75^4 ≈ 0.316 at 4+ uses). Each modifier is
        # independent and CK3 multiplies them together when all apply.
        if s["energy_cost"] > 0:
            for threshold in (1, 2, 3, 4):
                out.append("\t\t\tmodifier = {")
                out.append("\t\t\t\tfactor = 0.75")
                out.append("\t\t\t\thas_variable = pod_combat_player_energy_used")
                out.append(f"\t\t\t\tvar:pod_combat_player_energy_used >= {threshold}")
                out.append("\t\t\t}")

        # Situational modifiers
        for mod_block in _ai_situational_modifiers(s):
            for ml in mod_block:
                out.append("\t" + ml)

        # Body: call the player move effect directly. For single-ally,
        # single-pc, and priority-tagged single-enemy skills, bracket the
        # call with a swap/restore dance so the opponent workspace holds
        # the correct target for the duration of the move body.
        if is_single_ally:
            # Pick the swap variant based on the CSV target_priority hint:
            #   wounded     → prefer lowest-HP same-team ally
            #   healthy     → prefer full-HP same-team ally
            #   round_robin → distribute picks across alive candidates
            #   threat      → prefer high-prowess same-team ally
            #   default     → first alive non-self same-team ally (legacy)
            swap_effect = _ally_swap_for_priority(target_priority)
            priority_comment = _priority_comment(target_priority)
            comment = "\t\t\t# Swap the AI's enemy target out for a same-team ally"
            if priority_comment:
                comment += " " + priority_comment + ","
            else:
                comment += ","
            out.append(comment)
            out.append("\t\t\t# fire the move, then put the enemy target back.")
            out.append(f"\t\t\t{swap_effect} = yes")
            out.append(f"\t\t\tpod_combat_use_{key}_effect = yes")
            out.append("\t\t\tpod_combat_ai_restore_enemy_target_effect = yes")
        elif is_single_pc:
            out.append("\t\t\t# Swap the AI's enemy target out for slot 0 (the PC),")
            out.append("\t\t\t# fire the move, then put the enemy target back.")
            out.append("\t\t\tpod_combat_ai_swap_to_pc_target_effect = yes")
            out.append(f"\t\t\tpod_combat_use_{key}_effect = yes")
            out.append("\t\t\tpod_combat_ai_restore_enemy_target_effect = yes")
        elif single_enemy_with_priority:
            # Per-skill enemy preference: temporarily override the AI's
            # turn-start enemy target with a priority-matched opposing-team
            # slot for THIS move only, then restore the original target so
            # subsequent attacks in the same turn keep using it.
            swap_effect = _enemy_swap_for_priority(target_priority)
            priority_comment = _priority_comment(target_priority)
            out.append(f"\t\t\t# Override the AI's turn-start enemy target {priority_comment},")
            out.append("\t\t\t# fire the move, then put the original target back.")
            out.append(f"\t\t\t{swap_effect} = yes")
            out.append(f"\t\t\tpod_combat_use_{key}_effect = yes")
            out.append("\t\t\tpod_combat_ai_restore_enemy_target_effect = yes")
        else:
            out.append(f"\t\t\tpod_combat_use_{key}_effect = yes")
        out.append(f"\t\t\tset_variable = {{ name = pod_combat_ai_last_move value = flag:{key} }}")
        out.append("\t\t}")
        out.append("")

    out.append("\t}")
    out.append("}")

    return BOM + "\n".join(out) + "\n"


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────

def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def write_file(path, content):
    """Write content to file with UTF-8 encoding."""
    ensure_dir(path)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  Written: {path}")


def main():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found.")
        print("The CSV is expected to sit next to this script. If you moved it,")
        print("update CSV_PATH at the top of generate_combat_files.py.")
        return
    if not os.path.isdir(DEVPOD_DIR):
        print(f"ERROR: devpod directory not found at {DEVPOD_DIR}")
        print("Expected repository layout is POD-Integration/{scripts,devpod}/.")
        print("If your devpod lives elsewhere, update DEVPOD_DIR at the top of")
        print("generate_combat_files.py.")
        return

    print(f"Script dir:   {SCRIPT_DIR}")
    print(f"Devpod dir:   {DEVPOD_DIR}")
    print()
    print("Reading CSV...")
    skills = parse_csv(CSV_PATH)
    all_implemented = [s for s in skills if is_implemented(s)]
    active_skills = [s for s in skills if is_active(s)]
    passive_skills = [s for s in all_implemented if is_passive(s)]

    print(f"  Total skills: {len(skills)}")
    print(f"  Implemented: {len(all_implemented)}")
    print(f"  Active (non-passive): {len(active_skills)}")
    print(f"  Passive: {len(passive_skills)}")
    print(f"  Future/planned (skipped): {len(skills) - len(all_implemented)}")

    print()
    print("Generating files...")

    # File 1: Effects
    content = generate_effects_file(active_skills)
    write_file(devpod_path("common/scripted_effects/POD_combat/pod_combat_move_effects.txt"), content)

    # File 2: Triggers
    content = generate_triggers_file(active_skills, all_implemented)
    write_file(devpod_path("common/scripted_triggers/pod_combat_triggers.txt"), content)

    # File 3: Combat GUIs
    content = generate_combat_guis_file(active_skills)
    write_file(devpod_path("common/scripted_guis/pod_combat_guis.txt"), content)

    # File 4: Skill GUIs
    content = generate_skill_guis_file(active_skills, all_implemented)
    write_file(devpod_path("common/scripted_guis/pod_combat_skill_guis.txt"), content)

    # File 5: Script Values
    content = generate_values_file(active_skills, all_implemented)
    write_file(devpod_path("common/script_values/pod_combat_values.txt"), content)

    # File 6: Combat Window GUI
    content = generate_combat_window_gui(active_skills)
    write_file(devpod_path("gui/POD_windows/pod_combat_window.gui"), content)

    # File 7: Skills Window GUI
    content = generate_skills_window_gui(active_skills, passive_skills, all_implemented)
    write_file(devpod_path("gui/POD_windows/pod_combat_skills_window.gui"), content)

    # File 8: Localization
    content = generate_localization_file(all_implemented)
    write_file(devpod_path("localization/english/pod_combat_l_english.yml"), content)

    # File 9: AI Select Effect (group mode, CSV-driven)
    content = generate_ai_select_effect(active_skills)
    write_file(devpod_path("common/scripted_effects/POD_combat/pod_combat_ai_generated_effects.txt"), content)

    print()
    print("Done! 9 files generated.")
    print(f"  {len(active_skills)} active skills processed")
    print(f"  {len(passive_skills)} passive skills processed")
    print(f"  {len(skills) - len(all_implemented)} future/planned skills skipped")

    # Report any invalid perk references that were dropped during generation.
    # These pod_perk_key values don't exist in PoD and were emitted as None
    # so the skills still work (trait gate alone), but the CSV should be
    # fixed up to use real perk keys.
    if _INVALID_PERKS_SEEN:
        print()
        print(f"WARNING: {len(_INVALID_PERKS_SEEN)} pod_perk_key value(s) "
              f"do not exist in PoD Reference and were dropped:")
        for perk, skills_affected in sorted(_INVALID_PERKS_SEEN.items()):
            unique_skills = sorted(set(s for s in skills_affected if s))
            affected_str = ", ".join(unique_skills) if unique_skills else "(unknown)"
            print(f"  {perk}  used by: {affected_str}")


if __name__ == "__main__":
    main()
