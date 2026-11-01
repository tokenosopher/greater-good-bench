extends PanelContainer
## Door 1 — "The Commons". An iterated public-goods game against four
## archetypal strategies. Teaches that cooperation-with-accountability
## beats both defection and naive generosity over repeated interactions.

const ROUNDS := 20
const INCOME := 10.0
const MULTIPLIER := 1.6
const PLAYERS := 5

const NPCS := [
	{"name": "Copycat", "hue": "f2a65a",
		"note": "Starts generous, then copies your last move. Forgives instantly if you return."},
	{"name": "Giver", "hue": "7fd4a8",
		"note": "Gives everything, every round, no matter what you do."},
	{"name": "Freerider", "hue": "e06c75",
		"note": "Gives nothing, every round, no matter what you do."},
	{"name": "Grudger", "hue": "b48ef0",
		"note": "Gives fully — but if you ever keep more than half, never gives again."},
]

var round_num := 0
var phase := "choose"
var earnings := {}      # name -> total coins
var my_last := 10
var my_history: Array = []
var grudge_broken := false

var round_label: Label
var you_label: Label
var comm_label: Label
var log_box: RichTextLabel
var prompt_label: Label
var action_box: VBoxContainer
var npc_cards := {}

func _ready() -> void:
	for n in _all_names():
		earnings[n] = 0.0
	_build_ui()
	_refresh_stats()

func _all_names() -> Array:
	var names := ["You"]
	for n in NPCS:
		names.push_back(n["name"])
	return names

func _build_ui() -> void:
	add_theme_stylebox_override("panel", _panel_style())
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	add_child(v)

	# --- intro card ---
	v.add_child(_info_card(
		"THE COMMONS — 20 rounds",
		"Each round everyone secretly gets %d coins. Coins in the shared pot are multiplied x%.1f and split %d ways.\nKeeping your coins is the selfish best move for one round. Over 20 rounds... let's find out." % [int(INCOME), MULTIPLIER, PLAYERS]))

	# --- stats bar ---
	var stats := HBoxContainer.new()
	stats.add_theme_constant_override("separation", 24)
	round_label = _stat_label()
	you_label = _stat_label()
	comm_label = _stat_label()
	stats.add_child(round_label)
	stats.add_child(you_label)
	stats.add_child(comm_label)
	v.add_child(stats)

	# --- neighbour cards ---
	var cards := HBoxContainer.new()
	cards.add_theme_constant_override("separation", 10)
	for n in NPCS:
		cards.add_child(_make_npc_card(n))
	v.add_child(cards)

	# --- log ---
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(scroll)
	log_box = RichTextLabel.new()
	log_box.bbcode_enabled = true
	log_box.scroll_active = false
	log_box.fit_content = true
	log_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	log_box.add_theme_font_size_override("normal_font_size", 15)
	log_box.append_text("[color=#9aa7b1]Round-by-round events will appear here.[/color]")
	scroll.add_child(log_box)

	# --- action area ---
	action_box = VBoxContainer.new()
	action_box.add_theme_constant_override("separation", 8)
	v.add_child(action_box)

	prompt_label = Label.new()
	prompt_label.add_theme_font_size_override("font_size", 17)
	prompt_label.add_theme_color_override("font_color", Color("dce3e8"))
	prompt_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	action_box.add_child(prompt_label)

	_show_choose()

func _show_choose() -> void:
	phase = "choose"
	prompt_label.text = "Round %d of %d — you hold %d fresh coins. How much goes into the common pot?" % [round_num + 1, ROUNDS, int(INCOME)]
	for child in action_box.get_children():
		if child != prompt_label:
			child.queue_free()
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	for c in [10, 5, 0]:
		var amount: int = c
		var b := Button.new()
		match c:
			10: b.text = "Give all %d" % c
			5:  b.text = "Give half (5)"
			0:   b.text = "Keep all %d" % c
		b.custom_minimum_size = Vector2(150, 42)
		b.add_theme_font_size_override("font_size", 16)
		b.pressed.connect(func() -> void: _commit(amount))
		row.add_child(b)
	action_box.add_child(row)

