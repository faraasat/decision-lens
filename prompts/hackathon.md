I am participating in hackathon: Sky’s the Limit - Cloud9 x JetBrains Hackathon. The basic details are as follows:

What to Build

Entrants must build or update a working application that is:

A comprehensive Assistant Coach powered by Data Science and AI: that merges micro-level player analytics with macro-level strategic review. Inspired by Moneyball (Jonah Hill’s Peter Brand), this near-real-time application analyzes historical match data to provide a holistic and actionable review. The platform crunches the numbers to identify recurring individual mistakes and connects them directly to their impact on team-wide macro strategy, generating targeted insights for coaches and players.

Descriptive details for this coach is as follows:

Category 1: Comprehensive Assistant Coach
What to Build
You are hired as a Data Scientist & AI Strategist for Cloud9. You are tasked by the coaching staff to build a comprehensive "Assistant Coach" that can analyze performance data and provide actionable strategic insights.

Inspired by Moneyball's Peter Brand, you will build a near-real-time application that merges micro-level player analytics with macro-level strategic review. Your tool must analyze an individual player's Match data to provide a holistic and actionable review for coaches and players.

Assistant Coach Requirements
Your AI assistant could perform the following core functions, powered by official esports data from GRID (for League of Legends and VALORANT).

Provide Personalized Player/Team Improvement Insights: Analyze individual player data and/or team data to identify and present recurring mistakes, suboptimal patterns, or statistical outliers. The goal is to develop a tool that surfaces low-level insights, pinpoints areas for improvement, analyzes the data, and provides strategic insights for the team.

Generate an Automated Macro Game Review: Use historical match data (e.g., from a recently concluded match) to automatically generate a review agenda. This agenda must highlight critical macro-level decision points, team-wide errors, or significant strategic moments.

How can you take it to the next level?

Predict Hypothetical Outcomes: Use historical data to model and predict the likely outcomes of alternative "what if" scenarios. This feature should allow a coach to query the tool about a past in-game decision or event in reference to the Macro Game Review (see above) and receive a predictive analysis. A key factor for success here will be the accuracy of this feature.

You have the freedom to develop the project in any direction you consider valuable, leveraging your creative ideas and the available data.

Demonstration Prompts & Required Outputs
Your submission (in your video and/or a live demo) must demonstrate your tool successfully processing data and generating insights. The following prompts are examples only, intended to illustrate the type and depth of analysis your tool should be capable of. Hackers have the freedom to and are welcome to let the creative juices flow!

Important: Your submission is not bound by these specific examples. You will not receive additional points for successfully replicating these exact outputs. The tool will be judged on its overall functionality and value.

For all outputs, your system should provide the data or reasoning behind its insights.

1. Main Prompt: Personalized Insight Generation
   Task: "Analyze this player's match data and provide direct, data-backed feedback."

Example Output (VALORANT):

Data 1: C9 loses nearly 4 out of 5 rounds (78%) when OXY dies 'for free' (without a KAST)

Sample Insight 1: Player OXY's opening duel success rate heavily impacts the team, leading to a 78% round loss rate when dying first without a KAST. Recommend reviewing opening pathing and strategy.

Sample Insight 1: Our strategy must ensure OXY is always in a position to get KAST. If he dies, it must be for a trade, kill, or assist, as 78% of rounds are lost otherwise.

Data 2: C9 loses both pistol rounds 7/10 times they play 1-3-1 on Split.

Sample Insight 2: Review starting composition or pistol round strategies on Split.

An example of Data + Insight: C9 won the force buy in the 2nd round 7/10 times in the last 15 maps, but subsequently lost rounds 3 and 4, which started a snowball effect, having an overall negative impact on their game.

Example Output (League of Legends):
Data: When our jungler ganks top lane pre-6 minutes, their success rate is 22%. When ganking bot lane pre-6, the success rate is 68%.

Sample Insight: This player's early topside pathing is frequently counter-jungled or results in low-impact ganks. Recommend prioritizing botside pathing to secure early drake control and play to the higher-success-rate lane.

2. Main Prompt: Automated Macro Review Generation
   Task: "Take the data from this concluded match and generate a Game Review Agenda."

