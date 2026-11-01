extends Control
class_name CommonGroundBoard

signal site_clicked(index: int)

var sites: Array = []
var selected_action: int = 0
var hovered_site: int = -1
var selected_site: int = -1
var animation_time: float = 0.0

const SITE_RADIUS := 57.0
const RING_SITES := 6

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	custom_minimum_size = Vector2(720, 492)
	set_process(true)

func _process(delta: float) -> void:
	animation_time += delta
	queue_redraw()

func layout_sites() -> void:
	if sites.is_empty():
		return
	var center := Vector2(size.x * 0.51, size.y * 0.49)
	var ring_radius := Vector2(size.x * 0.335, size.y * 0.345)
	for i in range(sites.size()):
		var site: Dictionary = sites[i]
		if i == 0:
			site["position"] = center
		else:
			var n := i - 1
			var angle := -PI * 0.5 + TAU * float(n) / float(RING_SITES)
			site["position"] = center + Vector2(cos(angle) * ring_radius.x, sin(angle) * ring_radius.y)
		sites[i] = site
	queue_redraw()

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		var old_hover := hovered_site
		hovered_site = _site_at(event.position)
		if old_hover != hovered_site:
			queue_redraw()
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		var index := _site_at(event.position)
		if index >= 0:
			selected_site = index
			queue_redraw()
			site_clicked.emit(index)

func _site_at(point: Vector2) -> int:
	for i in range(sites.size()):
		var site: Dictionary = sites[i]
		if point.distance_to(site["position"]) <= SITE_RADIUS + 5.0:
			return i
	return -1

func _draw() -> void:
	if sites.is_empty():
		return
	var center := Vector2(size.x * 0.51, size.y * 0.49)

	# The central circle is a shared watershed, tying every district together.
	draw_circle(center + Vector2(0, 7), 132.0, Color(0.20, 0.39, 0.34, 0.08))
	draw_arc(center, 127.0, 0, TAU, 96, Color(0.28, 0.51, 0.45, 0.24), 2.0, true)
	for i in range(1, sites.size()):
		var site: Dictionary = sites[i]
		var p: Vector2 = site["position"]
		var pulse := 1.0 + sin(animation_time * 1.2 + float(i)) * 0.012
		draw_dashed_line(center, p, Color(0.29, 0.52, 0.45, 0.30), 2.0, 7.0)
		draw_circle(p, 8.0 * pulse, Color(0.30, 0.55, 0.48, 0.34))

	for i in range(sites.size()):
		_draw_site(i, sites[i])

	# A tiny compass-like title makes the map feel intentionally illustrated.
	var font := ThemeDB.fallback_font
	draw_string(font, Vector2(18, 29), "THE LIVING COMMONS", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(0.20, 0.40, 0.35, 0.72))
	draw_string(font, Vector2(size.x - 92, size.y - 15), "8 DAY PLAN", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.20, 0.40, 0.35, 0.55))

