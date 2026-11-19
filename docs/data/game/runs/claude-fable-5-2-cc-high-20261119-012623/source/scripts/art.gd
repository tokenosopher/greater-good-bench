extends RefCounted
## Palette and drawing helpers. Every picture in the game is drawn in code.

const CREAM := Color("f6efe6")
const PAPER := Color("fffaf3")
const INK := Color("22303f")
const INK_SOFT := Color("5d6a7a")
const CORAL := Color("e5533d")
const CORAL_DARK := Color("b93a28")
const TEAL := Color("1f9e8e")
const AMBER := Color("eda02f")
const BLOOD := Color("b3202a")
const SKINS: Array[Color] = [Color("f7d7bd"), Color("e8b993"), Color("c98d62"), Color("9c6541"), Color("6f452c")]
const HAIRS: Array[Color] = [Color("2b211c"), Color("5a3a22"), Color("b5722f"), Color("d9d4cb"), Color("14161a"), Color("8c2f1b")]

static var _bold: FontVariation
static var _boxes: Dictionary = {}


# ---------------------------------------------------------------- text

static func font() -> Font:
	return ThemeDB.fallback_font


static func bold() -> Font:
	if _bold == null:
		_bold = FontVariation.new()
		_bold.base_font = ThemeDB.fallback_font
		_bold.variation_embolden = 0.7
	return _bold


static func text(ci: CanvasItem, pos: Vector2, s: String, size: int, col: Color, b: bool = false) -> void:
	var f: Font = bold() if b else font()
	ci.draw_string(f, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


static func text_c(ci: CanvasItem, center: Vector2, s: String, size: int, col: Color, b: bool = false) -> void:
	var f: Font = bold() if b else font()
	var w: float = f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	ci.draw_string(f, Vector2(center.x - w * 0.5, center.y + size * 0.36), s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


static func text_w(s: String, size: int, b: bool = false) -> float:
	var f: Font = bold() if b else font()
	return f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x


## Wrapped text. Returns the height used.
static func para(ci: CanvasItem, pos: Vector2, s: String, width: float, size: int, col: Color, b: bool = false) -> float:
	var f: Font = bold() if b else font()
	ci.draw_multiline_string(f, pos + Vector2(0, f.get_ascent(size)), s, HORIZONTAL_ALIGNMENT_LEFT, width, size, -1, col)
	return f.get_multiline_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, width, size).y


static func para_h(s: String, width: float, size: int, b: bool = false) -> float:
	var f: Font = bold() if b else font()
	return f.get_multiline_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, width, size).y


# ---------------------------------------------------------------- shapes

static func flat(bg: Color, radius: int = 12, border: Color = Color(0, 0, 0, 0), bw: int = 0, mx: int = 16, my: int = 9) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.set_corner_radius_all(radius)
	sb.corner_detail = 8
	sb.anti_aliasing = true
	if bw > 0:
		sb.border_color = border
		sb.set_border_width_all(bw)
	sb.content_margin_left = mx
	sb.content_margin_right = mx
	sb.content_margin_top = my
	sb.content_margin_bottom = my
	return sb


static func rrect(ci: CanvasItem, r: Rect2, col: Color, radius: float = 12.0) -> void:
	if r.size.x < 1.0 or r.size.y < 1.0 or col.a <= 0.003:
		return
	var key := "%s|%d" % [col.to_html(), int(radius)]
	var sb: StyleBoxFlat = _boxes.get(key)
	if sb == null:
		if _boxes.size() > 500:
			_boxes.clear()
		sb = flat(col, int(radius))
		_boxes[key] = sb
	ci.draw_style_box(sb, r)


static func card(ci: CanvasItem, r: Rect2, col: Color = PAPER, radius: float = 22.0) -> void:
	rrect(ci, Rect2(r.position + Vector2(0, 6), r.size), Color(0.1, 0.12, 0.18, 0.13), radius)
	rrect(ci, r, col, radius)


static func disc(ci: CanvasItem, c: Vector2, r: float, col: Color) -> void:
	if r > 0.2:
		ci.draw_circle(c, r, col, true, -1.0, true)


static func ring(ci: CanvasItem, c: Vector2, r: float, col: Color, w: float = 3.0) -> void:
	if r > 0.5:
		ci.draw_arc(c, r, 0.0, TAU, 48, col, w, true)


