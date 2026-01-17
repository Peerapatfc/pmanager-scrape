# 13. Tactics
Tactics play a key role in PManager. We can basically divide the tactics module of the game in four parts: the selection of the starting eleven, formations, advanced tactics and events. All of them have a key role in the way matches are processed. We'll now make individual distinctions between these four parts.

Starting Eleven
You can set the starting eleven under “Games >> Match Day”. In case you're redirected to the fixtures page it means that the system needed to refresh your team fixtures in order to let you select your team for the following matches. To go back to the Starting Eleven selection you must select the “Starting Eleven” option again from the top menu. You'll be taken to a page where you can set three of the four tactical parts of PManager: the Starting eleven, team's formation and advanced tactics. We'll only focus on the Starting Eleven in this part.

First of all, you should select the best players as your starting eleven since you, obviously, want to maximize your odds of winning the match. You'll have all players from both A and B teams to choose from. Check Section 7 so you can know which skills are more important for each position, and who the best players are.

Some users reported to us that they had some trouble when they wanted to make their first selection ever. The system is quite easy, but it might confuse less experienced users. Anyways, here's a quick video of the process: Starting 11 Video ... Now here are the instructions for the html version: you should click on the player's row you want to change and then change that player with another player by clicking on the second player's row. It's a click and change process, basically. After you have all of the players ordered as you wish, just click on the "Send Starting Eleven" button.

Formation
In the formation part of the Starting Eleven page you're required to select the way players will be positioned on the field, the style of play and the passing style.

We'll start with the formations. Well the formations are probably the most important part of a football match. There's no good in having 11 magnificent players playing a bad formation. In PM formations are really important! Basically you should try to have men advantages in the areas of the field where you want to carry the game through and also to have that very same advantage in the areas where your opponent pretends to carry its game through. An example: If you play with only one central-defender against a three-player central attack, your team is likely to suffer a lot of scoring chances if the ball is nicely put on those three forwards.

The formation selector should be very easy to understand: just move the circles (simulating the team players) to the positions you want and thus set your formation. You should know that any formation has to have at least 3 defenders, 2 midfielders and 1 forward. You can have no more than 1 player on each wing and no more than 3 in the middle.

The style of play and passing style are also part of the formation and can be selected right above the formation selector.

So, what are the available passing styles?
There are four:
- Short: The ball usually goes through all sectors before it reaches the attacking zones. You should play in this style if you are confident that you are going to win all midfield “battles” (comparisons). A good indication that you've made the right decision about choosing short passing is when you have more ball possession. Do not consider playing with this style if your midfield is weak or you predict that it will be weak in a given game (for example, if you are going to play against a midfield with 3 players on the center and you will only play with 1).
- Long: If you play with this style it's common that you see the ball going directly from your defensive-midfield to the attack. It's a very nice style to play if you have a poor midfield and a good attack; and a good attack why? Because there is an extra risk in long passes and it's easier to the opposite defenders to win the possession of the ball. Despite this extra-advantage to the defense, this is not noticed in the defense zone ratings.
- Direct: Works about the same as long passing, however the probabilities of making long passes are higher. Use it whenever you are sure that your attack ratings are much better than the defensive ratings of the other team.
- Mixed: Combines both short and long passes.

The conclusion here is that, despite having good attacking ratings, if you choose the wrong passing style you can have some troubles in creating scoring chances.

And what about the style of play? What to choose? Defensive, normal or attacking?
- Defensive: It will give a boost to your defensive and goalkeeper ratings and your attacking ratings will be equally decreased.
- Attacking: It will give a boost to your attacking ratings and your defensive ratings will be equally decreased.
- Normal: No change will be made to the ratings.

So, what to choose? Choose the one that will better balance your team! Example: if you have an outstanding attack and a lousy defense, perhaps would be a better idea to play with defensive style (or instead, give an extra boost to your attack in even a greater expense of your poor defense). Or if you want to play for a draw then consider playing Defensive with a formation containing 5 defenders!

