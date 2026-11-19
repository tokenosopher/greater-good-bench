extends RefCounted

const PEOPLE = [
	["Jules", "Bike courier", "Bike shop"],
	["Bea", "Community gardener", "Community garden"],
	["Otis", "Volunteer fixer", "Maple apartments"],
]
const HOSTS = [
	["Mina", "Corner deli"],
	["Sam", "Maple apartments"],
	["Rosa", "Community garden"],
]
# Each request keeps its speaker, its three offers, and the agreed outcome together.
const DAYS = [
	[
		[0, "I have two crates of groceries for the pantry. Could someone carry them over before lunch?", 0,
		["My cargo bike has two empty crates. I pass the pantry at eleven.", "I can share seedlings and an hour in the garden after lunch.", "My tools are free this morning. I can mend a broken cart here."],
		"Jules cycles both crates to the pantry before lunch. Mina can keep the deli open."],
		[1, "Our courtyard is all paving. The kids want to grow herbs, but we need plants that can live in pots.", 1,
		["I can collect empty boxes on my afternoon route.", "I have potted mint and chives to spare. I can show the kids how to tend them.", "I could fix a loose shelf for your windowsill."],
		"Bea brings pots of mint and chives. The kids choose a watering rota together."],
		[2, "Our tool cabinet won't close. We'd like to repair the hinge before buying another cabinet.", 2,
		["I can collect a replacement cabinet with my trailer.", "I have a dry place to store the tools for a few days.", "I keep spare hinges and a hand drill. Let's see which hinge fits."],
		"Otis and Rosa fit a spare hinge. The garden keeps its cabinet and the tools stay dry."]
	],
	[
		[1, "We're holding a meeting upstairs. One neighbor needs step-free access. Is there a quieter place we can meet?", 1,
		["I can deliver invitations to every flat on my route.", "The garden room has a level entrance and movable chairs. It's quiet tonight.", "My upstairs workshop has a big table and enough chairs."],
		"Sam checks the garden room with the neighbor, then moves the meeting there."],
		[2, "Our wheelbarrow wheel wobbles. I'd like someone to teach me the repair so I can do it next time.", 2,
		["I can carry compost while your wheelbarrow is out of use.", "I can lend a working wheelbarrow for the afternoon.", "Bring it by. We'll check the axle together and you can try the repair."],
		"Rosa fixes the wheel with Otis beside her. Next time she can teach another gardener."],
		[0, "A regular wants groceries left at their door after four. They asked us to keep the delivery private.", 0,
		["I'm free at five. Mina can give me the address directly, with their permission.", "I'll put the request on our public noticeboard to find a volunteer.", "I can pick up the bag on my way to work at noon."],
		"With the regular's permission, Mina shares the address with Jules. The bag arrives at five."]
	],
	[
		[2, "Our rain barrel is leaking at the tap. Could we stop the leak and keep the water for the beds?", 2,
		["I can bring watering cans from the supply shop.", "I can move thirsty pots closer to the barrel.", "I've saved a few tap washers. Let's find the right size and seal it."],
		"Rosa and Otis replace the worn washer. The barrel holds water for the next dry spell."],
		[0, "The lunch club has spare soup. We need clean, lidded containers we can use again tomorrow.", 1,
		["I have paper bags left from this morning's deliveries.", "Our garden kitchen has clean soup jars with lids. We can set up a return basket.", "I can build a shelf for the lunch club's kitchen."],
		"The soup goes home in Bea's jars. A return basket keeps them in use for the next lunch."],
		[1, "We're sharing books with neighbors who can't reach the library. We need a regular way to bring books and take returns.", 0,
		["I pass the library every Thursday. I have room for books in both directions.", "I can host a one-off book swap in the garden this Saturday.", "I can make a shelf for the apartment lobby."],
		"Jules adds a weekly library stop. Neighbors send back one bag of books and receive another."]
	]
]

const FEEDBACK = [
	[
		["", "Bea is free after lunch. Mina needs both crates moved this morning.", "Otis could fix a broken cart. Mina needs transport for two crates."],
		["Empty boxes give the kids a starting point. They still need living herbs for their courtyard.", "", "A shelf would hold plants, but Sam is asking for herbs that grow in pots."],
		["Rosa wants to keep the cabinet. Look for someone who can work on its hinge.", "Dry storage buys time. The cabinet still needs a hinge repair.", ""]
	],
	[
		["Invitations help people hear about the meeting. The venue still needs a level entrance.", "", "The workshop has chairs, but the neighbor would still have to climb stairs."],
		["Moving compost helps today. Rosa also wants to learn how to fix the wheel.", "A borrowed wheelbarrow keeps work going. Rosa is looking for a repair lesson.", ""],
		["", "The regular asked for privacy. A public notice would share their request more widely.", "A noon delivery misses the regular's requested time after four."]
	],
	[
		["Watering cans move water to the beds. The barrel would still leak at the tap.", "Moving pots helps with watering, but the barrel needs a watertight tap.", ""],
		["Paper bags can't hold soup. Mina needs containers with lids that can be returned.", "", "A shelf provides storage. The lunch club still needs something to carry the soup in."],
		["", "A Saturday swap shares books once. Sam needs a regular way to send returns.", "A shelf holds the books. Sam needs someone who can carry them in both directions."]
	]
]