static func poly(ci: CanvasItem, pts: PackedVector2Array, col: Color) -> void:
	ci.draw_colored_polygon(pts, col)
	var closed := pts.duplicate()
	closed.append(pts[0])
	ci.draw_polyline(closed, col, 1.2, true)


static func oval(ci: CanvasItem, c: Vector2, r: Vector2, col: Color, rot: float = 0.0) -> void:
	if r.x < 0.6 or r.y < 0.6:
		return
	var pts := PackedVector2Array()
	for i in 32:
		var a := TAU * i / 32.0
		pts.append(c + Vector2(cos(a) * r.x, sin(a) * r.y).rotated(rot))
	poly(ci, pts, col)


static func limb(ci: CanvasItem, a: Vector2, b: Vector2, w: float, col: Color) -> void:
	if a.distance_squared_to(b) > 0.01:
		ci.draw_line(a, b, col, w, true)
	disc(ci, a, w * 0.5, col)
	disc(ci, b, w * 0.5, col)


static func star(ci: CanvasItem, c: Vector2, r: float, col: Color) -> void:
	if r < 1.0:
		return
	var pts := PackedVector2Array()
	for i in 10:
		var a := -PI / 2.0 + TAU * i / 10.0
		var rr := r if i % 2 == 0 else r * 0.46
		pts.append(c + Vector2(cos(a), sin(a)) * rr)
	poly(ci, pts, col)


static func heart(ci: CanvasItem, c: Vector2, s: float, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in 44:
		var a := TAU * i / 44.0
		var x := 16.0 * pow(sin(a), 3.0)
		var y := -(13.0 * cos(a) - 5.0 * cos(2.0 * a) - 2.0 * cos(3.0 * a) - cos(4.0 * a))
		pts.append(c + Vector2(x, y - 2.0) * s / 17.0)
	poly(ci, pts, col)


static func check(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float = 4.0) -> void:
	var pts := PackedVector2Array([c + Vector2(-0.5, 0.0) * s, c + Vector2(-0.12, 0.38) * s, c + Vector2(0.55, -0.42) * s])
	ci.draw_polyline(pts, col, w, true)


static func cross(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float = 4.0) -> void:
	ci.draw_line(c + Vector2(-0.45, -0.45) * s, c + Vector2(0.45, 0.45) * s, col, w, true)
	ci.draw_line(c + Vector2(-0.45, 0.45) * s, c + Vector2(0.45, -0.45) * s, col, w, true)


static func drop(ci: CanvasItem, c: Vector2, s: float, col: Color) -> void:
	var pts := PackedVector2Array()
	pts.append(c + Vector2(0, -1.0) * s)
	for i in 21:
		var a := -0.25 * PI + 1.5 * PI * i / 20.0
		pts.append(c + Vector2(0, 0.3) * s + Vector2(cos(a), sin(a)) * s * 0.62)
	poly(ci, pts, col)


static func icon(ci: CanvasItem, kind: String, c: Vector2, s: float, col: Color) -> void:
	match kind:
		"heart":
			heart(ci, c, s, col)
		"airway":
			ring(ci, c, s * 0.8, col, s * 0.2)
			disc(ci, c, s * 0.36, col)
		"clock":
			ring(ci, c, s * 0.82, col, s * 0.18)
			ci.draw_line(c, c + Vector2(0, -0.5) * s, col, s * 0.16, true)
			ci.draw_line(c, c + Vector2(0.36, 0.1) * s, col, s * 0.16, true)
		"drop":
			drop(ci, c, s, col)
		"flame":
			var pts := PackedVector2Array([
				c + Vector2(0.0, -1.0) * s, c + Vector2(0.3, -0.5) * s, c + Vector2(0.62, -0.1) * s,
				c + Vector2(0.7, 0.4) * s, c + Vector2(0.42, 0.85) * s, c + Vector2(0.0, 1.0) * s,
				c + Vector2(-0.42, 0.85) * s, c + Vector2(-0.7, 0.4) * s, c + Vector2(-0.55, -0.05) * s,
				c + Vector2(-0.3, 0.1) * s, c + Vector2(-0.25, -0.5) * s])
			poly(ci, pts, col)
		"phone":
			rrect(ci, Rect2(c.x - s * 0.5, c.y - s * 0.9, s, s * 1.8), col, s * 0.2)


# ---------------------------------------------------------------- bubbles

static func cleanup() -> void:
	_boxes.clear()
	_bold = null


## `shown` >= 0 draws only the first `shown` characters (the bubble keeps its full size).
static func bubble(ci: CanvasItem, tip: Vector2, s: String, size: int = 18, thought: bool = false, max_w: float = 250.0, alpha: float = 1.0, dx: float = 0.0, shown: int = -1) -> void:
	if alpha <= 0.01:
		return
	var f := font()
	var ts: Vector2 = f.get_multiline_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, max_w, size)
	var w := ts.x + 30.0
	var h := ts.y + 20.0
	var r := Rect2(tip.x - w * 0.5 + dx, tip.y - 24.0 - h, w, h)
	rrect(ci, Rect2(r.position + Vector2(0, 4), r.size), Color(0.1, 0.12, 0.18, 0.14 * alpha), 16)
	var bg := Color(1, 1, 1, alpha)
	rrect(ci, r, bg, 16)
	if thought:
		disc(ci, tip + Vector2(dx * 0.3, -17), 6.0, bg)
		disc(ci, tip + Vector2(0, -5), 3.5, bg)
	else:
		var bx := clampf(tip.x, r.position.x + 22.0, r.end.x - 22.0)
		poly(ci, PackedVector2Array([Vector2(bx - 11, r.end.y - 2), Vector2(bx + 11, r.end.y - 2), tip + Vector2(0, -4)]), bg)
	var txt := s if shown < 0 else s.left(shown)
	ci.draw_multiline_string(f, Vector2(r.position.x + 15, r.position.y + 10 + f.get_ascent(size)), txt, HORIZONTAL_ALIGNMENT_LEFT, max_w, size, -1, Color(INK, alpha))


