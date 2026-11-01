extends PanelContainer
## Door 2 — "The Aid Office". A budget-allocation game about evidence,
## cost-effectiveness, diminishing returns, and the value of information.

const MAX_LEVEL := 5

## Each option: name, cost per unit, claimed "people helped" per unit,
## evidence (1=weak, 2=moderate, 3=strong), true people helped per unit,
## cap (units beyond the cap work at 15% effectiveness; 0 = no cap).
var levels: Array = [
	{
		"title": "Level 1 — A village in malaria country",
		"budget": 500,
		"lesson_title": "Cost-effectiveness is wildly unequal",
		"lesson": "Three options, three price tags, one real effect. Cheap + boring + heavily tested beat shiny + expensive. In the real world, top global-health interventions deliver on the order of 100x more good per dollar than average ones — that gap is the single biggest lever a helper has.",
		"options": [
			{"name": "Insecticide-treated bed nets", "cost": 5, "claimed": 1.0, "evidence": 3, "true": 1.0, "cap": 0,
				"note": "Randomized trials in several countries. A net protects a child for about a year."},
			{"name": "Gala fundraising dinner", "cost": 100, "claimed": 0.6, "evidence": 2, "true": 0.05, "cap": 0,
				"note": "Feels wonderful, raises 'awareness'. Very little reaches anyone in need."},
			{"name": 'Anti-mosquito "wellness" bracelets', "cost": 3, "claimed": 1.4, "evidence": 1, "true": 0.1, "cap": 0,
				"note": "Viral on social media. One small unreplicated study, run by the seller."},
		],
	},
	{
		"title": "Level 2 — Child health, district-wide",
		"budget": 2000,
		"lesson_title": "Test your fancy ideas against a benchmark",
		"lesson": "Direct cash transfers to very poor families are the benchmark every intervention should be compared against — they're simple, rigorously studied, and they let people solve their own problems. Anything that beats cash deserves attention. Anything that can't say whether it beats cash is guessing with money.",
		"options": [
			{"name": "Measles vaccination drive", "cost": 2, "claimed": 1.5, "evidence": 3, "true": 1.5, "cap": 700,
				"note": "One of the most cost-effective health interventions known."},
			{"name": "Direct cash transfers to poorest families", "cost": 10, "claimed": 1.0, "evidence": 3, "true": 1.0, "cap": 0,
				"note": "Multiple large randomized trials. The benchmark."},
			{"name": "Vitamin A supplementation", "cost": 1, "claimed": 1.0, "evidence": 2, "true": 0.7, "cap": 0,
				"note": "Older studies suggest benefit; newer ones are less sure. Cheap enough to hedge."},
			{"name": "Motivational murals about health", "cost": 50, "claimed": 0.9, "evidence": 1, "true": 0.05, "cap": 0,
				"note": "Everyone loves the unveiling ceremony. Nobody measured behaviour change."},
		],
	},
	{
		"title": "Level 3 — Clean water for a valley",
		"budget": 5000,
		"lesson_title": "Diminishing returns: spend at the margin",
		"lesson": "The first chlorination points serve the dirtiest water and the most people; each additional one reaches fewer. Smart giving spreads money at the MARGIN — where each next dollar still buys a lot — instead of dumping everything into one visible bucket. That's why funders split across causes as budgets grow.",
		"options": [
			{"name": "Community chlorination points", "cost": 25, "claimed": 5.0, "evidence": 3, "true": 5.0, "cap": 120,
				"note": "Cheap, boring, hugely effective. The valley only has so much untreated water to cover."},
			{"name": "Hygiene & handwashing training", "cost": 100, "claimed": 9.0, "evidence": 2, "true": 7.0, "cap": 20,
				"note": "Strong studies on handwashing; only so many classrooms and trainers exist."},
			{"name": "Trucked bottled water", "cost": 2, "claimed": 1.0, "evidence": 2, "true": 0.4, "cap": 0,
				"note": "Trucks, fuel, branding — the water is clean but the money leaks out of the program."},
			{"name": "Deep-drilled 'forever wells'", "cost": 500, "claimed": 40.0, "evidence": 1, "true": 6.0, "cap": 0,
				"note": "Big concrete objects photograph beautifully. Many go unmaintained within a few years."},
		],
	},
	{
		"title": "Level 4 — A fog of claims",
		"budget": 3000,
		"lesson_title": "Sometimes the best purchase is information",
		"lesson": "A pilot study costs money and helps no one directly — but it collapses your uncertainty before you commit thousands. Funders call this 'the value of information'. Cheap experiments before big spending is why medicine stopped being guesswork.",
		"options": [
			{"name": "Pilot study: test everything first", "cost": 200, "claimed": 0.0, "evidence": 3, "true": 0.0, "cap": 0,
				"note": "Helps no one directly — but if you buy at least one, the outcome reveal becomes accurate for ALL your spending this level.", "research": true},
			{"name": "Oral rehydration + zinc kits", "cost": 4, "claimed": 1.2, "evidence": 3, "true": 1.2, "cap": 0,
				"note": "Treats the top child killer. Ironclad evidence."},
			{"name": "New 'micro-credit for health' scheme", "cost": 20, "claimed": 3.5, "evidence": 1, "true": 1.1, "cap": 0,
				"note": "The founder's TED talk has 4 million views. The data is one pilot in a friendly district."},
			{"name": "Surgical outreach missions", "cost": 120, "claimed": 8.0, "evidence": 2, "true": 5.0, "cap": 15,
				"note": "Genuinely saves lives — but surgical capacity is limited (cap 15) and follow-up is patchy."},
		],
	},
	{
		"title": "Level 5 — The big portfolio",
		"budget": 10000,
		"lesson_title": "Spread, but tilt: expected value and headroom",
		"lesson": "At scale, you balance certain near-term gains (vaccines, water) against long-shot huge payoffs (research, pandemic preparedness) — using expected value, not vibes. The worst move is the comfortable middle: big spends on middling, unmeasured things. This is how the world's biggest funders (and your own giving) should think.",
		"options": [
			{"name": "Vaccines & bed nets (proven core)", "cost": 5, "claimed": 1.2, "evidence": 3, "true": 1.2, "cap": 1200,
				"note": "The reliable backbone. Coverage saturates eventually."},
			{"name": "Research into a cheaper vaccine", "cost": 500, "claimed": 30.0, "evidence": 2, "true": 30.0, "cap": 4,
				"note": "Risky, slow — if it works, it compounds for decades."},
			{"name": "Pandemic early-warning network", "cost": 250, "claimed": 25.0, "evidence": 2, "true": 25.0, "cap": 6,
				"note": "Rarely pays off, catastrophically valuable when it does. Cap: only so many labs to wire."},
			{"name": "Flagship 'World Day' campaign", "cost": 1000, "claimed": 12.0, "evidence": 1, "true": 0.5, "cap": 0,
				"note": "Conferences, hashtags, a logo. The least examined thing in all of aid."},
		],
	},
]

