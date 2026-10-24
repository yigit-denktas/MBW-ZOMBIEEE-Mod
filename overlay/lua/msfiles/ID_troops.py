# Bounded, read-only troop-label aid for the ZDB1 probe (task-19 roster labels).
#
# WSE2 builds `game.const.troops` from this file, so the probe can label only
# these documented roster entries. IDs are pinned to the original ZOMBIEEE
# Beta 0.4 numbering (original troop IDs 0..980 are unchanged; defenders
# 981..984 are appended by the remaster patch). A probe cannot prove an ID
# belongs to the installed module version, so labels are an observation aid:
# ids outside this file stay numeric and are counted as unknown.
#
# Native invader block 894..911 (A's native_roster_patch scans 894..911 for
# fac_kingdom_invaders). The 2012 module has duplicated invader names; a
# name->id table cannot represent a duplicate name, so later duplicates carry
# an explicit id suffix (e.g. _905). Roster classification in the summary is by
# ID range, never by label, so this ambiguity cannot change the class.
# This is NOT a game asset and must stay limited to the documented roster.
trp_invader_multiplayer_ai = 873
trp_invaderb_multiplayer_ai = 874
trp_swadian_crossbowman_multiplayer = 875
trp_swadian_sniper_multiplayer = 876
trp_swadian_infantry_multiplayer = 877
trp_swadian_man_at_arms_multiplayer = 878
trp_mercenary_horseman = 32
trp_mercenary_cavalry = 33
trp_invader1_multiplayer_ai = 894
trp_invader2_multiplayer_ai = 895
trp_invader3_multiplayer_ai = 896
trp_invader4_multiplayer_ai = 897
trp_invader5_multiplayer_ai = 898
trp_invader6_multiplayer_ai = 899
trp_invader7_multiplayer_ai = 900
trp_invader8_multiplayer_ai = 901
trp_invader_new_1_multiplayer_ai = 902
trp_invader_new_2_multiplayer_ai = 903
trp_invader_new2_8_multiplayer_ai = 904
trp_invader4_multiplayer_ai_905 = 905
trp_invader5_multiplayer_ai_906 = 906
trp_invader6_multiplayer_ai_907 = 907
trp_invader_new_3_multiplayer_ai = 908
trp_invader_new_4_multiplayer_ai = 909
trp_invader7_multiplayer_ai_910 = 910
trp_invader8_multiplayer_ai_911 = 911
trp_zdr_commando_bot = 981
trp_zdr_sniper_bot = 982
trp_zdr_scout_bot = 983
trp_zdr_lumberjack_bot = 984
