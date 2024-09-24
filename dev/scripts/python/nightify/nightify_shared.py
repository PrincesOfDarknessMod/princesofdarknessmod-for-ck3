
night_trigger = "POD_day_background_trigger = no"

bg_path_prefix = "gfx/interface/illustrations/"
video_path_prefix = "gfx/interface/video/"

ignore_folders = [
	"activity_splash_screens",
	"event_story",
	"holding_types",
	"interior", # TODO: change these too?
	"regional_patterns",
	"terrain_types", # TODO: change these too?
	"tournament_contest_illustrations", # TODO: change these too?
]


# These illustrations don't have a nighttime version
# either because they already take place at night, or because they're an indoor scene with firelight
do_not_nightify = [
	"blank.dds",

	# Event backgrounds
	"event_scenes/alley.dds",
	"event_scenes/bp1_bonfire.dds",
	"event_scenes/bp1_corridor_indian_night.dds",
	"event_scenes/bp1_wine_cellar.dds",
	"event_scenes/corridor.dds",
	"event_scenes/dungeon.dds",
	"event_scenes/ep2_feast_steppe.dds",
	"event_scenes/ep2_feast_sub_saharan.dds",
	"event_scenes/ep2_wedding_bedroom_mena.dds",
	"event_scenes/feast.dds",
	"event_scenes/fp1_throneroom_nontribal.dds",
	"event_scenes/fp1_throneroom_tribal.dds",
	"event_scenes/fp1_tribal_corridor.dds",
	"event_scenes/fp1_tribal_prison.dds",
	"event_scenes/fp1_tribal_temple.dds",
	"event_scenes/fp1_viking_feast.dds",
	"event_scenes/fp2_corridor_night.dds",
	"event_scenes/fp3_courtyard_night.dds",
	"event_scenes/fp4_catacombs.dds",
	"event_scenes/fp4_condemned_village.dds",
	"event_scenes/fp4_funeral_pyre.dds",
	"event_scenes/fp4_physician_tribal.dds",
	"event_scenes/study_physician.dds",
	"event_scenes/tavern.dds",
	"event_scenes/test_event.dds",

	# Activity backgrounds
	"activity_backgrounds/activity_feast.dds",
	"activity_backgrounds/activity_gruesome_festival.dds",
	"activity_backgrounds/bp1_bonfire.dds",
	"activity_backgrounds/fp1_tribal_temple.dds",

	# Grand activity assets
	"activity_backgrounds/tournament_terrain_europe_farmland.dds",
	"activity_backgrounds/tournament_terrain_jungle.dds",
	"activity_backgrounds/tournament_terrain_mena.dds",

	# Character view
	"character_view/bonfire.dds",
	"character_view/fp1_throneroom_nontribal.dds",
	"character_view/fp1_throneroom_tribal.dds",
	"character_view/tavern.dds",

	# ROADS TO POWER (TODO: check if these fit)
	"event_scenes/ep3_campfire.dds",
	"event_scenes/ep3_constantinople_riot.dds",
	"event_scenes/ep3_feast_byzantine.dds",
	"event_scenes/ep3_military_tent.dds",
	"event_scenes/ep3_relaxing_tent.dds",

	# PoD backgrounds
	"activity_backgrounds/activity_colosseum.dds",
]


