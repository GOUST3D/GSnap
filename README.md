GSnap
----

GSnap is a matching tool, in UI form. 

This is meant to Snap objects to locators, that are set-up by the user, in order to maintain a specific position/rotation, in world space, or relative to another object.


----


+ *Snapping objects*:  The first selection, will Snap to the second selection. If the first is a ***parentConstrained Locator***, the parentConstraint will be re-applied **after**.

+ *Adding locators*:  Selecting 1 object will create a locator at the same pivot. Selecting 2 objects, will parentConstrain the locator relative to the second object.


+ *Deleting locators*:  If there is nothing selected, a prompt will appear to delete all GSnap nodes (GSnap group+locators).


+ *Locator shape scale slider*


+ *Hide/Unhide all locators checkbox*


![Snap](https://cdn.discordapp.com/attachments/561729288609595402/815708764861628416/iQdov4BvOV.gif)


 Installation 
----

Maya compatibility:    2020

+ Place files in "\Documents\maya\2020\scripts\GSnap"

+ Create a shelf button, set it to "Python"!

+ Add lines:


import GSnap

reload(GSnap)

-----

Enjoy!
