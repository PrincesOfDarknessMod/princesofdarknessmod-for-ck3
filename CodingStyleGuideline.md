Coding Style Guideline 
======================

Intro
-----
This guideline is being created with the goal to standardise the coding style throughout the mod as a whole, increasing both readability and ease of future modification. *This is a work in progress and currently nothing in this document is to be considered the final iteration.*

**Important Note:** Please avoid full file tidying when you are changing other things within a file, as this can make Karde's job a lot harder.

That said, let's begin.

General Rules for Maintaining Ease of Patch Updating
----------------------------------------------------
When you are not overwriting localisation, the Jomini engine will allow you to overwrite a vanilla key by simply adding it to any file in the correct folder. This, functionally, means that you should never have to add a vanilla file to the mod, outside of potentially GUI. When in doubt, ask Karde, Sparc, or another Senior Developer. Avoiding adding vanilla files allows for much more ease in updating between patches, and allows for focus to be maintained on continued development.
On the matter of GUI files, when you are modifying a Vanilla GUI file, please place a comment of #CfV(Changed from Vanilla) before and after your changes/additions. This, much like the prior point, helps prevent work from being overwritten in any update, and prevents avoidable conflicts when integrating.

General Code Structure
-----------------------
### Curly Braces
Your opening brace `{` should always be on the same line, as so:
```
this_is_an_example = {
```
Whereas your closing brace `}` should never be on the same line as any other code, like so:
```
this_is_an_example = {
	Example_part_two = {

	}
}
```

### Indenting and Aligning Code
Indentation should always be done according to these four rules, to allow for easier changes in future, and for much better readability for anyone that has to work with your code in future.

**Rule One:** Each opening brace `{` increases the line indent by 1

**Rule Two:** Each closing brace `}` decreases the line indent by 1

**Rule Three:** Line Indentation begins at 0

**Rule Four:** Indentation should always be done using Tabs rather than Spaces, ask someone if you are unsure as to how to set this up using your text editor.

Encoding
--------

## .yml Files
All .yml files must be saved in UTF8-BOM encoding. To make this much easier on yourself, as near all text editors will open a UTF8-BOM file *in* UTF8-BOM, you can copy and paste another .yml file, rename it, and change the interior localisation, whilst maintaining the desired encoding.

Optimisation
------------

## Triggers
CK3, much like every Paradox Game, relies on ticks, or calculations that your CPU has to go through before it can advance a day. For this guide, these matter predominantly through their generation from Checks.

As a general rule, put your most exclusive check first. For an explanation as to why, contine reading.

The goal with optimising triggers is to reduce these ticks as much as possible, and thus reduce the amount of impact on performance that our code has on the base game. The easiest way to do this is through the order of our checks, for an example let us assume that there is one player, 10 000 characters, and some random value of prestige for each of those characters.

```
trigger = {
	is_ai = yes
	prestige = 0
	this = character:790117
	piety = 0
}
```
We have three checks in this event, and we start with 10 000 eligible characters. We have one player, so we remove it from the eligible pool, and go to the next check, with 9 999 eligible characters. Let us assume that around half have more than 0 prestige, and so we go onto the next check with about 5 000 eligible characters. From all these eligible characters, we are looking for character 790117, so the list of eligible characters drops to 1. This one character is then subject to another check, as to if they have more than 0 piety.

So four checks, generating 25 001 ticks. Whereas, if we rewrite this code to, instead, resemble this:

```
trigger = {
	this = character:790117
	prestige = 0
	piety = 0
	is_ai = yes
}
```

Here we go from having 10 000 eligible characters, to having 1 eligible character in a single check. Which then compounds with only having one tick per check following, as it must *only* check that one character. Hence we go from 25 001 ticks, to only 10 004 ticks, for the same result. Which is a rather massive improvement of 60% performance wise, for the same result, with the same amount of checks.

Naming conventions
------------------
| **What**                              | **Convention**                                                          | **Examples**                            |
|---------------------------------------|-------------------------------------------------------------------------|-----------------------------------------|
| Scripted Triggers                     | Start with POD_ and end with _trigger                                   | `POD_is_vampire_trigger`   		        |
| Scripted Effects                      | Start with POD_ and end with _effect                                    | `POD_blood_surge_prowess_effect`        |
| Event File Names                      | Event Files should be titled POD_(Event_File_Name) to prevent conflict  | `POD_artifacts_events.txt`              |
| Event Namespaces                      | Event Namespaces should either be POD_(Namespace) or POD(Namespace)     | `POD_artifacts`, `PODKuejin`            |
| Localisation File Names               | Localisation Files MUST be saved in the format (Name)l_<language>.yml   |  `dialog_POD_l_english.yml`             |
