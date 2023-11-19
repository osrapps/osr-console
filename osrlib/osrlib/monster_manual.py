from osrlib.monster import MonsterStatsBlock
from osrlib.enums import CharacterClassType
from osrlib.player_character import Alignment
from osrlib.treasure import TreasureType

berserker_stats = MonsterStatsBlock(
    name="Berserker",
    description="Berserkers are simple fighters who go mad in battle. They react normally at first, but once a battle starts they will always fight to the death, sometimes attacking their comrades in their blind rage. When fighting humans or human-like creatures, they add +2 to 'to hit' rolls due to this ferocity. They never retreat, surrender, or take prisoners. Treasure Type (B) is only found in the wilderness.",
    armor_class=7,
    hit_dice="1d8+1",
    num_appearing="1d6",
    movement=120,
    num_special_abilities=0,
    attacks_per_round=1,
    damage_per_attack="1d8",
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=1,
    morale=12,
    treasure_type=TreasureType.B,
    alignment=Alignment.NEUTRAL
)

boar_stats = MonsterStatsBlock(
    name="Boar",
    description="Wild boars generally prefer forested areas, but can be found nearly everywhere. They are omnivorous and have extremely nasty tempers when disturbed.",
    armor_class=7,
    hit_dice="3d8",
    num_appearing="1d6",
    movement=150,
    num_special_abilities=0,
    attacks_per_round=1,
    damage_per_attack="2d8",
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=2,
    morale=9,
    treasure_type=TreasureType.NONE,
    alignment=Alignment.NEUTRAL
)

bugbear_stats = MonsterStatsBlock(
    name="Bugbear",
    description="Bugbears are giant hairy goblins. Despite their size and awkward walk, they move very quietly and attack without warning when they can. They surprise on a roll of 1-3 (on 1d6) due to their stealth. When using weapons, they add +1 to all damage rolls due to their strength.",
    armor_class=5,
    hit_dice="3d8+1",
    num_appearing="2d4",
    movement=90,
    num_special_abilities=0,
    attacks_per_round=1,
    damage_per_attack="2d8+1",
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=3,
    morale=9,
    treasure_type=TreasureType.B,
    alignment=Alignment.CHAOTIC
)

carrion_crawler_stats = MonsterStatsBlock(
    name="Carrion Crawler",
    description="This scavenger is worm-shaped, 9' long and 3' high with many legs. It can move equally well on a floor, wall, or ceiling like a spider. Its mouth is surrounded by 8 tentacles, each 2' long, which can paralyze on a successful hit unless a saving throw vs. Paralysis is made. Once paralyzed, a victim will be eaten unless the carrion crawler is being attacked. The paralysis can be removed by a cure light wounds spell, but any spell so used will have no other effect. Without a spell, the paralysis will wear off in 2-8 turns.",
    armor_class=7,
    hit_dice="3d8+1",
    num_appearing="1d3",
    movement=120,
    num_special_abilities=1,  # For the paralysis ability
    attacks_per_round=8,  # One attack per tentacle
    damage_per_attack="2d8",  # TODO: Handle Paralysis special ability instead of applying damage
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=2,
    morale=9,
    treasure_type=TreasureType.B,
    alignment=Alignment.NEUTRAL
)

cyclops_stats = MonsterStatsBlock(
    name="Cyclops",
    description="A rare type of giant, the cyclops is noted for its great size and single eye in the center of its forehead. Cyclops have poor depth perception due to their single eye.",
    armor_class=5,
    hit_dice="13d8",
    num_appearing="d1",
    movement=90,
    num_special_abilities=1,
    attacks_per_round=1, # TODO: Add support for attack and damage modifiers (Cyclops has -2 on attack rolls)
    damage_per_attack="3d10",
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=13,
    morale=9,
    treasure_type=TreasureType.E,
    alignment=Alignment.CHAOTIC
)

