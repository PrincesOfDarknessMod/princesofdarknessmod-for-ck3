
nightify_header = """
  ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗██╗███████╗██╗   ██╗
  ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝██║██╔════╝╚██╗ ██╔╝
  ██╔██╗ ██║██║██║  ███╗███████║   ██║   ██║█████╗   ╚████╔╝ 
  ██║╚██╗██║██║██║   ██║██╔══██║   ██║   ██║██╔══╝    ╚██╔╝  
  ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██║██║        ██║   
  ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝╚═╝        ╚═╝   
╔╗╔═╗╔══════════════════════════════════════════════════╗╔═╗╔╗
║║║ ║║   1-CLICK NIGHTIFICATION FOR EVENT BACKGROUNDS   ║║ ║║║
╚╝╚═╝╚══════════════════════════════════════════════════╝╚═╝╚╝
"""

##### USAGE:
#
# You need Python and have installed pyparsing via pip.
# Open a command line in this folder and run:
# python .\nightify.py .\01_event_backgrounds.txt
# (or whatever the name of the input file is, assuming it's in the same folder)
#
# The input file needs to be a VANILLA event background file.
# e.g. this one: common\event_backgrounds\01_event_backgrounds.txt
#
# Doing this for the first time on a new DLC will probably result in errors.
# Take note of the missing illustrations, then add them to nightify_shared.py.
# Add illustrations that already take place at night/indoors to do_not_nightify.
# Append missing daytime illustrations to nightify_illustrations, with a fitting nighttime version.
# (There are already some example placeholder illustrations at the end of that dictionary.)
# Run this script again and it should work.
#
# To see all valid arguments, run the script with the argument -h


import nightify_shared
import argparse
import pyparsing as pp
import re
import os
from copy import deepcopy


launch_options = argparse.ArgumentParser(description='1-click nightification for CK3 event backgrounds')
launch_options.add_argument("-o", "--output", help="Specify output file name", action="store", metavar="output_file")
launch_options.add_argument("-a", "--activity", help="Use activity scopes for nighttime triggers (scope:host)", action="store_true")
launch_options.add_argument("-s", "--scripted", help="Use for parsing scripted_illustration files instead of event backgrounds", action="store_true")
launch_options.add_argument("-r", "--regex", help="Use regex to replace vanilla religion triggers (unreliable!)", action="store_true")
launch_options.add_argument("-l", "--log", help="Display verbose logs", action="store_true")
launch_options.add_argument("-p", "--pprint", help="Print the parser's raw results", action="store_true")
launch_options.add_argument("-t", "--test", help="Only test (don't write output file)", action="store_true")
launch_options.add_argument("input_file", help="Input file for nightification")
args = launch_options.parse_args()


pp.ParserElement.set_default_whitespace_chars('\r')

ck3_space    = pp.White(' \t')[...]
ck3_bigspace = pp.White(' \t\n')[...]
ck3_comment  = pp.Literal("#") + pp.Opt(pp.restOfLine)
ck3_ignore   = pp.Combine(ck3_bigspace + pp.ZeroOrMore(ck3_comment + ck3_bigspace))

ck3_word = pp.Word(pp.alphanums + "_-.:!@")
ck3_operator = pp.Combine(ck3_space + pp.Word("=!?<>", max=2) + ck3_space)
# ck3_string = pp.Group(
#     pp.Literal("\"") + pp.Word(pp.alphanums + "_-.:/") + pp.Literal("\"")
# )
ck3_string = pp.Group(
    pp.Literal("\"") + pp.Word(pp.printables, exclude_chars="\"\n") + pp.Literal("\"")
)

ck3_statement = pp.Forward()
ck3_block = pp.Forward()

ck3_statement <<= pp.Group(
    ck3_word + ck3_operator + (ck3_string | ck3_word | ck3_block)
)

ck3_block <<= pp.Group(
    pp.Literal("{") + ck3_ignore + pp.ZeroOrMore(ck3_statement + ck3_ignore) + pp.Literal("}")
)

ck3_file = ck3_ignore + pp.OneOrMore(ck3_statement + ck3_ignore)
ck3_file.parse_with_tabs()


with open(args.input_file, 'r', encoding='utf_8_sig') as file:
    file_content = file.read()


