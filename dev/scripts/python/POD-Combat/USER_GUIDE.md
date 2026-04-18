# Combat-PoD User Guide

A tactical combat minigame for Princes of Darkness. When your character is challenged to a duel or initiates one, this mod replaces the vanilla dice-roll system with a turn-based combat encounter where you choose your moves.

---

## Getting Started

### Equipping Skills

Before your first fight, open the skill configuration screen:

1. Go to your **Decisions** panel
2. Select **Configure Combat Skills**
3. The skill list appears, grouped by section (Base Physical, Vampire Disciplines, Fera Gifts, etc.)
4. Click **Equip** on moves you want to bring into combat
5. Click **Remove** to unequip a move
6. Close the window when done

You can equip up to **16 moves total**: 4 per category (ATK, DEF, CTL, PWR). The equipped count is shown at the top of the screen.

Only moves you qualify for are visible. A vampire sees Discipline moves; a werewolf sees Gifts; a mortal sees only the base physical and tactical set. If you unlock new traits (e.g., learn a new Discipline), new sections appear automatically.

If you enter combat with nothing equipped, a default loadout is applied: Strike, Heavy Blow, Quick Jab, Reckless Charge, Guard, Feint, Intimidate, and Rally.

Your loadout persists between fights.

---

## The Combat Screen

When combat begins, a three-panel window appears:

```
┌──────────┬──────────────────────────────────────┬──────────┐
│  ALLIES  │            COMBAT AREA               │ ENEMIES  │
│          │                                      │          │
│ [You]    │  Round 1    Action Points: 4 / 6     │ [Enemy]  │
│ HP ████  │                                      │ HP ████  │
│ Morale █ │  ── ATK ───────────────────────      │ Morale █ │
│ +20 Soak │  [Strike 2] [Heavy Blow 4]           │ -20 Hit  │
│  (C)     │  [Quick Jab 1]                       │   (R)    │
│          │                                      │          │
│ [Ally 1] │  ── DEF ───────────────────────      │ [Foe 2]  │
│ HP ████  │  [Guard 2] [Blood Heal 2]            │ HP ████  │
│          │                                      │          │
│          │  [End Turn] [Auto-Resolve] [Help]    │          │
│          │                                      │          │
│          │  ── Combat Log ────────────────      │          │
│          │  You hit Enemy for 3 damage          │          │
│          │  Enemy's Guard blocked!              │          │
└──────────┴──────────────────────────────────────┴──────────┘
```

### Left Panel — Your Team

Shows your character (slot 0) and any allies (slots 1-4) in group combat. Each card displays:

- **Name**
- **HP track** (health boxes, color-coded: empty = healthy, red = superficial damage, dark red = aggravated)
- **Morale bar**
- **Prowess, Hit Chance, Soak** stats
- **Active tiered buffs and debuffs** — a compact line showing things like `+20 Soak (C)` (green, combat-duration) or `-20 Hit (R)` (red, round-duration). Only appears when a tier is active on that combatant.
- **Status icons** (top-right corner): Guard shield, Dodge arrow, or Stealth silhouette when those stances are active
- **KNOCKED OUT** label when HP or morale reaches 0

In group combat, click an ally card to target them with support skills.

### Right Panel — Enemy Team

Shows the primary opponent (slot 5) and any reinforcements (slots 6-9). Same card layout as allies.

**Click an enemy card to select them as your target.** The selected enemy shows a **TARGETED** badge. All your offensive moves fire at the targeted enemy.

### Center Panel — Your Actions

- **Round counter** and **AP remaining** at the top (shown as `4 / 6`, the current AP over the per-round base)
- **Skill buttons** organized by category (ATK, CTL, DEF, PWR)
- **Action buttons** at the bottom: End Turn, Auto-Resolve, Help
- **Help button** opens the Combat System Overview — a quick rules reference you can read mid-fight
- **Forfeit** is the X (close) button in the top-right of the window
- **Combat log** showing the last 30 actions with damage numbers and status effects

---

## How a Turn Works

### Initiative

At the start of each round, every combatant rolls initiative:

```
Initiative = Prowess + random(1-30)
```

Combatants act in descending initiative order. Higher prowess characters tend to go first, but the random factor keeps it unpredictable. You are **not** guaranteed to act first — if an enemy rolls higher, they attack before you see the UI.

### Your Turn

You start with **6 Action Points (AP)** each turn. Spend them on moves:

| AP Cost | Typical Moves |
|---------|---------------|
| 1 AP | Quick Jab (fast, light damage) |
| 2 AP | Strike, Guard, most buffs and debuffs |
| 3 AP | Heavy attacks, powerful supernatural moves |
| 4+ AP | Devastating finishers |