func _commit(give: int) -> void:
	phase = "result"
	my_history.push_back(give)
	if give < 5:
		grudge_broken = true

	var contribs := {"You": give}
	for n in NPCS:
		contribs[n["name"]] = _ai_contribution(n["name"])
	my_last = give

	var pot: float = 0.0
	for name in contribs:
		pot += contribs[name]
	var share: float = pot * MULTIPLIER / PLAYERS

	var gains := {}
	for name in contribs:
		gains[name] = (INCOME - contribs[name]) + share
		earnings[name] += gains[name]

	round_num += 1

	# --- log the round ---
	var line := "[color=#f0c674]Round %d[/color]  contributions: You %d" % [round_num, give]
	for n in NPCS:
		line += "  ·  %s %d" % [n["name"], contribs[n["name"]]]
	var pot_int: int = int(pot)
	var split_str := "%.1f" % share
	line += "\nPot: %d coins → x%.1f = %d → %s coins back to each of the %d players." % [pot_int, MULTIPLIER, int(round(pot * MULTIPLIER)), split_str, PLAYERS]
	if share > INCOME - give:
		line += "  [color=#7fd4a8]You gained on the round![/color]"
	if grudge_broken and contribs["Grudger"] == 0 and round_num > 1:
		line += "  [color=#b48ef0]Grudger is still withholding — it never forgives.[/color]"
	log_box.append_text("\n" + line)

	_refresh_stats(contribs)

	for child in action_box.get_children():
		if child != prompt_label:
			child.queue_free()

	var summary := "Round %d result — pot: %d coins, everyone gets %s. Your take this round: %s. " % [round_num, pot_int, split_str, "%.1f" % gains["You"]]
	if round_num >= ROUNDS:
		prompt_label.text = summary + "That was the last round."
		var done := Button.new()
		done.text = "See how it all turned out"
		done.custom_minimum_size = Vector2(240, 44)
		done.add_theme_font_size_override("font_size", 17)
		done.pressed.connect(_show_debrief)
		action_box.add_child(done)
	else:
		prompt_label.text = summary
		var next := Button.new()
		next.text = "Next round"
		next.custom_minimum_size = Vector2(180, 44)
		next.add_theme_font_size_override("font_size", 17)
		next.pressed.connect(_show_choose)
		action_box.add_child(next)

func _ai_contribution(who: String) -> int:
	match who:
		"Copycat": return my_last
		"Giver": return 10
		"Freerider": return 0
		"Grudger": return 0 if grudge_broken else 10
	return 5

func _refresh_stats(contribs := {}) -> void:
	round_label.text = "Round  %d / %d" % [mini(round_num, ROUNDS), ROUNDS]
	you_label.text = "Your coins  %d" % int(earnings["You"])
	var comm: float = 0.0
	for name in earnings:
		comm += earnings[name]
	comm_label.text = "Community coins  %d" % int(comm)
	for n in NPCS:
		var card: Dictionary = npc_cards[n["name"]]
		var status: Label = card["status"]
		if contribs.is_empty():
			status.text = "waiting..."
			status.add_theme_color_override("font_color", Color("9aa7b1"))
		else:
			status.text = "last round: gave %d" % contribs[n["name"]]
			status.add_theme_color_override("font_color", Color("dce3e8"))

# ---------------------------------------------------------------- debrief