# First pass: Simple text substitution for religion triggers
# TODO: make the regex work reliably
if args.regex:
    for trigger in nightify_shared.replace_religion_triggers.keys():
        file_content = re.sub(trigger, nightify_shared.replace_religion_triggers[trigger], file_content)


results = ck3_file.parse_string(file_content)
results_list = results.as_list()

output_list = deepcopy(results_list)


#####   PARSER EXPLANATION   #####
#
# The parser outputs a nested List that divides the entire file into "Whitespace" and "Statements".
#
# "Whitespace" is a String that contains an uninterrupted block of ignored tokens.
# (meaning both whitespace and code comments)
#
# "Statements" are the basic building blocks of CK3 script. Each Statement is a List made of 3 Strings:
# statement[0]: The key/trigger/effect/scope
# statement[1]: An operator surrounded by whitespace
# statement[2]: A second key or value
#
# So a Statement might look like this:
# ["scope:vassal"," ?= ","root.father"]
#
# Instead of the second key, statement[2] might also be one of two Lists:
#   - A "CK3_String", which is made of two quotation marks and the string's content
#     Example: ["\"","environment_event_alley","\""]
#   - A "Block", which is made of two curly brackets and an arbitrary number of Statements and Whitespace
#     Example: ["{"," ",["has_building_gfx"," = ","iberian_building_gfx"]," ","}"]
#
# Launch the script with the -p argument to show the parser's raw output.
#
# For more info on pyparsing, see the docs:
# https://pyparsing-docs.readthedocs.io/en/latest/HowToUsePyparsing.html

if args.pprint: results.pprint()


def     formatRed(text): return "\033[91m{}\033[00m".format(text)
def  formatOrange(text): return "\033[33m{}\033[00m".format(text)
def    formatCyan(text): return "\033[94m{}\033[00m".format(text)
def    formatBlue(text): return "\033[34m{}\033[00m".format(text)
def formatMagenta(text): return "\033[95m{}\033[00m".format(text)
def   formatGreen(text): return "\033[92m{}\033[00m".format(text)
def    formatGrey(text): return "\033[90m{}\033[00m".format(text)


added_backgrounds = 0
changed_vanilla_environments = 0

parse_errors = []
unknown_bgs  = []
unknown_environments = []

if args.activity:
    night_trigger = nightify_shared.night_trigger_activity
elif args.scripted:
    night_trigger = nightify_shared.night_trigger_scripted
else:
    night_trigger = nightify_shared.night_trigger

night_trigger_new_block = "trigger = { " + night_trigger + " }"

scripted_illustration = args.scripted


