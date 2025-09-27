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


import pyparsing as pp
import io


def ck3_parse(file_content):
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
    
    return ck3_file.parse_string(file_content)


def ck3_parse_results_as_list(parse_results):
    return parse_results.as_list()


def ck3_parse_results_pprint(parse_results):
    parse_results.pprint()


def ck3_parse_results_pformat(parse_results):
    output = io.StringIO()
    parse_results.pprint(stream=output)
    contents = output.getvalue()
    output.close()
    return contents
