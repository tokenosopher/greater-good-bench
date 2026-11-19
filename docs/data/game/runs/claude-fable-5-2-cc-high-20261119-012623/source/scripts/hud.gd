extends CanvasLayer
## The coach: top bar, the bottom panel with prompts, choices and feedback.
## One instance per moment, freed together with it.

signal chosen(idx: int)
signal continued
signal menu_pressed

const Art = preload("res://scripts/art.gd")

var auto := false
var mode := ""          # "", "say", "choose", "instruct"

var _title: Label
var _meter: Control
var _meter_label := ""
var _meter_target := 1.0
var _meter_value := 1.0
var _panel: PanelContainer
var _style: StyleBoxFlat
var _tag: Label
var _text: Label
var _buttons: VBoxContainer
var _since := 0.0
var _n := 0
var _sound: Button


func _ready() -> void:
	layer = 5
	var root := MarginContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_theme_constant_override("margin_left", 26)
	root.add_theme_constant_override("margin_right", 26)
	root.add_theme_constant_override("margin_top", 16)
	root.add_theme_constant_override("margin_bottom", 18)
	add_child(root)

	var col := VBoxContainer.new()
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(col)

	var top := HBoxContainer.new()
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_theme_constant_override("separation", 12)
	col.add_child(top)

	var menu := Button.new()
	menu.text = "Menu"
	Art.style_button(menu, "ghost", 16)
	menu.pressed.connect(_on_menu)
	top.add_child(menu)

	_sound = Button.new()
	_sound.text = "Sound off" if Sfx.muted else "Sound on"
	Art.style_button(_sound, "ghost", 16)
	_sound.pressed.connect(_on_sound)
	top.add_child(_sound)

	var pill := PanelContainer.new()
	pill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pill.add_theme_stylebox_override("panel", Art.flat(Color(Art.PAPER, 0.95), 18, Color(0, 0, 0, 0), 0, 18, 7))
	top.add_child(pill)
	_title = Label.new()
	_title.add_theme_font_override("font", Art.bold())
	_title.add_theme_font_size_override("font_size", 17)
	_title.add_theme_color_override("font_color", Art.INK)
	pill.add_child(_title)

	var gap := Control.new()
	gap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(gap)

	_meter = Control.new()
	_meter.custom_minimum_size = Vector2(340, 38)
	_meter.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_meter.visible = false
	_meter.draw.connect(_draw_meter)
	top.add_child(_meter)

	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(spacer)

	_panel = PanelContainer.new()
	_style = Art.flat(Art.PAPER, 20, Art.INK, 0, 26, 18)
	_style.border_width_left = 10
	_style.border_color = Art.INK
	_style.shadow_color = Color(0.1, 0.12, 0.18, 0.2)
	_style.shadow_size = 10
	_style.shadow_offset = Vector2(0, 4)
	_panel.add_theme_stylebox_override("panel", _style)
	_panel.visible = false
	col.add_child(_panel)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 28)
	_panel.add_child(row)

	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_theme_constant_override("separation", 4)
	row.add_child(left)

	_tag = Label.new()
	_tag.add_theme_font_override("font", Art.bold())
	_tag.add_theme_font_size_override("font_size", 14)
	left.add_child(_tag)

	_text = Label.new()
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size = Vector2(300, 0)
	_text.add_theme_font_size_override("font_size", 21)
	_text.add_theme_color_override("font_color", Art.INK)
	_text.add_theme_constant_override("line_spacing", 3)
	left.add_child(_text)

	_buttons = VBoxContainer.new()
	_buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	_buttons.add_theme_constant_override("separation", 8)
	row.add_child(_buttons)


func _process(delta: float) -> void:
	_since += delta
	_meter_value = lerpf(_meter_value, _meter_target, 1.0 - exp(-6.0 * delta))
	if _meter.visible:
		_meter.queue_redraw()
	if auto and _since > 0.08:
		if mode == "say":
			_continue()
		elif mode == "choose":
			_pick(randi() % _n)


