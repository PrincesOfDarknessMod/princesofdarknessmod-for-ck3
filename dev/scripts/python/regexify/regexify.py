#####
#
# A simple tool for turning text into a format that can be read by VSCode's regular expressions.
# You can also test regular expressions online with: https://regex101.com/
#
#       FEATURES:
# - Escape curly brackets as \{ and \}
# - Turn all whitespaces into [ \t\n]+ (\s doesn't seem to work properly in VSCode)
# - Automatically set up capture groups for text substitution
#
#       HOW TO USE:
# You need Python with tkinter (should be installed with Python by default).
# Open a command line in this folder and run:
# python .\regexify.py
#
#####


from tkinter import *
from tkinter.ttk import *
import re


escape_chars = [ "{", "}", "[", "]", "(", ")", "\"", "?", "|" ]
whitespace_regex = r"[ \\t\\n]*"


def trim_trailing_whitespace(text):
    #output_text = text
    output_text = text.strip()
    
    # remove whitespaces at the start of the string
    #output_text = re.sub(r"^\s+", r"", output_text)
    
    # remove whitespaces at the end of lines
    output_text = re.sub(r"[ \t]+(?=\n)", r"", output_text)
    
    # remove whitespaces at the end
    #output_text = re.sub(r"\s+$", r"", output_text)
    
    return output_text

def allow_trailing_comments(text):
    return re.sub(r"[ \t]*\n[ \t\n]*", r"[ \\t]*(?:#*(?<=#).*\\n)*[ \\t\\n]*", text)

def regexify_string(text, capture, capture_regex, whitespace, comments, trim):
    output_text = text
    
    for char in escape_chars:
        output_text = output_text.replace(char, "\\" + char)
    
    if trim:
        output_text = trim_trailing_whitespace(output_text)
    
    if whitespace:
        if comments:
            # allow comments before newlines
            output_text = allow_trailing_comments(output_text)
        # match whitespace, but not the ones necessary for regex
        output_text = re.sub(r"(?<!\[)\s+", whitespace_regex, output_text)
    
    sanitized_capture = trim_trailing_whitespace(capture)
    
    if len(sanitized_capture) > 0:
        output_text = re.sub(sanitized_capture, capture_regex, output_text)
    
    return output_text

def get_replacement_string(text, capture):
    sanitized_capture = trim_trailing_whitespace(capture)
    
    if len(sanitized_capture) > 0:
        return text.replace(capture,"$1")
    else:
        return text

def get_text(field):
    return field.get( "1.0", END )

def set_text(field, text):
    field.delete("1.0", END)
    field.insert(END, text)

def reload_window( input_text,
                   replace_text,
                   capture_text,
                   capture_regex,
                   whitespace,
                   comments,
                   trim,
                   output_field,
                   outputreplace_field ):
    new_text = regexify_string(input_text, capture_text, capture_regex, whitespace, comments, trim)
    new_replace_text = get_replacement_string(replace_text, capture_text)
    set_text(output_field, new_text)
    set_text(outputreplace_field, new_replace_text)


window_padx     = 16
window_pady     = 16
textarea_height = 5
textarea_width  = 120
textarea_padx   = 4
textarea_pady   = 4


window = Tk()
window.title('Regexify for CK3 + VSCode')

frame = Frame(window)

label_input = Label(frame, text="Input text:")

textarea_input = Text( frame,
                       height = textarea_height,
                       width = textarea_width,
                       padx = textarea_padx,
                       pady = textarea_pady )

# this doesn't do anything, it's just for clarity
escape_var = IntVar()
escape_toggle = Checkbutton( frame,
                                 text = "Escape VSCode Regex characters, e.g. curly brackets (always necessary)", 
                                 variable = escape_var, 
                                 onvalue = True, 
                                 offvalue = False,
                                 state = DISABLED )

trim_var = IntVar()
trim_toggle = Checkbutton( frame,
                           text = "Trim trailing whitespace from the input text", 
                           variable = trim_var, 
                           onvalue = True, 
                           offvalue = False )

whitespace_var = IntVar()
whitespace_toggle = Checkbutton( frame,
                                 text = "Allow matching any length of whitespace", 
                                 variable = whitespace_var, 
                                 onvalue = True, 
                                 offvalue = False )

comments_var = IntVar()
comments_toggle = Checkbutton( frame,
                                 text = "Also account for code comments when matching whitespace (slower, and will delete comments when replacing)", 
                                 variable = comments_var, 
                                 onvalue = True, 
                                 offvalue = False )

label_replace = Label(frame, text="Replacement text:")

textarea_replace = Text( frame,
                       height = textarea_height,
                       width = textarea_width,
                       padx = textarea_padx,
                       pady = textarea_pady )

label_capture = Label(frame, text="Text to use as template for capture group (can also be left empty):")

textarea_capture = Text( frame,
                        height = 1,
                        width = textarea_width,
                        padx = textarea_padx,
                        pady = textarea_pady )

capture_regex_1 = r"(\\w+)"
capture_regex_2 = r"([^ \\t\\n]+)"
capture_regex_var = StringVar(window, capture_regex_2)
button_capture_regex_1 = Radiobutton( frame,
                                      text = "Capture group (\\w+) (numbers, letters, underscores)",
                                      variable = capture_regex_var, 
                                      value = capture_regex_1 )
button_capture_regex_2 = Radiobutton( frame,
                                      text = "Capture group ([^ \\t\\n]+) (any non-whitespace)",
                                      variable = capture_regex_var, 
                                      value = capture_regex_2 )

label_output = Label(frame, text="Regex for finding the text:")

textarea_output = Text( frame,
                        height = textarea_height,
                        width = textarea_width,
                        padx = textarea_padx,
                        pady = textarea_pady )

label_output_replace = Label(frame, text="Regex for the replacement:")

textarea_output_replace = Text( frame,
                        height = textarea_height,
                        width = textarea_width,
                        padx = textarea_padx,
                        pady = textarea_pady )

button_execute = Button( frame,
                         text = 'Convert Text',
                         command = lambda:reload_window( get_text(textarea_input),
                                                         get_text(textarea_replace),
                                                         trim_trailing_whitespace(get_text(textarea_capture)),
                                                         capture_regex_var.get(),
                                                         whitespace_var.get(),
                                                         comments_var.get(),
                                                         trim_var.get(),
                                                         textarea_output,
                                                         textarea_output_replace ) )

frame.pack( fill = 'both',
            expand = True,
            padx = window_padx,
            pady = window_pady )
label_input.pack()
textarea_input.pack()
escape_toggle.pack()
trim_toggle.pack()
whitespace_toggle.pack()
comments_toggle.pack()
label_replace.pack()
textarea_replace.pack()
label_capture.pack()
textarea_capture.pack()
button_capture_regex_1.pack()
button_capture_regex_2.pack()
button_execute.pack(pady = 20, ipadx = 12, ipady = 6)
label_output.pack()
textarea_output.pack()
label_output_replace.pack()
textarea_output_replace.pack()


sample_input = """            add_character_flag = {
                flag = has_scripted_appearance
            }"""
sample_replace = "add_character_flag = has_scripted_appearance"
sample_capture = "has_scripted_appearance"


set_text(textarea_input, sample_input)
set_text(textarea_replace, sample_replace)
set_text(textarea_capture, sample_capture)
escape_var.set(True)
whitespace_var.set(True)
#comments_var.set(True)
trim_var.set(True)
button_execute.invoke()


window.mainloop()