# ---------------------------------------------------------------- people

## Two-bone IK: returns the elbow/knee, choosing the bend that points along `prefer`.
static func joint(a: Vector2, c: Vector2, l1: float, l2: float, prefer: Vector2) -> Vector2:
	var d := c - a
	var dist := clampf(d.length(), 0.001, l1 + l2 - 0.01)
	var dir := d.normalized() if d.length() > 0.001 else Vector2.DOWN
	var x := (l1 * l1 - l2 * l2 + dist * dist) / (2.0 * dist)
	var h := sqrt(maxf(l1 * l1 - x * x, 0.0))
	var n := Vector2(-dir.y, dir.x)
	var e1 := a + dir * x + n * h
	var e2 := a + dir * x - n * h
	return e1 if (e1 - a).dot(prefer) >= (e2 - a).dot(prefer) else e2


static func reach(a: Vector2, c: Vector2, max_len: float) -> Vector2:
	var d := c - a
	if d.length() > max_len:
		return a + d.normalized() * max_len
	return c


## Head in its own space: centre (0,0), radius 27. `xf` places it on screen.
static func head(ci: CanvasItem, xf: Transform2D, look: Dictionary, face: Dictionary = {}) -> void:
	ci.draw_set_transform_matrix(xf)
	var skin: Color = look.get("skin", SKINS[1])
	var hair: Color = look.get("hair", HAIRS[0])
	var style: int = look.get("style", 0)
	var tint: Color = face.get("tint", Color(0, 0, 0, 0))
	if tint.a > 0.0:
		skin = skin.lerp(Color(tint, 1.0), tint.a)
	var R := 27.0
	match style:
		1:
			rrect(ci, Rect2(-R - 5, -R * 0.75, 2 * R + 10, R * 2.3), hair, 18)
		2:
			disc(ci, Vector2(0, -R - 6), 12.0, hair)
		5:
			disc(ci, Vector2(0, -8), R + 10.0, hair)
		6:
			rrect(ci, Rect2(-R - 5, -R * 0.85, 2 * R + 10, R * 1.75), hair, 20)
	disc(ci, Vector2(-R + 1, 3), 5.5, skin.darkened(0.07))
	disc(ci, Vector2(R - 1, 3), 5.5, skin.darkened(0.07))
	disc(ci, Vector2.ZERO, R, skin)
	if look.get("back", false):
		disc(ci, Vector2(0, -2), R + 1.5, hair)
		ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return
	if style != 3:
		var cap_col: Color = look.get("hat", hair) if style == 4 else hair
		var cap := PackedVector2Array()
		for i in 19:
			var a := lerpf(deg_to_rad(196.0), deg_to_rad(344.0), i / 18.0)
			cap.append(Vector2(cos(a), sin(a)) * (R + 2.5))
		cap.append(Vector2(R * 0.72, -R * 0.44))
		cap.append(Vector2(0, -R * 0.56))
		cap.append(Vector2(-R * 0.72, -R * 0.44))
		poly(ci, cap, cap_col)
		if style == 4:
			rrect(ci, Rect2(-R - 7, -R * 0.5, 2 * R + 14, 8), cap_col.darkened(0.18), 4)
	else:
		disc(ci, Vector2(-R + 3, -8), 6.0, hair)
		disc(ci, Vector2(R - 3, -8), 6.0, hair)
		disc(ci, Vector2.ZERO, R - 1.0, skin)

	var gaze: Vector2 = face.get("gaze", Vector2.ZERO)
	var eyes: String = face.get("eyes", "open")
	var droop: float = face.get("droop", 0.0)
	var side: float = face.get("side", 1.0)
	var smile: float = face.get("smile", 0.2)
	var mouth: String = face.get("mouth", "line")
	var brow: float = face.get("brow", 0.0)
	var ink := INK
	for sx: float in [-1.0, 1.0]:
		var dr := droop if sx == side else 0.0
		var e := Vector2(sx * 10.0, 2.0) + gaze
		if eyes == "closed":
			ci.draw_arc(e + Vector2(0, -2), 4.5, 0.12 * PI, 0.88 * PI, 8, ink, 2.0, true)
		else:
			if eyes == "wide":
				disc(ci, e - gaze * 0.5, 6.2, Color.WHITE)
			disc(ci, e + Vector2(0, dr * 1.5), 3.3 if eyes != "wide" else 3.6, ink)
			if dr > 0.05:
				ci.draw_line(e + Vector2(-5.5, -2.5 + dr * 3.0), e + Vector2(5.5, -2.0 + dr * 4.0), skin.darkened(0.3), 2.4, true)
		var b0 := Vector2(sx * 5.0, -7.5 - brow * 3.0 + dr * 2.0)
		var b1 := Vector2(sx * 15.0, -7.5 + brow * 2.0 + dr * 4.0)
		ci.draw_line(b0, b1, Color(ink, 0.7), 2.0, true)
	disc(ci, Vector2(-15, 11), 4.5, Color(CORAL, 0.16))
	disc(ci, Vector2(15, 11), 4.5, Color(CORAL, 0.16))
	if mouth == "open":
		oval(ci, Vector2(0, 14.5), Vector2(6.0, 7.0), Color("5a1f1f"))
	elif mouth == "gasp":
		oval(ci, Vector2(0, 14.5), Vector2(4.0, 4.5), Color("5a1f1f"))
	else:
		var pts := PackedVector2Array()
		for i in 15:
			var x := lerpf(-10.5, 10.5, i / 14.0)
			var k := x / 10.5
			var on_side := signf(x) == side
			var m := smile * (1.0 - droop) if on_side else smile
			var y := 14.0 - m * 6.5 * k * k + m * 2.2
			if on_side:
				y += droop * 5.5 * k * k
			pts.append(Vector2(x, y))
		ci.draw_polyline(pts, ink, 2.5, true)
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