You can use multiple moves per turn as long as you have AP. A turn with 6 AP might look like:
- Quick Jab (1 AP) → Strike (2 AP) → Strike (2 AP) → end with 1 AP left
- Guard (2 AP) → Blood Heal (2 AP) → end with 2 AP left

Buttons grey out when you lack the AP to use them.

When you're done (or out of AP), click **End Turn**. The remaining combatants act in initiative order, then a new round begins.

### AI Turns

AI combatants use the same move pool you do (filtered by their traits). They:
- Favor attacks (ATK moves weighted highest)
- Guard more when wounded
- Heal when hurt (if they have healing moves)
- Try to break your Guard with Feint-type moves
- Avoid repeating the same move twice in a row
- Target low-HP enemies when possible

---

## Combat Mechanics

### Hit Chance

Physical attacks roll to hit:

```
Hit Chance = 60 + (Your Prowess - Enemy Prowess) / 2
Clamped between 20% and 95%
```

A character with 15 prowess attacking one with 10 prowess has a 62.5% hit chance. Missing is shown as **Missed!** in the combat log.

Supernatural and Mental attacks **auto-hit** (no miss chance). Switching targets mid-combat recomputes your hit chance against the new enemy's prowess.

### Status Stances (Guard / Dodge / Stealth)

All three stances **persist until triggered by an attack or combat ends.** They do not clear at round end — you can queue up defenses in advance and they stay until something tests them.

**Guard** — Blocks the next physical attack entirely (0 damage). Consumed when it blocks. Doesn't stop supernatural or mental attacks. Feint can break the enemy's guard without dealing damage.

**Dodge** — Negates the next incoming attack, regardless of source. Consumed when triggered. Shows as **Dodged!** in the log.

**Stealth** — Negates the next incoming attack AND grants **+30 Hit Chance** on your next strike. Consumed whichever happens first — you attack, or you get hit. Stealth is checked **before** Dodge in the damage pipeline, so a stealthed-and-dodging character keeps their dodge after the first attack (stealth is the more fragile layer).

Some attacks carry `Bypass Guard`, `Undodgeable`, or `Breaks Stealth` flags that skip or strip the relevant stance.

### Soak

Each character has a soak percentage (based on their PoD stats). When an attack connects (not dodged, not guarded), the target rolls against soak — a successful roll absorbs the damage entirely. Soaked attacks show as **Soaked!** in the log.

**Aggravated damage soaks at half effectiveness (−50% soak chance).** It doesn't bypass soak entirely — you still get your soak check, it just succeeds less often. Fire against vampires, silver against werewolves, and moves marked as Aggravated all hit harder but aren't unstoppable.

### Morale

Every combatant has a morale bar. Morale drops from:
- Direct morale damage (Mental attacks, Intimidate)
- Spillover from HP damage (taking HP damage also drains morale proportionally)

When morale hits 0, the character is defeated. This is an alternative win condition to reducing HP to 0.

### Damage Types

| Source | Hits? | Blocked by Guard? | Affected by Soak? |
|--------|-------|-------------------|-------------------|
| Physical | Roll vs hit chance | Yes | Yes (half soak when Aggravated) |
| Supernatural | Auto-hit | No | Yes (half soak when Aggravated) |
| Mental | Auto-hit | No | No |
| Fire | Roll vs hit chance | Yes | Yes; promoted to Aggravated (half soak) vs vampires |
| Silver | Roll vs hit chance | Yes | Yes; promoted to Aggravated (half soak) vs werewolves/Bastet |
| Gold | Roll vs hit chance | Yes | Yes; promoted to Aggravated (half soak) vs Mokole |
| Holy | Roll vs hit chance | Yes | Yes; promoted to Aggravated (half soak) vs vampires/demons/kuei-jin/wraiths |

**Aggravated** damage is soaked at half effectiveness (−50% soak chance) and is tracked separately on the PoD health track. When written back after combat, aggravated damage is harder to heal than superficial damage.

### Buffs and Debuffs

Stat buffs and debuffs (soak and hit chance) come in three **tiers** and two **durations**:

- **Size**: small (±10), medium (±20), large (±30)
- **Duration**: round (expires at end of the round) or combat (lasts the whole fight)

A character holds at most **one buff AND one debuff per stat + duration pair.** Applying a higher tier overwrites a lower one — small → medium → large is a clean upgrade. Applying the **same tier or lower** while a higher one is already active is blocked (the skill button greys out).

Example: you've got a `medium` combat soak buff (+20). You use a skill with a `large` combat soak buff — it overwrites, and you're now at +30. You try to use a `small` soak buff later — the button is unavailable because you already have a higher tier.

A compact summary row on each combatant's card shows which tiers are currently active:

