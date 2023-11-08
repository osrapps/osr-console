from osrlib.enums import CharacterClassType
from osrlib.combat import AttackType

saving_throws = {
    CharacterClassType.CLERIC: {
        range(1, 5): {
            AttackType.DEATH_RAY_POISON: 11,
            AttackType.MAGIC_WANDS: 12,
            AttackType.PARALYSIS_TURN_TO_STONE: 14,
            AttackType.DRAGON_BREATH: 16,
            AttackType.RODS_STAVES_SPELLS: 15
        },
        range(5, 9): {
            AttackType.DEATH_RAY_POISON: 9,
            AttackType.MAGIC_WANDS: 10,
            AttackType.PARALYSIS_TURN_TO_STONE: 12,
            AttackType.DRAGON_BREATH: 14,
            AttackType.RODS_STAVES_SPELLS: 12
        },
        range(9, 13): {
            AttackType.DEATH_RAY_POISON: 6,
            AttackType.MAGIC_WANDS: 7,
            AttackType.PARALYSIS_TURN_TO_STONE: 9,
            AttackType.DRAGON_BREATH: 11,
            AttackType.RODS_STAVES_SPELLS: 9
        },
        range(13, 17): {
            AttackType.DEATH_RAY_POISON: 3,
            AttackType.MAGIC_WANDS: 5,
            AttackType.PARALYSIS_TURN_TO_STONE: 7,
            AttackType.DRAGON_BREATH: 8,
            AttackType.RODS_STAVES_SPELLS: 7
        },
    },
    CharacterClassType.ELF: {
        range(1, 4): {
            AttackType.DEATH_RAY_POISON: 12,
            AttackType.MAGIC_WANDS: 13,
            AttackType.PARALYSIS_TURN_TO_STONE: 13,
            AttackType.DRAGON_BREATH: 15,
            AttackType.RODS_STAVES_SPELLS: 15
        },
        range(4, 7): {
            AttackType.DEATH_RAY_POISON: 10,
            AttackType.MAGIC_WANDS: 11,
            AttackType.PARALYSIS_TURN_TO_STONE: 11,
            AttackType.DRAGON_BREATH: 13,
            AttackType.RODS_STAVES_SPELLS: 12
        },
        range(7, 10): {
            AttackType.DEATH_RAY_POISON: 8,
            AttackType.MAGIC_WANDS: 9,
            AttackType.PARALYSIS_TURN_TO_STONE: 9,
            AttackType.DRAGON_BREATH: 10,
            AttackType.RODS_STAVES_SPELLS: 10
        },
        range(10,11): {
            AttackType.DEATH_RAY_POISON: 6,
            AttackType.MAGIC_WANDS: 7,
            AttackType.PARALYSIS_TURN_TO_STONE: 8,
            AttackType.DRAGON_BREATH: 8,
            AttackType.RODS_STAVES_SPELLS: 8
        },
    },
    CharacterClassType.THIEF: {
        range(1, 5): {
            AttackType.DEATH_RAY_POISON: 13,
            AttackType.MAGIC_WANDS: 14,
            AttackType.PARALYSIS_TURN_TO_STONE: 13,
            AttackType.DRAGON_BREATH: 16,
            AttackType.RODS_STAVES_SPELLS: 15
        },
        range(5, 9): {
            AttackType.DEATH_RAY_POISON: 12,
            AttackType.MAGIC_WANDS: 13,
            AttackType.PARALYSIS_TURN_TO_STONE: 11,
            AttackType.DRAGON_BREATH: 14,
            AttackType.RODS_STAVES_SPELLS: 13
        },
        range(9, 13): {
            AttackType.DEATH_RAY_POISON: 10,
            AttackType.MAGIC_WANDS: 11,
            AttackType.PARALYSIS_TURN_TO_STONE: 9,
            AttackType.DRAGON_BREATH: 12,
            AttackType.RODS_STAVES_SPELLS: 10
        },
        range(13, 17): {
            AttackType.DEATH_RAY_POISON: 8,
            AttackType.MAGIC_WANDS: 9,
            AttackType.PARALYSIS_TURN_TO_STONE: 7,
            AttackType.DRAGON_BREATH: 10,
            AttackType.RODS_STAVES_SPELLS: 8
        },
    },
    CharacterClassType.MAGIC_USER: {
        range(1, 6): {
            AttackType.DEATH_RAY_POISON: 13,
            AttackType.MAGIC_WANDS: 14,
            AttackType.PARALYSIS_TURN_TO_STONE: 13,
            AttackType.DRAGON_BREATH: 16,
            AttackType.RODS_STAVES_SPELLS: 15
        },
        range(6, 11): {
            AttackType.DEATH_RAY_POISON: 11,
            AttackType.MAGIC_WANDS: 12,
            AttackType.PARALYSIS_TURN_TO_STONE: 11,
            AttackType.DRAGON_BREATH: 14,
            AttackType.RODS_STAVES_SPELLS: 12
        },
        range(11, 16): {
            AttackType.DEATH_RAY_POISON: 8,
            AttackType.MAGIC_WANDS: 9,
            AttackType.PARALYSIS_TURN_TO_STONE: 8,
            AttackType.DRAGON_BREATH: 11,
            AttackType.RODS_STAVES_SPELLS: 8
        },
    },
    CharacterClassType.FIGHTER: {
        range(1, 4): {
            AttackType.DEATH_RAY_POISON: 12,
            AttackType.MAGIC_WANDS: 13,
            AttackType.PARALYSIS_TURN_TO_STONE: 14,
            AttackType.DRAGON_BREATH: 15,
            AttackType.RODS_STAVES_SPELLS: 16
        },
        range(4, 7): {
            AttackType.DEATH_RAY_POISON: 10,
            AttackType.MAGIC_WANDS: 11,
            AttackType.PARALYSIS_TURN_TO_STONE: 12,
            AttackType.DRAGON_BREATH: 13,
            AttackType.RODS_STAVES_SPELLS: 14
        },
        range(7, 10): {
            AttackType.DEATH_RAY_POISON: 8,
            AttackType.MAGIC_WANDS: 9,
            AttackType.PARALYSIS_TURN_TO_STONE: 10,
            AttackType.DRAGON_BREATH: 10,
            AttackType.RODS_STAVES_SPELLS: 12
        },
        range(10, 13): {
            AttackType.DEATH_RAY_POISON: 6,
            AttackType.MAGIC_WANDS: 7,
            AttackType.PARALYSIS_TURN_TO_STONE: 8,
            AttackType.DRAGON_BREATH: 8,
            AttackType.RODS_STAVES_SPELLS: 10
        },
        range(13, 16): {
            AttackType.DEATH_RAY_POISON: 4,
            AttackType.MAGIC_WANDS: 5,
            AttackType.PARALYSIS_TURN_TO_STONE: 6,
            AttackType.DRAGON_BREATH: 5,
            AttackType.RODS_STAVES_SPELLS: 8
        },
    },
    CharacterClassType.DWARF: {
        range(1, 4): {
            AttackType.DEATH_RAY_POISON: 8,
            AttackType.MAGIC_WANDS: 9,
            AttackType.PARALYSIS_TURN_TO_STONE: 10,
            AttackType.DRAGON_BREATH: 13,
            AttackType.RODS_STAVES_SPELLS: 12
        },
        range(4, 7): {
            AttackType.DEATH_RAY_POISON: 6,
            AttackType.MAGIC_WANDS: 7,
            AttackType.PARALYSIS_TURN_TO_STONE: 8,
            AttackType.DRAGON_BREATH: 10,
            AttackType.RODS_STAVES_SPELLS: 10
        },
        range(7, 10): {
            AttackType.DEATH_RAY_POISON: 4,
            AttackType.MAGIC_WANDS: 5,
            AttackType.PARALYSIS_TURN_TO_STONE: 6,
            AttackType.DRAGON_BREATH: 7,
            AttackType.RODS_STAVES_SPELLS: 8
        },
        range(10, 13): {
            AttackType.DEATH_RAY_POISON: 2,
            AttackType.MAGIC_WANDS: 3,
            AttackType.PARALYSIS_TURN_TO_STONE: 4,
            AttackType.DRAGON_BREATH: 4,
            AttackType.RODS_STAVES_SPELLS: 6
        },
    },
}

saving_throws[CharacterClassType.HALFLING] = saving_throws[CharacterClassType.DWARF].copy()

saving_throws[CharacterClassType.COMMONER] = {
    level_range: {save: val + 2 for save, val in values.items()}
    for level_range, values in saving_throws[CharacterClassType.FIGHTER].items()
    if level_range.stop <= 11
}
