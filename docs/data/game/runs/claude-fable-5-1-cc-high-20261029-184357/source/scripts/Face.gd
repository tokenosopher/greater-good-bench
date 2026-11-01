extends Control
## A small drawn face whose expression follows a wellbeing value.

var wellbeing := 60.0
var tint := Color.WHITE
var hungry := false


func _ready() -> void:
	custom_minimum_size = Vector2(44, 44)


func set_state(w: float, c: Color, h: bool) -> void:
	wellbeing = w
	tint = c
	hungry = h
	queue_redraw()


func _draw() -> void:
	var r := minf(size.x, size.y) * 0.5
	var c := size * 0.5
	draw_circle(c, r, tint.darkened(0.35))
	draw_circle(c, r - 2.0, tint)
	var eye_y := c.y - r * 0.2
	var eye_dx := r * 0.35
	var dark := Color(0.12, 0.1, 0.1)
	if wellbeing < 20.0:
		# tired eyes
		draw_line(Vector2(c.x - eye_dx - 4, eye_y), Vector2(c.x - eye_dx + 4, eye_y + 2), dark, 2.0)
		draw_line(Vector2(c.x + eye_dx - 4, eye_y + 2), Vector2(c.x + eye_dx + 4, eye_y), dark, 2.0)
	else:
		draw_circle(Vector2(c.x - eye_dx, eye_y), r * 0.1, dark)
		draw_circle(Vector2(c.x + eye_dx, eye_y), r * 0.1, dark)
	# mouth: curvature from -1 (frown) to +1 (smile)
	var k: float = clampf((wellbeing - 50.0) / 40.0, -1.0, 1.0)
	var mouth_y := c.y + r * 0.35
	var pts := PackedVector2Array()
	var n := 12
	for i in range(n + 1):
		var u := float(i) / float(n)
		var x := c.x - r * 0.45 + u * r * 0.9
		var y := mouth_y - k * r * 0.3 * (4.0 * u * (1.0 - u)) + k * r * 0.12
		pts.append(Vector2(x, y))
	draw_polyline(pts, dark, 2.0)
	if hungry:
		draw_arc(c, r + 3.0, 0.0, TAU, 24, Color(0.95, 0.4, 0.3, 0.9), 2.0)
