extends Node2D
## Base for a moment. Each moment is a coroutine (`run`) that scripts the scene,
## plus `tick` / `_draw` for the hands-on parts.

signal finished(result: Dictionary)
signal step_done
signal picked(what)
signal frame

const Art = preload("res://scripts/art.gd")

var hud
var number := "112"
var auto := false
var t := 0.0
var mistakes := 0
var skill := 1.0
var mouse := Vector2(-999, -999)
var phase := ""
var phase_t := 0.0
var fired := false


func _process(delta: float) -> void:
	t += delta
	tick(delta)
	queue_redraw()
	frame.emit()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		mouse = event.position
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		mouse = event.position
		if event.pressed:
			press(event.position)
		else:
			release(event.position)
	elif event is InputEventKey and not event.echo:
		key(event.keycode, event.pressed)


# ---- overridables
func run() -> void:
	pass

func tick(_delta: float) -> void:
	pass

func press(_p: Vector2) -> void:
	pass

func release(_p: Vector2) -> void:
	pass

func key(_code: int, _down: bool) -> void:
	pass

func on_mistake() -> void:
	pass


# ---- scripting helpers
func set_phase(p: String) -> void:
	phase = p
	phase_t = t
	fired = false


func since() -> float:
	return t - phase_t


func pause(sec: float) -> void:
	var end := t + sec
	while t < end:
		await frame


func say(text: String, tag: String = "") -> void:
	hud.say(text, tag)
	await hud.continued


func choose(prompt: String, options: Array, tag: String = "") -> int:
	hud.choose(prompt, options, tag)
	var i: int = await hud.chosen
	return i


func good(text: String) -> void:
	Sfx.play("good")
	hud.feedback(true, text)
	await hud.continued


func bad(text: String) -> void:
	mistakes += 1
	on_mistake()
	Sfx.play("bad")
	hud.feedback(false, text)
	await hud.continued


## options: [{t: text, ok: bool, fb: feedback}]. Repeats until the right one is picked.
func quiz(prompt: String, options: Array, tag: String = "") -> int:
	var opts := options.duplicate()
	opts.shuffle()
	var wrong := 0
	while true:
		var labels: Array = []
		for o: Dictionary in opts:
			labels.append(o["t"])
		var i: int = await choose(prompt, labels, tag)
		var pick: Dictionary = opts[i]
		if pick["ok"]:
			if pick.has("fb"):
				await good(pick["fb"])
			break
		wrong += 1
		await bad(pick["fb"])
		opts.remove_at(i)
	return wrong


func stars() -> int:
	if mistakes == 0 and skill >= 0.7:
		return 3
	if mistakes <= 2 and skill >= 0.4:
		return 2
	return 1


func finish(headline: String, outcome: String) -> void:
	finished.emit({"stars": stars(), "headline": headline, "outcome": outcome, "mistakes": mistakes, "skill": skill})
