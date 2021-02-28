# GSnap
GSnap is a matching tool, in UI form. 

This tool is meant to snap objects to locators, that are set by the user in order to maintain a specific position/rotation.


Snapping objects: The first selection, will snap to the second selection. If object 1 is a parentConstrained Locator, the parentConstraint will be re-applied after.

Adding locators: Selecting 1 object will create a locator at the same pivot. Selecting 2 objects, will parentConstrain the locator relative to the second object.

Deleting locators: If there is nothing selected, a prompt will appear to delete all GSnap nodes (GSnap group+locators).

+ Locator shape scale slider

+ Hide/Unhide all locators checkbox


--- Installation ---
Maya compatibility: 2020

+ Place files in "\Documents\maya\2020\scripts\GSnap"

+ Create a shelf button, set it to "Python"!

+ Add lines:

import GSnap
reload(GSnap)


Enjoy!