# REPLACEMENTS
for bg_index, background in enumerate(results_list):
    if not isinstance(background, list): # if an entry isn't a list it means it's whitespace or a comment
        continue

    # skip religion_interior in ingame.txt since its root scope type isn't character
    # (leads to errors when using POD_day_background_trigger)
    if background[0] == "religion_interior":
        continue

    output_sbg_index = -1 # make sure to start at 0 in the loop

    for sbg_index, subbackground in enumerate(background[2]): # element 2 of the statement array is the actual block
        output_sbg_index += 1

        if not isinstance(subbackground, list):
            continue
        
        if (not scripted_illustration and subbackground[0] != "background") or (scripted_illustration and subbackground[0] != "texture"):
            continue

        log_string = "Found a replacement for subbackground (" + formatOrange(str(sbg_index)) + ") of "
        log_string += formatMagenta(background[0]) + " (" + formatOrange(str(bg_index)) + "):\n"

        found_trigger = False
        replace_bg = False

        for st_index, statement in enumerate(subbackground[2]):
            if not isinstance(statement, list):
                continue
            
            match statement[0]:
                # make sure this works with activity files too
                case "reference" | "texture":
                    reference_index = st_index
                    bg_reference = statement[2][1]

                    if scripted_illustration or bg_reference.startswith(nightify_shared.bg_path_prefix):
                        if scripted_illustration:
                            bg_path = bg_reference
                        else:
                            bg_path = bg_reference.removeprefix(nightify_shared.bg_path_prefix)
                        
                        # This is where we look up nighttime illustrations in our dictionary
                        if bg_path in nightify_shared.do_not_nightify:
                            log_string += formatGrey("\t" + bg_path + " is already a nighttime illustration. Skipping it")

                        elif bg_path in nightify_shared.nightify_illustrations.keys():
                            nightified_bg = nightify_shared.nightify_illustrations[bg_path]

                            log_string += "\t" + formatGreen(bg_path) + " has a nighttime version: "
                            log_string += formatCyan(nightified_bg) + "\n"

                            if nightified_bg in nightify_shared.nightify_environments.keys():
                                nightified_environment = nightify_shared.nightify_environments[nightified_bg]
                                log_string += "\t" + formatCyan(nightified_bg) + " has a fitting portrait environment: "
                                log_string += formatBlue(nightified_environment) + "\n"
                                replace_bg = True
                            else:
                                if not scripted_illustration and nightified_bg not in unknown_environments:
                                    unknown_environments.append(nightified_bg)

                        elif bg_path.partition("/")[0] in nightify_shared.ignore_folders:
                            log_string += formatGrey("\t" + bg_path + " is in a blacklisted folder. Skipping it")

                        else:
                            if bg_path not in unknown_bgs:
                                unknown_bgs.append(bg_path)

                    elif bg_reference.startswith(nightify_shared.video_path_prefix):
                        log_string += formatGrey("\t" + bg_reference + " is a video file. Skipping it")
                    
                    else:
                        error_string = "Subbackground at index " + str(sbg_index) + " of background " + background[0]
                        error_string += " has an unexpected reference: " + bg_reference + " (path doesn't start with gfx/interface/illustrations/)"
                        error_string = formatRed(error_string)
                        parse_errors.append(error_string)
                        
                case "environment":
                    environment_index = st_index
                    # Check if the vanilla portrait_environment needs changing
                    if statement[2][1] in nightify_shared.replace_vanilla_environments.keys():
                        new_vanilla_environment = nightify_shared.replace_vanilla_environments[statement[2][1]]
                        output_list[bg_index][2][output_sbg_index][2][environment_index][2][1] = new_vanilla_environment
                        changed_vanilla_environments += 1

                case "trigger":
                    trigger_index = st_index
                    found_trigger = True
                
                case "ambience":
                    ambience_index = st_index

        if replace_bg:
            subbackground_copy = deepcopy(subbackground)

            sbg_whitespace_copy = output_list[bg_index][2][output_sbg_index-1]
            output_list[bg_index][2].insert(output_sbg_index-1, sbg_whitespace_copy)
            output_list[bg_index][2].insert(output_sbg_index, subbackground_copy)

            if found_trigger:
                whitespace_copy = output_list[bg_index][2][output_sbg_index][2][trigger_index][2][1]
                output_list[bg_index][2][output_sbg_index][2][trigger_index][2].insert(1, whitespace_copy)
                output_list[bg_index][2][output_sbg_index][2][trigger_index][2].insert(2, night_trigger)

                log_string += formatRed("\t(has existing trigger)\n")
            else:
                whitespace_copy = output_list[bg_index][2][output_sbg_index][2][1]
                output_list[bg_index][2][output_sbg_index][2].insert(1, whitespace_copy)
                output_list[bg_index][2][output_sbg_index][2].insert(2, night_trigger_new_block)

                reference_index   += 2
                if not scripted_illustration:
                    environment_index += 2
                    ambience_index    += 2

                log_string += formatGrey("\t(no existing trigger)\n")
            
            if scripted_illustration:
                output_list[bg_index][2][output_sbg_index][2][reference_index][2][1] = nightified_bg
            else:
                output_list[bg_index][2][output_sbg_index][2][reference_index][2][1] = nightify_shared.bg_path_prefix + nightified_bg
                output_list[bg_index][2][output_sbg_index][2][environment_index][2][1] = nightified_environment

                if nightified_bg in nightify_shared.nightify_ambience.keys():
                    output_list[bg_index][2][output_sbg_index][2][ambience_index][2][1] = nightify_shared.nightify_ambience[nightified_bg]

            output_sbg_index += 2

            added_backgrounds += 1

            if args.log:
                print(log_string)



# this is crucial. trust me bro
def format_header(text):
    output_text = ""
    line_counter = 1
    for char in text:
        match char:
            case "█":
                output_text += "\033[94m{}\033[00m".format(char) # cyan
            case "═" | "║" | "╔" | "╗" | "╝" | "╚":
                if line_counter <= 7:
                    output_text += "\033[34m{}\033[00m".format(char) # dark blue
                else:
                    output_text += "\033[94m{}\033[00m".format(char) # cyan
            case char if char.isalnum() or char == "-":
                output_text += "\033[33m{}\033[00m".format(char) # orange
            case "\n":
                output_text += char
                line_counter += 1
            case _:
                output_text += char

    return output_text