## Front-view person. `p` is the point between the feet; about 255 units tall at s = 1.
## pose: rot, lh, rh (hand targets, local), lf, rf (feet), tilt, face{}, sleeves(bool)
static func person(ci: CanvasItem, p: Vector2, s: float, look: Dictionary, pose: Dictionary = {}) -> void:
	var skin: Color = look.get("skin", SKINS[1])
	var top: Color = look.get("top", TEAL)
	var legs: Color = look.get("legs", INK)
	var shoe: Color = look.get("shoe", Color("1a2330"))
	var rot: float = pose.get("rot", 0.0)
	var base := Transform2D(rot, Vector2(s, s), 0.0, p)
	ci.draw_set_transform_matrix(base)
	var lf: Vector2 = pose.get("lf", Vector2(-15, -9))
	var rf: Vector2 = pose.get("rf", Vector2(15, -9))
	limb(ci, Vector2(-13, -102), lf, 23, legs)
	limb(ci, Vector2(13, -102), rf, 23, legs)
	oval(ci, lf + Vector2(-3, 5), Vector2(15, 8), shoe)
	oval(ci, rf + Vector2(3, 5), Vector2(15, 8), shoe)
	rrect(ci, Rect2(-33, -193, 66, 106), top, 24)
	if look.has("stripe"):
		var st: Color = look["stripe"]
		ci.draw_rect(Rect2(-33, -150, 66, 9), st)
	ci.draw_rect(Rect2(-8, -205, 16, 18), skin.darkened(0.1))
	var tilt: float = pose.get("tilt", 0.0)
	var hx := base * Transform2D(tilt, Vector2(0, -198)) * Transform2D(0.0, Vector2(0, -26))
	var face: Dictionary = pose.get("face", {})
	head(ci, hx, look, face)
	ci.draw_set_transform_matrix(base)
	var sleeves: bool = look.get("sleeves", true)
	for sx: float in [-1.0, 1.0]:
		var sh := Vector2(sx * 30.0, -178.0)
		var hand: Vector2 = pose.get("lh" if sx < 0.0 else "rh", Vector2(sx * 41.0, -99.0))
		hand = reach(sh, hand, 83.0)
		var el := joint(sh, hand, 42.0, 42.0, Vector2(sx, 0.7))
		limb(ci, sh, el, 18, top.darkened(0.07))
		limb(ci, el, hand, 15, top.darkened(0.07) if sleeves else skin)
		disc(ci, hand, 9.5, skin)
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


