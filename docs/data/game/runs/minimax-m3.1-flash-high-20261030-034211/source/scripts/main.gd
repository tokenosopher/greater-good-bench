extends Control

const BoardScript := preload("res://scripts/board.gd")

const CREAM := Color("#fbf8ef")
const INK := Color("#243b35")
const MUTED := Color("#5e7169")
const GREEN := Color("#3f8268")
const TERRA := Color("#d27659")
const GOLD := Color("#d6a84b")
const PALE_GREEN := Color("#e4eee2")
const PALE_GOLD := Color("#f4e9cf")
const PALE_TERRA := Color("#f3ded3")

const ACTION_NAMES := ["Restore nature", "Care for people", "Nurture together", "Private gathering"]
const ACTION_COSTS := [2, 2, 3, 0]
const ACTION_DESCRIPTIONS := [
	"+22 nature here, +3 people, and a little nature for nearby districts.",
	"+22 people here, +3 nature, and a little care for nearby districts.",
	"+13 nature and +13 people here, plus +4 of each nearby.",
	"Gain wellbeing now, but draw down nature. A tempting short-term choice."
]

var sites: Array = []
var day: int = 1
var energy: int = 4
var trust: float = 62.0
var selected_action: int = 0
var selected_site: int = 0
var gather_used: bool = false
var total_actions: int = 0
var finished: bool = false
var log_lines: Array = []

var board: CommonGroundBoard
var day_value: Label
var energy_value: Label
var trust_value: Label
var objective_value: Label
var averages_value: Label
var selected_value: Label
var prompt_value: Label
var log_value: Label
var end_button: Button
var action_buttons: Array = []
var header_stats: Array = []
var result_overlay: Control

func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_reset_game()
	_build_interface()

func _reset_game() -> void:
	sites = [
		{"name": "Commons", "kind": "commons", "nature": 64.0, "people": 68.0, "position": Vector2.ZERO},
		{"name": "Old Forest", "kind": "forest", "nature": 61.0, "people": 72.0, "position": Vector2.ZERO},
		{"name": "Reed Wetland", "kind": "wetland", "nature": 58.0, "people": 65.0, "position": Vector2.ZERO},
		{"name": "Silver River", "kind": "river", "nature": 55.0, "people": 70.0, "position": Vector2.ZERO},
		{"name": "Tidal Coast", "kind": "coast", "nature": 63.0, "people": 61.0, "position": Vector2.ZERO},
		{"name": "Meadow", "kind": "meadow", "nature": 68.0, "people": 62.0, "position": Vector2.ZERO},
		{"name": "Neighborhood", "kind": "community", "nature": 57.0, "people": 66.0, "position": Vector2.ZERO}
	]
	day = 1
	energy = 4
	trust = 62.0
	selected_action = 0
	selected_site = 0
	gather_used = false
	total_actions = 0
	finished = false
	log_lines = ["Welcome, steward. Keep every district healthy — and remember that nearby districts share the same fate."]

func _build_interface() -> void:
	var bg: Control = get_node_or_null("Background")
	if bg:
		bg.set_anchors_preset(Control.PRESET_FULL_RECT)

	var outer := MarginContainer.new()
	outer.set_anchors_preset(Control.PRESET_FULL_RECT)
	outer.add_theme_constant_override("margin_left", 22)
	outer.add_theme_constant_override("margin_right", 22)
	outer.add_theme_constant_override("margin_top", 16)
	outer.add_theme_constant_override("margin_bottom", 16)
	add_child(outer)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	outer.add_child(column)

	column.add_child(_build_header())
	column.add_child(_build_body())
	column.add_child(_build_footer())

	_update_all_ui()

