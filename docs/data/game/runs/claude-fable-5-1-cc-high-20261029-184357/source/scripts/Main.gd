extends Control
## Common Ground - a small village shares one lake.
## Every season each household decides how much to take. The lake regrows
## in proportion to what is left. The score is the whole village's score.

const SEASONS := 20
const CAPACITY := 100.0
const GROWTH := 0.6
const NEED := 2.0

enum Action { REST, SHARE, WATCH, PACT }

const FaceScript := preload("res://scripts/Face.gd")
const LakeScript := preload("res://scripts/LakeView.gd")

const ACTION_HELP := {
	Action.REST: "Rest: recover a little (+3 wellbeing). Nothing else changes.",
	Action.SHARE: "Share: give one fish from your store to the household that needs it most. Trust grows (+8), and people remember.",
	Action.WATCH: "Watch: see exactly what each household takes this season. People fish more carefully when they are seen.",
	Action.PACT: "Propose a limit: ask every household to take no more than this each season. Whether they keep it depends on trust, and on whether you keep it yourself.",
}

const REAL_THINGS := [
	"Pick one shared thing you use - a kitchen, a street, a group chat, a park - and leave it a little better than you found it this week.",
	"Thank someone, by name, for work they did that nobody usually notices.",
	"Ask someone what they actually need before deciding what to give them.",
	"Keep one small promise you made and were quietly planning to let slide.",
	"When you next feel the urge to grab your share before it runs out, pause and check whether it is really running out.",
	"Tell someone the rule you are following and why. People keep agreements they can see others keeping.",
	"Give something away that you have more of than you need: time, food, a skill, a word in someone's favour.",
]

var rng := RandomNumberGenerator.new()
var fish := 70.0
var regrowth_last := 0.0
var lake_drop := 0.0
var trust := 45.0
var season := 1
var pact_limit := -1
var houses: Array = []
var player: Household
var catch_choice := 3
var action_choice: int = Action.REST
var pact_choice := 3
var player_broke := false
var watched_this_season := false
var game_over := false
var lake_dead := false
var shares_given := 0
var seasons_all_kept := 0
var hungry_events := 0

# UI references
var season_label: Label
var lake_bar: ProgressBar
var lake_label: Label
var trust_bar: ProgressBar
var trust_label: Label
var hint_label: Label
var lake_view: Control
var cards_row: HBoxContainer
var cards: Array = []
var catch_buttons: Array = []
var action_buttons: Dictionary = {}
var pact_row: HBoxContainer
var pact_buttons: Array = []
var action_desc: Label
var end_button: Button
var log_box: RichTextLabel
var overlay: Control
var overlay_box: VBoxContainer


func _ready() -> void:
	var theme_res := Theme.new()
	theme_res.default_font_size = 15
	theme = theme_res
	_build_ui()
	_new_game()
	_show_intro()


# ---------------------------------------------------------------- UI build

func _style(bg: Color, radius: int = 8, border: Color = Color(0, 0, 0, 0)) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.set_corner_radius_all(radius)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 8
	sb.content_margin_bottom = 8
	if border.a > 0.0:
		sb.set_border_width_all(2)
		sb.border_color = border
	return sb


func _label(text: String, size: int = 15, color: Color = Color(0.92, 0.9, 0.84)) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l


