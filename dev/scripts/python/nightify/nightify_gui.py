##### USAGE:
#
# You need Python and have installed pyparsing via pip.


from nightify_lib import *
from tkinter import *
from tkinter import filedialog
from tkinter.scrolledtext import *
from tkinter.ttk import *
import os


class NightifyHandler:
    def __init__(self):
        self.log_main   = ""
        self.log_parser = ""
        self.log_pprint = ""
        self.raw_output = ""
        self.n = None
    
    def process_string(
            self,
            file_content,
            use_regex = False,
            is_activity = False,
            is_scripted_illustration = False,
            ):
        self.n = Nightify(file_content, use_regex, is_activity, is_scripted_illustration, False)
        
        self.log_main   = self.n.get_full_log()
        self.log_parser = self.n.get_parser_log()
        self.log_pprint = self.n.pformat()
        self.raw_output = self.n.get_file_output()


class TextHandler:
    def __init__(self):
        pass
    
    def init_widgets(
            self,
            nightify_handler,
            regex_var,
            activity_var,
            scripted_var,
            textarea_logs,
            textarea_parser,
            textarea_pprint,
            textarea_raw,
        ):
        self.nightify_handler = nightify_handler
        self.regex_var        = regex_var
        self.activity_var     = activity_var
        self.scripted_var     = scripted_var
        self.textarea_logs    = textarea_logs
        self.textarea_parser  = textarea_parser
        self.textarea_pprint  = textarea_pprint
        self.textarea_raw     = textarea_raw
    
    def set_text(self, field, text):
        field.delete("1.0", END)
        field.insert(END, text)
    
    def reload(self, file_content):
        self.nightify_handler.process_string(
                file_content,
                self.regex_var.get(),
                self.activity_var.get(),
                self.scripted_var.get(),
            )
        self.set_text(self.textarea_logs,   self.nightify_handler.log_main)
        self.set_text(self.textarea_parser, self.nightify_handler.log_parser)
        self.set_text(self.textarea_pprint, self.nightify_handler.log_pprint)
        self.set_text(self.textarea_raw,    self.nightify_handler.raw_output)
    
    def get_raw_output(self):
        return self.nightify_handler.raw_output



text_handler = TextHandler()


def select_file():
    filetypes = (
        ('text files', '*.txt'),
        ('All files', '*.*')
    )

    filename = filedialog.askopenfilename(
        title='Open a file',
        initialdir='./',
        filetypes=filetypes
        )

    return filename

def reload_from_string( file_content, text_handler ):
    text_handler.reload(file_content)

def reload_from_file( text_handler ):
    filename = select_file()
    
    if filename != "":
        with open(filename, 'r', encoding='utf_8_sig') as file:
            file_content = file.read()
    
        reload_from_string(file_content, text_handler)

def save_to_clipboard( window, text_handler ):
    window.clipboard_clear()
    window.clipboard_append(text_handler.get_raw_output())
    window.update() # now it stays on the clipboard after the window is closed


def default_textbox( parent ):
    return ScrolledText( parent,
                         height = 45,
                         width = 200,
                         padx = 4,
                         pady = 4 )

def default_checkbutton( parent, var, text ):
    return Checkbutton( parent,
                        text = text, 
                        variable = var, 
                        onvalue = True, 
                        offvalue = False )


window = Tk()
window.title('Nightify')

frame_main = Frame(window)

regex_var = IntVar()
regex_toggle = default_checkbutton(frame_main, regex_var, "Use regex to preprocess input (unreliable)")

activity_var = IntVar()
activity_toggle = default_checkbutton(frame_main, activity_var, "Treat the input as an activity")

scripted_var = IntVar()
scripted_toggle = default_checkbutton(frame_main, scripted_var, "Treat the input as a scripted_illustration")

tabs_logs = Notebook(frame_main)

textarea_logs   = default_textbox(frame_main)
textarea_parser = default_textbox(frame_main)
textarea_pprint = default_textbox(frame_main)
textarea_raw    = default_textbox(frame_main)

tabs_logs.add(textarea_logs, text="Main Log")
tabs_logs.add(textarea_parser, text="Parser Log")
tabs_logs.add(textarea_pprint, text="Parser pprint")
tabs_logs.add(textarea_raw, text="Raw Output")

frame_input_buttons = Frame(frame_main)

text_handler.init_widgets(
        NightifyHandler(),
        regex_var,
        activity_var,
        scripted_var,
        textarea_logs,
        textarea_parser,
        textarea_pprint,
        textarea_raw,
)

button_open_file = Button(
    frame_input_buttons,
    text='Open a File',
    command=lambda:reload_from_file(text_handler),
)

button_open_clipboard = Button(
    frame_input_buttons,
    text='Open from clipboard',
    command=lambda:reload_from_string(
            window.clipboard_get(),
            text_handler,
    ),
)

button_save_to_clipboard = Button(
    frame_main,
    text='Save Raw Output to Clipboard',
    command=lambda:save_to_clipboard(window,text_handler),
)


frame_main.pack( fill = 'both',
            expand = True,
            padx = 16,
            pady = 16 )
regex_toggle.pack()
activity_toggle.pack()
scripted_toggle.pack()
frame_input_buttons.pack(
            padx = 8,
            pady = 8 )
button_open_file.pack( side = LEFT )
button_open_clipboard.pack( side = LEFT )
tabs_logs.pack(fill = 'both', expand = True)
button_save_to_clipboard.pack()


window.mainloop()