func _build_header() -> Control:
	var header := HBoxContainer.new()
	header.custom_minimum_size.y = 66
	header.add_theme_constant_override("separation", 14)

	var title_box := VBoxContainer.new()
	title_box.custom_minimum_size.x = 390
	title_box.add_theme_constant_override("separation", -2)
	header.add_child(title_box)

	var eyebrow := Label.new()
	eyebrow.text = "A COOPERATIVE STEWARDSHIP GAME"
	eyebrow.add_theme_font_size_override("font_size", 12)
	eyebrow.add_theme_color_override("font_color", GREEN)
	title_box.add_child(eyebrow)

	var title := Label.new()
	title.text = "Common Ground"
	title.add_theme_font_size_override("font_size", 31)
	title.add_theme_color_override("font_color", INK)
	title_box.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Build an everyday habit of caring for what we all share."
	subtitle.add_theme_font_size_override("font_size", 13)
	subtitle.add_theme_color_override("font_color", MUTED)
	title_box.add_child(subtitle)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(spacer)

	var stats := HBoxContainer.new()
	stats.add_theme_constant_override("separation", 8)
	stats.alignment = BoxContainer.ALIGNMENT_END
	header.add_child(stats)

	day_value = _add_stat_chip(stats, "DAY", "1 / 8", PALE_GREEN, GREEN)
	energy_value = _add_stat_chip(stats, "ENERGY", "4", PALE_GOLD, GOLD)
	trust_value = _add_stat_chip(stats, "TRUST", "62%", PALE_TERRA, TERRA)
	header_stats = [day_value, energy_value, trust_value]
	return header

func _add_stat_chip(parent: Control, caption: String, value: String, bg: Color, accent: Color) -> Label:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(112, 58)
	var style := _panel_style(bg, accent, 14)
	panel.add_theme_stylebox_override("panel", style)
	parent.add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_top", 7)
	margin.add_theme_constant_override("margin_bottom", 7)
	panel.add_child(margin)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", -2)
	margin.add_child(box)
	var cap := Label.new()
	cap.text = caption
	cap.add_theme_font_size_override("font_size", 10)
	cap.add_theme_color_override("font_color", accent)
	box.add_child(cap)
	var val := Label.new()
	val.text = value
	val.add_theme_font_size_override("font_size", 21)
	val.add_theme_color_override("font_color", INK)
	box.add_child(val)
	return val

func _build_body() -> Control:
	var body := HBoxContainer.new()
	body.custom_minimum_size.y = 524
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 14)

	var board_panel := PanelContainer.new()
	board_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	board_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	board_panel.add_theme_stylebox_override("panel", _panel_style(Color(0.98, 0.985, 0.945, 0.94), Color(0.33, 0.55, 0.47, 0.38), 22))
	body.add_child(board_panel)

	var board_margin := MarginContainer.new()
	board_margin.add_theme_constant_override("margin_left", 8)
	board_margin.add_theme_constant_override("margin_right", 8)
	board_margin.add_theme_constant_override("margin_top", 5)
	board_margin.add_theme_constant_override("margin_bottom", 7)
	board_panel.add_child(board_margin)

	board = BoardScript.new()
	board.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	board.size_flags_vertical = Control.SIZE_EXPAND_FILL
	board.site_clicked.connect(_on_site_clicked)
	board_margin.add_child(board)
	board.sites = sites
	board.layout_sites()

	var side := VBoxContainer.new()
	side.custom_minimum_size.x = 324
	side.size_flags_horizontal = Control.SIZE_SHRINK_END
	side.add_theme_constant_override("separation", 9)
	body.add_child(side)

	side.add_child(_build_mission_panel())
	side.add_child(_build_action_panel())
	side.add_child(_build_end_button())
	return body

func _build_mission_panel() -> Control:
	var panel := PanelContainer.new()
	panel.custom_minimum_size.y = 132
	panel.add_theme_stylebox_override("panel", _panel_style(CREAM, Color(0.33, 0.55, 0.47, 0.28), 16))
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 14)
	margin.add_theme_constant_override("margin_right", 14)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_bottom", 10)
	panel.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	margin.add_child(box)

	var row := HBoxContainer.new()
	box.add_child(row)
	var mission := Label.new()
	mission.text = "THE 8-DAY PROMISE"
	mission.add_theme_font_size_override("font_size", 11)
	mission.add_theme_color_override("font_color", GREEN)
	row.add_child(mission)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(spacer)
	var legend := Label.new()
	legend.text = "● NATURE   ● PEOPLE"
	legend.add_theme_font_size_override("font_size", 10)
	legend.add_theme_color_override("font_color", MUTED)
	row.add_child(legend)

	objective_value = Label.new()
	objective_value.text = "Give every district Nature ≥ 50 and People ≥ 55.\nReach averages of 60 Nature and 65 People."
	objective_value.add_theme_font_size_override("font_size", 13)
	objective_value.add_theme_color_override("font_color", INK)
	objective_value.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(objective_value)

	averages_value = Label.new()
	averages_value.add_theme_font_size_override("font_size", 12)
	averages_value.add_theme_color_override("font_color", MUTED)
	box.add_child(averages_value)
	return panel

