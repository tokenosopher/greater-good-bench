extends Control
## A soft, slowly breathing landscape painted entirely in code.

const UIKit = preload("res://scripts/ui_kit.gd")

var t := 0.0
var _stars: Array[Vector3] = []


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var rng := RandomNumberGenerator.new()
	rng.seed = 20261029
	for i in range(54):
		_stars.append(Vector3(rng.randf(), rng.randf(), rng.randf_range(0.6, 1.8)))


func _process(delta: float) -> void:
	t += delta
	queue_redraw()


func _draw() -> void:
	var w := size.x
	var h := size.y
	if w <= 1.0 or h <= 1.0:
		return
	draw_rect(Rect2(Vector2.ZERO, size), UIKit.CREAM)

	# Warm sun.
	var sun := Vector2(w * 0.83, h * 0.17)
	draw_circle(sun, 150.0 + sin(t * 0.35) * 4.0, Color(0.89, 0.68, 0.33, 0.075))
	draw_circle(sun, 96.0 + sin(t * 0.35 + 1.2) * 3.0, Color(0.89, 0.68, 0.33, 0.075))
	draw_circle(sun, 54.0, Color(0.89, 0.68, 0.33, 0.10))

	# Soft drifting shapes.
	for i in range(3):
		var phase := t * (0.07 + i * 0.015) + i * 2.1
		var pos := Vector2(
			w * (0.18 + 0.24 * i) + sin(phase) * 26.0,
			h * (0.52 + 0.10 * i) + cos(phase * 1.3) * 14.0
		)
		draw_circle(pos, 110.0 + i * 24.0, Color(0.18, 0.37, 0.27, 0.022))

	# Tiny dust motes.
	for s in _stars:
		var x := fmod(s.x * w + t * (3.0 + s.z * 2.0), w)
		var y := s.y * h + sin(t * 0.3 + s.x * 9.0) * 4.0
		draw_circle(Vector2(x, y), s.z, Color(0.35, 0.30, 0.20, 0.055))

	# Layered hills.
	_hill(w, h, h * 0.80, 26.0, Color(0.23, 0.40, 0.30, 0.055), 0.9)
	_hill(w, h, h * 0.88, 34.0, Color(0.23, 0.40, 0.30, 0.065), 1.7)
	_hill(w, h, h * 0.97, 22.0, Color(0.18, 0.33, 0.24, 0.07), 2.6)


func _hill(w: float, h: float, base_y: float, amp: float, color: Color, offset: float) -> void:
	var pts := PackedVector2Array()
	var steps := 64
	for i in range(steps + 1):
		var x := w * float(i) / float(steps)
		var y := base_y + sin(float(i) * 0.21 + offset) * amp + sin(float(i) * 0.083 + offset * 2.0) * amp * 0.45
		y = clampf(y, 0.0, h - 1.0)
		pts.append(Vector2(x, y))
	pts.append(Vector2(w, h))
	pts.append(Vector2(0.0, h))
	draw_colored_polygon(pts, color)
