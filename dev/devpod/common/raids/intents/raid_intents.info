A raid intent is something a raiding army has to determine what to do with raid loot when returning, and 
adding special modifiers while raiding.

NOTE: 
The first available intent will be set to the default for characters
== Structure ==

my_intent = {

	# Brief : on_return_raid_loot
	# on_return_raid_loot triggers when returning raid loot
	# scope:raid_loot is the loot that you gained from the raid
	# scope:raider is the character owning the raiding army

	on_return_raid_loot = {
		scope:raider = {
			add_gold = scope:raid_loot
		}
	}

	# Brief: modifier
	# The modifier will apply a modifier to the ARMY that's raiding - 
	# not the character. This will then be added together with the characters modifier.
	# The following modifiers are available for raid intents:
	# raid_speed
	# movement_speed_land_raiding
	# hostile_county_attrition_raiding

	modifier = { 
		raid_speed = 0.2 
		movement_speed_land_raiding = 0
		hostile_county_attrition_raiding = 0
	}

	# Brief: ai_will_do
	# Scripted value to determine if the AI will select this intent or not
	# Selects the weighted random intent based on their score
	#
	# root = character picking this intent

	ai_will_do = {
		value = 100
	}

	# Brief: is_shown
	# Scripted value to determine if this intent should be shown in the selection
	# i.e this should maybe be false if it's about herd and your raider is a character that doesn't use herd.
	#
	# root = character owning the raiding army with this intent

	is_shown = {}

	# Brief: is_shown
	# Scripted value to determine if this intent should be enabled in the selection
	#
	# root = character picking this intent

	is_valid = {}

	# Brief: on_invalidated
	# effect to run on invalidated intent
	#
	# root = army who picked this intent
	# scope:raider is the character owning the raiding army
	
	on_invalidated = {
		scope:raider = {
		}
	}

}