func _unhandled_key_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	if mode == "say" and _since > 0.7 and (k.keycode == KEY_SPACE or k.keycode == KEY_ENTER or k.keycode == KEY_KP_ENTER):
		get_viewport().set_input_as_handled()
		_continue()
	elif (mode == "choose" or mode == "instruct") and _n > 0 and _since > 0.3:
		var i := -1
		if k.keycode >= KEY_1 and k.keycode <= KEY_9:
			i = k.keycode - KEY_1
		if i >= 0 and i < _n:
			get_viewport().set_input_as_handled()
			_pick(i)


# ---------------------------------------------------------------- API

func set_title(s: String) -> void:
	_title.text = s


func show_meter(label: String) -> void:
	_meter_label = label
	_meter.visible = true


func set_meter(v: float) -> void:
	_meter_target = clampf(v, 0.0, 1.0)


func waiting() -> bool:
	return mode == "choose" or mode == "instruct"


func hide_panel() -> void:
	_panel.visible = false
	mode = ""


func say(text: String, tag: String = "") -> void:
	_show(tag, text, Art.INK, Art.INK_SOFT, ["Continue"], "primary")
	mode = "say"


func choose(prompt: String, options: Array, tag: String = "") -> void:
	_show(tag if tag != "" else "YOUR CALL", prompt, Art.AMBER, Art.AMBER.darkened(0.25), options, "option")
	mode = "choose"


func feedback(ok: bool, text: String) -> void:
	if ok:
		_show("YES", text, Art.TEAL, Art.TEAL, ["Continue"], "primary")
	else:
		_show("NOT QUITE", text, Art.CORAL, Art.CORAL, ["Continue"], "primary")
	mode = "say"


func instruct(text: String, tag: String = "", options: Array = []) -> void:
	_show(tag, text, Art.INK, Art.INK_SOFT, options, "option")
	mode = "instruct"


# ---------------------------------------------------------------- internals

func _show(tag: String, text: String, accent: Color, tag_col: Color, options: Array, kind: String) -> void:
	_panel.visible = true
	_tag.text = tag
	_tag.visible = tag != ""
	_tag.add_theme_color_override("font_color", tag_col)
	_text.text = text
	_style.border_color = accent
	for c in _buttons.get_children():
		_buttons.remove_child(c)
		c.queue_free()
	_n = options.size()
	_buttons.visible = _n > 0
	for i in _n:
		var b := Button.new()
		b.text = str(options[i])
		Art.style_button(b, kind, 19)
		if kind == "option":
			b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			b.custom_minimum_size = Vector2(600, 46)
			b.pressed.connect(_pick.bind(i))
		else:
			b.custom_minimum_size = Vector2(170, 52)
			b.pressed.connect(_continue)
		_buttons.add_child(b)
	_since = 0.0


func _pick(i: int) -> void:
	if _since < 0.25 and not auto:
		return
	if mode == "choose":
		mode = ""
	Sfx.play("click")
	chosen.emit(i)


func _continue() -> void:
	if mode != "say" or (_since < 0.25 and not auto):
		return
	mode = ""
	Sfx.play("click")
	continued.emit()


func _on_menu() -> void:
	menu_pressed.emit()


func _on_sound() -> void:
	Sfx.set_muted(not Sfx.muted)
	refresh_sound()


func refresh_sound() -> void:
	_sound.text = "Sound off" if Sfx.muted else "Sound on"


func _draw_meter() -> void:
	var sz := _meter.size
	Art.rrect(_meter, Rect2(Vector2.ZERO, sz), Color(Art.PAPER, 0.95), 19)
	Art.text(_meter, Vector2(18, 24), _meter_label, 13, Art.INK, true)
	var bx := 18.0 + Art.text_w(_meter_label, 13, true) + 12.0
	var bw := sz.x - bx - 18.0
	Art.rrect(_meter, Rect2(bx, 13, bw, 12), Color(Art.INK, 0.13), 6)
	var v := clampf(_meter_value, 0.0, 1.0)
	var q := roundf(v * 30.0) / 30.0
	var c := Art.CORAL.lerp(Art.AMBER, q * 2.0) if q < 0.5 else Art.AMBER.lerp(Art.TEAL, (q - 0.5) * 2.0)
	Art.rrect(_meter, Rect2(bx, 13, maxf(bw * v, 12.0), 12), c, 6)