func _bar(color: Color) -> ProgressBar:
	var b := ProgressBar.new()
	b.min_value = 0
	b.max_value = 100
	b.show_percentage = false
	b.custom_minimum_size = Vector2(160, 14)
	b.add_theme_stylebox_override("background", _style(Color(0.1, 0.12, 0.13), 4))
	b.add_theme_stylebox_override("fill", _style(color, 4))
	return b


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.09, 0.13, 0.15)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var root := MarginContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	for side in ["margin_left", "margin_right", "margin_top", "margin_bottom"]:
		root.add_theme_constant_override(side, 14)
	add_child(root)

	var main_v := VBoxContainer.new()
	main_v.add_theme_constant_override("separation", 10)
	root.add_child(main_v)

	# --- top bar
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 24)
	main_v.add_child(top)
	top.add_child(_label("COMMON GROUND", 22, Color(0.95, 0.85, 0.55)))
	season_label = _label("Season 1 of %d" % SEASONS, 17)
	top.add_child(season_label)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(spacer)

	var lake_v := VBoxContainer.new()
	lake_label = _label("Lake: 70 / 100", 14)
	lake_v.add_child(lake_label)
	lake_bar = _bar(Color(0.3, 0.65, 0.8))
	lake_v.add_child(lake_bar)
	top.add_child(lake_v)

	var trust_v := VBoxContainer.new()
	trust_label = _label("Village trust: 45", 14)
	trust_v.add_child(trust_label)
	trust_bar = _bar(Color(0.85, 0.7, 0.35))
	trust_v.add_child(trust_bar)
	top.add_child(trust_v)

	# --- body
	var body := HBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 14)
	main_v.add_child(body)

	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 8)
	body.add_child(left)

	cards_row = HBoxContainer.new()
	cards_row.add_theme_constant_override("separation", 8)
	left.add_child(cards_row)

	lake_view = Control.new()
	lake_view.set_script(LakeScript)
	lake_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(lake_view)

	hint_label = _label("", 14, Color(0.75, 0.82, 0.8))
	hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left.add_child(hint_label)

	var right := VBoxContainer.new()
	right.custom_minimum_size = Vector2(390, 0)
	right.add_theme_constant_override("separation", 8)
	body.add_child(right)

	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _style(Color(0.13, 0.18, 0.2), 10))
	right.add_child(panel)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 6)
	panel.add_child(pv)

	pv.add_child(_label("How many fish will you take?", 16, Color(0.95, 0.85, 0.55)))
	var catch_row := HBoxContainer.new()
	catch_row.add_theme_constant_override("separation", 4)
	pv.add_child(catch_row)
	var cg := ButtonGroup.new()
	for i in range(6):
		var b := Button.new()
		b.text = str(i)
		b.toggle_mode = true
		b.button_group = cg
		b.custom_minimum_size = Vector2(54, 36)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(_on_catch.bind(i))
		catch_row.add_child(b)
		catch_buttons.append(b)
	catch_buttons[3].button_pressed = true

	pv.add_child(_label("And what else will you do?", 16, Color(0.95, 0.85, 0.55)))
	var act_row := HBoxContainer.new()
	act_row.add_theme_constant_override("separation", 4)
	pv.add_child(act_row)
	var ag := ButtonGroup.new()
	for entry in [[Action.REST, "Rest"], [Action.SHARE, "Share"], [Action.WATCH, "Watch"], [Action.PACT, "Propose limit"]]:
		var b := Button.new()
		b.text = entry[1]
		b.toggle_mode = true
		b.button_group = ag
		b.custom_minimum_size = Vector2(0, 36)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(_on_action.bind(entry[0]))
		act_row.add_child(b)
		action_buttons[entry[0]] = b
	action_buttons[Action.REST].button_pressed = true

	pact_row = HBoxContainer.new()
	pact_row.add_theme_constant_override("separation", 4)
	pv.add_child(pact_row)
	pact_row.add_child(_label("Limit per household:", 14))
	var pg := ButtonGroup.new()
	for i in range(1, 5):
		var b := Button.new()
		b.text = str(i)
		b.toggle_mode = true
		b.button_group = pg
		b.custom_minimum_size = Vector2(44, 30)
		b.pressed.connect(_on_pact_choice.bind(i))
		pact_row.add_child(b)
		pact_buttons.append(b)
	pact_buttons[2].button_pressed = true
	pact_row.visible = false

	action_desc = _label(ACTION_HELP[Action.REST], 14, Color(0.8, 0.85, 0.82))
	action_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	action_desc.custom_minimum_size = Vector2(0, 58)
	pv.add_child(action_desc)

	end_button = Button.new()
	end_button.text = "End season"
	end_button.custom_minimum_size = Vector2(0, 44)
	end_button.add_theme_font_size_override("font_size", 18)
	end_button.pressed.connect(_on_end_season)
	pv.add_child(end_button)

	log_box = RichTextLabel.new()
	log_box.bbcode_enabled = true
	log_box.scroll_following = true
	log_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	log_box.add_theme_stylebox_override("normal", _style(Color(0.07, 0.1, 0.11), 10))
	log_box.add_theme_font_size_override("normal_font_size", 14)
	right.add_child(log_box)

	# --- overlay for intro / ending
	overlay = Control.new()
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(overlay)
	var dim := ColorRect.new()
	dim.color = Color(0.03, 0.05, 0.06, 0.82)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.add_child(center)
	var opanel := PanelContainer.new()
	opanel.custom_minimum_size = Vector2(720, 0)
	opanel.add_theme_stylebox_override("panel", _style(Color(0.13, 0.18, 0.2), 12, Color(0.95, 0.85, 0.55)))
	center.add_child(opanel)
	overlay_box = VBoxContainer.new()
	overlay_box.add_theme_constant_override("separation", 10)
	opanel.add_child(overlay_box)
	overlay.visible = false


