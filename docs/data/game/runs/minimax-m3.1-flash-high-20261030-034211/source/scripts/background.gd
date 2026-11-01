extends Control
class_name SoftBackground

## A lightweight, asset-free painted background. All shapes are generated at runtime.

func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _draw() -> void:
	var w := size.x
	var h := size.y
	draw_rect(Rect2(0, 0, w, h), Color("#eef4e7"))

	# Broad, soft color pools suggest land, water and sunlight.
	draw_circle(Vector2(w * 0.10, h * 0.88), 360.0, Color(0.72, 0.84, 0.76, 0.22))
	draw_circle(Vector2(w * 0.92, h * 0.08), 310.0, Color(0.95, 0.78, 0.52, 0.12))
	draw_circle(Vector2(w * 0.72, h * 0.82), 420.0, Color(0.48, 0.72, 0.70, 0.10))

	# Topographic lines add quiet depth without relying on image assets.
	var line_color := Color(0.31, 0.49, 0.43, 0.075)
	for ring in range(7):
		var points := PackedVector2Array()
		var center := Vector2(w * 0.16, h * 0.14)
		var rx := 115.0 + ring * 38.0
		var ry := 54.0 + ring * 19.0
		for i in range(49):
			var a := TAU * float(i) / 48.0
			var wobble := sin(a * 3.0 + ring * 0.7) * 8.0 + cos(a * 5.0) * 3.0
			points.append(center + Vector2(cos(a) * (rx + wobble), sin(a) * (ry + wobble)))
		draw_polyline(points, line_color, 1.5, true)

	# Fine dotted grid, fading toward the right.
	for x in range(24, int(w), 28):
		for y in range(24, int(h), 28):
			var fade: float = 1.0 - clamp(float(x) / maxf(w, 1.0), 0.0, 1.0)
			draw_circle(Vector2(x, y), 1.1, Color(0.20, 0.38, 0.33, 0.08 * fade))