# Daytime illustrations keyed to their nighttime versions
# An error will be thrown if a texture is neither in this dictionary nor the do_not_nightify array
nightify_illustrations = {
	# Event backgrounds
	"event_scenes/alley_day.dds":					"event_scenes/alley.dds", # vanilla nighttime illustration
	"event_scenes/armory.dds":						"event_scenes/armory_night.dds",
	"event_scenes/battlefield.dds":					"event_scenes/battlefield_night.dds",
	"event_scenes/bedchamber.dds":					"event_scenes/bedchamber_night.dds",
	"event_scenes/bp1_corridor_indian_day.dds":		"event_scenes/bp1_corridor_indian_night.dds", # vanilla nighttime illustration
	"event_scenes/bp1_courtyard_mena.dds":			"event_scenes/fp2_courtyard_night.dds", # duplicate image in vanilla?
	"event_scenes/bp1_garden_mena_day.dds":			"event_scenes/fp2_garden_night.dds", # duplicate image in vanilla?
	"event_scenes/bp1_plains.dds":					"event_scenes/pod_nightlandscape5.dds",
	"event_scenes/bp1_relaxing_room_mena.dds":		"event_scenes/fp2_relaxing_room_night.dds", # duplicate image in vanilla?
	"event_scenes/bp2_courtyard.dds":				"event_scenes/bp2_courtyard_night.dds",
	"event_scenes/bp2_indian_garden.dds":			"event_scenes/bp2_indian_garden_night.dds",
	"event_scenes/bp2_nursery.dds":					"event_scenes/bp2_nursery_night.dds",
	"event_scenes/bp2_study_indian.dds":			"event_scenes/bp2_study_indian_night.dds",
	"event_scenes/bp2_tavern_mena.dds":				"event_scenes/bp2_tavern_mena_night.dds",
	"event_scenes/bp2_university_mena.dds":			"event_scenes/bp2_university_mena_night.dds",
	"event_scenes/church.dds":						"event_scenes/church_night.dds",
	"event_scenes/corridor_day.dds":				"event_scenes/corridor.dds", # vanilla nighttime illustration
	"event_scenes/councilchamber.dds":				"event_scenes/councilchamber_night.dds",
	"event_scenes/courtyard.dds":					"event_scenes/courtyard_night.dds",
	"event_scenes/docks.dds":						"event_scenes/docks_night.dds",
	"event_scenes/drylands.dds":					"event_scenes/drylands_night.dds",
	"event_scenes/ep2_holysite_indian.dds":			"event_scenes/ep2_holysite_indian_night.dds",
	"event_scenes/ep2_holysite_jerusalem.dds":		"event_scenes/ep2_holysite_jerusalem_night.dds",
	"event_scenes/ep2_holysite_mecca.dds":			"event_scenes/ep2_holysite_mecca_night.dds",
	"event_scenes/ep2_holysite_mena.dds":			"event_scenes/ep2_holysite_mena_night.dds",
	"event_scenes/ep2_holysite_western.dds":		"event_scenes/ep2_holysite_western_night.dds",
	"event_scenes/ep2_hunt_cave_entrance.dds":		"event_scenes/ep2_hunt_cave_entrance_night.dds",
	"event_scenes/ep2_hunt_falconry_mews.dds":		"event_scenes/ep2_hunt_falconry_mews_night.dds",
	"event_scenes/ep2_hunt_foggy_forest.dds":		"event_scenes/ep2_hunt_foggy_forest_night.dds",
	"event_scenes/ep2_hunt_generic.dds":			"event_scenes/ep2_hunt_generic_night.dds",
	"event_scenes/ep2_hunt_poachers_camp.dds":		"event_scenes/ep2_hunt_poachers_camp_night.dds",
	"event_scenes/ep2_hunt_snowy_forest.dds":		"event_scenes/ep2_hunt_snowy_forest_night.dds",
	"event_scenes/forest_pine.dds":					"event_scenes/forest_pine_night.dds",
	"event_scenes/fp2_corridor_day.dds":			"event_scenes/fp2_corridor_night.dds", # vanilla nighttime illustration
	"event_scenes/fp2_courtyard.dds":				"event_scenes/fp2_courtyard_night.dds",
	"event_scenes/fp2_garden.dds":					"event_scenes/fp2_garden_night.dds",
	"event_scenes/fp2_prison.dds":					"event_scenes/fp2_prison_night.dds",
	"event_scenes/fp2_relaxing_room.dds":			"event_scenes/fp2_relaxing_room_night.dds",
	"event_scenes/fp2_temple.dds":					"event_scenes/fp2_temple_night.dds",
	"event_scenes/fp2_throneroom.dds":				"event_scenes/fp2_throneroom_night.dds",
	"event_scenes/fp3_bathhouse.dds":				"event_scenes/fp3_bathhouse_night.dds",
	"event_scenes/fp3_cave.dds":					"event_scenes/fp3_cave_night.dds",
	"event_scenes/fp3_docks.dds":					"event_scenes/fp3_docks_night.dds",
	"event_scenes/fp3_temple.dds":					"event_scenes/fp3_temple_night.dds",
	"event_scenes/fp3_throneroom.dds":				"event_scenes/fp3_throneroom_night.dds",
	"event_scenes/fp4_legendary_battlefield.dds":	"event_scenes/fp4_legendary_battlefield_night.dds",
	"event_scenes/fp4_legendary_oasis.dds":			"event_scenes/fp4_legendary_oasis_night.dds",
	"event_scenes/fp4_legendary_spring.dds":		"event_scenes/fp4_legendary_spring_night.dds",
	"event_scenes/fp4_study_physician_indian.dds":	"event_scenes/fp4_study_physician_indian_night.dds",
	"event_scenes/fp4_study_physician_mena.dds":	"event_scenes/fp4_study_physician_mena_night.dds",
	"event_scenes/gallows.dds":						"event_scenes/gallows_night.dds",
	"event_scenes/garden.dds":						"event_scenes/garden_night.dds",
	"event_scenes/genericcamp.dds":					"event_scenes/genericcamp_night.dds",
	"event_scenes/market_east.dds":					"event_scenes/market_east_night.dds",
	"event_scenes/market_tribal.dds":				"event_scenes/market_tribal_night.dds",
	"event_scenes/market_west.dds":					"event_scenes/market_west_night.dds",
	"event_scenes/mosque.dds":						"event_scenes/mosque_night.dds",
	"event_scenes/raid_burning.dds":				"event_scenes/raid_burning_night.dds",
	"event_scenes/sittingroom.dds":					"event_scenes/sittingroom_night.dds",
	"event_scenes/study.dds":						"event_scenes/study_night.dds",
	"event_scenes/temple.dds":						"event_scenes/temple_night.dds",
	"event_scenes/throneroom_east.dds":				"event_scenes/throneroom_east_night.dds",
	"event_scenes/throneroom_india.dds":			"event_scenes/throneroom_india_night.dds",
	"event_scenes/throneroom_mediterranean.dds":	"event_scenes/throneroom_mediterranean_night.dds",
	"event_scenes/throneroom_tribal.dds":			"event_scenes/throneroom_tribal_night.dds",
	"event_scenes/throneroom_west.dds":				"event_scenes/throneroom_west_night.dds",

	# Activity backgrounds
	"activity_backgrounds/alley_day.dds":				"event_scenes/alley.dds", # vanilla nighttime illustration
	"activity_backgrounds/bp1_garden_mena_day.dds":		"event_scenes/fp2_garden_night.dds", # duplicate image in vanilla?
	"activity_backgrounds/contest_bg_archery.dds":		"activity_backgrounds/contest_bg_archery_night.dds",
	"activity_backgrounds/contest_bg_boardgames.dds":	"activity_backgrounds/contest_bg_boardgames_night.dds",
	"activity_backgrounds/contest_bg_horseracing.dds":	"activity_backgrounds/contest_bg_horseracing_night.dds",
	"activity_backgrounds/contest_bg_melee.dds":		"activity_backgrounds/contest_bg_melee_night.dds",
	"activity_backgrounds/ep2_holysite_indian.dds":		"event_scenes/ep2_holysite_indian_night.dds",
	"activity_backgrounds/ep2_holysite_jerusalem.dds":	"event_scenes/ep2_holysite_jerusalem_night.dds",
	"activity_backgrounds/ep2_holysite_mecca.dds":		"event_scenes/ep2_holysite_mecca_night.dds",
	"activity_backgrounds/ep2_holysite_mena.dds":		"event_scenes/ep2_holysite_mena_night.dds",
	"activity_backgrounds/ep2_holysite_western.dds":	"event_scenes/ep2_holysite_western_night.dds",
	"activity_backgrounds/ep2_hunt_cave_entrance.dds":	"event_scenes/ep2_hunt_cave_entrance_night.dds",
	"activity_backgrounds/ep2_hunt_falconry_mews.dds":	"event_scenes/ep2_hunt_falconry_mews_night.dds",
	"activity_backgrounds/ep2_hunt_foggy_forest.dds":	"event_scenes/ep2_hunt_foggy_forest_night.dds",
	"activity_backgrounds/ep2_hunt_generic.dds":		"event_scenes/ep2_hunt_generic_night.dds",
	"activity_backgrounds/ep2_hunt_poachers_camp.dds":	"event_scenes/ep2_hunt_poachers_camp_night.dds",
	"activity_backgrounds/ep2_hunt_snowy_forest.dds":	"event_scenes/ep2_hunt_snowy_forest_night.dds",
	"activity_backgrounds/fp2_garden.dds":				"event_scenes/fp2_garden_night.dds",
	"activity_backgrounds/fp2_temple.dds":				"event_scenes/fp2_temple_night.dds",
	"activity_backgrounds/garden.dds":					"event_scenes/garden_night.dds",
	"activity_backgrounds/temple.dds":					"event_scenes/temple_night.dds",

	# Big illustrations
	"event_story/fp4_heroic_legend.dds":	"event_story/fp4_heroic_legend_night.dds",
	"event_story/fp4_black_death.dds":		"event_story/fp4_black_death_night.dds",

	# Character view
	"character_view/courtyard_mena.dds":			"event_scenes/fp2_courtyard_night.dds",
	"character_view/docks.dds":						"event_scenes/market_tribal_night.dds",
	"character_view/fp2_iberian.dds":				"event_scenes/fp2_relaxing_room_night.dds",
	"character_view/fp2_throneroom_iberian.dds":	"event_scenes/fp2_throneroom_night.dds",
	"character_view/india.dds":						"character_view/india_night.dds",
	"character_view/mediterranean.dds":				"character_view/mediterranean_night.dds",
	"character_view/throneroom_east.dds":			"character_view/throneroom_east_night.dds",
	"character_view/throneroom_india.dds":			"event_scenes/throneroom_india_night.dds",
	"character_view/throneroom_mediterranean.dds":	"event_scenes/throneroom_mediterranean_night.dds",
	"character_view/throneroom_tribal.dds":			"event_scenes/throneroom_tribal_night.dds",
	"character_view/throneroom_west.dds":			"event_scenes/throneroom_west_night.dds",
	"character_view/mena.dds":						"character_view/mena_night.dds",
	"character_view/west.dds":						"character_view/west_night.dds",

	# This reference is a vanilla bug from 1.12.4, delete later if it's no longer in ingame.txt
	"event_scenes/ep2_events_generic_hunt.dds":		"event_scenes/ep2_hunt_generic_night.dds",


	##########################
	####### Duplicates #######
	##########################
	
	# Event backgrounds
	"event_scenes/bp1_desert.dds":			"event_scenes/pod_desert_night.dds",
	"event_scenes/desert.dds":				"event_scenes/pod_desert_night.dds",
	"event_scenes/ep2_travel_desert.dds":	"event_scenes/pod_desert_night.dds",

	"event_scenes/bp1_hills.dds":			"event_scenes/pod_alamut.dds",
	"event_scenes/ep2_travel_hills.dds":	"event_scenes/pod_alamut.dds",

	"event_scenes/bp1_jungle.dds":					"event_scenes/pod_forest_night.dds",
	"event_scenes/forest.dds":						"event_scenes/pod_forest_night.dds",
	"activity_backgrounds/wilderness_forest.dds":	"event_scenes/pod_forest_night.dds",
	
	"event_scenes/ep2_travel_farm.dds":		"event_scenes/farms_night.dds",
	"event_scenes/farms.dds":				"event_scenes/farms_night.dds",
	
	"event_scenes/ep2_travel_steppe.dds":	"event_scenes/steppe_night.dds",
	"event_scenes/steppe.dds":				"event_scenes/steppe_night.dds",
	
	"event_scenes/ep2_travel_mountains.dds":	"event_scenes/mountains_night.dds",
	"event_scenes/mountains.dds":				"event_scenes/mountains_night.dds",
	
	"event_scenes/fp1_ocean.dds":				"event_scenes/pod_sunless_sea.dds",
	"event_scenes/fp1_ocean_norse.dds":			"event_scenes/pod_sunless_sea.dds",

	# Activity backgrounds
	"activity_backgrounds/contest_archery_fail.dds":	"activity_backgrounds/contest_archery_fail.dds",
	"activity_backgrounds/contest_archery_neutral.dds":	"activity_backgrounds/contest_archery_fail.dds",
	"activity_backgrounds/contest_archery_win.dds":		"activity_backgrounds/contest_archery_fail.dds",


	####################################################################################
	####### TODO: placeholder illustrations in case no nightified version exists #######
	####################################################################################
	
	# Event backgrounds
	"event_scenes/bp1_courtyard_indian.dds":			"event_scenes/fp2_courtyard_night.dds",
	"event_scenes/bp1_crossroads_inn.dds":				"event_scenes/pod_alamut.dds",
	"event_scenes/bp1_docks_tribal.dds":				"event_scenes/docks_night.dds",
	"event_scenes/bp1_kitchen_western.dds":				"event_scenes/councilchamber_night.dds",
	"event_scenes/bp1_relaxing_room_western.dds":		"event_scenes/sittingroom_night.dds",
	"event_scenes/bp1_wetlands.dds":					"event_scenes/pod_nightlandscape4.dds",
	"event_scenes/bp2_university.dds":					"event_scenes/church_night.dds",
	"event_scenes/ep2_dog_kennels.dds":					"event_scenes/ep2_hunt_generic_night.dds",
	"event_scenes/ep2_feast_indian.dds":				"event_scenes/feast.dds",
	"event_scenes/ep2_feast_mena.dds":					"event_scenes/feast.dds",
	"event_scenes/ep2_holysite_tribal.dds":				"event_scenes/pod_nightlandscape5.dds",
	"event_scenes/ep2_hunt_forest_managed.dds":			"event_scenes/ep2_hunt_generic_night.dds",
	"event_scenes/ep2_tournament_india.dds":			"activity_backgrounds/contest_bg_melee_night.dds",
	"event_scenes/ep2_tournament_mena.dds":				"activity_backgrounds/contest_bg_melee_night.dds",
	"event_scenes/ep2_tournament_tribal.dds":			"activity_backgrounds/contest_bg_melee_night.dds",
	"event_scenes/ep2_tournament_western.dds":			"activity_backgrounds/contest_bg_melee_night.dds",
	"event_scenes/ep2_travel_bridge.dds":				"event_scenes/farms_night.dds",
	"event_scenes/ep2_village_festival_western.dds":	"event_scenes/market_west_night.dds",
	"event_scenes/ep2_wedding_bedroom_indian.dds":		"event_scenes/bedchamber_night.dds", # debatable, there's dappled light from outside
	"event_scenes/ep2_wedding_ceremony_indian.dds":		"event_scenes/bp2_indian_garden_night.dds",
	"event_scenes/ep2_wedding_ceremony_mena.dds":		"event_scenes/fp2_garden_night.dds",
	"event_scenes/ep2_wedding_ceremony_western.dds":	"event_scenes/garden_night.dds",
	"event_scenes/fp1_beached_longship.dds":			"event_scenes/pod_sunless_sea.dds",
	"event_scenes/fp1_runestone.dds":					"event_scenes/pod_nightlandscape5.dds",
	"event_scenes/fp1_runestone_circle.dds":			"event_scenes/pod_nightlandscape5.dds",
	"event_scenes/fp1_steward_study.dds":				"event_scenes/throneroom_tribal_night.dds",

	# Activity backgrounds
	"activity_backgrounds/ep2_holysite_tribal.dds":		"event_scenes/pod_nightlandscape5.dds",

	# Character view
	"character_view/courtyard_indian.dds":				"event_scenes/fp2_courtyard_night.dds",
	"character_view/crossroads_inn.dds":				"event_scenes/pod_alamut.dds",

	# ROADS TO POWER (TODO: check if these fit)
	"event_scenes/desert_nomad.dds":					"event_scenes/fp4_legendary_oasis_night.dds",
	"event_scenes/desert_settlement.dds":				"event_scenes/fp4_legendary_oasis_night.dds",
	"event_scenes/ep3_adventurer_background.dds":		"event_scenes/market_tribal_night.dds",
	"event_scenes/ep3_byzantine_throne_room.dds":		"event_scenes/fp3_throneroom_night.dds",
	"event_scenes/ep3_camp_arid_terrain.dds":			"event_scenes/genericcamp_night.dds",
	"event_scenes/ep3_chariots_track.dds":				"event_scenes/fp4_legendary_spring_night.dds",
	"event_scenes/ep3_city_gate.dds":					"event_scenes/fp2_courtyard_night.dds",
	"event_scenes/ep3_constantinople.dds":				"event_scenes/bp2_courtyard_night.dds",
	"event_scenes/ep3_hagia_sophia.dds":				"event_scenes/ep2_holysite_mena_night.dds",
	"event_scenes/ep3_hippodrome_chariot_race.dds":		"event_scenes/fp4_legendary_spring_night.dds",
	"event_scenes/ep3_holysite_orthodox.dds":			"event_scenes/ep2_holysite_western_night.dds",
	"event_scenes/ep3_medi_estate.dds":					"event_scenes/fp4_study_physician_mena_night.dds",
	"event_scenes/ep3_medi_market.dds":					"event_scenes/market_east_night.dds",
	"event_scenes/ep3_medi_study.dds":					"event_scenes/study_night.dds",
	"event_scenes/ep3_relaxing_room.dds":				"event_scenes/fp2_relaxing_room_night.dds",
}


