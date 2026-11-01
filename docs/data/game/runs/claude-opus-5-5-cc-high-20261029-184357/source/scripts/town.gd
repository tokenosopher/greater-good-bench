extends Control
## The town of Brindlewick drawn as a network of neighbours.
## Each choice the player makes sends a ripple outward from "you" along the
## friendship links, nudging each neighbour towards clarity or fog.

signal clarity_changed

const TARGET_NODES := 42
const CLEAR_THRESHOLD := 0.5
const HOP_TIME := 0.26
const GOOD_COLOR := Color("#8ce99a")
const BAD_COLOR := Color("#ff6b6b")
const FOG_COLOR := Color("#6b6e80")
const CLEAR_COLOR := Color("#ffd97a")
const INK := Color("#1d2a3a")

var nodes: Array = []
var edges: Array = []
var adj: Array = []
var travelers: Array = []
var rings: Array = []
var time := 0.0
var you := 0
var rng := RandomNumberGenerator.new()
var bg_style: StyleBoxFlat


func setup(rect_size: Vector2) -> void:
	size = rect_size
	custom_minimum_size = rect_size
	mouse_filter = MOUSE_FILTER_IGNORE
	bg_style = StyleBoxFlat.new()
	bg_style.bg_color = Color("#1c2838")
	bg_style.set_corner_radius_all(14)
	rng.seed = 20261029
	_generate()
	reset()


func river_y(x: float) -> float:
	return size.y * 0.58 + sin(x / 85.0) * 22.0 + sin(x / 37.0) * 6.0


func _generate() -> void:
	nodes.clear()
	edges.clear()
	adj.clear()
	var tries := 0
	while nodes.size() < TARGET_NODES and tries < 40000:
		tries += 1
		var p := Vector2(rng.randf_range(26, size.x - 26), rng.randf_range(24, size.y - 34))
		if absf(p.y - river_y(p.x)) < 24.0:
			continue
		var ok := true
		for n in nodes:
			if n.pos.distance_to(p) < 46.0:
				ok = false
				break
		if ok:
			nodes.append({"pos": p, "clarity": 0.5, "phase": rng.randf() * TAU,
				"flash": 0.0, "flash_col": Color.WHITE, "recept": rng.randf_range(0.6, 1.3)})
	for i in nodes.size():
		adj.append([])
	for i in nodes.size():
		var others := []
		for j in nodes.size():
			if j != i:
				others.append([nodes[i].pos.distance_to(nodes[j].pos), j])
		others.sort_custom(func(a, b): return a[0] < b[0])
		for k in mini(3, others.size()):
			_link(i, others[k][1])
	# Join any separate clusters so every neighbour can be reached.
	while true:
		var comp := _component(0)
		if comp.size() == nodes.size():
			break
		var best := INF
		var bi := -1
		var bj := -1
		for i in comp.keys():
			for j in nodes.size():
				if not comp.has(j):
					var d: float = nodes[i].pos.distance_to(nodes[j].pos)
					if d < best:
						best = d
						bi = i
						bj = j
		_link(bi, bj)
	var center := Vector2(size.x * 0.5, size.y * 0.35)
	var best_d := INF
	for i in nodes.size():
		var d: float = nodes[i].pos.distance_to(center)
		if d < best_d:
			best_d = d
			you = i


func _link(i: int, j: int) -> void:
	if adj[i].has(j):
		return
	adj[i].append(j)
	adj[j].append(i)
	edges.append([i, j])


func _component(start: int) -> Dictionary:
	var seen := {start: true}
	var stack := [start]
	while not stack.is_empty():
		var n: int = stack.pop_back()
		for m in adj[n]:
			if not seen.has(m):
				seen[m] = true
				stack.append(m)
	return seen


func reset() -> void:
	for n in nodes:
		n.clarity = rng.randf_range(0.3, 0.68)
		n.flash = 0.0
	nodes[you].clarity = 0.7
	travelers.clear()
	rings.clear()
	clarity_changed.emit()


func count_clear() -> int:
	var c := 0
	for n in nodes:
		if n.clarity >= CLEAR_THRESHOLD:
			c += 1
	return c


func total() -> int:
	return nodes.size()


## Positive amounts spread clarity, negative amounts spread fog.
func send_wave(amount: float) -> void:
	var col := GOOD_COLOR if amount > 0.0 else BAD_COLOR
	_apply(you, amount, col)
	var dist := {you: 0}
	var queue := [you]
	while not queue.is_empty():
		var n: int = queue.pop_front()
		for m in adj[n]:
			if dist.has(m):
				continue
			# Not every conversation passes it on; another neighbour may still.
			if rng.randf() > 0.88:
				continue
			dist[m] = dist[n] + 1
			queue.append(m)
			var d: int = dist[m]
			travelers.append({"from": n, "to": m, "t0": time + (d - 1) * HOP_TIME,
				"t1": time + d * HOP_TIME, "amt": amount * pow(0.9, d), "col": col})