var level_index := 0
var total_helped := 0.0
var total_spent := 0
var spinboxes := {}
var deployed := false
var warned_leftover := false

var title_label: Label
var budget_label: Label
var lesson_label: Label
var rows_box: VBoxContainer
var action_box: VBoxContainer
var status_label: Label

func _ready() -> void:
	_build_level()

func _build_level() -> void:
	deployed = false
	warned_leftover = false
	spinboxes = {}
	for child in get_children():
		child.queue_free()
	var data: Dictionary = levels[level_index]

	add_theme_stylebox_override("panel", _panel_style())
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	add_child(v)

	title_label = Label.new()
	title_label.text = "%s   —   Budget: $%d" % [data["title"], data["budget"]]
	title_label.add_theme_font_size_override("font_size", 22)
	title_label.add_theme_color_override("font_color", Color("8ab6f0"))
	v.add_child(title_label)

	budget_label = Label.new()
	budget_label.add_theme_font_size_override("font_size", 18)
	budget_label.add_theme_color_override("font_color", Color("f0c674"))
	v.add_child(budget_label)

	var hint := Label.new()
	hint.text = "For each option, choose how many units to buy. 'Claimed' = what the seller says it achieves. Stars = strength of independent evidence."
	hint.add_theme_font_size_override("font_size", 14)
	hint.add_theme_color_override("font_color", Color("9aa7b1"))
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(hint)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(scroll)
	rows_box = VBoxContainer.new()
	rows_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows_box.add_theme_constant_override("separation", 8)
	scroll.add_child(rows_box)

	for opt in data["options"]:
		rows_box.add_child(_make_row(opt, data))

	action_box = VBoxContainer.new()
	action_box.add_theme_constant_override("separation", 8)
	v.add_child(action_box)

	status_label = Label.new()
	status_label.add_theme_font_size_override("font_size", 16)
	status_label.add_theme_color_override("font_color", Color("dce3e8"))
	status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	action_box.add_child(status_label)

	var deploy := Button.new()
	deploy.text = "Deploy the budget"
	deploy.custom_minimum_size = Vector2(200, 44)
	deploy.add_theme_font_size_override("font_size", 17)
	deploy.pressed.connect(_on_deploy)
	action_box.add_child(deploy)

	status_label.text = "Allocate your budget, then deploy."
	_update_budget()