# Nighttime illustrations keyed to fitting nighttime portrait_environments
nightify_environments = {
	# Moonlit environments
	"event_scenes/bedchamber_night.dds":				"POD_environment_event_night_light",
	"event_scenes/church_night.dds":					"POD_environment_event_night_light",
	"event_scenes/courtyard_night.dds":					"POD_environment_event_night_light",
	"event_scenes/ep2_holysite_jerusalem_night.dds":	"POD_environment_event_night_light",
	"event_scenes/ep2_hunt_cave_entrance_night.dds":	"POD_environment_event_night_light",
	"event_scenes/ep2_hunt_poachers_camp_night.dds":	"POD_environment_event_night_light",
	"event_scenes/fp2_prison_night.dds":				"POD_environment_event_night_light",
	"event_scenes/fp3_throneroom_night.dds":			"POD_environment_event_night_light",
	"event_scenes/fp4_legendary_battlefield_night.dds":	"POD_environment_event_night_light",
	"event_scenes/gallows_night.dds":					"POD_environment_event_night_light",
	"event_scenes/genericcamp_night.dds":				"POD_environment_event_night_light",
	"event_scenes/market_east_night.dds":				"POD_environment_event_night_light",
	"event_scenes/market_tribal_night.dds":				"POD_environment_event_night_light",
	"event_scenes/market_west_night.dds":				"POD_environment_event_night_light",
	"event_scenes/mosque_night.dds":					"POD_environment_event_night_light",
	"event_scenes/mountains_night.dds":					"POD_environment_event_night_light",
	"event_scenes/pod_alamut.dds":						"POD_environment_event_night_light",
	"event_scenes/pod_autochthonia.dds":				"POD_environment_event_night_light",
	"event_scenes/pod_cave.dds":						"POD_environment_event_night_light",
	"event_scenes/pod_coa_caeli.dds":					"POD_environment_event_night_light",
	"event_scenes/pod_coa_cappadocian.dds":				"POD_environment_event_night_light",
	"event_scenes/pod_coa_einherjar.dds":				"POD_environment_event_night_light",
	"event_scenes/pod_coa_giovanni.dds":				"POD_environment_event_night_light",
	"event_scenes/pod_coa_lamia.dds":					"POD_environment_event_night_light",
	"event_scenes/pod_coa_nosferatu.dds":				"POD_environment_event_night_light",
	"event_scenes/pod_coa_regalis.dds":					"POD_environment_event_night_light",
	"event_scenes/pod_coa_salubri.dds":					"POD_environment_event_night_light",
	"event_scenes/pod_coa_toreador.dds":				"POD_environment_event_night_light",
	"event_scenes/pod_coa_ventrue.dds":					"POD_environment_event_night_light",
	"event_scenes/pod_forestgraveyard.dds":				"POD_environment_event_night_light",
	"event_scenes/pod_nightlandscape1.dds":				"POD_environment_event_night_light",
	"event_scenes/pod_weaver_reaches.dds":				"POD_environment_event_night_light",
	"event_scenes/pod_wolves.dds":						"POD_environment_event_night_light",
	"event_scenes/raid_burning_night.dds":				"POD_environment_event_night_light",
	"event_scenes/sittingroom_night.dds":				"POD_environment_event_night_light",
	"event_scenes/throneroom_east_night.dds":			"POD_environment_event_night_light",
	"event_scenes/throneroom_west_night.dds":			"POD_environment_event_night_light",
	"activity_backgrounds/contest_bg_melee_night.dds":	"POD_environment_event_night_light",
	"event_story/fp4_black_death_night.dds":			"POD_environment_event_night_light",

	# Dark as balls
	"event_scenes/battlefield_night.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/bp2_courtyard_night.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/bp2_indian_garden_night.dds":				"POD_environment_event_night_deepblue",
	"event_scenes/bp2_tavern_mena_night.dds":				"POD_environment_event_night_deepblue",
	"event_scenes/bp2_university_mena_night.dds":			"POD_environment_event_night_deepblue",
	"event_scenes/docks_night.dds":							"POD_environment_event_night_deepblue",
	"event_scenes/drylands_night.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/ep2_holysite_indian_night.dds":			"POD_environment_event_night_deepblue",
	"event_scenes/ep2_holysite_mecca_night.dds":			"POD_environment_event_night_deepblue",
	"event_scenes/ep2_holysite_mena_night.dds":				"POD_environment_event_night_deepblue",
	"event_scenes/ep2_holysite_tribal_night.dds":			"POD_environment_event_night_deepblue",
	"event_scenes/ep2_hunt_falconry_mews_night.dds":		"POD_environment_event_night_deepblue",
	"event_scenes/ep2_hunt_foggy_forest_night.dds":			"POD_environment_event_night_deepblue",
	"event_scenes/ep2_hunt_generic_night.dds":				"POD_environment_event_night_deepblue",
	"event_scenes/ep2_hunt_snowy_forest_night.dds":			"POD_environment_event_night_deepblue",
	"event_scenes/ep2_travel_bridge.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/farms_night.dds":							"POD_environment_event_night_deepblue",
	"event_scenes/forest_pine_night.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/fp2_courtyard_night.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/fp2_relaxing_room_night.dds":				"POD_environment_event_night_deepblue",
	"event_scenes/fp3_bathhouse_night.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/fp3_cave_night.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/fp3_docks_night.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/fp3_temple_night.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/fp4_legendary_oasis_night.dds":			"POD_environment_event_night_deepblue",
	"event_scenes/fp4_legendary_spring_night.dds":			"POD_environment_event_night_deepblue",
	"event_scenes/garden_night.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/pod_coa_anda.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/pod_coa_banu_haqim.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/pod_coa_bestiae.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/pod_coa_danava.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/pod_coa_gangrel.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/pod_coa_nagaraja.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/pod_coa_osiris.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/pod_coa_ravnos.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/pod_coa_setite.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/pod_desert_night.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/pod_forest_night.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/pod_nightlandscape2.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/pod_nightlandscape5.dds":					"POD_environment_event_night_deepblue",
	"event_scenes/steppe_night.dds":						"POD_environment_event_night_deepblue",
	"event_scenes/study_night.dds":							"POD_environment_event_night_deepblue",
	"event_scenes/temple_night.dds":						"POD_environment_event_night_deepblue",
	"activity_backgrounds/contest_bg_archery_night.dds":	"POD_environment_event_night_deepblue",
	"event_story/fp4_heroic_legend_night.dds":				"POD_environment_event_night_deepblue",

	# Greenish
	"event_scenes/fp1_ocean.dds":					"POD_environment_event_night_deepgreen",
	"event_scenes/pod_dark_kingdom_of_jade.dds":	"POD_environment_event_night_deepgreen",
	"event_scenes/pod_sunless_sea.dds":				"POD_environment_event_night_deepgreen",
	"event_scenes/pod_wyrm_reaches.dds":			"POD_environment_event_night_deepgreen",

	# Purpleish
	"event_scenes/bp2_nursery_night.dds":						"POD_environment_event_night_purple",
	"event_scenes/bp2_study_indian_night.dds":					"POD_environment_event_night_purple",
	"event_scenes/councilchamber_night.dds":					"POD_environment_event_night_purple",
	"event_scenes/ep2_holysite_western_night.dds":				"POD_environment_event_night_purple",
	"event_scenes/fp2_courtyard_night.dds":						"POD_environment_event_night_purple",
	"event_scenes/fp2_garden_night.dds":						"POD_environment_event_night_purple",
	"event_scenes/fp2_temple_night.dds":						"POD_environment_event_night_purple",
	"event_scenes/fp2_throneroom_night.dds":					"POD_environment_event_night_purple",
	"event_scenes/fp4_study_physician_indian_night.dds":		"POD_environment_event_night_purple",
	"event_scenes/fp4_study_physician_mena_night.dds":			"POD_environment_event_night_purple",
	"event_scenes/pod_cloister_crypt.dds":						"POD_environment_event_night_purple",
	"event_scenes/throneroom_india_night.dds":					"POD_environment_event_night_purple",
	"event_scenes/throneroom_mediterranean_night.dds":			"POD_environment_event_night_purple",
	"activity_backgrounds/contest_bg_horseracing_night.dds":	"POD_environment_event_night_purple",
	
	# Misc
	"event_scenes/alley.dds":								"environment_event_alley",
	"activity_backgrounds/contest_bg_boardgames_night.dds":	"environment_event_alley",

	"event_scenes/armory_night.dds":	"environment_event_armory",
	
	"event_scenes/bp1_corridor_indian_night.dds":	"environment_event_bp1_corridor_indian_night",

	"event_scenes/corridor.dds":				"environment_event_corridor",
	"event_scenes/pod_nightlandscape4.dds":		"environment_event_corridor",
	"event_scenes/throneroom_tribal_night.dds":	"environment_event_corridor",

	"event_scenes/pod_atrocity_realm.dds":	"environment_event_dungeon",
	"event_scenes/pod_coa_toreador.dds":	"environment_event_dungeon",
	"event_scenes/pod_dark_kingdom.dds":	"environment_event_dungeon",
	"event_scenes/pod_labyrinth.dds":		"environment_event_dungeon",
	"event_scenes/pod_shadowlands.dds":		"environment_event_dungeon",
	"event_scenes/pod_spires.dds":			"environment_event_dungeon",
	"event_scenes/pod_veinous_stair.dds":	"environment_event_dungeon",

	"event_scenes/feast.dds":			"environment_event_feast",
	"event_scenes/pod_wyld_reaches.dds":	"environment_event_feast",

	"event_scenes/fp2_corridor_night.dds":	"environment_event_fp2_corridor_night",

	"event_scenes/pod_coa_tremere.dds":		"environment_event_study_physician",
}