func _build_action_panel() -> Control:
	var panel := PanelContainer.new()
	panel.custom_minimum_size.y = 283
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	panel.add_theme_stylebox_override("panel", _panel_style(CREAM, Color(0.33, 0.55, 0.47, 0.28), 16))
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_bottom", 10)
	panel.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 5)
	margin.add_child(box)

	var title := Label.new()
	title.text = "CHOOSE HOW TO CARE"
	title.add_theme_font_size_override("font_size", 11)
	title.add_theme_color_override("font_color", GREEN)
	box.add_child(title)

	var action_group := ButtonGroup.new()
	for i in range(4):
		var button := Button.new()
		button.toggle_mode = true
		button.button_group = action_group
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.custom_minimum_size.y = 48
		if ACTION_COSTS[i] > 0:
			button.text = "%d   %s   ·  %d energy" % [i + 1, ACTION_NAMES[i], ACTION_COSTS[i]]
		else:
			button.text = "4   %s   ·  no energy" % ACTION_NAMES[i]
		button.tooltip_text = ACTION_DESCRIPTIONS[i]
		button.add_theme_font_size_override("font_size", 13)
		button.add_theme_color_override("font_color", INK)
		button.add_theme_color_override("font_hover_color", GREEN.darkened(0.08))
		button.add_theme_color_override("font_pressed_color", GREEN.darkened(0.12))
		button.add_theme_color_override("font_focus_color", INK)
		button.pressed.connect(_select_action.bind(i))
		box.add_child(button)
		action_buttons.append(button)

	prompt_value = Label.new()
	prompt_value.text = ACTION_DESCRIPTIONS[0]
	prompt_value.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	prompt_value.custom_minimum_size.y = 35
	prompt_value.add_theme_font_size_override("font_size", 11)
	prompt_value.add_theme_color_override("font_color", MUTED)
	box.add_child(prompt_value)

	selected_value = Label.new()
	selected_value.text = "Commons · Nature 64  ·  People 68"
	selected_value.add_theme_font_size_override("font_size", 11)
	selected_value.add_theme_color_override("font_color", INK)
	box.add_child(selected_value)
	return panel

func _build_end_button() -> Control:
	end_button = Button.new()
	end_button.text = "END DAY 1  →"
	end_button.custom_minimum_size.y = 48
	end_button.add_theme_font_size_override("font_size", 15)
	end_button.add_theme_color_override("font_color", CREAM)
	end_button.add_theme_color_override("font_hover_color", CREAM)
	end_button.add_theme_color_override("font_pressed_color", CREAM)
	end_button.add_theme_stylebox_override("normal", _button_style(GREEN))
	end_button.add_theme_stylebox_override("hover", _button_style(GREEN.lightened(0.08)))
	end_button.add_theme_stylebox_override("pressed", _button_style(GREEN.darkened(0.08)))
	end_button.pressed.connect(_end_day)
	return end_button

func _build_footer() -> Control:
	var panel := PanelContainer.new()
	panel.custom_minimum_size.y = 48
	panel.add_theme_stylebox_override("panel", _panel_style(Color(0.98, 0.985, 0.945, 0.92), Color(0.33, 0.55, 0.47, 0.25), 14))
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 14)
	margin.add_theme_constant_override("margin_right", 14)
	margin.add_theme_constant_override("margin_top", 7)
	margin.add_theme_constant_override("margin_bottom", 7)
	panel.add_child(margin)
	var row := HBoxContainer.new()
	margin.add_child(row)
	var note := Label.new()
	note.text = "FIELD NOTE"
	note.add_theme_font_size_override("font_size", 10)
	note.add_theme_color_override("font_color", TERRA)
	row.add_child(note)
	var divider := Label.new()
	divider.text = "  /  "
	divider.add_theme_color_override("font_color", Color(0.33, 0.55, 0.47, 0.40))
	row.add_child(divider)
	log_value = Label.new()
	log_value.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	log_value.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	log_value.add_theme_font_size_override("font_size", 12)
	log_value.add_theme_color_override("font_color", INK)
	row.add_child(log_value)
	log_value.text = log_lines[-1]
	return panel

