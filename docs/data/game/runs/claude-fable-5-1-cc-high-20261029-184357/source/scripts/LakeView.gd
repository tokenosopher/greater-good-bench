extends Control
## Draws the shared lake. Fish count and water colour follow the stock.

var fish := 70.0
var capacity := 100.0
var dead := false
var _fish_seed: Array = []
var _t := 0.0


func _ready() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1234
	for i in range(30):
		var a := rng.randf() * TAU
		var d := sqrt(rng.randf()) * 0.85
		_fish_seed.append({"a": a, "d": d, "ph": rng.randf() * TAU, "dir": 1.0 if rng.randf() < 0.5 else -1.0, "spd": 0.6 + rng.randf() * 0.8})


func set_state(f: float, cap: float, is_dead: bool) -> void:
	fish = f
	capacity = cap
	dead = is_dead
	queue_redraw()


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _ellipse(c: Vector2, rx: float, ry: float, n: int = 48) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in range(n):
		var a := TAU * float(i) / float(n)
		pts.append(c + Vector2(cos(a) * rx, sin(a) * ry))
	return pts


func _draw() -> void:
	var c := size * 0.5
	var rx := size.x * 0.46
	var ry := size.y * 0.42
	var health: float = clampf(fish / capacity, 0.0, 1.0)
	# shore
	draw_colored_polygon(_ellipse(c, rx + 14.0, ry + 14.0), Color(0.36, 0.42, 0.24))
	draw_colored_polygon(_ellipse(c, rx + 6.0, ry + 6.0), Color(0.66, 0.6, 0.42))
	# water: clear blue when healthy, murky when drained
	var healthy := Color(0.2, 0.52, 0.66)
	var murky := Color(0.33, 0.36, 0.3)
	var water := murky.lerp(healthy, health)
	draw_colored_polygon(_ellipse(c, rx, ry), water)
	draw_colored_polygon(_ellipse(c + Vector2(0, -ry * 0.15), rx * 0.75, ry * 0.6), water.lightened(0.08))
	# ripples
	for i in range(3):
		var ph := fmod(_t * 0.25 + float(i) * 0.33, 1.0)
		var col := Color(1, 1, 1, 0.12 * (1.0 - ph))
		draw_arc(c + Vector2(rx * 0.2, ry * 0.1), 8.0 + ph * 40.0, 0.0, TAU, 40, col, 1.5)
	# fish
	var count: int = clampi(int(round(fish / capacity * 30.0)), 0, 30)
	var fcol := Color(0.95, 0.82, 0.42)
	for i in range(count):
		var s: Dictionary = _fish_seed[i]
		var a: float = s.a + _t * 0.15 * s.spd * s.dir
		var p := c + Vector2(cos(a) * rx * s.d, sin(a) * ry * s.d)
		p.y += sin(_t * 1.7 + s.ph) * 2.0
		var dir: float = 1.0 if -sin(a) * s.dir > 0.0 else -1.0
		var body := _ellipse(p, 7.0, 3.5, 12)
		draw_colored_polygon(body, fcol)
		var tail := PackedVector2Array([p + Vector2(-7.0 * dir, 0), p + Vector2(-12.0 * dir, -4.0), p + Vector2(-12.0 * dir, 4.0)])
		draw_colored_polygon(tail, fcol.darkened(0.15))
	if dead:
		var f := get_theme_default_font()
		draw_string(f, c + Vector2(-70, 6), "The lake is empty.", HORIZONTAL_ALIGNMENT_CENTER, 140, 18, Color(0.95, 0.9, 0.85))
