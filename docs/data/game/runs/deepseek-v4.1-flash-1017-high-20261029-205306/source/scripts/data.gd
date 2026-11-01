extends RefCounted
## All written content for Common Ground lives here.
## Each scenario has two parties, three hidden interests each, three genuine
## synergies, and six decoy pairings that look plausible but leave a need unmet.

static func scenarios() -> Array:
	return [
		{
			"id": "mill",
			"chapter": "Chapter I",
			"title": "The Mill and the River",
			"subtitle": "A factory town, divided by the water that runs through it.",
			"setting": "Kestrel Falls has one mill and one river. The mill employs a third of the town. The river is where everyone swims. A new report says the mill's runoff is unsafe. The mill says it cannot afford to change. The river group says it cannot afford not to. You have been asked to chair the conversation.",
			"a": {
				"name": "The Mill Workers",
				"role": "Assembly line & maintenance crew",
				"quote": "\"We built this town. We are not going to be thrown away.\"",
				"color": "#C9853F",
				"interests": [
					{
						"id": "a1",
						"title": "Steady paychecks",
						"need": "Reliable income for rent, food, and school.",
						"fear": "Being discarded when the machines change.",
						"tag": "LIVELIHOOD"
					},
					{
						"id": "a2",
						"title": "A voice in the decision",
						"need": "A seat at the table when the mill's future is decided.",
						"fear": "Plans made over our heads.",
						"tag": "DIGNITY"
					},
					{
						"id": "a3",
						"title": "A future for our kids",
						"need": "Jobs here that are still here in ten years.",
						"fear": "The town slowly emptying out.",
						"tag": "FUTURE"
					}
				]
			},
			"b": {
				"name": "The River Community",
				"role": "Residents, parents & river stewards",
				"quote": "\"Our children swim in that water. We are done being told to wait.\"",
				"color": "#3E7C8C",
				"interests": [
					{
						"id": "b1",
						"title": "Clean water",
						"need": "Safe drinking water and a living river.",
						"fear": "Illness that nobody will admit to.",
						"tag": "HEALTH"
					},
					{
						"id": "b2",
						"title": "Honest answers",
						"need": "Open data and someone accountable for it.",
						"fear": "Being ignored or lied to.",
						"tag": "TRUST"
					},
					{
						"id": "b3",
						"title": "A living town",
						"need": "A local economy that does not poison its own home.",
						"fear": "Decline dressed up as progress.",
						"tag": "BELONGING"
					}
				]
			},
			"synergies": {
				"a1|b1": {
					"title": "A job guarantee, inside a clean retrofit",
					"text": "Fund a filtration and efficiency retrofit, with every mill job protected through the transition. The workers keep their paychecks; the river gets cleaner every quarter."
				},
				"a2|b2": {
					"title": "A jointly owned oversight board",
					"text": "Workers and river residents co-own the data, the inspections, and the decisions. No side gets to audit the other without being audited itself."
				},
				"a3|b3": {
					"title": "A local clean manufacturing fund",
					"text": "Use the mill's site, skills, and supply chain to seed new clean industry and apprenticeships. A future the town can actually stay for."
				}
			},
			"decoys": {
				"a1|b2": {
					"text": "The workers would take the pay guarantee. The river group hears \"trust us\" with no independent check. Income is met; accountability is not."
				},
				"a1|b3": {
					"text": "Jobs now, but the river keeps taking the cost. The town's future is being borrowed from the people downstream."
				},
				"a2|b1": {
					"text": "A clean river and a voice for residents, but the workers lose their livelihoods without a plan. That is a win built on someone else's loss."
				},
				"a2|b3": {
					"text": "A seat at the table, but the table cannot decide anything. Voice without power becomes another meeting."
				},
				"a3|b1": {
					"text": "The vision is real, but the water is unsafe now. A future that arrives too late is not a bridge."
				},
				"a3|b2": {
					"text": "Transparency is not a transition plan. A report can describe a future without building one."
				}
			},
			"epilogue": "The retrofit broke ground in spring. The river tested clean by the next summer, and the first apprenticeship class graduated two years later. Nobody got everything they first demanded. Everybody got the thing they were actually afraid of losing.",
			"lesson": "The fight looked like jobs versus water. Underneath, both sides were afraid of being left behind. The answer was not to split the difference; it was to build something neither side could build alone."
		},
		{
			"id": "lot",
			"chapter": "Chapter II",
			"title": "The Shared Table",
			"subtitle": "One vacant lot. Two groups who have waited too long.",
			"setting": "A vacant lot sits between the market square and the housing blocks. The market vendors want it for stalls and storage. The youth league wants a pitch. Both have been told to \"wait their turn\" for years. The lot has room for more than one story.",
			"a": {
				"name": "The Market Vendors",
				"role": "Family stalls & neighborhood grocers",
				"quote": "\"We keep this neighborhood fed. We need a place that is ours.\"",
				"color": "#C46B48",
				"interests": [
					{
						"id": "a1",
						"title": "Affordable space",
						"need": "A stable, low-cost place to sell and store goods.",
						"fear": "Rents rising until only chains can stay.",
						"tag": "LIVELIHOOD"
					},
					{
						"id": "a2",
						"title": "A welcoming neighborhood",
						"need": "A market that feels like a front porch, not a border.",
						"fear": "Being pushed to the edges of town.",
						"tag": "BELONGING"
					},
					{
						"id": "a3",
						"title": "A clean, safe common",
						"need": "A lot that is lit, clean, and looked after.",
						"fear": "Neglect turning into danger.",
						"tag": "SAFETY"
					}
				]
			},
			"b": {
				"name": "The Youth League",
				"role": "Coaches, parents & players",
				"quote": "\"Our kids are not a nuisance. They just need somewhere to play.\"",
				"color": "#668C4B",
				"interests": [
					{
						"id": "b1",
						"title": "A place to play",
						"need": "A real pitch with room for practice and games.",
						"fear": "Another summer with nowhere to go.",
						"tag": "PLAY"
					},
					{
						"id": "b2",
						"title": "Recognition for our kids",
						"need": "To be seen as part of the neighborhood, not a problem.",
						"fear": "Being treated as a nuisance.",
						"tag": "DIGNITY"
					},
					{
						"id": "b3",
						"title": "Community safety",
						"need": "A safe route to the lot and trustworthy adults around.",
						"fear": "Violence and idle afternoons.",
						"tag": "SAFETY"
					}
				]
			},
			"synergies": {
				"a1|b1": {
					"title": "One lot, two rhythms",
					"text": "Market mornings, sports evenings, and a shared storage shed. Both needs fit because time was the resource neither side had counted."
				},
				"a2|b2": {
					"title": "Youth market ambassadors",
					"text": "Young players help run family market nights and get paid, named, and trusted. The market becomes a front porch; the kids become hosts instead of suspects."
				},
				"a3|b3": {
					"title": "A joint stewardship compact",
					"text": "Shared lighting, cleanups, and a safety walk. Both groups become the people who look after the lot, and both stop fearing the other's presence."
				}
			},
			"decoys": {
				"a1|b2": {
					"text": "Recognition is real, but it does not put a roof over a stall. The vendors still have nowhere to store their goods."
				},
				"a1|b3": {
					"text": "The vendors get space and safety, but the league loses the pitch. Safety built by exclusion is not shared safety."
				},
				"a2|b1": {
					"text": "The kids get their pitch, but the vendors are pushed out. Welcome for one group becomes displacement for another."
				},
				"a2|b3": {
					"text": "A warmer feeling, but the kids still have nowhere to play. Belonging without space is a promise with no floor."
				},
				"a3|b1": {
					"text": "The lot is safe and used, but the vendors' livelihoods are left out. One side's gain is the other's loss."
				},
				"a3|b2": {
					"text": "Recognition without resources. The league is thanked, then sent home."
				}
			},
			"epilogue": "The lot now has awnings in the morning and goalposts at dusk. The market nights are run by teenagers in team colors, and the storage shed has two sets of keys. It is louder than either group imagined, and busier than both.",
			"lesson": "They were not really fighting over a lot. They were fighting to belong somewhere. A shared calendar and a shared job did more than any compromise on square meters."
		},
		{
			"id": "school",
			"chapter": "Chapter III",
			"title": "The Newcomers",
			"subtitle": "An old neighborhood. New families. One crowded school.",
			"setting": "The school on Alder Street is bursting. Long-time residents remember when there was room for everyone. New families arrived after the factory closures and the long journey that followed. At the last meeting, both sides said the other was \"not listening.\" You have the floor.",
			"a": {
				"name": "The Long-time Residents",
				"role": "Neighbors, grandparents & school families",
				"quote": "\"We were here when nobody else wanted to be. Our history matters.\"",
				"color": "#865A77",
				"interests": [
					{
						"id": "a1",
						"title": "Respect for what we built",
						"need": "Our history and contributions acknowledged.",
						"fear": "Being erased from our own neighborhood.",
						"tag": "DIGNITY"
					},
					{
						"id": "a2",
						"title": "Fair access to the school",
						"need": "Our children's classes not overwhelmed.",
						"fear": "Crowding that nobody plans for.",
						"tag": "FAIRNESS"
					},
					{
						"id": "a3",
						"title": "A safe, stable neighborhood",
						"need": "Predictable change and safe streets.",
						"fear": "Rapid change with no say.",
						"tag": "STABILITY"
					}
				]
			},
			"b": {
				"name": "The Newcomer Families",
				"role": "Recently arrived parents & children",
				"quote": "\"We came here for our children. We want to belong, not to take.\"",
				"color": "#4F7CAC",
				"interests": [
					{
						"id": "b1",
						"title": "A good start for our children",
						"need": "Language support, supplies, and a fair chance.",
						"fear": "Our kids falling behind and being blamed.",
						"tag": "OPPORTUNITY"
					},
					{
						"id": "b2",
						"title": "A voice in school decisions",
						"need": "A seat and a vote on the council.",
						"fear": "Decisions made without us.",
						"tag": "VOICE"
					},
					{
						"id": "b3",
						"title": "Belonging in the community",
						"need": "Invitations, not just tolerance.",
						"fear": "Isolation and suspicion.",
						"tag": "BELONGING"
					}
				]
			},
			"synergies": {
				"a1|b3": {
					"title": "Story circles and a welcome table",
					"text": "Long-time residents share the neighborhood's history; new families share their journeys. A mutual welcome, where neither side has to disappear for the other to belong."
				},
				"a2|b1": {
					"title": "A shared school day, expanded",
					"text": "Staggered schedules and a joint push for extra classrooms and language staff. Fair access for residents, a real start for newcomers. The pie gets bigger."
				},
				"a3|b2": {
					"title": "A rotating neighborhood council",
					"text": "Residents and newcomers co-chair a council with real authority over school changes and safety plans. Stability through shared control, not exclusion."
				}
			},
			"decoys": {
				"a1|b1": {
					"text": "A nice heritage week. The school is still crowded on Monday. Respect and opportunity are not the same need."
				},
				"a1|b2": {
					"text": "A voice without power, and history treated as decoration. Neither side gets what it actually needs."
				},
				"a2|b2": {
					"text": "A fair process, but no new capacity. Both sides still fear the same shortage, now with a winner and a loser."
				},
				"a2|b3": {
					"text": "Smaller classes for some, exclusion for others. Stability bought by shutting the door."
				},
				"a3|b1": {
					"text": "More security at the school gate. Safety for some, suspicion for others. A gate is not a welcome."
				},
				"a3|b3": {
					"text": "A welcome banner and a stricter gate. Belonging for some, suspicion for others. Stability bought by making one group feel watched is not shared stability."
				}
			},
			"epilogue": "The welcome table ran every Saturday that autumn. The council's first budget paid for two new classrooms and a language aide. By spring, the argument at the school gate had changed from who belongs to who is picking up the keys.",
			"lesson": "Both sides were protecting something they had built: one a history, the other a future. Respect and belonging are not scarce. They grow when they are shared."
		}
	]