func _panel_style(bg: Color, border: Color, radius: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(radius)
	style.content_margin_left = 1
	style.content_margin_right = 1
	return style

func _button_style(bg: Color) -> StyleBoxFlat:
	var style := _panel_style(bg, bg.darkened(0.12), 12)
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 7
	style.content_margin_bottom = 7
	return style

func _select_action(index: int) -> void:
	if finished:
		return
	selected_action = index
	prompt_value.text = ACTION_DESCRIPTIONS[index]
	_update_action_buttons()
	board.selected_action = index
	board.queue_redraw()

func _on_site_clicked(index: int) -> void:
	if finished:
		return
	selected_site = index
	_apply_action(index)

func _apply_action(index: int) -> void:
	var cost: int = ACTION_COSTS[selected_action]
	if cost > energy:
		_add_log("Not enough energy today. Your neighbors still need you tomorrow.")
		_update_all_ui()
		return
	if selected_action == 3 and gather_used:
		_add_log("You have already gathered today. Put your attention toward the shared good.")
		_update_all_ui()
		return

	energy -= cost
	total_actions += 1
	var site: Dictionary = sites[index]
	var nature_before: float = site["nature"]
	var people_before: float = site["people"]

	match selected_action:
		0:
			site["nature"] = clampf(nature_before + 22.0, 0.0, 100.0)
			site["people"] = clampf(people_before + 3.0, 0.0, 100.0)
			_apply_neighbor_effect(index, 4.0, 0.0)
			trust += 2.0
			_add_log("You restored %s. The change reaches beyond its borders." % site["name"])
		1:
			site["people"] = clampf(people_before + 22.0, 0.0, 100.0)
			site["nature"] = clampf(nature_before + 3.0, 0.0, 100.0)
			_apply_neighbor_effect(index, 0.0, 4.0)
			trust += 2.0
			_add_log("You cared for %s. People there now have more room to contribute." % site["name"])
		2:
			site["nature"] = clampf(nature_before + 13.0, 0.0, 100.0)
			site["people"] = clampf(people_before + 13.0, 0.0, 100.0)
			_apply_neighbor_effect(index, 4.0, 4.0)
			trust += 3.0
			_add_log("You nurtured %s, bringing nature and people into balance." % site["name"])
		3:
			site["nature"] = clampf(nature_before - 14.0, 0.0, 100.0)
			site["people"] = clampf(people_before - 6.0, 0.0, 100.0)
			gather_used = true
			trust -= 8.0
			_add_log("You took a private gathering from %s. The gain is immediate; the cost is shared." % site["name"])

	sites[index] = site
	trust = clampf(trust, 0.0, 100.0)
	_update_all_ui()

func _apply_neighbor_effect(index: int, nature_amount: float, people_amount: float) -> void:
	for neighbor_index in _neighbors_of(index):
		var neighbor: Dictionary = sites[neighbor_index]
		neighbor["nature"] = clampf(float(neighbor["nature"]) + nature_amount, 0.0, 100.0)
		neighbor["people"] = clampf(float(neighbor["people"]) + people_amount, 0.0, 100.0)
		sites[neighbor_index] = neighbor

func _neighbors_of(index: int) -> Array:
	if index == 0:
		return [1, 2, 3, 4, 5, 6]
	var ring_index := index - 1
	var a := 1 + ((ring_index - 1 + 6) % 6)
	var b := 1 + ((ring_index + 1) % 6)
	return [0, a, b]

func _end_day() -> void:
	if finished:
		return
	if energy > 0:
		_add_log("You end the day with %d energy left. Next time, plan for a stronger finish." % energy)
	_apply_daily_change()
	if day >= 8:
		_finish_game()
		return
	day += 1
	energy = 4
	gather_used = false
	_add_log("Day %d begins. You have 4 energy and a whole community to care for." % day)
	_update_all_ui()

func _apply_daily_change() -> void:
	for i in range(sites.size()):
		var site: Dictionary = sites[i]
		site["nature"] = clampf(float(site["nature"]) - 2.0, 0.0, 100.0)
		site["people"] = clampf(float(site["people"]) - 1.0, 0.0, 100.0)
		if float(site["nature"]) < 35.0:
			site["people"] = clampf(float(site["people"]) - 2.0, 0.0, 100.0)
		sites[i] = site

	match day:
		2:
			_change_site(2, -6.0, 0.0)
			_change_site(3, -6.0, 0.0)
			_add_log("A dry spell lowers the wetland and river. Small buffers protect shared water.")
		3:
			_change_all(0.0, 3.0)
			_add_log("A community market lifts people's spirits everywhere.")
		4:
			_change_site(2, -6.0, -4.0)
			_change_site(4, -6.0, -4.0)
			_add_log("A coastal storm tests the wetland and tidal coast.")
		5:
			_change_all(-3.0, 0.0)
			_add_log("A heat wave puts pressure on every habitat.")
		6:
			_change_all(0.0, 4.0)
			_add_log("Neighbors organize mutual aid. People feel stronger together.")
		7:
			for i in range(sites.size()):
				var site: Dictionary = sites[i]
				if float(site["nature"]) < 45.0:
					site["people"] = clampf(float(site["people"]) - 3.0, 0.0, 100.0)
					sites[i] = site
			_add_log("An honest audit reveals where strain has become invisible.")
		8:
			_change_all(2.0, 2.0)
			_add_log("The final common day arrives. Everyone contributes what they can.")

func _change_site(index: int, nature: float, people: float) -> void:
	var site: Dictionary = sites[index]
	site["nature"] = clampf(float(site["nature"]) + nature, 0.0, 100.0)
	site["people"] = clampf(float(site["people"]) + people, 0.0, 100.0)
	sites[index] = site

func _change_all(nature: float, people: float) -> void:
	for i in range(sites.size()):
		_change_site(i, nature, people)

func _finish_game() -> void:
	finished = true
	var nature_average := _average("nature")
	var people_average := _average("people")
	var minimum_nature := 100.0
	var minimum_people := 100.0
	for site in sites:
		minimum_nature = minf(minimum_nature, float(site["nature"]))
		minimum_people = minf(minimum_people, float(site["people"]))
	var promise_met := minimum_nature >= 50.0 and minimum_people >= 55.0 and nature_average >= 60.0 and people_average >= 65.0

	var title := "A Flourishing Commons"
	var subtitle := "You kept every district healthy, and shared care grew trust."
	if promise_met and trust < 60.0:
		title = "Promise Kept, Trust Unfinished"
		subtitle = "The commons survived, but more people need to feel ownership of it."
	elif not promise_met and trust >= 50.0:
		title = "Uneven Ground"
		subtitle = "People are ready to act, but the living systems still need more care."
	elif not promise_met:
		title = "The Work Continues"
		subtitle = "The map is not healthy yet. A better plan starts with noticing what is weak."

	_show_result(title, subtitle, promise_met, nature_average, people_average)

func _show_result(title: String, subtitle: String, promise_met: bool, nature_average: float, people_average: float) -> void:
	result_overlay = Control.new()
	result_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	result_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(result_overlay)

	var dim := ColorRect.new()
	dim.color = Color(0.10, 0.20, 0.17, 0.58)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	result_overlay.add_child(dim)

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	result_overlay.add_child(center)

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(570, 360)
	panel.add_theme_stylebox_override("panel", _panel_style(CREAM, GREEN, 24))
	center.add_child(panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 38)
	margin.add_theme_constant_override("margin_right", 38)
	margin.add_theme_constant_override("margin_top", 30)
	margin.add_theme_constant_override("margin_bottom", 30)
	panel.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 12)
	margin.add_child(box)

	var tag := Label.new()
	tag.text = "THE 8-DAY PROMISE" if promise_met else "THE 8-DAY REFLECTION"
	tag.add_theme_font_size_override("font_size", 11)
	tag.add_theme_color_override("font_color", GREEN)
	box.add_child(tag)

	var heading := Label.new()
	heading.text = title
	heading.add_theme_font_size_override("font_size", 30)
	heading.add_theme_color_override("font_color", INK)
	box.add_child(heading)

	var description := Label.new()
	description.text = subtitle
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description.add_theme_font_size_override("font_size", 15)
	description.add_theme_color_override("font_color", MUTED)
	box.add_child(description)

	var stats_row := HBoxContainer.new()
	stats_row.add_theme_constant_override("separation", 12)
	box.add_child(stats_row)
	_add_result_stat(stats_row, "NATURE", "%.0f" % nature_average)
	_add_result_stat(stats_row, "PEOPLE", "%.0f" % people_average)
	_add_result_stat(stats_row, "TRUST", "%.0f%%" % trust)

	var impact := Label.new()
	impact.text = "Millions of small acts can become reliable public infrastructure. The game ends; the habits can continue."
	impact.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	impact.add_theme_font_size_override("font_size", 13)
	impact.add_theme_color_override("font_color", INK)
	box.add_child(impact)

	var restart := Button.new()
	restart.text = "PLAY A NEW PLAN"
	restart.custom_minimum_size.y = 46
	restart.add_theme_font_size_override("font_size", 15)
	restart.add_theme_color_override("font_color", CREAM)
	restart.add_theme_stylebox_override("normal", _button_style(GREEN))
	restart.add_theme_stylebox_override("hover", _button_style(GREEN.lightened(0.08)))
	restart.pressed.connect(_restart)
	box.add_child(restart)