func _build_cards() -> void:
	for c in cards_row.get_children():
		c.queue_free()
	cards.clear()
	for h in houses:
		var panel := PanelContainer.new()
		panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		panel.add_theme_stylebox_override("panel", _style(h.color.darkened(0.7), 10, h.color.darkened(0.3)))
		cards_row.add_child(panel)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 3)
		panel.add_child(v)

		var head := HBoxContainer.new()
		head.add_theme_constant_override("separation", 8)
		v.add_child(head)
		var face := Control.new()
		face.set_script(FaceScript)
		head.add_child(face)
		var names := VBoxContainer.new()
		names.add_theme_constant_override("separation", 0)
		head.add_child(names)
		var name_l := _label(h.name, 16, Color(1, 1, 1))
		names.add_child(name_l)
		var mood_l := _label("", 13, Color(0.8, 0.85, 0.82))
		names.add_child(mood_l)

		var well := _bar(h.color)
		well.custom_minimum_size = Vector2(0, 10)
		v.add_child(well)
		var stock_l := _label("", 13)
		v.add_child(stock_l)
		var took_l := _label("", 13, Color(0.95, 0.85, 0.55))
		v.add_child(took_l)
		var line_l := _label("", 13, Color(0.85, 0.88, 0.86))
		line_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		line_l.custom_minimum_size = Vector2(0, 54)
		v.add_child(line_l)
		cards.append({"face": face, "mood": mood_l, "well": well, "stock": stock_l, "took": took_l, "line": line_l})


# ---------------------------------------------------------------- game setup

func _new_game() -> void:
	rng.randomize()
	fish = 70.0
	regrowth_last = GROWTH * fish * (1.0 - fish / CAPACITY)
	lake_drop = 0.0
	trust = 45.0
	season = 1
	pact_limit = -1
	player_broke = false
	watched_this_season = false
	game_over = false
	lake_dead = false
	shares_given = 0
	seasons_all_kept = 0
	hungry_events = 0
	houses.clear()
	player = Household.new("You", "you", Color(0.55, 0.75, 0.95), rng)
	houses.append(player)
	houses.append(Household.new("Mira", "steady", Color(0.55, 0.8, 0.55), rng))
	houses.append(Household.new("Tomas", "mirror", Color(0.85, 0.7, 0.45), rng))
	houses.append(Household.new("Ragnar", "hungry", Color(0.85, 0.5, 0.45), rng))
	houses.append(Household.new("Elin", "anxious", Color(0.75, 0.6, 0.85), rng))
	for h in houses:
		h.line = ""
		h.take = -1
	player.line = "This is your household."
	_build_cards()
	log_box.clear()
	_log("[b]Spring, year one.[/b] Five households, one lake. Each household needs 2 fish a season to eat.")
	_log("Choose how much to take, choose one other thing to do, then end the season.")
	_set_action(Action.REST)
	_update_ui()


func _log(text: String) -> void:
	log_box.append_text(text + "\n")


# ---------------------------------------------------------------- input

func _on_catch(i: int) -> void:
	catch_choice = i


func _on_action(a: int) -> void:
	_set_action(a)


func _set_action(a: int) -> void:
	action_choice = a
	action_buttons[a].button_pressed = true
	pact_row.visible = (a == Action.PACT)
	action_desc.text = ACTION_HELP[a]


func _on_pact_choice(i: int) -> void:
	pact_choice = i


func _on_end_season() -> void:
	if game_over:
		return
	_resolve_season()


# ---------------------------------------------------------------- season

func _neediest() -> Household:
	var best: Household = null
	for h in houses:
		if h.is_player():
			continue
		if best == null or h.stock < best.stock or (h.stock == best.stock and h.wellbeing < best.wellbeing):
			best = h
	return best