print(format_header(nightify_header))


if len(parse_errors) > 0:
    print("\n".join(parse_errors))
    print() # line break

if len(unknown_bgs) > 0:
    unknown_bgs.sort()
    print(formatRed("ERROR:") + " Several unknown backgrounds were found.")
    print("Add these to the " + formatOrange("nightify_illustrations") + " Dictionary in nightify_shared.py:")
    print("(If these already take place at night or indoors, add them to the " + formatOrange("do_not_nightify") + " List instead)")
    for bg in unknown_bgs:
        print("\t" + formatRed(bg))
    print() # line break

if len(unknown_environments) > 0:
    unknown_environments.sort()
    print(formatRed("ERROR:") + " Several nighttime backgrounds don't have a portrait_environment.")
    print("Add these to the " + formatOrange("nightify_environments") + " Dictionary in nightify_shared.py:")
    for env in unknown_environments:
        print("\t" + formatRed(env))
    print() # line break


def recursive_concat(input_list):
    output_string = ""
    for element in input_list:
        if not isinstance(element, list):
            output_string += element
        else:
            output_string += recursive_concat(element)
    return output_string

file_header = """##### THIS FILE WAS AUTO-GENERATED
##### Refer to the 1-click nightification script for more information:
##### /dev/scripts/python/nightify/nightify.py

"""

output_folder = "./outputs/"

if args.output == None:
    output_path = output_folder + os.path.basename(args.input_file)
else:
    output_path = output_folder + args.output

if len(parse_errors) == 0 and len(unknown_bgs) == 0 and len(unknown_environments) == 0:
    print(formatGreen("Success!"))
    print(formatCyan(str(added_backgrounds)) + " nighttime backgrounds were added.")
    print(formatCyan(str(changed_vanilla_environments)) + " vanilla portrait environments were changed.")
    print()

    # flatten the list
    file_output = file_header + recursive_concat(output_list)

    if args.test:
        print("No output file was written because of the --test argument.")
        print()
    else:
        with open(output_path, 'w', encoding='utf_8_sig') as f:
            f.write(file_output)

        print("Wrote the output to " + formatOrange(output_path))
        print()

    # Checking for religions
    for vanilla_religion in nightify_shared.vanilla_religion_warnings.keys():
        if file_output.find(vanilla_religion) != -1:
            warning_string = formatRed("Warning:") + " The output contains at least one reference to the vanilla religion "
            warning_string += formatOrange(vanilla_religion)
            warning_string += "\n         Make sure to add or replace it with the PoD trigger "
            warning_string += formatGreen(nightify_shared.vanilla_religion_warnings[vanilla_religion])
            print(warning_string)
    
    if file_output.find(nightify_shared.nomadic_gov_warning) != -1:
        warning_string = formatRed("Warning:") + " The output contains at least one reference to the vanilla government flag "
        warning_string += formatOrange(nightify_shared.nomadic_gov_warning)
        warning_string += "\n         Make sure to add or replace it with the PoD trigger "
        warning_string += formatGreen(nightify_shared.nomadic_gov_trigger)
        print(warning_string)
    
    if file_output.find(nightify_shared.nomadic_tier_warning) != -1:
        warning_string = formatRed("Warning:") + " The output contains at least one reference to the vanilla nomad law "
        warning_string += formatOrange(nightify_shared.nomadic_tier_warning)
        warning_string += "\n         Make sure to add or replace it with a trigger that works for feudal governments: "
        warning_string += formatGreen(nightify_shared.nomadic_tier_trigger)
        print(warning_string)
    
    if file_output.find(nightify_shared.gruesome_festival_warning) != -1:
        warning_string = formatRed("Warning:") + " The output contains at least one reference to the Gruesome Festival background "
        warning_string += formatOrange(nightify_shared.gruesome_festival_warning)
        warning_string += "\n         Make sure to also add the Colosseum background for Rome:\n"
        warning_string += formatGreen(nightify_shared.gruesome_festival_sbg)
        warning_string += "\n(Replace " + formatOrange("reference") + " with " + formatOrange("texture")
        warning_string += " if editing the activity file)"
        print(warning_string)
    
    print()

else:
    print(formatRed("Since there were errors, no output file was written."))
    print() # line break