# Used when switching illustrations to their vanilla nighttime versions that have a different soundscape
nightify_ambience = {
	"event_scenes/alley.dds":						"event:/SFX/Events/Backgrounds/city_alley_night",
	"event_scenes/bp1_corridor_indian_night.dds":	"event:/SFX/Events/Backgrounds/castle_corridor_night",
	"event_scenes/fp2_corridor_night.dds":			"event:/DLC/FP2/SFX/Events/corridor_night",
	# TODO: more nighttime soundscapes? quiet alleys? landscapes with no birds?
}


# for throne room environments since those are hardcoded (thanks paradox)
replace_vanilla_environments = {
	"environment_frontend_west_main":			"POD_environment_frontend_west_main",
	"environment_frontend_india_main":			"POD_environment_frontend_india_main",
	"environment_frontend_east_main":			"POD_environment_frontend_east_main",
	"environment_frontend_mediterranean_main":	"POD_environment_frontend_mediterranean_main",
	"environment_fp1_frontend_nontribal_main":	"POD_environment_fp1_frontend_nontribal_main",
	"environment_fp1_frontend_tribal_main":		"POD_environment_fp1_frontend_tribal_main",
	"environment_frontend_tribal_main":			"POD_environment_frontend_tribal_main",
	"environment_fp2_frontend_iberian_main":	"POD_environment_fp2_frontend_iberian_main",
	"environment_fp3_frontend_iranian_main":	"POD_environment_fp3_frontend_iranian_main",

	# Roads to Power
	"environment_ep3_frontend_byzantine_main":	"POD_environment_ep3_frontend_byzantine_main",
	"environment_ep3_frontend_adventurer_main":	"POD_environment_ep3_frontend_adventurer_main",
}