func _resolve_season() -> void:
	var fish_at_start := fish
	watched_this_season = (action_choice == Action.WATCH)
	_log("")
	_log("[b]Season %d[/b]" % season)
	var hungry_house: Household = null
	for h in houses:
		if h.is_player():
			continue
		if h.kind == "hungry":
			hungry_house = h

	# --- the player's action
	match action_choice:
		Action.REST:
			player.wellbeing = minf(player.wellbeing + 3.0, 100.0)
			player.line = "You rest."
			_log("You rest a while by the shore.")
		Action.SHARE:
			var target := _neediest()
			if player.stock >= 1.0 and target != null:
				player.stock -= 1.0
				target.stock += 1.0
				trust += 8.0
				target.reform += 1.5 if target.kind == "hungry" else 0.5
				shares_given += 1
				player.line = "You share with %s." % target.name
				_log("You give a fish to %s's household. %s" % [target.name, _thanks(target)])
			else:
				player.line = "Nothing to share."
				_log("You have nothing to share this season.")
		Action.WATCH:
			player.line = "You keep an eye on the lake."
			_log("You spend the season on the water, watching who takes what.")
		Action.PACT:
			pact_limit = pact_choice
			player.line = "You propose a limit of %d." % pact_limit
			_log("You call the village together and propose: [b]no household takes more than %d a season[/b]." % pact_limit)

	# --- decisions
	player.take = catch_choice
	for h in houses:
		if h.is_player():
			continue
		var sum := 0.0
		var n := 0
		for o in houses:
			if o != h:
				sum += o.last_take
				n += 1
		var ctx := {
			"fish": fish, "capacity": CAPACITY, "trust": trust, "pact": pact_limit,
			"others_avg": sum / maxf(n, 1.0), "player_broke": player_broke,
			"lake_drop": lake_drop, "watched": watched_this_season,
		}
		h.take = h.decide(ctx)

	if action_choice == Action.PACT:
		var yes := []
		var no := []
		for h in houses:
			if h.is_player():
				continue
			if h.in_pact:
				yes.append(h.name)
			else:
				no.append(h.name)
		if yes.size() > 0:
			_log("Agree to the limit: %s." % ", ".join(yes))
		if no.size() > 0:
			_log("Not convinced: %s." % ", ".join(no))

	# --- the lake gives what it can
	var demand := 0.0
	for h in houses:
		demand += h.take
	var taken := 0.0
	if demand <= fish:
		for h in houses:
			h.got = h.take
	else:
		for h in houses:
			h.got = h.take * fish / maxf(demand, 0.001)
		_log("[color=#f0a070]The lake could not give everything that was asked. Everyone came home with less.[/color]")
	for h in houses:
		taken += h.got
	fish -= taken

	# --- eat
	for h in houses:
		h.settle(NEED)
	var went_hungry := []
	for h in houses:
		if h.hungry_seasons > 0:
			went_hungry.append(h.name)
	if went_hungry.size() > 0:
		hungry_events += went_hungry.size()
		_log("[color=#f08080]Went hungry this season: %s.[/color]" % ", ".join(went_hungry))

	# --- report takes
	if watched_this_season:
		var parts := []
		for h in houses:
			parts.append("%s %d" % [h.name, h.take])
		_log("Taken this season: %s (total %d)." % [", ".join(parts), int(round(demand))])
	else:
		_log("You took %d. The whole village took %d." % [player.take, int(round(demand))])

	# --- trust
	player_broke = pact_limit >= 0 and player.take > pact_limit
	if pact_limit >= 0:
		var all_kept := true
		for h in houses:
			if h.take <= pact_limit:
				trust += 1.5
			else:
				all_kept = false
				if h.is_player():
					trust -= 10.0
					_log("[color=#f0a070]You broke the limit you proposed. The village noticed.[/color]")
				else:
					trust -= 4.0
					if watched_this_season:
						_log("%s broke the limit." % h.name)
		if all_kept:
			seasons_all_kept += 1
			trust += 2.0
			_log("[color=#a0e0a0]Everyone kept the limit.[/color]")
	else:
		var all_modest := true
		for h in houses:
			if h.take > 3:
				all_modest = false
		if all_modest:
			trust += 1.0
		if player.take >= 5:
			trust -= 3.0
	if hungry_house != null and trust >= 60.0:
		hungry_house.reform += 0.5

	# --- the lake regrows
	if fish < 1.0:
		fish = 0.0
		if not lake_dead:
			lake_dead = true
			_log("[color=#f08080][b]The lake is empty. Nothing is left to grow back.[/b][/color]")
	regrowth_last = GROWTH * fish * (1.0 - fish / CAPACITY)
	fish = minf(fish + regrowth_last, CAPACITY)
	if lake_dead and fish > 0.0:
		lake_dead = false

	# --- weather and rumours
	if season >= 3 and rng.randf() < 0.3:
		_random_event()

	if fish >= 1.0 and lake_dead:
		lake_dead = false
	lake_drop = fish_at_start - fish
	if lake_drop > 8.0:
		trust -= 2.0
	trust = clampf(trust, 0.0, 100.0)

	season += 1
	if season > SEASONS:
		_update_ui()
		_end_game()
		return
	_update_ui()


