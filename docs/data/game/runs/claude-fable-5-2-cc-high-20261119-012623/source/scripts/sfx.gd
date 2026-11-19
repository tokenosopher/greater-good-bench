extends Node
## All sound is synthesised at start-up. No audio files.

const RATE := 22050

var muted := false
var _streams: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _loop: AudioStreamPlayer


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in 8:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
	_loop = AudioStreamPlayer.new()
	add_child(_loop)
	_build()


func play(id: String, vol_db: float = 0.0, pitch: float = 1.0) -> void:
	if muted or not _streams.has(id):
		return
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[id]
	p.volume_db = vol_db
	p.pitch_scale = pitch
	p.play()


func loop(id: String, vol_db: float = -14.0) -> void:
	if muted or not _streams.has(id):
		return
	_loop.stream = _streams[id]
	_loop.volume_db = vol_db
	_loop.play()


func stop_loop() -> void:
	_loop.stop()


func set_muted(m: bool) -> void:
	muted = m
	if m:
		_loop.stop()
		for p in _players:
			p.stop()


# ---------------------------------------------------------------- synthesis

func _build() -> void:
	_streams["click"] = _wav(_tone(620, 520, 0.05, 0.35))
	_streams["tick"] = _wav(_tone(1250, 1250, 0.035, 0.3))
	_streams["thump"] = _wav(_mix(_tone(120, 48, 0.13, 0.9), _noise(0.05, 0.18, 0.12), 0.0))
	_streams["thud"] = _wav(_mix(_tone(90, 38, 0.28, 0.95), _noise(0.12, 0.3, 0.08), 0.0))
	_streams["good"] = _wav(_mix(_tone(660, 660, 0.12, 0.33), _tone(990, 990, 0.3, 0.33), 0.09))
	_streams["bad"] = _wav(_mix(_tone(220, 180, 0.2, 0.3, 2), _tone(165, 130, 0.3, 0.3, 2), 0.12))
	_streams["beep"] = _wav(_tone(880, 880, 0.22, 0.3, 1))
	_streams["shock"] = _wav(_mix(_noise(0.3, 0.7, 0.5), _tone(70, 40, 0.35, 0.8), 0.0))
	_streams["crack"] = _wav(_noise(0.05, 0.75, 0.85))
	_streams["slap"] = _wav(_mix(_noise(0.09, 0.8, 0.3), _tone(150, 70, 0.1, 0.5), 0.0))
	_streams["soft"] = _wav(_noise(0.07, 0.25, 0.12))
	_streams["pop"] = _wav(_tone(280, 980, 0.1, 0.5))
	_streams["dial"] = _wav(_mix(_tone(770, 770, 0.1, 0.2), _tone(1336, 1336, 0.1, 0.2), 0.0))
	_streams["star"] = _wav(_mix(_tone(1046, 1046, 0.5, 0.3), _tone(1568, 1568, 0.5, 0.18), 0.0))
	var siren := PackedFloat32Array()
	for i in 4:
		siren = _mix(siren, _tone(660.0 if i % 2 == 0 else 880.0, 660.0 if i % 2 == 0 else 880.0, 0.36, 0.16, 2, 0.03), i * 0.33)
	_streams["siren"] = _wav(siren)
	var win := PackedFloat32Array()
	var notes := [523.25, 659.25, 783.99, 1046.5]
	for i in notes.size():
		win = _mix(win, _tone(notes[i], notes[i], 0.5, 0.26), i * 0.11)
	_streams["win"] = _wav(win)
	var water := _wav(_noise(1.2, 0.22, 0.5, false))
	water.loop_mode = AudioStreamWAV.LOOP_FORWARD
	water.loop_begin = 0
	water.loop_end = int(1.2 * RATE) - 1
	_streams["water"] = water


func _tone(f0: float, f1: float, dur: float, vol: float, shape: int = 0, attack: float = 0.004) -> PackedFloat32Array:
	var n := int(dur * RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var ph := 0.0
	for i in n:
		var k := float(i) / n
		ph += lerpf(f0, f1, k) / RATE
		var s := sin(ph * TAU)
		if shape == 1:
			s = signf(s) * 0.4 + s * 0.6
		elif shape == 2:
			s = 2.0 * absf(2.0 * (ph - floorf(ph + 0.5))) - 1.0
		var env := minf(float(i) / (attack * RATE), 1.0) * pow(1.0 - k, 2.0)
		out[i] = s * env * vol
	return out


func _noise(dur: float, vol: float, lp: float, fade: bool = true) -> PackedFloat32Array:
	var n := int(dur * RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var y := 0.0
	for i in n:
		y = lerpf(y, randf_range(-1.0, 1.0), lp)
		var env := pow(1.0 - float(i) / n, 2.0) if fade else 1.0
		out[i] = y * env * vol
	return out


func _mix(a: PackedFloat32Array, b: PackedFloat32Array, at: float) -> PackedFloat32Array:
	var off := int(at * RATE)
	var out := a.duplicate()
	if out.size() < off + b.size():
		var old := out.size()
		out.resize(off + b.size())
		for i in range(old, out.size()):
			out[i] = 0.0
	for i in b.size():
		out[off + i] += b[i]
	return out


func _wav(samples: PackedFloat32Array) -> AudioStreamWAV:
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	for i in samples.size():
		data.encode_s16(i * 2, int(clampf(samples[i], -1.0, 1.0) * 30000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.stereo = false
	w.data = data
	return w
