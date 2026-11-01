class_name Household
extends RefCounted
## One household on the lake. The player is a Household too (kind == "you").
## Each neighbour kind models a common human response to a shared resource:
##   steady  - cooperates by default, cuts back when the lake looks thin
##   mirror  - does what it sees others doing (conditional cooperation)
##   hungry  - takes as much as it can, until it learns it does not have to
##   anxious - follows rules gladly, but panics and over-fishes when things drop

var name := ""
var kind := ""
var color := Color.WHITE
var stock := 3.0          # fish on hand
var wellbeing := 50.0     # 0..100
var last_take := 3
var take := 3             # decided this season
var got := 0.0            # actually received this season (lake may run short)
var reform := 0.0         # hungry: grows when shown that trust pays
var in_pact := true       # whether they intend to honour the current limit
var line := ""            # what they said this season
var hungry_seasons := 0
var _rng: RandomNumberGenerator


func _init(p_name: String, p_kind: String, p_color: Color, rng: RandomNumberGenerator) -> void:
	name = p_name
	kind = p_kind
	color = p_color
	_rng = rng


func is_player() -> bool:
	return kind == "you"


func mood() -> String:
	if stock <= 0.0 and hungry_seasons > 0:
		return "hungry"
	if wellbeing >= 75.0:
		return "content"
	if wellbeing >= 45.0:
		return "getting by"
	if wellbeing >= 20.0:
		return "worried"
	return "desperate"


func _pick(options: Array) -> String:
	return options[_rng.randi_range(0, options.size() - 1)]


## Decide how many fish to take this season.
## ctx keys: fish, capacity, trust, pact (limit or -1), others_avg,
##           player_broke, lake_drop, watched
func decide(ctx: Dictionary) -> int:
	var pct: float = ctx.fish / ctx.capacity
	var pact: int = ctx.pact
	var trust: float = ctx.trust
	var t := 3
	in_pact = false
	line = ""

	match kind:
		"steady":
			t = 3
			if pct < 0.45:
				t = 2
			if pct < 0.2:
				t = 1
			if pact >= 0:
				t = mini(pact, t + 1) if pct < 0.3 else pact
				in_pact = true
				line = _pick(["A limit we all keep. Good.", "I'll hold to it.", "Fair is fair."])
			else:
				line = _pick(["We only take what grows back.", "The lake feeds us if we let it.", "Leave some for next year."])

		"mirror":
			t = clampi(roundi(ctx.others_avg), 1, 5)
			if pact >= 0:
				if ctx.player_broke:
					t = clampi(pact + 1, 1, 5)
					line = _pick(["You broke it first. Why should I hold back?", "Rules for me but not for you?"])
				elif trust >= 40.0:
					t = pact
					in_pact = true
					line = _pick(["If everyone keeps it, so will I.", "Fine by me, as long as it's everyone."])
				else:
					line = _pick(["Nobody trusts anybody here. I'll do what the others do.", "I'll believe it when I see it."])
			else:
				line = _pick(["I take what the others take.", "I'm not going to be the fool who holds back."])

		"hungry":
			t = 5
			if reform >= 3.0:
				t = 3
				line = _pick(["Turns out I don't need the whole lake.", "There's enough. I didn't believe that once."])
			else:
				line = _pick(["I'll take what I need.", "Nobody ever gave me anything.", "If I don't, someone else will."])
			if pact >= 0 and (trust >= 65.0 or reform >= 2.0):
				t = pact
				in_pact = true
				line = _pick(["...Alright. I'll keep to it. This time.", "If the others hold, I hold."])
			if ctx.watched and not in_pact and t > 3:
				t -= 1
				line = "I saw you watching."
			if pct < 0.15 and reform < 3.0:
				t = 5
				line = "Better me than nobody."

		"anxious":
			t = 3
			var panic: bool = ctx.lake_drop > 6.0 or pct < 0.3
			if pact >= 0 and trust >= 30.0:
				t = pact
				in_pact = true
				line = _pick(["A rule. Thank goodness, a rule.", "I'll keep it. I just need to know others will."])
				if panic and trust < 50.0:
					t = 5
					in_pact = false
					line = "It's dropping! I have to put something by!"
			elif panic:
				t = 5
				line = _pick(["It's shrinking! Take what you can!", "What if there's nothing next year?"])
			else:
				line = _pick(["Is it... is it still alright?", "I'll take my share. Just my share."])

	# Real hunger pushes anyone to take a little more.
	if stock <= 0.0 and wellbeing < 35.0 and t < 5:
		t += 1
		if kind != "hungry":
			line = "My children are hungry."
	return clampi(t, 0, 5)


## Apply what we received this season and eat.
func settle(need: float) -> void:
	stock += got
	stock -= need
	if stock < -0.01:
		var shortfall: float = -stock / need
		wellbeing -= 12.0 * shortfall
		stock = 0.0
		hungry_seasons += 1
	else:
		hungry_seasons = 0
		wellbeing += 2.0 if stock >= 2.0 else 0.5
	stock = minf(stock, 8.0)   # fish don't keep
	wellbeing = clampf(wellbeing, 0.0, 100.0)
	last_take = take