func _thanks(h: Household) -> String:
	match h.kind:
		"hungry":
			if h.reform >= 3.0:
				return "Ragnar nods. \"I'll remember that.\""
			return "Ragnar looks at it a long time. \"...Why?\""
		"anxious":
			return "Elin breathes out. \"Maybe it will be alright.\""
		"mirror":
			return "Tomas shrugs, but takes it. \"I'll do the same for you.\""
		_:
			return "Mira smiles. \"That's how it should be.\""


func _random_event() -> void:
	var roll := rng.randi_range(0, 3)
	match roll:
		0:
			fish = maxf(fish - 8.0, 0.0)
			_log("[i]A dry summer. The shallows bake and the lake shrinks.[/i]")
		1:
			fish = minf(fish + 8.0, CAPACITY)
			_log("[i]Heavy spring rains. The lake swells and the fish come up to feed.[/i]")
		2:
			if watched_this_season:
				trust += 3.0
				_log("[i]A rumour goes round that someone fishes at night. You were on the water; you can say it isn't so.[/i]")
			else:
				trust -= 6.0
				_log("[i]A rumour goes round that someone fishes at night. Nobody knows who, and nobody can say otherwise.[/i]")
		3:
			if trust >= 50.0:
				for h in houses:
					h.wellbeing = minf(h.wellbeing + 5.0, 100.0)
				_log("[i]The village holds a midsummer feast together. Everyone feels a little better.[/i]")
			else:
				_log("[i]Midsummer passes. Nobody suggests a feast.[/i]")


# ---------------------------------------------------------------- display

func _update_ui() -> void:
	season_label.text = "Season %d of %d" % [mini(season, SEASONS), SEASONS]
	lake_bar.value = fish
	lake_label.text = "Lake: %d / %d fish" % [int(round(fish)), int(CAPACITY)]
	trust_bar.value = trust
	trust_label.text = "Village trust: %d" % int(round(trust))
	lake_view.set_state(fish, CAPACITY, lake_dead)
	var next_regrow := GROWTH * fish * (1.0 - fish / CAPACITY)
	var pact_text := "No shared limit." if pact_limit < 0 else "Current limit: %d per household." % pact_limit
	hint_label.text = "The lake regrew %d fish last season and will regrow about %d after this one. Five households need %d just to eat. %s" % [int(round(regrowth_last)), int(round(next_regrow)), int(NEED * houses.size()), pact_text]
	for i in range(houses.size()):
		var h: Household = houses[i]
		var c: Dictionary = cards[i]
		c.face.set_state(h.wellbeing, h.color, h.hungry_seasons > 0)
		c.mood.text = h.mood()
		c.well.value = h.wellbeing
		c.stock.text = "Stored: %d fish" % int(floor(h.stock + 0.001))
		if h.take < 0:
			c.took.text = "Took: -"
		elif h.is_player() or watched_this_season:
			c.took.text = "Took: %d" % h.take
		else:
			c.took.text = "Took: ?"
		c.line.text = h.line
	action_buttons[Action.SHARE].disabled = player.stock < 1.0
	if action_buttons[Action.SHARE].disabled and action_choice == Action.SHARE:
		_set_action(Action.REST)
	end_button.disabled = game_over


# ---------------------------------------------------------------- overlays

func _clear_overlay() -> void:
	for c in overlay_box.get_children():
		c.queue_free()