ghoul_stats = MonsterStatsBlock(
    name="Ghoul",
    description="Ghouls are undead creatures. They are hideous, beast-like humans who attack anything living. Attacks by a ghoul will paralyze any creature of ogre-size or smaller, except elves, unless the victim saves vs. Paralysis. Once an opponent is paralyzed, the ghoul will turn and attack another opponent until either the ghoul or all the opponents are paralyzed or dead. The paralysis lasts 2-8 turns unless removed by a cure light wounds spell.",
    armor_class=6,
    hit_dice="2d8",  # The asterisk (*) in the rule book indicates a special ability, which in this case is paralysis
    num_appearing="1d6",  # For individual encounters
    movement=90,
    num_special_abilities=1,  # For the paralysis ability
    attacks_per_round=3,  # Two claws and one bite
    damage_per_attack="1d3+1",  # Assuming the special damage applies to each attack
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=2,
    morale=9,
    treasure_type=TreasureType.B,
    alignment=Alignment.CHAOTIC
)

gnoll_stats = MonsterStatsBlock(
    name="Gnoll",
    description="Gnolls are beings of low intelligence that resemble human-like hyenas. They can use any weapons and are strong but prefer to bully and steal for a living. They may have leaders with higher hit points and attack capabilities. Rumored to be the result of a magical combination of a gnome and a troll by an evil magic-user.",
    armor_class=5,
    hit_dice="2d8",  # Regular gnolls have 2 hit dice
    num_appearing="1d6",  # For individual encounters
    movement=90,
    num_special_abilities=0,  # No special abilities indicated
    attacks_per_round=1,  # One attack per round, as they use one weapon
    damage_per_attack="2d8+1",  # Assuming the +1 applies to their weapon attack
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=2,
    morale=8,
    treasure_type=TreasureType.D,
    alignment=Alignment.CHAOTIC
)

goblin_stats = MonsterStatsBlock(
    name="Goblin",
    description="A small and incredibly ugly humanoid with pale skin, like a chalky tan or sickly gray.",
    armor_class=6,
    hit_dice="1d8-1",
    num_appearing="2d4",
    movement=60,
    num_special_abilities=0,
    attacks_per_round=1,
    damage_per_attack="1d6",
    save_as_class=CharacterClassType.COMMONER,
    save_as_level=1,
    morale=7,
    treasure_type=TreasureType.R,
    alignment=Alignment.CHAOTIC
)

hobgoblin_stats = MonsterStatsBlock(
    name="Hobgoblin",
    description="A larger and meaner relative of the goblin.",
    armor_class=6,
    hit_dice="1d8+1",
    num_appearing="1d6",
    movement=90,
    num_special_abilities=0,
    attacks_per_round=1,
    damage_per_attack="1d8",
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=1,
    morale=8,
    treasure_type=TreasureType.D,
    alignment=Alignment.CHAOTIC
)

kobold_stats = MonsterStatsBlock(
    name="Kobold",
    description="A small, lizard-like humanoid.",
    armor_class=7,
    hit_dice="1d4",
    num_appearing="4d4",
    movement=60,
    num_special_abilities=0,
    attacks_per_round=1,
    damage_per_attack="1d4",
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=1,
    morale=6,
    treasure_type=TreasureType.P,
    alignment=Alignment.CHAOTIC
)

ogre_stats = MonsterStatsBlock(
    name="Ogre",
    description="Ogres are huge fearsome human-like creatures, usually 8 to 10 feet tall, wearing animal skins and often living in caves. They hate Neanderthals and attack them on sight. When encountered outside their lair, they carry significant gold.",
    armor_class=5,
    hit_dice="4d8+1",  # The +1 indicates additional hit points
    num_appearing="1d6",  # For individual encounters
    movement=90,
    num_special_abilities=0,  # No special abilities indicated
    attacks_per_round=1,  # One attack with a club
    damage_per_attack="1d10",  # Damage range of 1-10
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=4,
    morale=10,
    treasure_type=TreasureType.C,  # Plus 1000 gp, which may need special handling
    alignment=Alignment.CHAOTIC
)

orc_stats = MonsterStatsBlock(
    name="Orc",
    description="Orcs are ugly human-like creatures resembling a mix of animal and man. They are nocturnal, prefer underground living, and have poor vision in daylight, affecting their combat ability. Known for their bad tempers and cruelty. Leaders are stronger and have a morale impact.",
    armor_class=6,
    hit_dice="1d8",  # Standard hit dice for an orc
    num_appearing="2d4",  # For individual encounters, adjusting to match the range of 2-8
    movement=120,
    num_special_abilities=0,  # No special abilities, but note about daylight and leaders in description
    attacks_per_round=1,  # One attack with a weapon
    damage_per_attack="1d6",  # Assuming the standard weapon damage of 1-6
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=1,
    morale=8,  # Adjusts to 6 if the leader is killed
    treasure_type=TreasureType.D,
    alignment=Alignment.CHAOTIC
)

