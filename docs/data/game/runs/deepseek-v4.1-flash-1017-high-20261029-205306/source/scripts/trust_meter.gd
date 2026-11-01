extends Control

var value := 4
var max_value := 6
var fill_color := Color("#2E5E46")
var _glow := 0.0


func _ready() -> void:
	custom_minimum_size = Vector2(106, 18)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func set_values(v: int, m: int, color: Color) -> void:
	var changed := v != value or m != max_value
	value = v
	max_value = m
	fill_color = color
	if changed:
		_glow = 1.0
	queue_redraw()


func _process(delta: float) -> void:
	if _glow > 0.0:
		_glow = max(0.0, _glow - delta * 2.5)
		queue_redraw()


func _draw() -> void:
	var step := 16.0
	for i in range(max_value):
		var center := Vector2(7.0 + step * float(i), 9.0)
		if i < value:
			if i == value - 1 and _glow > 0.0:
				draw_circle(center, 6.5 + _glow * 2.0, Color(fill_color, 0.18 * _glow))
			draw_circle(center, 5.0, fill_color)
			draw_circle(center + Vector2(-1.2, -1.2), 1.6, Color(1, 1, 1, 0.35))
		else:
			draw_circle(center, 4.5, Color(0.2, 0.24, 0.2, 0.10))