static func ambulance(ci: CanvasItem, p: Vector2, s: float, t: float) -> void:
	ci.draw_set_transform(p, 0.0, Vector2(s, s))
	rrect(ci, Rect2(-150, -150, 300, 130), Color("fbfbf8"), 16)
	rrect(ci, Rect2(-150, -118, 92, 98), Color("fbfbf8"), 18)
	rrect(ci, Rect2(-138, -106, 60, 42), Color("9fd0e2"), 8)
	ci.draw_rect(Rect2(-150, -62, 300, 16), CORAL)
	ci.draw_rect(Rect2(10, -122, 16, 50), TEAL)
	ci.draw_rect(Rect2(-7, -105, 50, 16), TEAL)
	var on := fmod(t * 3.0, 1.0) < 0.5
	rrect(ci, Rect2(-20, -166, 40, 18), Color("3d7be0") if on else Color("9db8e8"), 7)
	if on:
		disc(ci, Vector2(0, -158), 34.0, Color(0.3, 0.55, 1.0, 0.18))
	disc(ci, Vector2(-88, -18), 25.0, Color("1a2330"))
	disc(ci, Vector2(-88, -18), 10.0, Color("aab3bd"))
	disc(ci, Vector2(88, -18), 25.0, Color("1a2330"))
	disc(ci, Vector2(88, -18), 10.0, Color("aab3bd"))
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


# ---------------------------------------------------------------- controls

static func style_button(b: Button, kind: String, size: int = 19) -> void:
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	b.add_theme_font_size_override("font_size", size)
	var normal: StyleBoxFlat
	var hover: StyleBoxFlat
	var pressed: StyleBoxFlat
	var fc := INK
	var fp := Color.WHITE
	match kind:
		"primary":
			normal = flat(CORAL, 16, CORAL, 0, 26, 12)
			hover = flat(CORAL.lightened(0.12), 16, CORAL, 0, 26, 12)
			pressed = flat(CORAL_DARK, 16, CORAL, 0, 26, 12)
			fc = Color.WHITE
			b.add_theme_font_override("font", bold())
		"option":
			normal = flat(Color.WHITE, 13, Color(INK, 0.22), 2, 18, 10)
			hover = flat(Color("fff0e6"), 13, CORAL, 2, 18, 10)
			pressed = flat(CORAL, 13, CORAL, 2, 18, 10)
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		_:
			normal = flat(Color(PAPER, 0.95), 18, Color(INK, 0.18), 2, 16, 7)
			hover = flat(Color.WHITE, 18, INK, 2, 16, 7)
			pressed = flat(INK, 18, INK, 2, 16, 7)
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("disabled", normal)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.add_theme_color_override("font_color", fc)
	b.add_theme_color_override("font_hover_color", fc)
	b.add_theme_color_override("font_focus_color", fc)
	b.add_theme_color_override("font_pressed_color", fp)
	b.add_theme_color_override("font_hover_pressed_color", fp)
