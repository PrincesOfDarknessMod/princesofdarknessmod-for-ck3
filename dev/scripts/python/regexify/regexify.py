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

def trim_whitespace(text):
    output_text = text
    output_text = re.sub(r"^\s+", r"", output_text)
    output_text = re.sub(r"\s+$", r"", output_text)
    return output_text

def regexify_string(text, capture, trim):
    sanitized_capture = trim_whitespace(capture)
    
    output_text = text
    
    if len(sanitized_capture) > 0:
        output_text = re.sub(sanitized_capture, r"(\\w+)", output_text)
    
    output_text = output_text.replace("{","\\{")
    output_text = output_text.replace("}","\\}")
    
    if trim:
        output_text = trim_whitespace(output_text)
    
    output_text = re.sub(r"\s+", r"[ \\t\\n]+", output_text)
    
    return output_text

def get_replacement_string(text, capture):
    sanitized_capture = trim_whitespace(capture)
    
    if len(sanitized_capture) > 0:
        return text.replace(capture,"$1")
    else:
        return text

def get_text(field):
    return field.get( "1.0", END )

def set_text(field, text):
    field.delete("1.0", END)
    field.insert(END, text)

def reload_window(input_text, replace_text, capture_text, trim, output_field, outputreplace_field):
    new_text = regexify_string(input_text, capture_text, trim)
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
#frame.pack( fill = 'both',
#            expand = True,
#            padx = window_padx,
#            pady = window_pady )

label_input = Label(frame, text="Input text:")
#label_input.pack()

textarea_input = Text( frame,
                       height = textarea_height,
                       width = textarea_width,
                       padx = textarea_padx,
                       pady = textarea_pady )
#textarea_input.pack()

label_replace = Label(frame, text="Replacement text:")
#label_replace.pack()

textarea_replace = Text( frame,
                       height = textarea_height,
                       width = textarea_width,
                       padx = textarea_padx,
                       pady = textarea_pady )
#textarea_replace.pack()

label_capture = Label(frame, text="Text to use as template for capture group (\\w+) (can also be left empty):")
#label_capture.pack()

textarea_capture = Text( frame,
                        height = 1,
                        width = textarea_width,
                        padx = textarea_padx,
                        pady = textarea_pady )
#textarea_capture.pack()

label_output = Label(frame, text="Regex for finding the text:")
#label_output.pack()

textarea_output = Text( frame,
                        height = textarea_height,
                        width = textarea_width,
                        padx = textarea_padx,
                        pady = textarea_pady )
#textarea_output.pack()

label_output_replace = Label(frame, text="Regex for the replacement:")
#label_output_replace.pack()

textarea_output_replace = Text( frame,
                        height = textarea_height,
                        width = textarea_width,
                        padx = textarea_padx,
                        pady = textarea_pady )
#textarea_output_replace.pack()

trim_var = IntVar()
trim_var.set(True)
trim_toggle = Checkbutton( frame,
                           text = "Trim whitespaces at the beginning and end of the input text?", 
                           variable = trim_var, 
                           onvalue = True, 
                           offvalue = False )
#trim_toggle.pack()

button_execute = Button( frame,
                         text = 'Convert Text',
                         command = lambda:reload_window( get_text(textarea_input),
                                                         get_text(textarea_replace),
                                                         trim_whitespace(get_text(textarea_capture)),
                                                         trim_var.get(),
                                                         textarea_output,
                                                         textarea_output_replace ) )
#button_execute.pack()

frame.pack( fill = 'both',
            expand = True,
            padx = window_padx,
            pady = window_pady )
label_input.pack()
textarea_input.pack()
label_replace.pack()
textarea_replace.pack()
label_capture.pack()
textarea_capture.pack()
trim_toggle.pack()
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
button_execute.invoke()


window.mainloop()