# surely this regex will never break. surely
# TODO: it does break for ingame.txt. need manual checking
replace_religion_triggers = {
	"{ religion = religion:christianity_religion }":	"{ is_POD_christian_religion_trigger = yes }",
	"{ religion = religion:islam_religion }":			"{ is_POD_muslim_religion_trigger = yes }",
	"\.religion \??= religion:islam_religion":			".faith ?= { is_POD_muslim_religion_trigger = yes }",
	"{ religion = religion:zoroastrianism_religion }":	"{ is_POD_zoroastrian_religion_trigger = yes }",
	"\.religion \??= religion:zoroastrianism_religion":	".faith ?= { is_POD_zoroastrian_religion_trigger = yes }",
	"{ religion = religion:germanic_religion }":		"{ is_POD_norse_religion_trigger = yes }",
	"faith = faith:norse_pagan":						"faith = { is_POD_norse_religion_trigger = yes }",
}

vanilla_religion_warnings = {
	"religion:christianity_religion":	"is_POD_christian_religion_trigger = yes",
	"religion:islam_religion":			"is_POD_muslim_religion_trigger = yes",
	"religion:zoroastrianism_religion":	"is_POD_zoroastrian_religion_trigger = yes",
	"religion:germanic_religion":		"is_POD_norse_religion_trigger = yes",
	"faith:norse_pagan":				"is_POD_norse_religion_trigger = yes",
	"religion:hinduism_religion":		"religion:raktasadhus_religion",
	"rf_eastern":						"is_POD_eastern_religion_trigger = yes",
}

gruesome_festival_warning = "activity_backgrounds/activity_gruesome_festival.dds"

gruesome_festival_sbg = """
	background = {
		trigger = {
			scope:activity.activity_location = {
				POD_is_colosseum_location_trigger = yes
			}
		}
		reference = "gfx/interface/illustrations/activity_backgrounds/activity_colosseum.dds"
		environment = "environment_event_fp1_tribal_corridor" 
		ambience = "event:/SFX/Events/Backgrounds/city_alley_night"
	}
"""