static func field_guide() -> Array:
	return [
		{
			"number": "01",
			"title": "Listen for the interest, not the position",
			"text": "A position is what someone says they want: \"Close the mill.\" An interest is why: \"I am afraid my children will get sick.\" Positions collide. Interests can often be met together."
		},
		{
			"number": "02",
			"title": "Name the fear underneath",
			"text": "Most hard demands are protecting something: safety, dignity, belonging, a future. When a fear is heard out loud, it stops running the conversation from underneath."
		},
		{
			"number": "03",
			"title": "Look for the bigger pie before you split it",
			"text": "Before dividing a scarce thing, ask what could be created, shared, sequenced, or traded. The best agreements are not halfway points; they are new arrangements."
		},
		{
			"number": "04",
			"title": "Attention is a resource",
			"text": "People leave the table when they feel invisible. A fair process needs visible care for everyone in it, not just the loudest or the most powerful."
		},
		{
			"number": "05",
			"title": "A win built on someone's loss is only a delay",
			"text": "If one side must lose for the other to win, the problem has been postponed, not solved. Durable common ground has to include the people who could undo it."
		}
	]


static func opening_lines() -> Array:
	return [
		"You take your seat between the two groups. Nobody looks happy to be here.",
		"You set a blank sheet of paper on the table. Both sides are watching it.",
		"You pour two glasses of water and slide one to each side. The room goes quiet.",
		"One side is talking first. You let them finish before you speak."
	]