owl_bear_stats = MonsterStatsBlock(
    name="Owl Bear",
    description="A huge bear-like creature with the head of a giant owl, standing 8' tall and weighing 1500 pounds. Known for its nasty temper and preference for meat. Capable of additional damage with a 'hug' attack if both paws hit the same opponent in one round.",
    armor_class=5,
    hit_dice="5d8",  # Standard hit dice for an owl bear
    num_appearing="1d4",  # For individual encounters
    movement=120,
    num_special_abilities=1,  # For the hug ability
    attacks_per_round=3,  # Two claws and one bite
    damage_per_attack="2d8+1",  # Assuming the +1 applies to each attack
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=3,
    morale=9,
    treasure_type=TreasureType.C,
    alignment=Alignment.NEUTRAL
)

skeleton_stats = MonsterStatsBlock(
    name="Skeleton",
    description="Animated undead creatures, often used as guards. Immune to sleep, charm, and mind-reading spells. Fights until destroyed.",
    armor_class=7,
    hit_dice="1d8+1",  # The +1 indicates a special ability, which is likely its undead nature
    num_appearing="1d6",  # For individual encounters
    movement=120,
    num_special_abilities=1,  # For undead nature (Turning resistance, etc.)
    attacks_per_round=1,  # One attack with a weapon
    damage_per_attack="1d8",  # Assuming standard weapon damage
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=1,
    morale=12,  # Skeletons are unyielding, hence a high morale
    treasure_type=TreasureType.P,  # (B) is noted but typically skeletons carry no treasure
    alignment=Alignment.NEUTRAL
)

troglodyte_stats = MonsterStatsBlock(
    name="Troglodyte",
    description="Intelligent human-like reptiles with chameleon-like abilities and a nauseating stench. Hostile towards most creatures.",
    armor_class=5,
    hit_dice="2d8",  # The asterisk suggests a special ability (stench and color changing)
    num_appearing="1d8",  # For individual encounters
    movement=120,
    num_special_abilities=2,  # For the stench and color-changing abilities
    attacks_per_round=3,  # Two claws and one bite
    damage_per_attack="1d4",  # 1-4 damage for each attack
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=2,
    morale=9,
    treasure_type=TreasureType.A,
    alignment=Alignment.CHAOTIC
)

yellow_mold_stats = MonsterStatsBlock(
    name="Yellow Mold",
    description="A deadly fungus that releases a cloud of spores when disturbed. Can only be killed by fire.",
    armor_class=0,  # "Can always be hit" implies an AC of 0
    hit_dice="2d8",  # Standard hit dice for yellow mold
    num_appearing="1d4",  # For individual occurrences
    movement=0,
    num_special_abilities=1,  # For the spore cloud release
    attacks_per_round=1,  # The spore attack
    damage_per_attack="1d6",  # Plus special effects from spores
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=2,
    morale=0,  # Not applicable to a fungus
    treasure_type=TreasureType.NONE,
    alignment=Alignment.NEUTRAL
)

zombie_stats = MonsterStatsBlock(
    name="Zombie",
    description="Undead humans or demi-humans, immune to mind-affecting spells and often used as silent guards. Slow fighters but relentless.",
    armor_class=8,
    hit_dice="2d8",  # Standard hit dice for a zombie
    num_appearing="2d4",  # For individual encounters
    movement=120,
    num_special_abilities=1,  # For undead nature (Turning resistance, etc.)
    attacks_per_round=1,  # One attack with a weapon
    damage_per_attack="1d8",  # Assuming standard weapon damage
    save_as_class=CharacterClassType.FIGHTER,
    save_as_level=1,
    morale=12,  # Zombies are unyielding, hence a high morale
    treasure_type=TreasureType.NONE,
    alignment=Alignment.CHAOTIC
)

monster_stats_blocks = [
    berserker_stats,
    boar_stats,
    bugbear_stats,
    carrion_crawler_stats,
    cyclops_stats,
    ghoul_stats,
    gnoll_stats,
    goblin_stats,
    hobgoblin_stats,
    kobold_stats,
    ogre_stats,
    orc_stats,
    owl_bear_stats,
    skeleton_stats,
    troglodyte_stats,
    yellow_mold_stats,
    zombie_stats
]