```
+20 Soak (C)   +10 Hit (R)     (green)
-20 Hit (R)                    (red)
```

A few non-tier flags work differently and **stack** on each use:

- **AP gain** — instant AP refund this turn
- **AP drain** — subtracts AP from the target's next turn
- **Initiative debuff** — subtracts from the target's next-round initiative roll

### Retaliation Stances (Counter-Stance / Miss-Counter)

**Counter-stance** — "If an enemy hits me before my next turn, I deal X damage back." Set and forget.
**Miss-counter** — Same but triggers on a missed attack ("I punish the whiffed swing").

Both persist until consumed (by a triggering incoming attack) or combat ends.

---

## Energy Costs

Supernatural moves cost energy from your character's resource pool:

| Splat | Resource | Shown As |
|-------|----------|----------|
| Vampire | Blood | Hunger increases |
| Werewolf / Bastet / Mokole | Gnosis | Gnosis spent |
| Kuei-jin | Chi | Chi spent |
| Sorcerer | Mana | Mana spent |
| Mummy | Sekhem | Sekhem spent |
| Demon | Faith | Faith spent |

Energy is spent from your actual PoD resource pool in real-time. Overusing expensive moves in combat will leave you drained afterward.

Moves with no energy cost (most base physical moves) are free to use.

---

## Ending Combat

### Victory or Defeat

Combat ends when:
- All enemies are knocked out (HP or morale at 0) — **you win**
- Your character is knocked out — **you lose**
- All your allies are knocked out (group combat) — **you lose**

A result screen appears showing the outcome with character portraits.

### Auto-Resolve

Click **Auto-Resolve** to skip the rest of combat. The winner is determined by a prowess comparison:

```
Your Score  = Prowess + random(0 to Prowess)
Enemy Score = Prowess + random(0 to Prowess)
Higher score wins.
```

This is a quick exit when the outcome is obvious or you don't want to play out the remaining rounds.

### Forfeit

Click the **X (close)** button in the top-right of the combat window to forfeit. Your opponent wins. Your morale drops to 0 and the loss is applied normally. Use this when you want to deliberately lose (e.g., to avoid killing someone in a duel you were forced into).

### Help / Overview

Click **Help** at any time to open the Combat System Overview — a single-screen reference covering the turn flow, damage pipeline, status moves, and keyboard of controls. Handy if you're returning to the game after a break.

---

## After Combat: Health Write-Back

When you click the result screen's button, combat damage is written back to the PoD health system:

- **HP damage** becomes damage boxes on your PoD health track
- **Aggravated damage** is tracked separately (harder to heal, takes longer to recover)
- If the damage exceeds your health track capacity, your character may suffer wounds or death based on PoD's wound system

This means combat has real consequences. A hard-fought victory may leave you wounded for weeks afterward.

---

## Duel Integration

When combat is triggered by the PoD duel system (character interactions, events, hold court, tournaments), additional rules apply based on the duel's fatality setting:

| Fatality | What Happens to the Loser |
|----------|--------------------------|
| Practice | Nothing — no wounds at all |
| No | Non-fatal wounds only |
| Possible | Wounds that can accumulate to death |
| Default | Death if attacker is tribal; wounds otherwise |
| Always | Loser dies (e.g., Jamal the Assamite's duel) |

After the wound/death outcome is applied, the original duel's follow-up event fires. This handles all downstream consequences — titles changing hands, prisoners released, reputation effects, diplomatic fallout — exactly as if the vanilla duel system had run.

Removing the Combat-PoD mod cleanly restores the vanilla duel behavior. No save-game data is permanently altered.

---

## Tips

- **Equip a balanced loadout.** 2-3 ATK moves for damage, 1-2 DEF for survival, 1-2 CTL for debuffs, and 1-2 PWR for powerful specials works well.
- **Guard early against strong opponents.** If their prowess is much higher than yours, guarding reduces the damage you take while you set up debuffs.
- **Use Feint against guarding enemies.** The AI guards more when wounded — break their guard, then follow up with a heavy attack.
- **Mental attacks bypass everything.** Intimidate and psychic attacks ignore guard and soak. Good against heavily armored opponents.
- **Watch your energy.** Vampire blood and fera gnosis are real resources. Spamming expensive supernatural moves will leave you hungry or weakened after the fight.
- **Aggravated damage is king.** Fire vs vampires, silver vs werewolves, holy vs demons — promoted damage sources deal aggravated damage that can't be soaked.
- **Auto-Resolve favors high prowess.** If your prowess is significantly higher, auto-resolve is almost a guaranteed win. If it's close, playing manually gives you more control.
- **Target selection matters in group combat.** Focus fire on one enemy to knock them out quickly rather than spreading damage across all of them.