func _apply(i: int, amt: float, col: Color) -> void:
	var n: Dictionary = nodes[i]
	n.clarity = clampf(n.clarity + amt * n.recept, 0.0, 1.0)
	n.flash = 1.0
	n.flash_col = col
	rings.append({"pos": n.pos, "t": 0.0, "col": col})
	clarity_changed.emit()


func _process(delta: float) -> void:
	time += delta
	var i := travelers.size() - 1
	while i >= 0:
		var tr: Dictionary = travelers[i]
		if time >= tr.t1:
			_apply(tr.to, tr.amt, tr.col)
			travelers.remove_at(i)
		i -= 1
	for n in nodes:
		n.flash = maxf(0.0, n.flash - delta * 1.6)
	for r in rings:
		r.t += delta
	rings = rings.filter(func(r): return r.t < 0.8)
	queue_redraw()


func _node_pos(i: int) -> Vector2:
	var n: Dictionary = nodes[i]
	return n.pos + Vector2(0, sin(time * 1.6 + n.phase) * 1.5)


func _draw() -> void:
	draw_style_box(bg_style, Rect2(Vector2.ZERO, size))
	var pts := PackedVector2Array()
	var x := 6.0
	while x <= size.x - 6.0:
		pts.append(Vector2(x, river_y(x)))
		x += 8.0
	draw_polyline(pts, Color("#24476b"), 20.0, true)
	draw_polyline(pts, Color("#3a6f9f"), 9.0, true)

	for e in edges:
		draw_line(_node_pos(e[0]), _node_pos(e[1]), Color(1, 1, 1, 0.09), 1.5, true)

	for tr in travelers:
		if time < tr.t0:
			continue
		var f: float = clampf((time - tr.t0) / (tr.t1 - tr.t0), 0.0, 1.0)
		var a := _node_pos(tr.from)
		var p := a.lerp(_node_pos(tr.to), f)
		draw_line(a, p, Color(tr.col, 0.45), 2.0, true)
		draw_circle(p, 3.5, tr.col)

	for r in rings:
		var k: float = r.t / 0.8
		draw_arc(r.pos, 9.0 + k * 22.0, 0, TAU, 32, Color(r.col, (1.0 - k) * 0.55), 2.0, true)

	for i in nodes.size():
		var n: Dictionary = nodes[i]
		var p := _node_pos(i)
		var c: float = n.clarity
		var col := FOG_COLOR.lerp(CLEAR_COLOR, smoothstep(0.25, 0.75, c))
		var r := 9.5 if i == you else 7.5
		if c < CLEAR_THRESHOLD:
			# A little cloud of fog around misled neighbours.
			var fog := Color(0.62, 0.64, 0.72, 0.12 + (CLEAR_THRESHOLD - c) * 0.5)
			draw_circle(p + Vector2(-5, -4), r + 2.0, fog)
			draw_circle(p + Vector2(5, -5), r + 1.0, fog)
			draw_circle(p + Vector2(0, 2), r + 4.0, fog)
		else:
			draw_circle(p, r + 6.0, Color(CLEAR_COLOR, 0.06 + (c - CLEAR_THRESHOLD) * 0.25))
		draw_circle(p, r, col)
		draw_circle(p + Vector2(-2.6, -1.2), 1.2, INK)
		draw_circle(p + Vector2(2.6, -1.2), 1.2, INK)
		if c >= CLEAR_THRESHOLD:
			draw_arc(p + Vector2(0, 0.6), 3.0, 0.35, PI - 0.35, 8, INK, 1.2, true)
		else:
			draw_line(p + Vector2(-2.6, 3.0), p + Vector2(2.6, 3.0), INK, 1.2, true)
		if n.flash > 0.0:
			draw_arc(p, r + 3.0 + (1.0 - n.flash) * 6.0, 0, TAU, 24, Color(n.flash_col, n.flash), 2.0, true)
		if i == you:
			draw_arc(p, r + 2.5, 0, TAU, 32, Color.WHITE, 2.0, true)
			draw_string(ThemeDB.fallback_font, p + Vector2(-30, -16), "you", HORIZONTAL_ALIGNMENT_CENTER, 60, 14, Color.WHITE)

	var font := ThemeDB.fallback_font
	var ly := size.y - 12.0
	draw_circle(Vector2(18, ly - 5), 5, CLEAR_COLOR)
	draw_string(font, Vector2(28, ly), "clear-minded", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color("#c9d1e3"))
	draw_circle(Vector2(128, ly - 5), 5, FOG_COLOR)
	draw_string(font, Vector2(138, ly), "misled", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color("#c9d1e3"))
	draw_string(font, Vector2(size.x - 160, ly), "Brindlewick", HORIZONTAL_ALIGNMENT_RIGHT, 150, 13, Color("#7f8aa3"))