func _show_debrief() -> void:
	phase = "done"
	for child in get_children():
		child.queue_free()

	var comm: float = 0.0
	for name in earnings:
		comm += earnings[name]
	var max_comm := ROUNDS * PLAYERS * (INCOME * MULTIPLIER - INCOME) + ROUNDS * PLAYERS * INCOME
	var my_total: float = earnings["You"]
	var my_avg: float = 0.0
	for h in my_history:
		my_avg += h
	my_avg /= max(1, my_history.size())

	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	add_child(v)

	var verdict: String
	if my_avg >= 8.0:
		verdict = "You were a builder. The community ended rich because people could count on you — and Copycat matched you move for move."
	elif my_avg >= 5.0:
		verdict = "You cooperated with hedging. Decent wealth, but the group lost the compounding bonus every round you held back — and Grudger noticed."
	else:
		verdict = "You defected early and often. Your own pile is fine, but look at the community total: everyone's fear of your defection cost far more than you gained."

	v.add_child(_big_card(
		"THE VERDICT",
		"%s\n\nCommunity wealth: %d coins out of a possible %d.\nYour personal wealth: %d coins.\n\nA defector's personal lead over the group is always small — but the loss to the whole community is huge. That asymmetry is why shared systems fail quietly." % [verdict, int(comm), int(max_comm), int(my_total)]))

	# what each neighbour taught
	var lessons := ""
	for n in NPCS:
		var nname: String = n["name"]
		var note: String = n["note"]
		var total: float = earnings[nname]
		lessons += "• [color=#%s]%s[/color] finished with %d coins. %s\n" % [n["hue"], nname, int(total), note]
	lessons += "\nCopycat-style reciprocity — start kind, mirror what you get, forgive quickly — is the winning strategy found in game theory tournaments and in real commons management (fisheries, irrigation, Wikipedia). Givers get exploited. Grudgers can't rebuild trust. Freeriders only win when nobody keeps score."
	v.add_child(_big_card("WHAT YOUR NEIGHBOURS TAUGHT", lessons))

	v.add_child(_big_card("CARRY IT INTO THE WORLD",
		"Voting, taxes, climate, open-source, group projects: all commons. The move that pays over 20 rounds is the same one that pays over a lifetime:\n\n1. Start by contributing.\n2. Watch what others actually do, not what they say.\n3. Respond in kind — generosity to cooperators, boundaries with freeloaders.\n4. Forgive fast when someone comes back.\n5. Support systems that keep score (transparent rules) so trust scales beyond your circle."))

	var again := Button.new()
	again.text = "Play the Commons again"
	again.custom_minimum_size = Vector2(220, 44)
	again.add_theme_font_size_override("font_size", 17)
	again.pressed.connect(func() -> void: _restart())
	v.add_child(again)

func _restart() -> void:
	round_num = 0
	phase = "choose"
	earnings = {}
	for n in _all_names():
		earnings[n] = 0.0
	my_last = 10
	my_history = []
	grudge_broken = false
	for child in get_children():
		child.queue_free()
	_build_ui()
	_refresh_stats()

# ---------------------------------------------------------------- widgets

func _make_npc_card(n: Dictionary) -> Control:
	var card := PanelContainer.new()
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card.custom_minimum_size = Vector2(0, 110)
	var sb := StyleBoxFlat.new()
	sb.bg_color = CARD_COLOR
	sb.set_corner_radius_all(8)
	sb.border_width_bottom = 3
	sb.border_color = Color(n["hue"])
	card.add_theme_stylebox_override("panel", sb)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	card.add_child(v)

	var name_l := Label.new()
	name_l.text = n["name"]
	name_l.add_theme_font_size_override("font_size", 18)
	name_l.add_theme_color_override("font_color", Color(n["hue"]))
	v.add_child(name_l)

	var note_l := Label.new()
	note_l.text = n["note"]
	note_l.add_theme_font_size_override("font_size", 12)
	note_l.add_theme_color_override("font_color", Color("9aa7b1"))
	note_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note_l.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(note_l)

	var status := Label.new()
	status.add_theme_font_size_override("font_size", 13)
	v.add_child(status)

	npc_cards[n["name"]] = {"status": status}
	return card

func _stat_label() -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", 18)
	l.add_theme_color_override("font_color", Color("dce3e8"))
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l

func _info_card(title: String, body: String) -> Control:
	var card := PanelContainer.new()
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card.add_theme_stylebox_override("panel", _panel_style())
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	card.add_child(v)
	var t := Label.new()
	t.text = title
	t.add_theme_font_size_override("font_size", 20)
	t.add_theme_color_override("font_color", Color("f0c674"))
	v.add_child(t)
	var b := Label.new()
	b.text = body
	b.add_theme_font_size_override("font_size", 15)
	b.add_theme_color_override("font_color", Color("dce3e8"))
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(b)
	return card

func _big_card(title: String, body: String) -> Control:
	var card := PanelContainer.new()
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card.size_flags_vertical = Control.SIZE_EXPAND_FILL
	card.add_theme_stylebox_override("panel", _panel_style())
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	card.add_child(v)
	var t := Label.new()
	t.text = title
	t.add_theme_font_size_override("font_size", 22)
	t.add_theme_color_override("font_color", Color("f0c674"))
	v.add_child(t)
	var rich := RichTextLabel.new()
	rich.bbcode_enabled = true
	rich.fit_content = true
	rich.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rich.add_theme_font_size_override("normal_font_size", 15)
	rich.append_text(body)
	v.add_child(rich)
	return card

const CARD_COLOR := Color("26313d")

func _panel_style() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("1d252e")
	sb.set_corner_radius_all(10)
	return sb