func _make_row(opt: Dictionary, data: Dictionary) -> Control:
	var card := PanelContainer.new()
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card.add_theme_stylebox_override("panel", _card_style(opt))
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 12)
	card.add_child(h)

	var info := VBoxContainer.new()
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.size_flags_vertical = Control.SIZE_EXPAND_FILL
	info.add_theme_constant_override("separation", 2)
	h.add_child(info)

	var name_l := Label.new()
	name_l.text = opt["name"]
	name_l.add_theme_font_size_override("font_size", 18)
	name_l.add_theme_color_override("font_color", Color("dce3e8"))
	info.add_child(name_l)

	var note_l := Label.new()
	note_l.text = opt["note"]
	note_l.add_theme_font_size_override("font_size", 13)
	note_l.add_theme_color_override("font_color", Color("9aa7b1"))
	note_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_child(note_l)

	var meta_l := Label.new()
	var stars := ""
	match opt["evidence"]:
		3: stars = "★★★ strong evidence"
		2: stars = "★★ moderate evidence"
		1: stars = "★ weak evidence"
	var cap_note := ""
	if opt.get("cap", 0) > 0:
		cap_note = "  ·  saturates after %d units" % opt["cap"]
	meta_l.text = "$%d per unit  ·  claims %s people helped each  ·  %s%s" % [opt["cost"], _fmt(opt["claimed"]), stars, cap_note]
	meta_l.add_theme_font_size_override("font_size", 14)
	meta_l.add_theme_color_override("font_color", Color("f0c674"))
	info.add_child(meta_l)

	var sb := SpinBox.new()
	sb.min_value = 0
	sb.step = 1
	sb.allow_greater = false
	var max_units: int = int(data["budget"] / opt["cost"])
	sb.max_value = max_units
	sb.value = 0
	sb.custom_minimum_size = Vector2(110, 40)
	sb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sb.value_changed.connect(func(_val: float) -> void: _update_budget())
	h.add_child(sb)
	spinboxes[opt["name"]] = sb
	return card

func _spent() -> int:
	var data: Dictionary = levels[level_index]
	var spent := 0
	for opt in data["options"]:
		var sb: SpinBox = spinboxes[opt["name"]]
		spent += int(sb.value) * opt["cost"]
	return spent

