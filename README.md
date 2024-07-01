Welcome to Blitzball, a modern 8-bit baseball game. 

To start, we explain how the game is played. When the game is first loaded, the user is greeted with a white screen and a prompt that asks for a username. Before they can continue, the user must enter a username that is non-empty and no more than 16 characters. Then, pressing return brings the user to the home screen, where they are told to click anywhere to begin. Clicking triggers a fade animation which begins the game. There is a strike zone in the middle of the screen, with a pitcher behind it, and the pitcher repeatedly winds up and throws a randomized pitch. The player must try to click on the ball as close to its center as possible, and with the correct timing as to hit it when it is close to them, but not before it is too late. When the ball is hit, the user can see an animation of it flying away, and the type of hit that it was is displayed on the screen. If it is hit really well, a nice color fading animation will play too. If the user hits a home run, or a really long home run ("GONE"), then their score goes up by one. Their longest hit is also kept track of. If they get a base hit, fly out, etc, i.e. if they make some kind of contact with the ball that does not result in a home run, then nothing happens to the user's score or the current game -- they have fought off the pitch, and remain in the same situation. However, if a pitch gets by the player that they do not manage to hit, it is recorded as a strike. Three strikes makes an out, and once an out is recorded (or multiple outs, if the user manually changes the num_outs parameter in the file to alter the game), the game ends and the player is taken to the leaderboard screen. On the leaderboard, the top 10 performances of all time are displayed, with their corresponding usernames, scores and maximum distances. If the player has managed to crack the top 10, their name is highlighted in yellow on this screen. Clicking anywhere takes the player back to the home screen, where they can play another game.

Now, we explain how to run the game. In the folder, there is a single python file called blitzball.py, a single SQL database called blitz_scores.db, and a variety of png and mp3 files. In order to load the game, one simply must run the blitzball.py file. Make sure that the python modules pygame, sys, random and sqlite3 are installed when the game is run, as these modules are used by the program, and running it without them will cause an error. The SQL database stores score and maximum distance information, where the key for each is the username -- in order to reset this database to erase all current data, one can simply delete the blitz_scores.db file, and the next time the game is run, an empty database file will automatically be created in its place.

Here are a couple clarifications about the game. The username set by the player is constant during a session, so the only way to play under a different username is to close the game, then launch it again. This is to make it easy to binge play the game without having to re-enter a username each time. Also, only the maximum score ever achieved and maximum distance ever achieved are stored for each username, so after a run of the game, even if the run was poor, if the user with this username has a leaderboard-worthy score recorded, this will be what is shown on the leaderboard. Also, the file blitzball.py has a large number of parameters that can be tweaked by the player in order to change the game -- these are things like background and text colors, width and height of the screen, duration of the pause time between each pitch, the functions determining pitch speed and computing hit distance, etc. These are all clearly commented in the file, and can be changed easily to modify and customize the game -- try it out!

Here is the URL of my youtube video: https://youtu.be/RQDZxEU3OvI