func _add_result_stat(parent: Control, caption: String, value: String) -> void:
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(box)
	var cap := Label.new()
	cap.text = caption
	cap.add_theme_font_size_override("font_size", 10)
	cap.add_theme_color_override("font_color", MUTED)
	box.add_child(cap)
	var val := Label.new()
	val.text = value
	val.add_theme_font_size_override("font_size", 25)
	val.add_theme_color_override("font_color", INK)
	box.add_child(val)

func _restart() -> void:
	if result_overlay:
		result_overlay.queue_free()
		result_overlay = null
	_reset_game()
	board.sites = sites
	board.layout_sites()
	_select_action(0)
	_update_all_ui()

func _add_log(message: String) -> void:
	log_lines.append(message)
	if log_lines.size() > 5:
		log_lines.remove_at(0)
	log_value.text = log_lines[-1]

func _update_all_ui() -> void:
	if not is_instance_valid(day_value):
		return
	day_value.text = "%d / 8" % day
	energy_value.text = str(energy)
	trust_value.text = "%d%%" % int(round(trust))
	objective_value.text = "Give every district Nature ≥ 50 and People ≥ 55.\nReach averages of 60 Nature and 65 People."
	log_value.text = log_lines[-1]
	averages_value.text = "COMMUNITY AVERAGES   Nature %d   ·   People %d" % [int(round(_average("nature"))), int(round(_average("people")))]
	var site: Dictionary = sites[selected_site]
	selected_value.text = "%s  ·  Nature %d  ·  People %d" % [site["name"], int(round(float(site["nature"]))), int(round(float(site["people"])))]
	end_button.text = ("FINISH THE PLAN  →" if day >= 8 else "END DAY %d  →" % day)
	end_button.disabled = finished
	_update_action_buttons()
	board.sites = sites
	board.selected_site = selected_site
	board.layout_sites()

