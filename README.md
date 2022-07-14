# Photon Ranch User Info

This repository is currently under construction.


This is the serverless app that manages user information and time allocation.

Table defined here is indexed using user ID, and it includes that, a user's available time, when that time was last updated, and whatever other user info we deem worthy of retaining.

4 methods: user_info_handler() to see user's current allocation, update_user_info to change non-time related info, add_time() to add time, deduct_time() to use up time.

authorizer needed for adding time - might be different than for deducting time??? will definitely be different from authorizer for update_user_info.

get_available_time() and deduct_time() would be used by the frontend or calendar api; we'd have to talk about where the time deduction actually occurs (is it at a calendar reservation? is it as the users are using the telescopes?) and where a user would be prevented from continuing if they don't have enough time.

add_time() would be used by moodle event triggers (and potentially somewhere that admin have access to, so we could "refund" time or grant people time as we so choose?) and would be tailored towards moodle limitations in posting http requests.