func _draw_site(index: int, site: Dictionary) -> void:
	var pos: Vector2 = site["position"]
	var nature: float = site["nature"]
	var people: float = site["people"]
	var min_health := minf(nature, people)
	var is_center := index == 0
	var radius := SITE_RADIUS + (8.0 if is_center else 0.0)
	var fill := Color("#f6f0df").lerp(Color("#b8d9ba"), clampf(min_health / 100.0, 0.0, 1.0) * 0.52)
	var accent := Color("#d27659").lerp(Color("#3f8268"), clampf(min_health / 100.0, 0.0, 1.0))
	var lift := sin(animation_time * 1.5 + float(index) * 0.8) * 1.4

	draw_circle(pos + Vector2(0, 7), radius, Color(0.17, 0.31, 0.27, 0.11))
	if hovered_site == index:
		draw_circle(pos, radius + 8.0, Color(1, 1, 1, 0.52))
		draw_arc(pos, radius + 7.0, 0, TAU, 64, Color(0.24, 0.45, 0.39, 0.55), 2.0, true)
	if selected_site == index:
		draw_arc(pos, radius + 5.0, -0.25, PI * 1.50, 64, Color(0.82, 0.42, 0.29, 0.95), 4.0, true)

	# An irregular landmass shape keeps the map playful and hand-made.
	var points := PackedVector2Array()
	var point_count := 18
	for p in range(point_count):
		var angle := TAU * float(p) / float(point_count)
		var wobble := 1.0 + sin(angle * 3.0 + float(index) * 1.4) * 0.045 + cos(angle * 5.0) * 0.025
		points.append(pos + Vector2(cos(angle) * radius * wobble, sin(angle) * radius * wobble) + Vector2(0, lift))
	draw_colored_polygon(points, fill)
	var outline := points.duplicate()
	outline.append(points[0])
	draw_polyline(outline, accent, 3.0, true)

	# Health halo: green for nature, terracotta for people.
	var start := -PI * 0.5
	draw_arc(pos, radius + 3.0, start, start + TAU * nature / 100.0, 72, Color("#43856a"), 3.0, true)
	draw_arc(pos, radius + 7.0, start, start + TAU * people / 100.0, 72, Color("#d27659"), 3.0, true)

	_draw_icon(site["kind"], pos + Vector2(0, -7), accent, index)

	var font := ThemeDB.fallback_font
	var label_width := 136.0
	draw_string(font, pos + Vector2(-label_width * 0.5, radius + 18.0), site["name"], HORIZONTAL_ALIGNMENT_CENTER, label_width, 15, Color(0.16, 0.29, 0.26))

	# Compact two-bar readout.
	var bar := Rect2(pos.x - 40, pos.y + radius + 25, 80, 7)
	draw_rect(bar, Color(0.20, 0.33, 0.29, 0.12), true)
	draw_rect(Rect2(bar.position, Vector2(bar.size.x * nature / 100.0, bar.size.y)), Color("#43856a"), true)
	var bar2 := Rect2(bar.position + Vector2(0, 10), bar.size)
	draw_rect(bar2, Color(0.20, 0.33, 0.29, 0.12), true)
	draw_rect(Rect2(bar2.position, Vector2(bar2.size.x * people / 100.0, bar2.size.y)), Color("#d27659"), true)

func _draw_icon(kind: String, pos: Vector2, color: Color, seed_value: int) -> void:
	match kind:
		"commons":
			_draw_tree(pos, color, 1.0)
		"forest":
			_draw_tree(pos + Vector2(-12, 2), color, 0.72)
			_draw_tree(pos + Vector2(12, 4), color, 0.82)
		"wetland":
			for row in range(3):
				var y := pos.y - 8 + row * 9
				draw_polyline(PackedVector2Array([pos + Vector2(-19, y), pos + Vector2(-7, y + 3), pos + Vector2(5, y - 1), pos + Vector2(19, y + 2)]), color, 2.0, true)
			draw_line(pos + Vector2(-10, 6), pos + Vector2(-10, -17), color, 2.0)
			draw_line(pos + Vector2(10, 6), pos + Vector2(10, -14), color, 2.0)
		"river":
			draw_polyline(PackedVector2Array([pos + Vector2(-22, -15), pos + Vector2(-7, -6), pos + Vector2(3, 5), pos + Vector2(-8, 15), pos + Vector2(19, 18)]), color, 4.0, true)
			draw_circle(pos + Vector2(18, -15), 5.0, color)
		"coast":
			draw_arc(pos + Vector2(0, -7), 10.0, 0, TAU, 32, color, 2.5, true)
			for row in range(3):
				var yy := pos.y + 3 + row * 7
				draw_polyline(PackedVector2Array([pos + Vector2(-21, yy), pos + Vector2(-8, yy + 3), pos + Vector2(7, yy - 1), pos + Vector2(21, yy + 2)]), color, 2.0, true)
		"meadow":
			draw_line(pos + Vector2(0, 16), pos + Vector2(0, -12), color, 2.0)
			for offset in [Vector2(-12, 6), Vector2(11, 2), Vector2(-7, -7), Vector2(9, -10)]:
				draw_circle(pos + offset, 5.0, color)
		"community":
			for house in [Vector2(-15, 3), Vector2(9, 6)]:
				var h: Vector2 = pos + house
				draw_rect(Rect2(h.x - 10, h.y - 7, 20, 17), color, true)
				draw_colored_polygon(PackedVector2Array([h + Vector2(-13, -7), h + Vector2(0, -19), h + Vector2(13, -7)]), color)
			draw_rect(Rect2(pos.x - 3, pos.y + 12, 6, 8), color, true)

func _draw_tree(pos: Vector2, color: Color, scale_factor: float) -> void:
	draw_rect(Rect2(pos.x - 3 * scale_factor, pos.y + 4, 6 * scale_factor, 13 * scale_factor), color, true)
	draw_colored_polygon(PackedVector2Array([
		pos + Vector2(0, -21 * scale_factor),
		pos + Vector2(-14 * scale_factor, 5 * scale_factor),
		pos + Vector2(14 * scale_factor, 5 * scale_factor)
	]), color)