func _update_action_buttons() -> void:
	for i in range(action_buttons.size()):
		var button: Button = action_buttons[i]
		button.set_pressed_no_signal(i == selected_action)
		button.disabled = finished or (ACTION_COSTS[i] > energy) or (i == 3 and gather_used)
		var normal_bg := CREAM
		var normal_border := Color(0.33, 0.55, 0.47, 0.28)
		if i == selected_action:
			normal_bg = PALE_GREEN
			normal_border = GREEN
		button.add_theme_stylebox_override("normal", _panel_style(normal_bg, normal_border, 11))
		button.add_theme_stylebox_override("hover", _panel_style(normal_bg.lightened(0.03), normal_border.lightened(0.12), 11))
		button.add_theme_stylebox_override("pressed", _panel_style(normal_bg.darkened(0.03), normal_border, 11))
		button.add_theme_stylebox_override("focus", _panel_style(Color(1, 1, 1, 0), normal_border, 11))

func _average(key: String) -> float:
	var total := 0.0
	for site in sites:
		total += float(site[key])
	return total / maxf(float(sites.size()), 1.0)

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1:
				_select_action(0)
			KEY_2:
				_select_action(1)
			KEY_3:
				_select_action(2)
			KEY_4:
				_select_action(3)
			KEY_SPACE:
				_end_day()
