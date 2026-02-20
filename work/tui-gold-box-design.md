# Gold Box-style TUI design (OSE SRD rules)

This document defines the gameplay flow for the osrgame TUI, modeled after the classic SSI Gold Box RPGs but using [Old-School Essentials (OSE) SRD](https://oldschoolessentials.necroticgnome.com/srd/index.php/Main_Page) rules (B/X D&D).

## Key rules differences from Gold Box (AD&D)

The Gold Box games used AD&D 1e/2e. OSE uses B/X, which differs in several important ways that affect the TUI design:

- **[Race-as-class](https://oldschoolessentials.necroticgnome.com/srd/index.php/Creating_a_Character)**: Dwarf, Elf, and Halfling are classes, not races. No separate race + class selection.
- **[3-point alignment](https://oldschoolessentials.necroticgnome.com/srd/index.php/Alignment)**: Lawful, Neutral, Chaotic. Not the AD&D 3x3 grid.
- **[Group initiative](https://oldschoolessentials.necroticgnome.com/srd/index.php/Combat)**: 1d6 per side each round, not individual initiative or weapon speed factors.
- **[Death at 0 HP](https://oldschoolessentials.necroticgnome.com/srd/index.php/Checks,_Damage,_Saves)**: No negative HP, no death saves. Dead is dead.
- **[Symmetrical modifiers](https://oldschoolessentials.necroticgnome.com/srd/index.php/Ability_Scores)**: Clean -3 to +3 curve. No exceptional strength (18/XX).
- **[Simpler magic](https://oldschoolessentials.necroticgnome.com/srd/index.php/Rules_of_Magic)**: No spell components, no casting time in segments.
- **[5 saving throw categories](https://oldschoolessentials.necroticgnome.com/srd/index.php/Checks,_Damage,_Saves)**: Death/Poison, Wands, Paralysis/Petrification, Breath Attacks, Spells/Rods/Staves.
- **[Level caps](https://oldschoolessentials.necroticgnome.com/srd/index.php/Advancement)**: 14 for humans, lower for demihumans (Dwarf 12, Elf 10, Halfling 8).

## Gameplay flow overview

```
┌─────────────┐
│  Main menu  │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────────┐
│  Character  │────►│  Party manager  │
│  creation   │     │  (review/order) │
└──────┬──────┘     └────────┬────────┘
       │                     │
       ▼                     ▼
┌─────────────────────────────────────┐
│            Town hub                 │
│  ┌─────────┬──────────┬──────────┐  │
│  │ Temple  │  Shop    │ Tavern   │  │
│  │ (heal)  │ (equip)  │ (rest)   │  │
│  ├─────────┼──────────┼──────────┤  │
│  │Training │  Inn     │  Quest   │  │
│  │ hall    │ (save)   │  board   │  │
│  └─────────┴──────────┴──────────┘  │
└──────────────────┬──────────────────┘
                   │
                   ▼
        ┌─────────────────┐
        │   Exploration   │◄─────────────┐
        │  (dungeon/wild) │              │
        └────────┬────────┘              │
                 │                       │
          ┌──────┴──────┐                │
          ▼             ▼                │
   ┌────────────┐ ┌──────────┐           │
   │  Encounter │ │ Camping  │           │
   │            │ │ (rest,   │           │
   └─────┬──────┘ │  spells) │           │
         │        └──────────┘           │
         ▼                               │
   ┌────────────┐                        │
   │   Combat   │                        │
   │ (tactical) │                        │
   └─────┬──────┘                        │
         │                               │
         ▼                               │
   ┌────────────┐                        │
   │    Loot    │────────────────────────┘
   └────────────┘
```

## 1. Main menu

**Screen**: Full-screen title with menu options.

**Options:**

- **New game** - Enter character creation
- **Load game** - Browse saved games (JSON files via TinyDB)
- **Quit**

No import from other games (Gold Box had this, but it's out of scope).

## 2. Character creation

**Rules reference**: [Creating a character](https://oldschoolessentials.necroticgnome.com/srd/index.php/Creating_a_Character)

**Steps (following the OSE SRD procedure):**

1. **Roll [ability scores](https://oldschoolessentials.necroticgnome.com/srd/index.php/Ability_Scores)**: 3d6 in order for STR, INT, WIS, DEX, CON, CHA. Display each roll with modifiers. Offer a **reroll** button (the Gold Box tradition of mashing reroll until you get good stats).
2. **Choose class**: [Cleric](https://oldschoolessentials.necroticgnome.com/srd/index.php/Cleric), [Dwarf](https://oldschoolessentials.necroticgnome.com/srd/index.php/Dwarf), [Elf](https://oldschoolessentials.necroticgnome.com/srd/index.php/Elf), [Fighter](https://oldschoolessentials.necroticgnome.com/srd/index.php/Fighter), [Halfling](https://oldschoolessentials.necroticgnome.com/srd/index.php/Halfling), [Magic-User](https://oldschoolessentials.necroticgnome.com/srd/index.php/Magic-User), [Thief](https://oldschoolessentials.necroticgnome.com/srd/index.php/Thief). Show prime requisite XP modifier for each class based on current scores. Grey out classes whose minimum requirements aren't met.
3. **Adjust ability scores** (optional): Player may lower STR, INT, or WIS by 2 to raise a prime requisite by 1. No score may drop below 9.
4. **Choose [alignment](https://oldschoolessentials.necroticgnome.com/srd/index.php/Alignment)**: Lawful, Neutral, or Chaotic.
5. **Roll HP**: Class hit die + CON modifier, minimum 1.
6. **Name the character**.
7. **Buy starting [equipment](https://oldschoolessentials.necroticgnome.com/srd/index.php/Adventuring_Gear)**: Starting gold is 3d6 x 10 gp. Shop for [weapons and armour](https://oldschoolessentials.necroticgnome.com/srd/index.php/Weapons_And_Armour).

**Party size**: Up to 6 PCs, matching the Gold Box standard. The OSE SRD recommends [6-8 characters](https://oldschoolessentials.necroticgnome.com/srd/index.php/Party_Organisation) including retainers.

## 3. Party manager

**Rules reference**: [Party organisation](https://oldschoolessentials.necroticgnome.com/srd/index.php/Party_Organisation)

**Functions:**

- **View character sheets**: Full stats, equipment, spells, XP
- **Set marching order**: Front-to-back formation. Front rank takes melee attacks; rear rank is protected. This maps directly to the Gold Box front/back row mechanic.
- **Add/remove characters**: Swap party members in and out
- **Drop character**: Permanently remove (with confirmation)

**Marching order matters** because it determines who can be targeted in melee combat and who gets surprised first.

## 4. Town hub

**Rules reference**: [Designing a base town](https://oldschoolessentials.necroticgnome.com/srd/index.php/Designing_a_Base_Town)

The town is a menu of locations, not a space to explore (same as Gold Box). Each location provides specific services:

### Training hall

- **Create new character** (launches character creation flow)
- **Level up**: When a PC has enough XP per [class advancement tables](https://oldschoolessentials.necroticgnome.com/srd/index.php/Advancement), they can train. Roll new hit die, update THAC0, saves, spell slots.
- **Manage party order**: Set front-to-back formation

### Temple

**Rules reference**: [Checks, damage, saves (healing)](https://oldschoolessentials.necroticgnome.com/srd/index.php/Checks,_Damage,_Saves)

- **Heal wounds**: Costs gold. Restores HP.
- **Cure poison**: Remove poison status.
- **Cure disease**: Remove disease status.
- **Remove curse**: Lift curses on characters or items.
- **Raise dead**: Revive a dead character (high cost, possible side effects per referee rules).

### Shop

**Rules reference**: [Wealth](https://oldschoolessentials.necroticgnome.com/srd/index.php/Wealth), [Adventuring gear](https://oldschoolessentials.necroticgnome.com/srd/index.php/Adventuring_Gear), [Weapons and armour](https://oldschoolessentials.necroticgnome.com/srd/index.php/Weapons_And_Armour)

- **Buy weapons, armour, gear**: Full equipment list from OSE SRD
- **Sell items**: At half purchase price (standard B/X rule)
- **Identify magic items**: Reveal properties of unidentified items (costs gold)
- **Pool gold**: Transfer gold between party members

**Currency**: [Platinum, gold, electrum, silver, copper](https://oldschoolessentials.necroticgnome.com/srd/index.php/Wealth) with standard B/X exchange rates.

### Tavern

- **Hear rumors**: Plot hooks and quest information. The OpenAI model generates these contextually.
- **Recruit [retainers](https://oldschoolessentials.necroticgnome.com/srd/index.php/Retainers)**: Hire NPC companions. Max retainers per PC based on CHA (1-7). Hiring uses the 2d6 reaction roll + CHA modifier. Retainers earn half XP and require wages (1 gp/day minimum) plus a half share of treasure.

### Inn

- **Save game**: Write game state to JSON
- **Long rest**: Full night's rest, memorize spells (see camping)

### Quest board

- **View available quests**: Current objectives
- **Review completed quests**: History of accomplishments
- **Advance main plot**: Triggered by quest completion

## 5. Exploration

**Rules reference**: [Dungeon adventuring](https://oldschoolessentials.necroticgnome.com/srd/index.php/Dungeon_Adventuring)

### Screen layout (Gold Box style)

```
┌──────────────────────┬──────────────────────┐
│                      │ Fighter    HP: 8/8   │
│                      │ Cleric     HP: 6/6   │
│   Map / viewport     │ Elf        HP: 5/5   │
│                      │ Thief      HP: 4/4   │
│                      │ Dwarf      HP: 7/7   │
│                      │ Magic-User HP: 3/3   │
├──────────────────────┴──────────────────────┤
│ Narrative text area                         │
│ (OpenAI-generated location descriptions)    │
├─────────────────────────────────────────────┤
│ Commands: (N)orth (S)outh (E)ast (W)est     │
│           (U)p (D)own (C)amp (M)ap (T)own   │
└─────────────────────────────────────────────┘
```

### Dungeon exploration rules

- **Time**: Measured in [turns (10 minutes)](https://oldschoolessentials.necroticgnome.com/srd/index.php/Time,_Weight,_Movement) during exploration
- **Movement**: Base movement rate in feet per turn; 3x speed in mapped/familiar areas
- **[Wandering monsters](https://oldschoolessentials.necroticgnome.com/srd/index.php/Dungeon_Adventuring)**: Checked every 2 turns, 1-in-6 chance
- **Doors**: Stuck doors require STR check (X-in-6). [Secret doors](https://oldschoolessentials.necroticgnome.com/srd/index.php/Dungeon_Adventuring) found on 1-in-6 when searching (Elves: 2-in-6).
- **Traps**: Trigger on 2-in-6. Detection by searching: 1-in-6. Dwarves detect construction traps on 2-in-6.
- **Rest requirement**: Must rest 1 turn every hour (6 turns). Skipping rest imposes -1 to attack and damage.
- **Light**: Torches last 6 turns, lanterns last 24 turns. Infravision for Dwarves, Elves (60').

### Encounter trigger

When entering a location with monsters or when a wandering monster check succeeds:

1. **[Surprise](https://oldschoolessentials.necroticgnome.com/srd/index.php/Encounters)**: Each side rolls 1d6; 1-2 = surprised (lose one round)
2. **Encounter distance**: 2d6 x 10 feet (dungeon)
3. **[Monster reaction](https://oldschoolessentials.necroticgnome.com/srd/index.php/Encounters)**: 2d6 + CHA modifier. Result ranges from hostile attack (2-) to friendly (12+). Not every encounter has to be a fight.
4. **Player choice**: Fight, parley, or flee ([evasion](https://oldschoolessentials.necroticgnome.com/srd/index.php/Evasion_and_Pursuit))

## 6. Camping

**Rules reference**: [Rules of magic](https://oldschoolessentials.necroticgnome.com/srd/index.php/Rules_of_Magic), [Spell books](https://oldschoolessentials.necroticgnome.com/srd/index.php/Spell_Books), [Checks, damage, saves](https://oldschoolessentials.necroticgnome.com/srd/index.php/Checks,_Damage,_Saves)

Available from the exploration screen. Camping in a dungeon is risky (wandering monster checks still apply).

### Camp menu

- **Rest**: Recover HP via [natural healing](https://oldschoolessentials.necroticgnome.com/srd/index.php/Checks,_Damage,_Saves) (1d3 HP per full day of complete rest). Short rests (1 turn) satisfy the hourly rest requirement but don't heal.
- **Memorize spells**: [Vancian magic system](https://oldschoolessentials.necroticgnome.com/srd/index.php/Rules_of_Magic). After a full night's rest, [Clerics](https://oldschoolessentials.necroticgnome.com/srd/index.php/Cleric) pray to select any spell from their class list. [Magic-Users](https://oldschoolessentials.necroticgnome.com/srd/index.php/Magic-User) and [Elves](https://oldschoolessentials.necroticgnome.com/srd/index.php/Elf) memorize from their [spell book](https://oldschoolessentials.necroticgnome.com/srd/index.php/Spell_Books). Same spell can fill multiple slots. Takes 1 hour.
- **Scribe spells**: Magic-Users/Elves copy scrolls into their spell book
- **Set watch order**: Determines who is alert if rest is interrupted by a wandering monster (surprised characters can't act in the first round)
- **Camp can be interrupted**: Wandering monster checks during rest. If interrupted, rest is incomplete -- no healing, partial spell memorization.

## 7. Combat

**Rules reference**: [Combat](https://oldschoolessentials.necroticgnome.com/srd/index.php/Combat), [Other combat issues](https://oldschoolessentials.necroticgnome.com/srd/index.php/Other_Combat_Issues), [Combat tables](https://oldschoolessentials.necroticgnome.com/srd/index.php/Combat_Tables)

### Screen layout

```
┌──────────────────────┬──────────────────────┐
│                      │ Party                │
│                      │ ──────               │
│   Tactical combat    │ Fighter    HP: 8/8   │
│   grid / display     │ Cleric     HP: 6/6   │
│                      │ Elf        HP: 3/5 * │
│                      │ Thief      HP: 4/4   │
│                      ├──────────────────────┤
│                      │ Monsters             │
│                      │ ──────               │
│                      │ Goblin x3  HP: ??    │
│                      │ Goblin Cpt HP: ??    │
├──────────────────────┴──────────────────────┤
│ Combat log                                  │
│ > Fighter hits Goblin for 5 damage (killed!)│
├─────────────────────────────────────────────┤
│ (A)ttack (C)ast (U)se item (G)uard (F)lee   │
└─────────────────────────────────────────────┘
```

### Combat sequence per round

Per the [OSE SRD combat procedure](https://oldschoolessentials.necroticgnome.com/srd/index.php/Combat):

1. **Declare spells and retreat movements** before initiative
2. **Roll [initiative](https://oldschoolessentials.necroticgnome.com/srd/index.php/Combat)**: 1d6 per side (group initiative). Re-rolled every round. DEX modifier applies if using optional individual initiative.
3. **Winning side acts** (in order):
   a. [Morale](https://oldschoolessentials.necroticgnome.com/srd/index.php/Morale_(Optional_Rule)) checks (if triggered)
   b. Movement
   c. Missile attacks
   d. Spell casting
   e. Melee attacks
4. **Losing side acts** in the same order
5. **Ties**: Both sides act simultaneously (or re-roll, referee's choice)

### Actions available per character

- **Attack (melee)**: Roll 1d20 vs. THAC0 matrix. STR modifier applies to hit and damage. Minimum 1 damage on a hit.
- **Attack (missile)**: Roll 1d20 vs. THAC0 matrix. DEX modifier to hit. Range modifiers: short +1, medium +0, long -1.
- **Cast spell**: Cannot move and cast in the same round. If caster takes damage before acting (lost initiative), the spell is lost. See [Cleric spells](https://oldschoolessentials.necroticgnome.com/srd/index.php/Cleric_Spells) and [Magic-User spells](https://oldschoolessentials.necroticgnome.com/srd/index.php/Magic-User_Spells).
- **Use item**: Potions, scrolls, wands, etc.
- **[Turn undead](https://oldschoolessentials.necroticgnome.com/srd/index.php/Cleric)**: Clerics only. Consult turning table by cleric level vs. undead HD.
- **Guard/delay**: Hold action, attack anything that enters melee range.
- **Fighting withdrawal**: Move at half encounter speed, can still attack.
- **Full retreat**: Move at full encounter speed, cannot attack. Enemies get +2 to hit, shield AC bonus ignored.
- **[Flee](https://oldschoolessentials.necroticgnome.com/srd/index.php/Evasion_and_Pursuit)**: Attempt to leave combat entirely. If fleeing side is faster, automatic escape. Otherwise, round-by-round pursuit. Monsters may stop for dropped treasure (3-in-6 for intelligent monsters) or food (3-in-6 for unintelligent).

### Morale

**Rules reference**: [Morale (optional rule)](https://oldschoolessentials.necroticgnome.com/srd/index.php/Morale_(Optional_Rule))

- Each monster type has a morale score (2-12)
- **Check triggers**: First ally killed, and when half the group is down
- **Resolution**: Roll 2d6. If roll > morale score, the monster flees/surrenders.
- **Two-pass rule**: After two successful morale checks in one encounter, no further checks needed -- the monster fights to the death.
- Morale 2 = never fights. Morale 12 = fights to the death.

### Death and defeat

- **[0 HP = dead](https://oldschoolessentials.necroticgnome.com/srd/index.php/Checks,_Damage,_Saves)**: No negative HP, no stabilization. Immediate death.
- **Total party kill**: Game over screen. Offer to load a save or return to main menu.
- **Party victory**: Proceed to loot.

## 8. Loot

**Rules reference**: [Placing treasure](https://oldschoolessentials.necroticgnome.com/srd/index.php/Placing_Treasure), [Treasure types](https://oldschoolessentials.necroticgnome.com/srd/index.php/Treasure_Types)

After combat victory:

- **Display treasure**: Coins ([by type](https://oldschoolessentials.necroticgnome.com/srd/index.php/Wealth)), [gems and jewellery](https://oldschoolessentials.necroticgnome.com/srd/index.php/Gems_and_Jewellery), [magic items](https://oldschoolessentials.necroticgnome.com/srd/index.php/Magic_Items_(General))
- **Take/leave items**: Player chooses what to pick up (encumbrance is a factor via [time, weight, movement](https://oldschoolessentials.necroticgnome.com/srd/index.php/Time,_Weight,_Movement))
- **Distribute to party members**: Assign items to specific characters
- **XP award**: [XP from monsters](https://oldschoolessentials.necroticgnome.com/srd/index.php/Awarding_XP) (based on HD and special abilities) split among surviving PCs. XP from treasure is awarded only when treasure is **brought back to safety** (town), not when looted.
- **OpenAI battle summary**: The model narrates combat highlights

## 9. Level up

**Rules reference**: [Advancement](https://oldschoolessentials.necroticgnome.com/srd/index.php/Advancement)

Leveling happens at the training hall in town, not automatically:

- **XP threshold**: Per class table ([Cleric](https://oldschoolessentials.necroticgnome.com/srd/index.php/Cleric), [Fighter](https://oldschoolessentials.necroticgnome.com/srd/index.php/Fighter), [Magic-User](https://oldschoolessentials.necroticgnome.com/srd/index.php/Magic-User), [Thief](https://oldschoolessentials.necroticgnome.com/srd/index.php/Thief), [Dwarf](https://oldschoolessentials.necroticgnome.com/srd/index.php/Dwarf), [Elf](https://oldschoolessentials.necroticgnome.com/srd/index.php/Elf), [Halfling](https://oldschoolessentials.necroticgnome.com/srd/index.php/Halfling))
- **[Prime requisite](https://oldschoolessentials.necroticgnome.com/srd/index.php/Ability_Scores) XP modifier**: Adjusts earned XP by -20% to +10% based on prime requisite score
- **One level per session max**: Cannot jump more than one level. Excess XP is capped at 1 below next threshold.
- **Gains on level up**: New hit die roll + CON modifier (min 1), updated THAC0, updated saving throws, new spell slots (if applicable), class-specific abilities

## 10. Save and load

- **Save at the inn**: Write full game state (party, dungeon progress, quest state, inventory) to JSON via TinyDB
- **Load from main menu**: Browse saved game files
- **Manual save only**: No autosave (matches Gold Box convention)

## 11. OpenAI integration (narrative layer)

The OpenAI model serves as the dungeon master for narrative purposes. It does NOT make rules decisions -- the engine (osrlib) handles all mechanics.

**The model provides:**

- Location descriptions when entering new areas
- Battle summaries after combat
- Tavern rumors and quest hooks
- NPC dialogue during encounters (when reaction roll indicates parley)
- Contextual flavor for events (traps sprung, doors opened, treasure found)

**The model does NOT control:**

- Dice rolls, damage, hit/miss
- Treasure generation (handled by [treasure type tables](https://oldschoolessentials.necroticgnome.com/srd/index.php/Treasure_Types))
- Monster stats or behavior (handled by [monster descriptions](https://oldschoolessentials.necroticgnome.com/srd/index.php/Monster_Descriptions))
- Character progression or XP awards
- Any mechanical game state

**Technical requirements:**

- All API calls must be async (Textual workers) with loading indicators
- Use the OpenAI Responses API (not the legacy Chat Completions API)
- Graceful fallback when API key is missing or network is unavailable -- the game should be fully playable without OpenAI, just without narrative flavor text

## Appendix: OSE SRD quick reference links

### Characters

- [Creating a character](https://oldschoolessentials.necroticgnome.com/srd/index.php/Creating_a_Character)
- [Ability scores](https://oldschoolessentials.necroticgnome.com/srd/index.php/Ability_Scores)
- [Alignment](https://oldschoolessentials.necroticgnome.com/srd/index.php/Alignment)
- [Languages](https://oldschoolessentials.necroticgnome.com/srd/index.php/Languages)
- [Advancement](https://oldschoolessentials.necroticgnome.com/srd/index.php/Advancement)

### Classes

- [Cleric](https://oldschoolessentials.necroticgnome.com/srd/index.php/Cleric)
- [Dwarf](https://oldschoolessentials.necroticgnome.com/srd/index.php/Dwarf)
- [Elf](https://oldschoolessentials.necroticgnome.com/srd/index.php/Elf)
- [Fighter](https://oldschoolessentials.necroticgnome.com/srd/index.php/Fighter)
- [Halfling](https://oldschoolessentials.necroticgnome.com/srd/index.php/Halfling)
- [Magic-User](https://oldschoolessentials.necroticgnome.com/srd/index.php/Magic-User)
- [Thief](https://oldschoolessentials.necroticgnome.com/srd/index.php/Thief)

### Equipment and services

- [Wealth](https://oldschoolessentials.necroticgnome.com/srd/index.php/Wealth)
- [Adventuring gear](https://oldschoolessentials.necroticgnome.com/srd/index.php/Adventuring_Gear)
- [Weapons and armour](https://oldschoolessentials.necroticgnome.com/srd/index.php/Weapons_And_Armour)
- [Retainers](https://oldschoolessentials.necroticgnome.com/srd/index.php/Retainers)

### Magic

- [Rules of magic](https://oldschoolessentials.necroticgnome.com/srd/index.php/Rules_of_Magic)
- [Spell books](https://oldschoolessentials.necroticgnome.com/srd/index.php/Spell_Books)
- [Cleric spells](https://oldschoolessentials.necroticgnome.com/srd/index.php/Cleric_Spells)
- [Magic-User spells](https://oldschoolessentials.necroticgnome.com/srd/index.php/Magic-User_Spells)

### Adventuring

- [Party organisation](https://oldschoolessentials.necroticgnome.com/srd/index.php/Party_Organisation)
- [Time, weight, movement](https://oldschoolessentials.necroticgnome.com/srd/index.php/Time,_Weight,_Movement)
- [Checks, damage, saves](https://oldschoolessentials.necroticgnome.com/srd/index.php/Checks,_Damage,_Saves)
- [Dungeon adventuring](https://oldschoolessentials.necroticgnome.com/srd/index.php/Dungeon_Adventuring)
- [Wilderness adventuring](https://oldschoolessentials.necroticgnome.com/srd/index.php/Wilderness_Adventuring)
- [Encounters](https://oldschoolessentials.necroticgnome.com/srd/index.php/Encounters)
- [Evasion and pursuit](https://oldschoolessentials.necroticgnome.com/srd/index.php/Evasion_and_Pursuit)

### Combat

- [Combat](https://oldschoolessentials.necroticgnome.com/srd/index.php/Combat)
- [Other combat issues](https://oldschoolessentials.necroticgnome.com/srd/index.php/Other_Combat_Issues)
- [Combat tables](https://oldschoolessentials.necroticgnome.com/srd/index.php/Combat_Tables)
- [Morale (optional rule)](https://oldschoolessentials.necroticgnome.com/srd/index.php/Morale_(Optional_Rule))

### Treasure

- [Placing treasure](https://oldschoolessentials.necroticgnome.com/srd/index.php/Placing_Treasure)
- [Treasure types](https://oldschoolessentials.necroticgnome.com/srd/index.php/Treasure_Types)
- [Gems and jewellery](https://oldschoolessentials.necroticgnome.com/srd/index.php/Gems_and_Jewellery)
- [Magic items (general)](https://oldschoolessentials.necroticgnome.com/srd/index.php/Magic_Items_(General))

### Monsters

- [Monster descriptions](https://oldschoolessentials.necroticgnome.com/srd/index.php/Monster_Descriptions)
- [Dungeon encounters](https://oldschoolessentials.necroticgnome.com/srd/index.php/Dungeon_Encounters)

### Running the game

- [Designing a base town](https://oldschoolessentials.necroticgnome.com/srd/index.php/Designing_a_Base_Town)
- [Designing a dungeon](https://oldschoolessentials.necroticgnome.com/srd/index.php/Designing_a_Dungeon)
- [Awarding XP](https://oldschoolessentials.necroticgnome.com/srd/index.php/Awarding_XP)