Advanced Tactics
Advanced tactics (ATs) are one the most challenging parts of the game. The mechanism behind ATs is quite simple: basically the Match Engine compares directly the sum (or the average, depending on the AT) of the player skills the AT requires. If the conditions are verified than the team will receive a bonus. Pay attention to the fact that this bonus might not be the same in each zonal rating. ATs bonuses are added directly to the sum of the global skill of the team that is lately used to calculate the final zonal ratings. For more information about this please check "The Match" section of this manual.
You'll know that you win an AT when you see its related sentence shown on the Match Report. Some ATs are made of 2 condition or even 3. This means that, in order to win the AT, your team must win all the conditions. However each condition has its own bonus; this means that for example in 3 conditions ATs, even if you lose the AT by only one condition, if you still win the other 2, your team will have a bonus. And in ATs with 2 conditions the same thing can happen, however, usually, 2 condition ATs balance themselves (if you win one and lose other you won't have any bonus or penalization). We'll be making a full description on all conditions ATs have.

We'll now make a full description on each Advanced Tactic there is.

Pressing
Here's how it works:
NORMAL: The AT will not be activated.
LOW
Works well if:
1. The sum of speed of your players is lower than the opponent players;
2. The sum of tackling of your players is higher than the opponent players.

Both conditions have the same weight.
HIGH
Works well if:
1. The sum of speed of your players is higher than the opponent players;
2. The sum of passing of your players is higher than the opponent players;
Both conditions have the same weight.

Offside Trap
How it works:
ENABLED:
Works well if:
1. Your defenders have more positioning than the opposing team's forwards (by calculating the average);
2. Your defenders have more speed than the opposing forwards (by calculating averages).
Both conditions have the same weight.
DISABLED: The AT will not be activated.

Counter attack
How it works:
ENABLED:
Works well if:
1. The sum of passing of your players is higher than the opponent players;
2. The sum of speed of your players is higher than the opponent players (higher bonus than passing);
3. Your tactic (formation + style of play) is defensive (for example, an offensive formation with a defensive style might do it. You'll have to make your own experiences and use your common sense to find this out). There is also small boost if the opponent's team mentality is attacking (mix of tactic/mentality) but this is not a condition to win this Advanced Tactic.

Speed is the most important condition of this AT; followed by passing. The last is the defensive formation. In case the defensive formation has the opponent attacking formation bonus, this condition will have a higher bonus than passing but still less than speed.

This means that in case you win 2 of these conditions you'll have a bonus despite losing the AT. If you will only one you'll always have a penalization.
DISABLED: The AT will not be activated.

Tackling
How it works:
NORMAL: The AT will not be activated.
EASY:
1. reduces the probability of your players getting booked/sent off;
2. reduces the probability of the opposing team's players to get injured.
HARD:
1. increases the probability of your players getting booked;
2. increases the probability of the opposing team's players getting injured;
3. Extremely small bonus to the team, in all zonal ratings.

You'll never see a report (comment) on the Match Engine caused by this AT, but still it's quite important.

High Balls
How it works:
NO: The AT will not be activated.
YES
Works well if:
1. The sum of the heading attribute of your players is higher than the opponent players;
2. The sum of the strength attribute of your players is higher than the opponent players.
Both conditions have the same weight.

One on Ones
How it works:
NO: The AT will not be activated.
YES
Works well if:
1. the sum of the technique and strength of your midfielders and forwards is higher to the sum of the tackling and strength of the opponent defenders and midfielders (using averages).
This is a one condition AT, so either you'll win it and receive a full bonus or you lose it and receive a full penalization.

Keeping Style
How it works:
NOT DEFINED: The AT will not be activated.
STAND IN
Works well if:
1. the sum of the reflexes and handling attributes of your keeper is higher than the sum of the heading and finishing attributes of the opponent forwards (using averages).

This is a one condition AT.
RUSHING OUT
Works well if:
1. the sum of the agility and crosses attributes of your keeper is higher than the sum of the heading and technique attributes of the opponent forwards (using averages).
This is a one condition AT.

Man Marking
How it works:
NOT DEFINED: The AT will not be activated.
ZONAL
Works well if:
1. the sum of the speed and tackling attributes of your defenders and midfielders is higher than the sum of the positioning and speed attributes of the opponent midfielders and forwards (using averages).

This is a one condition AT
MAN-TO-MAN
Works well if:
1. the sum of the strength and tackling attributes of your defenders and midfielders is higher than the sum of the positioning and strength attributes of the opponent midfielders and forwards (using averages).
This is a one condition AT.

Long Shots
How it works:
Yes - Will work well if the sum of the finishing and technique of your midfielders and forwards is higher than the sum of the agility of the opponent’s goalkeeper and positioning of the opponent’s defenders. (All these using averages.)
No - The AT will not be activated.

First Time Shots
How it works:
Yes - Will work well if the sum of the finishing and heading of your forwards is higher than the sum of the reflexes of the opponent’s goalkeeper and heading of the opponent’s defenders. All these using averages. You will also need to have at least three forwards.
No - The AT will not be activated.

Weather
Despite being an AT, managers do not have the possibility to activate/deactivate it, obviously. On each single game under sun, snow or rain both teams have this AT automatically calculated. There are two types of weather ATs: good or bad weather. Good when the weather is sunny and bad when the weather is snowy or rainy.
For good weather, the ME will compare speed between all players on the field.
For bad weather, the ME will compare strength.
You should now that this AT bonus will depend on the difference between speed/strength between all players. So the bonus given by this AT might be very big in case the difference between players' skills is big as well.

These are all ATs regarding player skills we have in PM. You might be wondering now what are the ATs that give the highest bonuses. Well, considering that the Weather AT is variable, here's the ranking (starting with the higher bonus AT)
1) Counter-Attack
--- All at the same level ---
2) Man Marking
3) Pressing
4) Offside Trap
5) One on Ones
6) High Balls
7) First Time
8) Long Shots
--- All at the same level ---
9) Keeping Style
--- All at the same level ---
10) Tackling

