# 14. The Match
The match is where everything happens! The Match Engine (often referred to as the ME) is the core of PManager. You should read this section carefully to understand how the match engine works.

The best thing to do is to read Section 13 and Section 14 – twice.

Basically, the match is divided into 12 zones – as you can see below:
____________
| 1 | 4 | 7 | 10 |
-------------------
| 2 | 5 | 8 | 11 |
-------------------
| 3 | 6 | 9 | 12 |
¯¯¯¯¯¯¯¯¯¯¯¯

Home Team
Zones:
1 Left-Defense
2 Central-Defense
3 Right-Defense
4 Left-Midfield (defensive)
5 Central-Midfield (defensive)
6 Right-Midfield (defensive)
7 Left-Midfield (offensive)
8 Central-Midfield (offensive)
9 Right-Midfield (offensive)
10 Left-Attack
11 Central-Attack
12 Right-Attack

Away Team
Zones:
12 Left-Defense
11 Central-Defense
10 Right-Defense
9 Left-Midfield (defensive)
8 Central-Midfield (defensive)
7 Right-Midfield (defensive)
6 Left-Midfield (offensive)
5 Central-Midfield (offensive)
4 Right-Midfield (offensive)
3 Left-Attack
2 Central-Attack
1 Right-Attack

Note: At the moment, both the defensive and offensive midfield use the same ratings. However, both zones are considered different zones by the Match Engine, and are part of the sequential zones that the ball must pass through when it's played from the defense to the attacking zone.

