##### USAGE:
#
# You need Python and have installed pyparsing via pip.
# Open a command line in this folder and run:
# python .\nightify_cli.py .\01_event_backgrounds.txt
# (or whatever the name of the input file is, assuming it's in the same folder)
#
# The input file needs to be a VANILLA event background file.
# e.g. this one: common\event_backgrounds\01_event_backgrounds.txt
#
# Doing this for the first time on a new DLC will probably result in errors.
# Take note of the missing illustrations, then add them to nightify_data.py.
# Add illustrations that already take place at night/indoors to do_not_nightify.
# Append missing daytime illustrations to nightify_illustrations, with a fitting nighttime version.
# (There are already some example placeholder illustrations at the end of that dictionary.)
# Run this script again and it should work.
#
# To see all valid arguments, run the script with the argument -h


from nightify_lib import *
import argparse
import os


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


with open(args.input_file, 'r', encoding='utf_8_sig') as file:
    file_content = file.read()


n = Nightify(file_content, args.regex, args.activity, args.scripted, True)


if args.pprint: n.pprint()
if args.log: print(n.get_parser_log())

print(n.get_full_log())


output_folder = "./outputs/"

if args.output == None:
    output_path = output_folder + os.path.basename(args.input_file)
else:
    output_path = output_folder + args.output

if not args.test:
    file_log = n.attempt_file_output(output_path)
    print(file_log)