Example Output (VALORANT):

Generated Game Review Agenda:

Match: BO1

Opponent: [Team X]

Map: Corrode

Composition: 1-3-1

Pistol Rounds: Lost both pistols.

Eco Management: Unsuccessful force-buy on Round 2 led to a bonus round loss (Round 3). Review force-buy vs. save criteria.

Mid-Round Calls: 4/10 attacking rounds on Map 1 saw a late A-main push with <20s left, resulting in 3 losses.

Ultimate Economy: On Map 1, only 7 orbs were picked up vs. 11 orbs picked up by the enemy team.

Let the creative juices flow!

Example Output (League of Legends):

Generated Game Review Agenda:

First Drake setup: Inadequate deep vision, teleport wards not swept.

Atakhan setup: Excessive unspent gold in player inventories, suggest a base timer 45s prior, after 2nd tower down in mid lane.

Isolated deaths: 23:20 (Top in Top), 27:15 (Mid in Bot, before drake spawn).

Teleport use: Poor TP flank at 19:40 led to a lost teamfight.

Let the creative juices flow!

3. Main Prompt: Hypothetical Outcome Prediction
   Task: "Answer this 'what if' question about a past strategic decision."

Example Query (VALORANT):

“On Round 22 (score 10-11) on Haven, we attempted a 3v5 retake on C-site and lost. Would it have been better to save our weapons?”

Example Output (VALORANT):

Analyzing the game state (player health, weapons, enemy utility, time) and predicting the probability. e.g., "The 3v5 retake had a 15% probability of success. Conceding the round and saving 3 rifles would have given the team a 60% chance to win the following gun round, versus the 35% chance they had on a broken buy. Saving was the superior strategic choice."

Example Query (League of Legends):

“C9 contested a Drake at 24:15 and everybody died. Would it have been better to not contest the objective at all?”

Example Output (League of Legends):

Analyzing the game state (gold, items, levels, vision, other objectives) and predicting the likely outcome of conceding the objective (e.g., "85% probability of 2 turret kills and +200 XP advantage per player") versus contesting it (e.g., "22% probability of winning the fight or the objective").

--

Judges & Criteria

Eligible submissions will be evaluated by a panel of judges selected by the Sponsor in its sole and absolute discretion (the “Judges”). Judges may be employees of the Sponsor or third parties, may or may not be listed individually on the Hackathon Website, and may change before or during the Judging Period. Judging may take place in one or more rounds with one or more panels of Judges, at the discretion of the sponsor.

Stage One) The first stage will determine via pass/fail whether the ideas meet a baseline level of viability, in that the Project reasonably fits the theme and reasonably applies the required APIs/SDKs featured in the Hackathon.

Stage Two) All Submissions that pass Stage One will be evaluated in Stage Two based on the following equally weighted criteria (the “Judging Criteria”):

Entries will be judged on the following equally weighted criteria, and according to the sole and absolute discretion of the judges:

Technological Implementation:
Does the project demonstrate quality software development? Does the project leverage the JetBrains IDEs or AI Coding Agent Junie (encouraged)? How is the quality of the code?

Design:
Is the user experience and design of the project well thought out?

Potential Impact:
How big of an impact could the project have on the specific community or target audience?

Quality of the Idea:
How creative and unique is the project?

The judges will score each criterion out of five (5) points for a maximum total of twenty (20) points. The scores from the Judges will determine the potential winners of the applicable prizes. The Entrant(s) that are eligible for a Prize, and whose Submissions earn the highest overall scores based on the applicable Judging Criteria, will become potential winners of that Prize.

Most Valuable JetBrains Software or Junie Feedback Submission Criteria

Enter by submitting your feedback through your Devpost submission form. Eligible Feedback Submissions will be evaluated based on the completeness, viability, and potential impact of the feedback. Sponsor reserves the right to choose any one feedback submission as the winner.

Best Written Blog Post Submission Criteria

Enter by submitting your blog post link to your Devpost submission form. Eligible Blog Post Submissions may be posted on any public platform and must be publicly accessible. Sponsor reserves the right to choose any one post as the winner.

---

For now just analyze it, review it and internalize it.