How does this work?
The ball goes from one point to another, but it always moves horizontally or diagonally – never vertically (the ball can't go from zone 7 to 9, for example).

Both teams have their own zone ratings that are constantly being compared to decide where the ball goes next, and what team gets possession.

For example:
The home team has the ball in zone 6, and a long pass is made to zone 10.

Now, let's imagine all scenarios:
The ball possession goes to the home team:
-> the next comparison will be the zone 10 rating (left attack) vs. the away team zone 10 rating (right defense).
-> If the home team wins this comparison, there will be a scoring opportunity for the home team. And the next comparison will be the home team zone 10 rating (left attack) against the away team goalkeeper rating.

-> If the away team wins it then they will gain ball possession and…

The ball possession goes to the away team:
-> the away team will decide its next pass.
-> and the process is repeated.

How are the zone ratings calculated?
The ratings are calculated mainly based on the players' global skill (a formula combining all player skills. This formula has not been made available to the general public, although some users have succeeded in making their own approaches to what they think it might be). They are also based on the players that are in that specific zone. Example: the home team zone 1 rating is based on the right-defender global skill with a small influence of the average of the team's global skill (of all players)

If you have more than one player in one zone (ex: three central-defenders) then the rating is the average of their global skills.

The ME will, however, give a boost on a team's zone rating if it has more players on that same zone than the other team.
This boost will be higher as higher as the player difference on the zone.
Example: You play with a 3 central-defenders formation against a 1 central-attacker formation. The ME will give your central defense rating a boost and will decrease the central attacking rating of the other team.

There are also other things that might increase or decrease the zone ratings;
- Players: (All the following player items have the influence on the player global skill and not directly on the zone ratings. But of course the zone ratings are based on the player's global skills, so this influence is indirect.)
- Form
- Experience
- Fitness
- Happiness/Unhappiness
- Player playing in wrong positions and sides will have their global skill decreased
- Weather
- Home factor (slightly increased if your stadium is full)
- Advanced Tactics
- Formation Style (Defensive/Attacking)

How do formations influence the ME?
The formation is very important. Your results will depend much on the formation you choose!
Imagine:
If you play with only one central defender against a three-player central attack, your team is likely to suffer a lot of scoring chances if the ball is placed nicely to those three forwards.

Player Ratings
The player ratings represent the player performance in the game in a 0-10 scale. Here are the factors that have influence on a player's rating:
- Fitness
- Weather
- Global skill of the player
- Number of minutes played
- Form
- Experience
- Happiness/Unhappiness
- Player playing in wrong positions and sides (left, center, right)
- Goals
- Goal assists.
- Important tackles
- Saves (for goalkeepers)

Possession
The ball possession is a consequence of the game, and it's not obtained from any direct, known formula. It really tells you how much time in a game the ball was in possession of a certain team. The ball possession is mostly influenced by the passing style of both teams.

Team Integration
This is a very important feature of ME. It your TI has high values it will give all of your zone ratings a boost from 0.5 to 1 stars.
The TI is the sum of the integration of each starting eleven player. Every time a player plays a game, his individual integration value rises. If another team buys the player then his integration value is reset to zero. More details can be found in Section 13.

Match of the Season / Play it Cool (Team Attitude)
MOTS will give your team an extra-boost to all of your zone ratings (almost a whole star on each zone). PIC is the exact opposite of MOTS (also almost a whole star on each zone). The PIC indication at the report will only be shown to you, meaning that in a game where two teams play PIC – you won't be able to see that information through the match report unless one of the teams is yours (and you'll only see if your team played PIC, not your opponent's information)!
For more information please read Section 13.

Team morale / Team professionalism / Lectures
Team morale will give you a separate bonus by itself if it's higher than the other team's morale. The greater the difference between the two teams, the larger the bonus will be. However, if both teams have the same team morale then there will not be a bonus given.
Team professionalism / Lectures are used together: focus in having a starting eleven with good professionalism averages. The lecture "Always respect your opponents" is also very important in cases where your team's morale is higher than your opponent's morale. More details about Lectures can be found in Section 13.

Zone ratings presentation
The zone ratings you see at the end of the match are the average between the ratings at the beginning of the first half and the end of the second half.

What is the relax mode?
The relax mode is a mechanism the Match Engine has that makes the offensive ratings of a team less effective when the team is winning by a large goal difference. Relax mode is automatically activated when there's a 2 goal difference, and increases as the goal difference increases. To ensure that matches don't lose its fun over time, the relax mode is also decreased as the game approaches full time. You'll often read some comments in the match report about this!

Attack on the wings
Attacks through wings will suffer a penalty if there's a defender from the opposing team present in the same zone as the attacker.
If an opposing defender is present, then the penalty given will depend on the number of attackers a team has on the field. If a team plays with the maximum number of attackers (5) there is no penalty. The penalty is greater as the number of attackers decreases. The full penalty will take effect if there is 1 or less attackers playing for the team. This penalization will only be used once the attacking ratings are being compared with the opposite goalkeeper rating.

Stadiums: Pitch Types
All clubs will start with a grassy pitch, by default. Clubs in the top 2 divisions will be obligated to have a grassy pitch. Clubs from the bottom divisions will have the option to downgrade their pitch to "dirt".
Dirty pitches will give a bonus to the team winning the weather event (the normal bonus will be increased by 50%). The downside of having a dirt pitch is that all players will get more tired during a match. Also, a dirt pitch will give you a 10% reduction on the stadium maintenance cost.
For more information about pitch types check Section 12.

Stadiums: Covers/Roofs
Stadium covers will decrease the bonus of the weather events by half.
Stadium covers can be built regardless of the division the club is playing in, and regardless of the type of pitch/size of the stadium.
For more information about stadium covers please check Section 12.

Injuries
Players can get themselves injured during matches. Injuries only happen in matches, and players recover on a daily basis. There are some players that are more prone to injuries than others. Although, this is a hidden attribute.
When a player is injured, the ME will try to replace him with players with the same position and side as the injured player. In case the ME is not able to find players for the same position and side, it will only try to find players sharing the same position. If no players are found for the same position or side then the ME will get any other available player. Please remember that players marked for events won't be available to be selected in an injury substitution.
Another aspect that shouldn't be forgotten is that when you're playing against a team who is using Hard Tackling then your players are more prone to get injured.

As injuries are updated (and decreased) on a daily basis, they are carried over seasons.

Suspensions
In all matches, players can get yellow and red cards. Temperamental players have a higher chance of being booked; and playing in Hard Tackling will probably increase the odds for more cards. Another factor that might influence the number of cards in a match is the referee's type: harsh, passive and fair.

There are 3 types of matches where players can get suspended. League/Cup matches, International team competitions and National team matches. Each one of these groups has a distinct suspension. In friendly and tournament matches there are no suspensions (all players can play even if they are suspended for other competitions), and players sent off during these matches will be able to play all of the other games afterwards. They'll only have to leave the field after the red card.

We'll talk now about suspensions in League and Cup matches. Players will get suspended for 2 or 3 matches when they are sent off with a direct red card. When they are sent off after 2 yellow cards, players will always be suspended for one match. Also, players will get suspended for 1 match whenever they are shown 4 cumulative yellow cards in the same season. So, at yellow card number 4, 8, 12, etc players will be suspended for one match.

Cards for International team competitions and National team matches work more or less the same. This includes an automatic suspension on each series of 4 yellow cards (on ITCs, series of 2 instead of 4).

Suspensions are carried over seasons.

What are “walkovers”?
A walkover (WO) happens when a team fails to present at least 7 players for a match. If this happens, the team will lose by 3-0, they won't receive any gate receipts (if applicable) and players won't train (they'll have non-game training in case of league training). On the other side, the team that won the game by 3-0 will receive gate receipts, 3 points (if applicable) and training for the starting eleven players. They won't get experience points though, and substitutions won't take place.
When two teams fail to present to the match, the final result will be 0-0, but a defeat will be awarded to both teams. If this happens in a match where a decision must be made (in a cup match for example) then a team will be selected randomly to go through to the next round.

I haven't played with a right midfielder but I have a rating at that zone. How?
The rating zone is made up of the rating of the player there (or in this case, none) and a sort of average of the whole team. So you'll hardly get zero on any zone. Also, ATs won give a boost to all zones, including those without players.

How are penalties scored?
This is a direct confrontation between the player that shoots the penalty and the goalkeeper that tries to save it. Goalkeepers will use their global skill to try to save the penalty, and the penalty taker will use a mix/formula between his scoring, technique and global skill. In case the penalty taker wins the confrontation, a goal will be awarded to his team. In case the goalkeeper saves it, the penalty is considered missed.

What are the fitness losses in matches?
They are as follows:
Friendlies / Cup: 1% for players in the 17-23 age range; 2% in 24-30 ; 3% in 31+
League: 2% for players in the 17-23 age range; 3% in 24-30 ; 4% in 31+
NTeams: 2% for players in the 17-23 age range; 3% in 24-30 ; 4% in 31+
Cup PIC: 0% for players in the 17-23 age range; 1% in 24-30 ; 2% in 31+
League PIC: 0% for players in the 17-23 age range; 1% in 24-30 ; 2% in 31+
Cup MOTS: 2% for players in the 17-23 age range; 3% in 24-30 ; 4% in 31+
League MOTS: 3% for players in the 17-23 age range; 4% in 24-30 ; 5% in 31+
NTeams PIC: 0% for players in the 17-23 age range; 1% in 24-30 ; 2% in 31+
NTeams MOTS: 3% for players in the 17-23 age range; 4% in 24-30 ; 5% in 31+

Be aware that if you play on a dirty pitch, you'll have an extra penalization of 2% over these values. Another important feature is that the number of minutes a player plays has a direct influence on the amount of fitness a players loses. For example, imagine that a player would lose 4% in a full match. If he was replaced at half time then he would only lose 2%. You should also know that fitness values cannot hold decimal values. This means that a 0.5 fitness loss is rounded to 1%.