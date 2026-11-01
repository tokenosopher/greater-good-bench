extends RefCounted
## Shared palette, type styles, and control factories.

const INK := Color("#22302B")
const INK_SOFT := Color("#48564D")
const MUTED := Color("#7A8178")
const FAINT := Color("#A9A99C")
const CREAM := Color("#F6EFE4")
const PAPER := Color("#FFFBF3")
const PAPER_WARM := Color("#FBF3E3")
const LINE := Color("#DED2C0")
const GREEN := Color("#2E5E46")
const GREEN_DARK := Color("#1E3D2F")
const GREEN_LIGHT := Color("#E7F0E7")
const GOLD := Color("#D9A441")
const GOLD_LIGHT := Color("#FBF0D6")
const TERRA := Color("#C46B48")
const BLUE := Color("#4F7CAC")
const RED := Color("#B5533F")


static func bold_font(weight: float = 0.65) -> FontVariation:
	var f := FontVariation.new()
	f.base_font = ThemeDB.fallback_font
	f.variation_embolden = weight
	return f


static func box(color: Color, radius: int = 14, border_color: Color = Color(0, 0, 0, 0), border_width: int = 0, shadow: bool = false) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.corner_radius_top_left = radius
	s.corner_radius_top_right = radius
	s.corner_radius_bottom_left = radius
	s.corner_radius_bottom_right = radius
	s.content_margin_left = 14
	s.content_margin_right = 14
	s.content_margin_top = 12
	s.content_margin_bottom = 12
	if border_width > 0:
		s.border_color = border_color
		s.set_border_width_all(border_width)
	if shadow:
		s.shadow_color = Color(0.12, 0.14, 0.11, 0.13)
		s.shadow_size = 12
		s.shadow_offset = Vector2(0, 5)
	return s


static func label(text: String, font_size: int, color: Color = INK, bold: bool = false) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	if bold:
		l.add_theme_font_override("font", bold_font())
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


static func wrapped_label(text: String, font_size: int, color: Color = INK_SOFT, bold: bool = false) -> Label:
	var l := label(text, font_size, color, bold)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l


static func style_primary_button(b: Button, accent: Color = GREEN) -> void:
	b.add_theme_font_size_override("font_size", 15)
	b.add_theme_stylebox_override("normal", box(accent, 12))
	b.add_theme_stylebox_override("hover", box(accent.lightened(0.08), 12))
	b.add_theme_stylebox_override("pressed", box(accent.darkened(0.08), 12))
	b.add_theme_stylebox_override("focus", box(accent, 12, Color(1, 1, 1, 0.55), 2))
	b.add_theme_stylebox_override("disabled", box(Color("#E6E0D3"), 12))
	b.add_theme_color_override("font_color", Color("#FFFDF6"))
	b.add_theme_color_override("font_hover_color", Color("#FFFDF6"))
	b.add_theme_color_override("font_pressed_color", Color("#FFFDF6"))
	b.add_theme_color_override("font_focus_color", Color("#FFFDF6"))
	b.add_theme_color_override("font_disabled_color", Color("#8E887A"))
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND


static func style_secondary_button(b: Button, accent: Color = GREEN) -> void:
	b.add_theme_font_size_override("font_size", 14)
	b.add_theme_stylebox_override("normal", box(PAPER, 11, LINE, 1))
	b.add_theme_stylebox_override("hover", box(PAPER_WARM, 11, accent, 1))
	b.add_theme_stylebox_override("pressed", box(Color("#F0E7D7"), 11, accent, 1))
	b.add_theme_stylebox_override("focus", box(PAPER, 11, accent, 2))
	b.add_theme_stylebox_override("disabled", box(Color("#EDE8DC"), 11, Color("#DDD6C8"), 1))
	b.add_theme_color_override("font_color", INK_SOFT)
	b.add_theme_color_override("font_hover_color", accent)
	b.add_theme_color_override("font_pressed_color", accent)
	b.add_theme_color_override("font_focus_color", INK_SOFT)
	b.add_theme_color_override("font_disabled_color", FAINT)
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND


static func style_ghost_button(b: Button) -> void:
	b.add_theme_font_size_override("font_size", 13)
	b.add_theme_stylebox_override("normal", box(Color(0, 0, 0, 0), 9))
	b.add_theme_stylebox_override("hover", box(Color(1, 1, 1, 0.45), 9))
	b.add_theme_stylebox_override("pressed", box(Color(1, 1, 1, 0.7), 9))
	b.add_theme_stylebox_override("focus", box(Color(1, 1, 1, 0.4), 9, GREEN, 1))
	b.add_theme_color_override("font_color", MUTED)
	b.add_theme_color_override("font_hover_color", INK)
	b.add_theme_color_override("font_pressed_color", INK)
	b.add_theme_color_override("font_focus_color", INK)
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND


static func make_button(text: String, primary: bool = false, accent: Color = GREEN) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_ALL
	if primary:
		style_primary_button(b, accent)
	else:
		style_secondary_button(b, accent)
	return b


static func hsep(amount: int = 8) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(amount, 0)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


static func vsep(amount: int = 8) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, amount)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c
