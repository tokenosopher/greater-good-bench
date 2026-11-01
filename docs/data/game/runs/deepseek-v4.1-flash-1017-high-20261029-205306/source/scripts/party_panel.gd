extends PanelContainer
## One side of the table: identity, trust, and their three interest cards.

signal listen_pressed(party_id: String)
signal reassure_pressed(party_id: String)
signal card_pressed(interest_id: String)

const UIKit = preload("res://scripts/ui_kit.gd")
const TrustMeter = preload("res://scripts/trust_meter.gd")
const InterestCard = preload("res://scripts/interest_card.gd")

var party_id := ""
var party_data: Dictionary = {}
var party_color := UIKit.GREEN
var cards: Array = []
var trust_meter: Control
var trust_label: Label
var listen_button: Button
var reassure_button: Button
var section_label: Label
var quote_label: Label
var hidden_count := 0


func setup(data: Dictionary, id: String) -> void:
	party_id = id
	party_data = data
	party_color = Color(str(data.get("color", "#2E5E46")))
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(330, 0)
	add_theme_stylebox_override("panel", UIKit.box(UIKit.PAPER, 18, Color(party_color, 0.34), 1, true))

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 5)
	add_child(box)

	# Header.
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 9)
	box.add_child(header)

	var emblem := PanelContainer.new()
	emblem.custom_minimum_size = Vector2(42, 42)
	emblem.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var emblem_style := UIKit.box(party_color, 21)
	emblem_style.content_margin_left = 0
	emblem_style.content_margin_right = 0
	emblem_style.content_margin_top = 0
	emblem_style.content_margin_bottom = 0
	emblem.add_theme_stylebox_override("panel", emblem_style)
	header.add_child(emblem)

	var initials := UIKit.label(_initials(str(data.get("name", ""))), 15, Color("#FFFDF6"), true)
	initials.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	initials.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	emblem.add_child(initials)

	var name_box := VBoxContainer.new()
	name_box.add_theme_constant_override("separation", -1)
	name_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_box.alignment = BoxContainer.ALIGNMENT_CENTER
	header.add_child(name_box)

	var name_label := UIKit.label(str(data.get("name", "")), 16, UIKit.INK, true)
	name_label.max_lines_visible = 1
	name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	name_box.add_child(name_label)

	var role_label := UIKit.label(str(data.get("role", "")).to_upper(), 8, UIKit.MUTED, true)
	role_label.max_lines_visible = 1
	role_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	name_box.add_child(role_label)

	# Quote (the stated position).
	quote_label = UIKit.wrapped_label(str(data.get("quote", "")), 11, UIKit.INK_SOFT)
	quote_label.max_lines_visible = 2
	quote_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	quote_label.custom_minimum_size = Vector2(0, 28)
	box.add_child(quote_label)

	# Trust.
	var trust_row := HBoxContainer.new()
	trust_row.add_theme_constant_override("separation", 7)
	box.add_child(trust_row)
	var trust_title := UIKit.label("GOODWILL", 8, UIKit.MUTED, true)
	trust_title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	trust_row.add_child(trust_title)
	trust_meter = TrustMeter.new()
	trust_meter.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	trust_row.add_child(trust_meter)
	trust_label = UIKit.label("4 / 6", 10, UIKit.MUTED)
	trust_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	trust_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	trust_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	trust_row.add_child(trust_label)

	# Actions.
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 6)
	box.add_child(actions)

	listen_button = UIKit.make_button("Listen", true, party_color)
	listen_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	listen_button.custom_minimum_size = Vector2(0, 30)
	listen_button.tooltip_text = "Hear one hidden need. Builds goodwill with this side; the other side feels ignored."
	listen_button.pressed.connect(func() -> void: listen_pressed.emit(party_id))
	actions.add_child(listen_button)

	reassure_button = UIKit.make_button("Reassure", false, party_color)
	reassure_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	reassure_button.custom_minimum_size = Vector2(0, 30)
	reassure_button.tooltip_text = "Spend a turn restoring goodwill without revealing a need. The other side still feels the attention shift."
	reassure_button.pressed.connect(func() -> void: reassure_pressed.emit(party_id))
	actions.add_child(reassure_button)

	# Cards.
	section_label = UIKit.label("WHAT THEY NEED", 8, UIKit.MUTED, true)
	box.add_child(section_label)

	var cards_box := VBoxContainer.new()
	cards_box.add_theme_constant_override("separation", 5)
	cards_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(cards_box)

	for interest in data.get("interests", []):
		var card := InterestCard.new()
		card.setup(interest, party_color)
		card.card_pressed.connect(func(cid: String) -> void: card_pressed.emit(cid))
		cards_box.add_child(card)
		cards.append(card)


func set_trust(value: int, max_value: int) -> void:
	trust_meter.set_values(value, max_value, party_color)
	trust_label.text = str(value) + " / " + str(max_value)
	if value <= 1:
		trust_label.add_theme_color_override("font_color", UIKit.RED)
	else:
		trust_label.add_theme_color_override("font_color", UIKit.MUTED)


func set_interests(revealed: Dictionary, resolved: Dictionary, selected: Array) -> void:
	hidden_count = 0
	for card in cards:
		card.is_revealed = revealed.has(card.interest_id)
		card.is_resolved = resolved.has(card.interest_id)
		card.is_selected = selected.has(card.interest_id)
		card.refresh()
		if not card.is_revealed and not card.is_resolved:
			hidden_count += 1
	if hidden_count > 0:
		listen_button.disabled = false
		listen_button.text = "Listen · " + str(hidden_count) + " left"
	else:
		listen_button.disabled = true
		listen_button.text = "All needs heard"
	section_label.text = "WHAT THEY NEED · " + str(hidden_count) + " UNHEARD" if hidden_count > 0 else "WHAT THEY NEED · ALL HEARD"


func _initials(full_name: String) -> String:
	var skip := ["the", "of", "and", "a", "an"]
	var result := ""
	for word in full_name.split(" ", false):
		if word.to_lower() in skip:
			continue
		result += word.substr(0, 1).to_upper()
		if result.length() >= 2:
			break
	return result
