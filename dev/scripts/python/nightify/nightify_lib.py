
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

import nightify_data
import ck3_parser
import re
import os
from copy import deepcopy


class TextFormatter:
    def __init__( self, use_colors = True ):
        self.use_colors = use_colors
    
    def     red(self,text): return "\033[91m{}\033[00m".format(text) if self.use_colors else text
    def  orange(self,text): return "\033[33m{}\033[00m".format(text) if self.use_colors else text
    def    cyan(self,text): return "\033[94m{}\033[00m".format(text) if self.use_colors else text
    def    blue(self,text): return "\033[34m{}\033[00m".format(text) if self.use_colors else text
    def magenta(self,text): return "\033[95m{}\033[00m".format(text) if self.use_colors else text
    def   green(self,text): return "\033[92m{}\033[00m".format(text) if self.use_colors else text
    def    grey(self,text): return "\033[90m{}\033[00m".format(text) if self.use_colors else text
    
    # this is crucial. trust me bro
    def format_header(self,text):
        if self.use_colors:
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
        else:
            output_text = text

        return output_text


class Nightify:
    
    def __init__(
            self,
            file_content,
            use_regex = False,
            is_activity = False,
            is_scripted_illustration = False,
            use_colors = True,
            ):
        
        self.txt = TextFormatter(use_colors)
        
        self.is_activity = is_activity
        self.is_scripted_illustration = is_scripted_illustration
        
        if use_regex:
            for trigger in nightify_data.replace_religion_triggers.keys():
                file_content = re.sub(trigger, nightify_data.replace_religion_triggers[trigger], file_content)
        
        self.results = ck3_parser.ck3_parse(file_content)
        self.results_list = ck3_parser.ck3_parse_results_as_list(self.results)
        
        self.output_list = deepcopy(self.results_list)
        
        
        self.added_backgrounds = 0
        self.changed_vanilla_environments = 0
        
        self.parser_log = ""

        self.parse_errors = []
        self.unknown_bgs  = []
        self.unknown_environments = []

        if self.is_activity:
            self.night_trigger = nightify_data.night_trigger_activity
        elif self.is_scripted_illustration:
            self.night_trigger = nightify_data.night_trigger_scripted
        else:
            self.night_trigger = nightify_data.night_trigger

        self.night_trigger_new_block = "trigger = { " + self.night_trigger + " }"
        
        
        for bg_index, background in enumerate(self.results_list):
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
                
                if (not self.is_scripted_illustration and subbackground[0] != "background") or (self.is_scripted_illustration and subbackground[0] != "texture"):
                    continue

                current_log = "Found a replacement for subbackground (" + self.txt.orange(str(sbg_index)) + ") of "
                current_log += self.txt.magenta(background[0]) + " (" + self.txt.orange(str(bg_index)) + "):\n"

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

                            if self.is_scripted_illustration or bg_reference.startswith(nightify_data.bg_path_prefix):
                                if self.is_scripted_illustration:
                                    bg_path = bg_reference
                                else:
                                    bg_path = bg_reference.removeprefix(nightify_data.bg_path_prefix)
                                
                                # This is where we look up nighttime illustrations in our dictionary
                                if bg_path in nightify_data.do_not_nightify:
                                    current_log += self.txt.grey("\t" + bg_path + " is already a nighttime illustration. Skipping it")

                                elif bg_path in nightify_data.nightify_illustrations.keys():
                                    nightified_bg = nightify_data.nightify_illustrations[bg_path]

                                    current_log += "\t" + self.txt.green(bg_path) + " has a nighttime version: "
                                    current_log += self.txt.cyan(nightified_bg) + "\n"

                                    if nightified_bg in nightify_data.nightify_environments.keys():
                                        nightified_environment = nightify_data.nightify_environments[nightified_bg]
                                        current_log += "\t" + self.txt.cyan(nightified_bg) + " has a fitting portrait environment: "
                                        current_log += self.txt.blue(nightified_environment) + "\n"
                                        replace_bg = True
                                    else:
                                        if not self.is_scripted_illustration and nightified_bg not in self.unknown_environments:
                                            self.unknown_environments.append(nightified_bg)

                                elif bg_path.partition("/")[0] in nightify_data.ignore_folders:
                                    current_log += self.txt.grey("\t" + bg_path + " is in a blacklisted folder. Skipping it")

                                else:
                                    if bg_path not in self.unknown_bgs:
                                        self.unknown_bgs.append(bg_path)

                            elif bg_reference.startswith(nightify_data.video_path_prefix):
                                current_log += self.txt.grey("\t" + bg_reference + " is a video file. Skipping it")
                            
                            else:
                                error_string = "Subbackground at index " + str(sbg_index) + " of background " + background[0]
                                error_string += " has an unexpected reference: " + bg_reference + " (path doesn't start with gfx/interface/illustrations/)"
                                error_string = self.txt.red(error_string)
                                self.parse_errors.append(error_string)
                                
                        case "environment":
                            environment_index = st_index
                            # Check if the vanilla portrait_environment needs changing
                            if statement[2][1] in nightify_data.replace_vanilla_environments.keys():
                                new_vanilla_environment = nightify_data.replace_vanilla_environments[statement[2][1]]
                                self.output_list[bg_index][2][output_sbg_index][2][environment_index][2][1] = new_vanilla_environment
                                self.changed_vanilla_environments += 1

                        case "trigger":
                            trigger_index = st_index
                            found_trigger = True
                        
                        case "ambience":
                            ambience_index = st_index

                if replace_bg:
                    subbackground_copy = deepcopy(subbackground)

                    sbg_whitespace_copy = self.output_list[bg_index][2][output_sbg_index-1]
                    self.output_list[bg_index][2].insert(output_sbg_index-1, sbg_whitespace_copy)
                    self.output_list[bg_index][2].insert(output_sbg_index, subbackground_copy)

                    if found_trigger:
                        whitespace_copy = self.output_list[bg_index][2][output_sbg_index][2][trigger_index][2][1]
                        self.output_list[bg_index][2][output_sbg_index][2][trigger_index][2].insert(1, whitespace_copy)
                        self.output_list[bg_index][2][output_sbg_index][2][trigger_index][2].insert(2, self.night_trigger)

                        current_log += self.txt.red("\t(has existing trigger)\n")
                    else:
                        whitespace_copy = self.output_list[bg_index][2][output_sbg_index][2][1]
                        self.output_list[bg_index][2][output_sbg_index][2].insert(1, whitespace_copy)
                        self.output_list[bg_index][2][output_sbg_index][2].insert(2, self.night_trigger_new_block)

                        reference_index   += 2
                        if not self.is_scripted_illustration:
                            environment_index += 2
                            ambience_index    += 2

                        current_log += self.txt.grey("\t(no existing trigger)\n")
                    
                    if self.is_scripted_illustration:
                        self.output_list[bg_index][2][output_sbg_index][2][reference_index][2][1] = nightified_bg
                    else:
                        self.output_list[bg_index][2][output_sbg_index][2][reference_index][2][1] = nightify_data.bg_path_prefix + nightified_bg
                        self.output_list[bg_index][2][output_sbg_index][2][environment_index][2][1] = nightified_environment

                        if nightified_bg in nightify_data.nightify_ambience.keys():
                            self.output_list[bg_index][2][output_sbg_index][2][ambience_index][2][1] = nightify_data.nightify_ambience[nightified_bg]

                    output_sbg_index += 2

                    self.added_backgrounds += 1

                    self.parser_log += current_log + "\n"
        
        self.successful_parse = ( len(self.parse_errors) == 0 and len(self.unknown_bgs) == 0 and len(self.unknown_environments) == 0 )
        
        if self.successful_parse:
            # flatten the list
            self.file_output = nightify_data.file_header + ck3_parser.recursive_concat(self.output_list)
        else:
            self.file_output = ""
    
    def is_parse_successful(self):
        return self.successful_parse
    
    def get_ascii_art_header(self):
        return self.txt.format_header(nightify_header)
    
    def pprint(self):
        ck3_parser.ck3_parse_results_pprint(self.results)
    
    def pformat(self):
        return ck3_parser.ck3_parse_results_pformat(self.results)
    
    def get_parser_log(self):
        return self.parser_log
    
    def get_error_log(self):
        log = ""
        
        if len(self.parse_errors) > 0:
            log += "\n".join(self.parse_errors)
            log += "\n\n"
        
        if len(self.unknown_bgs) > 0:
            self.unknown_bgs.sort()
            log += self.txt.red("ERROR:") + " Several unknown backgrounds were found.\n"
            log += "Add these to the " + self.txt.orange("nightify_illustrations") + " Dictionary in nightify_data.py:\n"
            log += "(If these already take place at night or indoors, add them to the " + self.txt.orange("do_not_nightify") + " List instead)\n"
            for bg in self.unknown_bgs:
                log += "\t" + self.txt.red(bg) + "\n"
            log += "\n\n"

        if len(self.unknown_environments) > 0:
            self.unknown_environments.sort()
            log += self.txt.red("ERROR:") + " Several nighttime backgrounds don't have a portrait_environment.\n"
            log += "Add these to the " + self.txt.orange("nightify_environments") + " Dictionary in nightify_data.py:\n"
            for env in self.unknown_environments:
                log += "\t" + self.txt.red(env) + "\n"
            log += "\n\n"
        
        return log
    
    def get_success_log(self):
        log = ""
        
        if self.successful_parse:
            log += self.txt.green("Success!") + "\n"
            log += self.txt.cyan(str(self.added_backgrounds)) + " nighttime backgrounds were added.\n"
            log += self.txt.cyan(str(self.changed_vanilla_environments)) + " vanilla portrait environments were changed.\n"
            log += "\n\n"
        
        return log
    
    def get_warnings_log(self):
        log = ""
        
        if self.successful_parse:
            # Checking for religions
            for vanilla_religion in nightify_data.vanilla_religion_warnings.keys():
                if self.file_output.find(vanilla_religion) != -1:
                    log += self.txt.red("Warning:") + " The output contains at least one reference to the vanilla religion "
                    log += self.txt.orange(vanilla_religion)
                    log += "\n         Make sure to add or replace it with the PoD trigger "
                    log += self.txt.green(nightify_data.vanilla_religion_warnings[vanilla_religion])
                    log += "\n\n"
            
            if self.file_output.find(nightify_data.nomadic_gov_warning) != -1:
                log += self.txt.red("Warning:") + " The output contains at least one reference to the vanilla government flag "
                log += self.txt.orange(nightify_data.nomadic_gov_warning)
                log += "\n         Make sure to add or replace it with the PoD trigger "
                log += self.txt.green(nightify_data.nomadic_gov_trigger)
                log += "\n\n"
            
            if self.file_output.find(nightify_data.nomadic_tier_warning) != -1:
                log += self.txt.red("Warning:") + " The output contains at least one reference to the vanilla nomad law "
                log += self.txt.orange(nightify_data.nomadic_tier_warning)
                log += "\n         Make sure to add or replace it with a trigger that works for feudal governments: "
                log += self.txt.green(nightify_data.nomadic_tier_trigger)
                log += "\n\n"
            
            if self.file_output.find(nightify_data.gruesome_festival_warning) != -1:
                log += self.txt.red("Warning:") + " The output contains at least one reference to the Gruesome Festival background "
                log += self.txt.orange(nightify_data.gruesome_festival_warning)
                log += "\n         Make sure to also add the Colosseum background for Rome:\n"
                log += self.txt.green(nightify_data.gruesome_festival_sbg)
                log += "\n(Replace " + self.txt.orange("reference") + " with " + self.txt.orange("texture")
                log += " if editing the activity file)"
                log += "\n\n"
        
        return log
    
    def get_full_log(self):
        log = ""
        
        log += self.get_ascii_art_header() + "\n"
        log += self.get_error_log()
        log += self.get_success_log()
        log += self.get_warnings_log()
        
        #log += "\n"
        
        return log
    
    def get_file_output(self):
        return self.file_output
    
    def attempt_file_output(self, path):
        if self.successful_parse:
            with open(path, 'w', encoding='utf_8_sig') as f:
                f.write(self.file_output)
            return "Wrote the output to " + self.txt.orange(path) + "\n\n"
        else:
            return self.txt.red("Since there were errors, no output file was written.") + "\n\n"