func _overlay_text(text: String, size: int = 15, color: Color = Color(0.92, 0.9, 0.84)) -> void:
	var l := _label(text, size, color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	overlay_box.add_child(l)


func _show_intro() -> void:
	_clear_overlay()
	_overlay_text("COMMON GROUND", 30, Color(0.95, 0.85, 0.55))
	_overlay_text("Five households. One lake. Twenty seasons.")
	_overlay_text("Each season you choose how many fish to take, and one other thing to do: rest, share, watch, or propose a limit. Your neighbours choose too. The lake grows back in proportion to what is left in it.")
	_overlay_text("Every household needs 2 fish a season to eat. Taking more builds a store; the store does not keep past 8.")
	_overlay_text("Your neighbours are not villains. One is steady, one copies the crowd, one takes all he can because nobody ever shared with him, and one panics when the water drops. They remember what you do.")
	_overlay_text("There is no score for you alone. The game is scored on how the whole village is doing when the twenty seasons end, with extra weight on whoever is worst off.", 15, Color(0.95, 0.85, 0.55))
	var b := Button.new()
	b.text = "Begin"
	b.custom_minimum_size = Vector2(0, 44)
	b.add_theme_font_size_override("font_size", 18)
	b.pressed.connect(func() -> void: overlay.visible = false)
	overlay_box.add_child(b)
	overlay.visible = true


func _end_game() -> void:
	game_over = true
	end_button.disabled = true
	var sum := 0.0
	var low := 999.0
	var low_name := ""
	for h in houses:
		sum += h.wellbeing
		if h.wellbeing < low:
			low = h.wellbeing
			low_name = h.name
	var avg := sum / houses.size()
	var lake_pct := fish / CAPACITY * 100.0
	var score := 0.5 * avg + 0.3 * low + 0.2 * lake_pct
	var grade := ""
	var grade_col := Color(0.95, 0.85, 0.55)
	if score >= 78.0:
		grade = "The village is flourishing."
		grade_col = Color(0.6, 0.9, 0.6)
	elif score >= 58.0:
		grade = "The village is holding together."
	elif score >= 38.0:
		grade = "The village is struggling."
		grade_col = Color(0.95, 0.7, 0.5)
	else:
		grade = "The village has come apart."
		grade_col = Color(0.95, 0.5, 0.45)

	_clear_overlay()
	_overlay_text("Twenty seasons later", 26, Color(0.95, 0.85, 0.55))
	_overlay_text(grade, 22, grade_col)
	_overlay_text("Village score: %d of 100   (average wellbeing %d, lowest household %d - %s, lake at %d%%)" % [int(round(score)), int(round(avg)), int(round(low)), low_name, int(round(lake_pct))])
	_overlay_text("Your own household: %d.   Seasons everyone kept the limit: %d.   Times you shared: %d.   Hungry seasons across the village: %d." % [int(round(player.wellbeing)), seasons_all_kept, shares_given, hungry_events])

	var reflection := ""
	if player.wellbeing >= avg + 15.0 and score < 58.0:
		reflection = "You came out ahead of your neighbours. The village did not. In this game, and in most places, that is a loss."
	elif score >= 78.0:
		reflection = "Nobody here took the most they could. That is the whole trick. A limit people can see each other keeping, a fish given when someone was short, and a lake left with enough in it to grow back."
	elif lake_pct < 20.0:
		reflection = "The lake gives back in proportion to what is left in it. Once it was drained, no amount of fairness could feed anyone. Restraint has to come before the crisis, not after."
	elif low < 30.0:
		reflection = "Most people did fine. %s did not. The households that panic or grab are usually the ones most afraid of going without; they change fastest when someone shares with them, not when they are shamed." % low_name
	else:
		reflection = "Steady, if not generous. Trust grew slowly when the limit was kept and fell fast when it was broken. That asymmetry is real, and it is why keeping small promises matters more than it seems."
	_overlay_text(reflection, 15)
	_overlay_text("Why this game exists: nearly everything that matters is a commons - the air, the fisheries, the group project, the shared kitchen, the public mood. Almost everyone can see what cooperation would look like. What stops it is fear of being the only one. The things that fix that in the game are the things that fix it in life: make the agreement visible, keep it yourself first, share when someone is short, and look instead of assuming.", 14, Color(0.8, 0.85, 0.82))
	_overlay_text("One real thing to try this week:", 16, Color(0.95, 0.85, 0.55))
	_overlay_text(REAL_THINGS[rng.randi_range(0, REAL_THINGS.size() - 1)], 16)

	var b := Button.new()
	b.text = "Play again"
	b.custom_minimum_size = Vector2(0, 44)
	b.add_theme_font_size_override("font_size", 18)
	b.pressed.connect(func() -> void:
		overlay.visible = false
		_new_game())
	overlay_box.add_child(b)
	overlay.visible = true
