#Photon Ranch User Info
This repository is currently under construction


This is the serverless app that manages time allocation (among other things? we said it'd be nice to have a way to store other user info)

table defined here is indexed using user ID, includes that, a user's available time, and when that time was last updated

3 methods: getAvailableTime() to see user's current allocation, addTime() to add time, deductTime() to use up time

authorizer needed for adding time - might be different than for deducting time???

getAvailableTime() and deductTime() would be used by the frontend or calendar api

addTime() would be used by moodle event triggers (and potentially somewhere that admin have access to, so we could "refund" time or grant people time as we so choose?)

Is it better practice to have these separate endpoints, or would a generic "get attribute", "change attribute" be less bulky (especially if we want to add more user info to this table)? I'd imagine the pros of the latter would be simpler code, but the former allows for different levels of authentication - then would it make sense to separate something like time from a more generic "change/view/other attribute" (if the other attributes are things like site preferences, etc that don't need to be secure)