func _update_budget() -> void:
	if deployed:
		return
	var data: Dictionary = levels[level_index]
	var left: int = data["budget"] - _spent()
	budget_label.text = "Unspent: $%d of $%d" % [left, data["budget"]]

func _on_deploy() -> void:
	if deployed:
		return
	var data: Dictionary = levels[level_index]
	var left: int = data["budget"] - _spent()
	if left < 0:
		status_label.text = "Over budget by $%d — trim something first." % (-left)
		return
	if left > 0 and not warned_leftover:
		warned_leftover = true
		status_label.text = "You'd leave $%d unspent — that helps no one. Adjust, or press Deploy again to accept the loss." % left
		return
	deployed = true

	# noise range depends on evidence quality and whether research was bought
	var researched := false
	for opt in data["options"]:
		if opt.get("research", false) and int(spinboxes[opt["name"]].value) >= 1:
			researched = true

	var rng := RandomNumberGenerator.new()
	rng.randomize()

	var results := ""
	var helped_total := 0.0
	var player_lines: Array = []
	for opt in data["options"]:
		var sb: SpinBox = spinboxes[opt["name"]]
		var qty: int = int(sb.value)
		var eff: float = qty
		var cap: int = opt.get("cap", 0)
		if cap > 0 and qty > cap:
			eff = cap + (qty - cap) * 0.15
		var noise := 1.0
		if not researched:
			match opt["evidence"]:
				3: noise = rng.randf_range(0.95, 1.05)
				2: noise = rng.randf_range(0.7, 1.2)
				1: noise = rng.randf_range(0.05, 1.3)
		var actual: float = eff * opt["true"] * noise
		helped_total += actual
		player_lines.push_back({
			"name": opt["name"], "qty": qty, "actual": actual, "cost": opt["cost"],
		})
	total_helped += helped_total
	total_spent += data["budget"] - left

	# oracle: greedy by true value/cost with caps, for "best possible"
	var best := 0.0
	var budget_left: float = data["budget"]
	var order: Array = data["options"].duplicate()
	order.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return (a["true"] / a["cost"]) > (b["true"] / b["cost"]))
	for opt in order:
		if budget_left < opt["cost"]:
			break
		var cap: int = opt.get("cap", 0)
		var units: int = 0
		if cap > 0:
			units = mini(int(budget_left / opt["cost"]), cap)
			budget_left -= units * opt["cost"]
			best += units * opt["true"]
			# leftovers beyond cap at 15% may still beat other options
			var next_best_ratio: float = 0.0
			for other in order:
				if other != opt:
					next_best_ratio = max(next_best_ratio, other["true"] / other["cost"])
			if opt["true"] * 0.15 / opt["cost"] > next_best_ratio and budget_left >= opt["cost"]:
				var extra: int = int(budget_left / opt["cost"])
				best += extra * opt["true"] * 0.15
				budget_left -= extra * opt["cost"]
		else:
			units = int(budget_left / opt["cost"])
			best += units * opt["true"]
			budget_left -= units * opt["cost"]

	results = "OUTCOMES (revealed):\n"
	for pl in player_lines:
		var pct: int = pl["qty"]
		if pct == 0:
			results += "• %s — not funded.\n" % pl["name"]
		else:
			results += "• %s — %d units for $%d → actually helped %s people.\n" % [pl["name"], pct, pct * pl["cost"], _fmt(pl["actual"])]

	results += "\nTotal people helped this level: [color=#7fd4a8]%s[/color]" % _fmt(helped_total)
	results += "\nA perfectly-informed funder could have reached: %s." % _fmt(best)
	if researched:
		results += "\n[color=#9aa7b1](Your pilot study worked — outcomes matched claims almost exactly.)[/color]"

	status_label.text = ""
	var rich := RichTextLabel.new()
	rich.bbcode_enabled = true
	rich.fit_content = true
	rich.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rich.add_theme_font_size_override("normal_font_size", 15)
	rich.append_text(results)
	action_box.add_child(rich)

	var lesson_card := PanelContainer.new()
	lesson_card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lesson_card.add_theme_stylebox_override("panel", _panel_style())
	var lv := VBoxContainer.new()
	lesson_card.add_child(lv)
	var lt := Label.new()
	lt.text = data["lesson_title"]
	lt.add_theme_font_size_override("font_size", 19)
	lt.add_theme_color_override("font_color", Color("f0c674"))
	lv.add_child(lt)
	var lb := Label.new()
	lb.text = data["lesson"]
	lb.add_theme_font_size_override("font_size", 15)
	lb.add_theme_color_override("font_color", Color("dce3e8"))
	lb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lv.add_child(lb)
	action_box.add_child(lesson_card)

	var next := Button.new()
	if level_index + 1 < MAX_LEVEL:
		next.text = "Next level  (%d / %d)" % [level_index + 2, MAX_LEVEL]
	else:
		next.text = "Final report card"
	next.custom_minimum_size = Vector2(220, 44)
	next.add_theme_font_size_override("font_size", 17)
	next.pressed.connect(_on_next)
	action_box.add_child(next)