Advanced Tactics calculations are made each and every time a player's change occur in the game (substitution, red cards, etc). However the comments you often see in the match report are always due to the initial calculations once the match starts. This is due to practical reasons. It would get really messy to see dozens of similar ATs comments in a very eventful match.

Preferred Side
You can choose through what side your team will try to attack the most (Right/Left/Center). It's wise to choose a side where your team has (good) players.
Remember that the ball usually passes through the midfield before reaching the attacking zone.

Example: You play in a formation with 3 central midfielders and 3 central attackers, choosing anything else rather than Center will be a bad option.

Example #2: It would also be bad to choose the left side and do not play with any left-midfielder (despite having a brilliant left attacker).

If you select the “Normal” option, your players will randomly select the side of your team's attacks.

Captain
Choose the team captain. In case you don't choose any captain, the Match Engine will randomly select one when the game is about to be played. A good captain will be a player with a high professionalism level. The team captain has little influence on the Match Engine but, however, it will give your team a little boost in its morale. This bonus will be as higher as the professionalism level of your captain is.

Penalty Taker
Choose the team's penalty taker. A good penalty taker has high Technique and Finishing levels.

Team's attitude
The team's attitude is one of the most important features of the game and can be used in all matches except in friendly and tournament matches. National teams can also use this feature in friendly matches though.

Here's an explanation about all the three options.
Match of the season
Match of the season (MOTS) can be used in order to increase the team's performance on all zonal ratings. You should use this feature wisely as, for example, if you lose a match using MOTS, your team's morale will be severely affected. Also bare in mind that if you use MOTS your players will get more tired than usual.
A team can use the match of the season feature twice a season. On national team's matches, they can be used both in official & friendly games. A national team has the possibility to use 2 MOTS in the friendly + qualifying stage and another 2 in the World Cup stage.

Normal
The team's attitude will be deactivated if you select this option. This is the normal state of this feature.

Play it Cool
By using the Play it Cool (PIC) mode your team will suffer a penalization in all zonal ratings. The effect will be the exactly the opposite of the match of the season: besides the penalization on ratings, your players will get less tired and in case you win the match your team's morale will increase. If a National Team plays in PIC, the experience players get will be reduced. Under these conditions the experience gained by a player will be exactly the same to the experience gain they would get a normal league match.

You can use this mode whenever you want. There are no restrictions for PIC.

Events
Events play a key role in the tactical side of the game (as all the other parts of this section!). Events will allow managers to change the outcome of a game while it is happening. This is a simulation of the ability real-life managers have to interfere on the match during its duration.

At the moment, there are four types of events in PManager: substitutions, formation changes, style (passing style and style of play) and preferred side. We'll describe each type of event later on this section.