func _on_next() -> void:
	if level_index + 1 < MAX_LEVEL:
		level_index += 1
		_build_level()
	else:
		_show_report()

func _show_report() -> void:
	for child in get_children():
		child.queue_free()
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	add_child(v)

	var title := Label.new()
	title.text = "AID OFFICE — FINAL REPORT"
	title.add_theme_font_size_override("font_size", 24)
	title.add_theme_color_override("font_color", Color("8ab6f0"))
	v.add_child(title)

	var rich := RichTextLabel.new()
	rich.bbcode_enabled = true
	rich.fit_content = true
	rich.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rich.add_theme_font_size_override("normal_font_size", 16)
	rich.append_text(
		"You spent $%d across %d funding decisions and helped [color=#7fd4a8]%s people[/color].\n\n" % [total_spent, MAX_LEVEL, _fmt(total_helped)] +
		"The five rules you just practised:\n\n" +
		"1. [b]Cost-effectiveness first.[/b] Before asking 'is this good?', ask 'how much good per dollar, compared to the alternatives?'\n" +
		"2. [b]Evidence beats vibes.[/b] Stars over slogans. One well-run trial outranks a million impressions.\n" +
		"3. [b]Spend at the margin.[/b] The 500th net helps less than the 1st; the 1st research dollar helps more than the 500th.\n" +
		"4. [b]Buy information.[/b] A small pilot that changes a big decision is the highest-return purchase in the room.\n" +
		"5. [b]Benchmark against cash.[/b] If a program can't say why it beats handing people money, that's an answer.\n\n" +
		"People who internalize these rules — whether they give $10 or $10 million — move real lives. The same thinking scaled up is how smallpox was ended and how river blindness is being ended.")
	v.add_child(rich)

	var again := Button.new()
	again.text = "Run the Aid Office again"
	again.custom_minimum_size = Vector2(220, 44)
	again.add_theme_font_size_override("font_size", 17)
	again.pressed.connect(func() -> void:
		level_index = 0
		total_helped = 0.0
		total_spent = 0
		_build_level())
	v.add_child(again)

# ---------------------------------------------------------------- helpers

func _fmt(x: float) -> String:
	if x >= 100.0:
		return "%d" % int(round(x))
	return "%.1f" % x

func _card_style(opt: Dictionary) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("26313d")
	sb.set_corner_radius_all(8)
	match opt["evidence"]:
		3: sb.border_color = Color("7fd4a8")
		2: sb.border_color = Color("f0c674")
		1: sb.border_color = Color("e06c75")
	sb.border_width_left = 4
	return sb

func _panel_style() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("1d252e")
	sb.set_corner_radius_all(10)
	return sb