Once you are about to set an even, you have to selecting his initial trigger. The available options are Minute and Sent Off. While the Minute condition is pretty self-explanatory the Sent Off condition requires you to select the position of the player that will trigger the event if someone playing at this position is sent off. You can't select the GK position as there are already automated actions if a GK is sent off. After selecting these two conditions, you can proceed to the following items:

Result: Either if you're winning, losing or drawing. Plain simple!
By: The exact goal difference for the event to occur. Either by 1, 2 ,3 ,4, or more than 4 goals. Please note, and this is very important, that, for example, winning for 1 goal is winning by 1-0, 2-1, etc. If the result is 2-0, you're not winning by 1 goal, but by 2 goals. We plan to make this feature more flexible in the future.
After goal: in case you want the event to occur after a goal scored by your team or by the opponent's team. This condition will only be checked if the minute condition is not selected.

Okay, now we'll be talking about the types of events that exist:
Substitution:The most common event, replace one player by the other. Once you program a substitution, you can set the new position for the player that will enter on the field (the same or any of the other field positions). And also set the priority of the substitution: high priority if you want the keep the "new" player out of injury (automatic) replacements or normal if you want to keep the player available for injury subs.
New Player Position / Swap Player Positions: These are two different types of events, but both very easy to understand and apply: at any time of the match you can directly set a player to play in another position of the field. This will easily allow you to set new formations during the match and having full flexibility when doing it. Also with the second event you can change swap players position by simply setting the two players on the even.
Change of Style: You can change your playing style during the match.
Preferred Side: So that you can change the side of your attacking flow during the game.

These events might allow you to totally change the outcome of a match, for the best and for the worst so use them wisely. There are some things you should also know about match events:
-The ME will only load 100 events per match
-The events will be executed in the order they are presented on the page
-You need to respect formation rules once you change your team's formation during a match. For example if you have a group of substitutions planned at the 60th minute in which you will change from a 4-2-4 to 5-3-2 in which you would move one midfielder to the defense (first change) and two forward to the midfield (second & third change). This case would fail as after the first substitution your formation was a 5-1-4 that is an irregular formation (you need to have at least 2 midfielders). In order to make a successful change you would need to make the second & third change first. This was you would be moving from a 4-2-4 to an 4-4-2 and finally from this last to the 5-3-2.

There's another important characteristic regarding formation changes and player ratings. As player ratings are calculated once the match starts the formation changes and its related players repositioning aren't taken into consideration once a re-positioning occurs.

Other important aspects regarding your strategy
Despite not being directly related with specific tactics for matches, there are two things we'd like to mention on this section: Lectures, Team Morale and Team Integration.

Lectures
By going to Team >> Games (left menu) and then selecting Lecture in the top menu, you'll have access to a page where you can lecture your players. Lectures basically affect your team morale. As you can read in the “The Match” section of this manual, team morale is a ME variable you might not want to forget.

The variables that will help a lecture to be successful or not are basically your starting eleven's professionalism level, your current team's morale and your latest match results. You should know that, usually, lectures won't have positive effects in case your player's professionalism isn't at least average. So be wise when you lecture your players: bad lectures will have negative effects on the team's morale!

The only lecture that does not have a negative effect is the “You should always respect your opponents”.

Team Morale
As said previously, team morale is something you might not want to ignore. It's not a key part of the ME, but it will definitely help you win matches in case you are able to optimize this feature of the game. Team morale is only affected by results on league and cup matches. Winning matches will make your morale go higher and losing will have the opposite effect. This is especially valid in sequences (wins/loses in a row)! Lectures will help you to increase the team morale in case you use them well.

Team Integration
As team morale, this is also an important feature you might not want to ignore/forget. Just imagine this feature as when, in real-life, a team is made up of players that play together for a long time and know each other very well: the ultimate consequence is that they'll play much better as a team. In PManager is more or less the same: each player has its own integration level. This integration level is increased with league, cup and friendly matches. The overall integration level of the team is the integration average for the players in the starting eleven. Only the team integration of these eleven players will be used for match purposes.

Once a player joins a team this integration counter is reset. Team integration has a limit (as well as the individual integration level of players).

The ME will only use the integration level of the players that are currently playing.