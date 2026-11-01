// Content for the seven core lessons. {{N}} is replaced with the local emergency number.
export const LESSONS = [
  {
    id: "cpr",
    n: "Skill 1",
    title: "Hands-only CPR",
    short: "Someone collapses and isn't breathing. Push hard and fast in the centre of the chest.",
    minutes: 3,
    why: "Every year millions of people have a cardiac arrest outside hospital. Most die. When a bystander starts CPR right away, the chance of survival doubles or triples. Every minute without it, survival falls by about 10%. You do not need to breathe into their mouth: hands-only CPR works for adults and teens.",
    recognize: [
      ["Not responding", "Tap their shoulders firmly and shout “Are you OK?” — nothing."],
      ["Not breathing, or only gasping", "Look at the chest for up to 10 seconds. Occasional gasps or snorts are NOT breathing — treat as cardiac arrest."],
    ],
    steps: [
      ["Check it's safe, then check them", "Tap and shout. Look for normal breathing for no more than 10 seconds."],
      ["Call {{N}} — put the phone on speaker", "If others are there, point at one person: “You — call {{N}}. You — find a defibrillator (AED).” The dispatcher will coach you."],
      ["Kneel beside them, hands in the centre of the chest", "Heel of one hand on the lower half of the breastbone, other hand on top, fingers interlocked. Arms straight, shoulders directly over your hands."],
      ["Push hard and fast", "At least 5 cm (2 in) deep, 100–120 pushes a minute — the tempo of “Stayin’ Alive”. Let the chest come fully back up between pushes. Don't stop. Broken ribs are OK; a stopped heart is not."],
      ["Use the AED the moment it arrives", "Turn it on and do what it says. It will not shock anyone who doesn't need it. Keep pushing while the pads go on."],
      ["Keep going until help takes over", "Swap with someone every 2 minutes if you can — you'll tire faster than you think. Stop only if they start breathing normally or professionals take over."],
    ],
    dont: [
      "Don't wait to see if they “come round”. Minutes matter.",
      "Don't check for a pulse — it wastes time and even professionals get it wrong. No normal breathing = start.",
      "Don't be afraid of hurting them or of being sued. Good-Samaritan laws protect helpers in most countries, and a person with no heartbeat can't get worse.",
      "Don't do CPR on someone who is breathing normally — put them in the recovery position instead (Skill 6).",
    ],
    drill: "metronome",
    check: [
      {
        q: "A man collapses in a café. He doesn't respond and is making occasional snoring gasps. What do you do?",
        a: ["Put him in the recovery position — he's breathing", "Call {{N}} and start chest compressions now", "Check his pulse for a full minute to be sure"],
        correct: 1,
        why: "Gasping is not breathing. It's a sign of cardiac arrest. Call and push.",
      },
      {
        q: "How fast should you push?",
        a: ["About once a second (60/min)", "100–120 per minute", "As fast as you possibly can"],
        correct: 1,
        why: "100–120 per minute. Faster than that and the heart doesn't refill; slower and not enough blood moves.",
      },
    ],
  },
  {
    id: "choking",
    n: "Skill 2",
    title: "Choking",
    short: "They can't cough, speak or breathe. Five back blows, five abdominal thrusts, repeat.",
    minutes: 2,
    why: "Choking kills thousands of people a year, often at the dinner table with family watching. Someone whose airway is fully blocked has only a few minutes. The fix is simple and physical, and you can do it.",
    recognize: [
      ["Hands at the throat, panic, can't speak", "Ask “Are you choking?” If they can't answer, nod or point — act."],
      ["Weak or silent cough, high-pitched noises, going blue", "A strong cough means air is moving — encourage it. Silence means it isn't."],
    ],
    steps: [
      ["Ask “Are you choking? Can you speak?”", "If they CAN cough forcefully: let them. Stay with them. Don't slap their back yet — a strong cough is better than anything you can do."],
      ["If they can't breathe, cough or speak: shout for help and give 5 back blows", "Stand to the side and slightly behind. Support their chest with one hand and lean them forward. Hit firmly between the shoulder blades with the heel of your hand, up to 5 times. Check after each."],
      ["Then 5 abdominal thrusts", "Stand behind, wrap your arms around their waist. Make a fist, thumb side in, just above the navel and well below the ribs. Grab it with your other hand and pull sharply inwards and upwards. Up to 5 times."],
      ["Keep alternating 5 and 5", "Back blows, thrusts, back blows, thrusts — until the object comes out or they go limp. If you haven't yet, get someone to call {{N}}."],
      ["If they become unresponsive: lower them to the floor, call {{N}}, start CPR", "Chest compressions can push the object out. Look in the mouth before any breaths and remove anything you can see. Don't sweep blindly with a finger."],
    ],
    dont: [
      "Don't do abdominal thrusts on someone pregnant or very large — use chest thrusts instead (same place as CPR, sharp pulls backwards).",
      "Don't give abdominal thrusts to a baby under 1. Lay them face-down along your forearm, head low, 5 back blows, then turn over for 5 chest thrusts with two fingers.",
      "Don't give them a drink or tell them to swallow.",
      "After successful abdominal thrusts, they should still see a doctor — the thrusts can injure internal organs.",
    ],
    drill: "flow",
    flow: {
      start: "c1",
      nodes: {
        c1: {
          q: "At dinner, your uncle suddenly stops talking, grips his throat and looks terrified. He's coughing hard and loudly. What first?",
          choices: [
            { t: "Start back blows immediately", next: "c1wrong" },
            { t: "Ask “Are you choking?” and encourage him to keep coughing", next: "c2", ok: true },
            { t: "Give him water to wash it down", next: "c1wrong" },
          ],
        },
        c1wrong: {
          explain: "A loud, forceful cough means air is still moving. Coughing is more effective than anything you can do. Stay close, encourage it, and be ready. Back blows now could lodge the object deeper; drinks can block it fully.",
          next: "c2", bad: true,
        },
        c2: {
          q: "His cough fades to silence. His lips are turning blue. He can't speak. Now?",
          choices: [
            { t: "Wait another 30 seconds to see if it clears", next: "c2wrong" },
            { t: "Lean him forward and give up to 5 firm back blows between the shoulder blades", next: "c3", ok: true },
            { t: "Reach into his mouth with your finger", next: "c2wrong" },
          ],
        },
        c2wrong: {
          explain: "Silence means the airway is fully blocked. He has minutes. Blind finger sweeps can push the object deeper. Start back blows right away and get someone to call {{N}}.",
          next: "c3", bad: true,
        },
        c3: {
          q: "Five back blows, still nothing. Next?",
          choices: [
            { t: "5 abdominal thrusts: fist above the navel, pull in and up sharply", next: "c4", ok: true },
            { t: "Lay him down and start CPR", next: "c3wrong" },
            { t: "Slap him on the back 20 more times", next: "c3wrong" },
          ],
        },
        c3wrong: {
          explain: "While he's still conscious, alternate 5 back blows and 5 abdominal thrusts. CPR comes only if he goes limp.",
          next: "c4", bad: true,
        },
        c4: {
          q: "On the third thrust, a piece of steak flies out. He gasps and breathes. What now?",
          choices: [
            { t: "Everyone relax — crisis over", next: "c4wrong" },
            { t: "Keep him calm, and have him checked by a doctor today — thrusts can cause internal injury", next: "end", ok: true },
          ],
        },
        c4wrong: {
          explain: "Abdominal thrusts can injure the abdomen. Anyone who's had them should be checked by a doctor.",
          next: "end", bad: true,
        },
        end: { done: "You just talked yourself through a choking rescue. Remember: cough → back blows → thrusts → repeat → CPR if they go limp." },
      },
    },
    check: [
      {
        q: "A pregnant colleague is choking and can't breathe. Where do your thrusts go?",
        a: ["Above the navel, like normal", "On the breastbone (chest thrusts)", "Don't thrust; only back blows"],
        correct: 1,
        why: "For pregnant or very large people, use chest thrusts: fist in the centre of the breastbone, pull sharply backwards.",
      },
    ],
  },
  {
    id: "stroke",
    n: "Skill 3",
    title: "Stroke: spot it FAST",
    short: "Face, Arms, Speech, Time. Every minute of delay kills brain cells.",
    minutes: 2,
    why: "Stroke is a leading cause of death and the leading cause of adult disability worldwide. Treatments that dissolve or remove the clot work only within hours, and work best in the first hour. Most delay is in recognising it and calling. Learn four letters.",
    recognize: [
      ["F — Face", "Ask them to smile. Does one side droop?"],
      ["A — Arms", "Ask them to raise both arms. Does one drift down or not lift?"],
      ["S — Speech", "Ask them to repeat a simple sentence. Slurred, strange, or can't?"],
      ["T — Time", "Any ONE of these: call {{N}} now. Note the time it started."],
    ],
    steps: [
      ["Run the three checks: smile, arms, sentence", "Takes 20 seconds. One failure is enough."],
      ["Call {{N}} and say the word “stroke”", "Don't drive them yourself unless there's truly no ambulance. Ambulance crews pre-alert the stroke team so treatment starts the moment they arrive."],
      ["Note the time the symptoms started", "Or the last time they were seen well. The hospital's treatment decisions depend on this number."],
      ["Keep them still, calm and lying with head slightly raised", "Nothing to eat or drink — swallowing may be unsafe. No aspirin: some strokes are bleeds, and aspirin makes those worse."],
      ["Stay, and watch their breathing", "If they become unresponsive and stop breathing normally, start CPR (Skill 1)."],
    ],
    dont: [
      "Don't wait to see if it “passes”. Even if symptoms fade (a mini-stroke/TIA), it's a warning of a major stroke — still call.",
      "Don't give aspirin, food or drink.",
      "Don't let them “sleep it off”. Sudden confusion, a thunderclap headache, sudden vision loss, or sudden loss of balance can all be stroke too (some teach BE FAST: Balance, Eyes).",
    ],
    drill: "flow",
    flow: {
      start: "s1",
      nodes: {
        s1: {
          q: "Your mother says she feels odd on a video call. Her words sound a little mushy. She says she's just tired. What do you do?",
          choices: [
            { t: "Tell her to lie down and call you in the morning", next: "s1wrong" },
            { t: "Ask her to smile, raise both arms, and repeat “The sky is blue in Cincinnati”", next: "s2", ok: true },
            { t: "Tell her to take an aspirin just in case", next: "s1wrong" },
          ],
        },
        s1wrong: {
          explain: "Mushy speech is a stroke sign until proven otherwise. Run the FAST check right there on the call. And no aspirin — a bleeding stroke gets worse with it.",
          next: "s2", bad: true,
        },
        s2: {
          q: "Her smile is lopsided. Her left arm drifts down. She insists she's fine and doesn't want a fuss. Now?",
          choices: [
            { t: "Respect her wishes and check again in an hour", next: "s2wrong" },
            { t: "Call {{N}} for her right now, say “stroke”, and note the time — about 7:40 pm", next: "s3", ok: true },
            { t: "Ask a neighbour to drive her to hospital when convenient", next: "s2wrong" },
          ],
        },
        s2wrong: {
          explain: "Two FAST signs. Stroke patients often don't realise anything is wrong — the stroke affects judgement too. Call for them. Time is brain: about 2 million neurons die every minute.",
          next: "s3", bad: true,
        },
        s3: {
          q: "The ambulance is 10 minutes out. She says she's thirsty. What do you tell her?",
          choices: [
            { t: "A small sip of water is fine", next: "s3wrong" },
            { t: "Nothing to eat or drink — swallowing may be unsafe. Sit comfortably, stay still, unlock the front door", next: "end", ok: true },
          ],
        },
        s3wrong: {
          explain: "Stroke can paralyse the swallowing muscles. Water can go into the lungs. Nothing by mouth until she's assessed.",
          next: "end", bad: true,
        },
        end: { done: "That's the whole skill. Face, Arms, Speech — any one of them — Time to call. Your mother would reach hospital inside the treatment window." },
      },
    },
    check: [
      {
        q: "Someone's stroke symptoms disappear after 15 minutes. What should they do?",
        a: ["Relief — nothing needed", "Call {{N}} anyway — a TIA is a warning of a major stroke", "Book a GP appointment for next week"],
        correct: 1,
        why: "A transient ischaemic attack (TIA) often precedes a full stroke within days. It's an emergency.",
      },
    ],
  },
  {
    id: "bleeding",
    n: "Skill 4",
    title: "Severe bleeding",
    short: "Press hard, don't let go. A person can bleed to death in five minutes.",
    minutes: 2,
    why: "Uncontrolled bleeding is the number one cause of preventable death after injury — car crashes, falls, tools, violence. The person next to the injured one is the only one who can act in time. The skill is pressure.",
    recognize: [
      ["Blood that is spurting, pooling, or soaking through clothes", "Or a wound you can't control with light pressure."],
      ["Pale, cold, confused, drowsy", "Signs they've lost a lot of blood. Lay them down and hurry."],
    ],
    steps: [
      ["Make sure you're safe, and call {{N}}", "Gloves if you have them, a plastic bag if you don't. Call, or get someone to."],
      ["Find where the blood is coming from", "Open or cut away clothing. Look for the source — there may be more than one."],
      ["Press hard, directly on the wound", "Use a clean cloth, gauze, or just your hands. Both hands, arms straight, lean your body weight in. It should hurt them. Don't ease off to look."],
      ["If it soaks through, add more on top", "Don't remove the first layer — it disturbs the clot. Pile on and press harder."],
      ["Arm or leg still bleeding badly? Tourniquet", "If you have one, put it 5–8 cm (2–3 in) above the wound (not on a joint) and tighten until the bleeding stops. It will hurt badly — that's expected. Write down the time. Never loosen it."],
      ["No tourniquet? Pack the wound", "Stuff clean cloth or gauze deep into the wound, right onto the bleeding vessel, then press hard on top. Keep pressing until help takes over."],
      ["Keep them warm and lying down", "Cover with a coat or blanket. Talk to them. If they stop responding and breathing normally, start CPR."],
    ],
    dont: [
      "Don't lift the cloth to check — it restarts the bleeding.",
      "Don't use a tourniquet on the neck, chest or abdomen — pack and press instead.",
      "Don't waste time cleaning the wound or looking for a bandage first. Pressure first, within seconds.",
      "Don't remove an object that's stuck in the wound — press around it.",
    ],
    drill: "pressure",
    check: [
      {
        q: "Your friend cut their thigh with a chainsaw. Blood is spurting. You're pressing hard with a T-shirt but it keeps soaking through. What next?",
        a: ["Take off the T-shirt and find a cleaner one", "Put more cloth on top, press harder, and apply a tourniquet above the wound if you have one", "Raise the leg and hope"],
        correct: 1,
        why: "Never remove soaked dressings. Add more, press harder, and a limb wound that won't stop is exactly what a tourniquet is for.",
      },
      {
        q: "The tourniquet is on and bleeding has stopped. Your friend begs you to loosen it because it hurts. You should:",
        a: ["Loosen it a little for comfort", "Leave it — a working tourniquet hurts. Note the time it went on", "Take it off every 10 minutes to let blood through"],
        correct: 1,
        why: "Loosening lets them bleed again. Pain means it's tight enough. Only medical staff remove it.",
      },
    ],
  },
  {
    id: "heart",
    n: "Skill 5",
    title: "Heart attack",
    short: "Chest pressure, breathless, sweating. Call before it becomes a cardiac arrest.",
    minutes: 2,
    why: "A heart attack is a blocked artery; the heart is still beating, but muscle is dying. Half of the people who die do so before reaching hospital, often because they waited, embarrassed, to see if it was indigestion. Called in time, it's very survivable.",
    recognize: [
      ["Pressure, squeezing, fullness or pain in the centre of the chest", "Lasting more than a few minutes, or going away and coming back. Often described as “an elephant on my chest”."],
      ["Pain spreading to arms, back, neck, jaw or stomach", "Women, older people and people with diabetes more often have these without classic chest pain."],
      ["Short of breath, cold sweat, nausea, light-headed", "Any of these with chest discomfort. Many people say they feel a sense of dread or “just not right”."],
    ],
    steps: [
      ["Call {{N}} — don't drive them yourself", "Paramedics can diagnose and start treatment in the ambulance, and they can restart the heart if it stops on the way. A car can't."],
      ["Sit them down and keep them still", "Knees bent, back supported, loosen tight clothing. Every bit of exertion makes the damage worse."],
      ["Aspirin, if they're not allergic and the dispatcher agrees", "One regular adult aspirin (300 mg, or 4 × 81 mg “baby” aspirin), chewed, not swallowed whole. It slows the clot. Skip it if they're allergic, bleeding, or you're unsure — the call matters far more than the pill."],
      ["Stay with them and keep talking", "Be calm. Reassure them. Note what time it started and any medicines they take."],
      ["If they collapse and stop breathing normally: CPR", "That's the heart attack becoming cardiac arrest. Start Skill 1 at once. Send someone for an AED."],
    ],
    dont: [
      "Don't let them “wait and see”, walk to the car, or climb stairs.",
      "Don't give food or drink other than the aspirin.",
      "Don't be talked out of calling because they're embarrassed. It is very common for people to minimise. Call anyway.",
    ],
    drill: "signs",
    signsDrill: {
      intro: "Which of these could be a heart attack? Tap every one you'd call for.",
      items: [
        { t: "Crushing pressure in the centre of the chest for 10 minutes", yes: true },
        { t: "A sharp, 1-second stab that disappears when you breathe differently", yes: false, why: "Brief, sharp, position-dependent pain is usually muscular or pleural. Still worth seeing a doctor, but not the pattern of a heart attack." },
        { t: "A 62-year-old woman: sudden breathlessness, nausea, jaw ache and cold sweat — no chest pain", yes: true, why: "Women often have heart attacks without the classic chest pain. This cluster is a heart attack until proven otherwise." },
        { t: "Chest discomfort that eases with rest but comes back on climbing stairs, a few times this week", yes: true, why: "This is unstable angina — the warning before a heart attack. Call." },
        { t: "A man with “bad indigestion” that isn't helped by antacids, sweating, and feels dread", yes: true, why: "Heart attacks are regularly mistaken for indigestion. Sweating and dread are the giveaway." },
        { t: "A tender spot on the ribs that hurts when pressed", yes: false, why: "Pain you can reproduce by pressing is usually from the chest wall, not the heart." },
      ],
    },
    check: [
      {
        q: "Your dad has chest pressure and is sweating. He says he'll drive himself to hospital. You:",
        a: ["Let him — it's quicker than waiting", "Call {{N}}, sit him down, and don't let him move", "Give him a glass of water and see if it passes"],
        correct: 1,
        why: "If his heart stops in the car, he dies and may kill others. Ambulance crews can treat on the way.",
      },
    ],
  },
  {
    id: "recovery",
    n: "Skill 6",
    title: "Recovery position",
    short: "Unconscious but breathing: roll them on their side so they can't choke.",
    minutes: 1,
    why: "Someone who is unconscious but breathing — from alcohol, drugs, a seizure, a faint, a head injury — can die by choking on their own tongue or vomit while lying on their back. Rolling them onto their side keeps the airway open. It takes 20 seconds.",
    recognize: [
      ["Unresponsive to tapping and shouting", "but"],
      ["Breathing normally", "Chest rising and falling regularly. If NOT breathing normally, it's CPR (Skill 1), not this."],
    ],
    steps: [
      ["Call {{N}} first, or have someone do it", "Unconscious is always an emergency. Check for and stop any severe bleeding."],
      ["Kneel at their side. Place the arm nearest you at a right angle", "Elbow bent, palm up, like they're waving."],
      ["Bring the far arm across their chest", "Hold the back of their hand against the cheek nearest you, and keep holding it."],
      ["With your other hand, pull up the far knee", "Foot flat on the floor."],
      ["Pull the knee towards you to roll them onto their side", "Keep their hand pressed to their cheek — it protects the head as they roll."],
      ["Tilt the head back to open the airway", "Mouth pointing slightly downwards so fluid drains. The bent knee stops them rolling onto their front."],
      ["Check breathing every minute until help arrives", "If breathing stops, roll them onto their back and start CPR. If more than 30 minutes, roll them onto the other side."],
    ],
    dont: [
      "Don't leave them on their back “to sleep it off”. That's how people die after parties.",
      "Don't put anything under their head.",
      "If you suspect a spinal injury (fall from height, crash), still turn them if you can't keep the airway open any other way — an open airway comes first.",
    ],
    drill: "order",
    orderDrill: {
      intro: "Put the steps in order. Tap them in sequence.",
      items: [
        "Near arm out at a right angle, palm up",
        "Far hand against their near cheek",
        "Pull the far knee up, foot flat",
        "Pull the knee to roll them towards you",
        "Tilt the head back, mouth downward",
      ],
    },
    check: [
      {
        q: "After a party, a friend is passed out on the sofa on his back, snoring loudly and breathing. What do you do?",
        a: ["Leave him; snoring means he's breathing", "Roll him into the recovery position and check on him regularly; call {{N}} if he can't be roused at all", "Prop him up with pillows and put a bucket nearby"],
        correct: 1,
        why: "Snoring in an unconscious person means a partly blocked airway. On his side, he can't choke on vomit. Alcohol poisoning is a genuine emergency.",
      },
    ],
  },
  {
    id: "crisis",
    n: "Skill 7",
    title: "Someone in crisis",
    short: "They seem to be giving up. Ask directly about suicide. Stay. Connect them to help.",
    minutes: 3,
    why: "More than 700,000 people die by suicide every year — one every 40 seconds — and most tell someone, in some way, first. Asking directly does not plant the idea; research shows it lowers risk. You don't need to be a therapist. You need to notice, ask, stay, and connect.",
    recognize: [
      ["Talking about being a burden, trapped, hopeless, or “wanting it to stop”", "Or saying goodbye, giving things away, tidying up affairs."],
      ["Withdrawing, sleeping very little or a lot, drinking more, sudden calm after deep depression", "That calm can mean a decision has been made."],
      ["Recent loss, breakup, job loss, diagnosis, shame, or a previous attempt", "Risk is highest in the weeks after."],
    ],
    steps: [
      ["Ask directly: “Are you thinking about suicide?”", "Use the word. Don't soften it to “you're not thinking of doing anything silly, are you?” — that tells them what answer you want. Then be quiet and let them talk."],
      ["Listen without arguing or fixing", "Don't say “you have so much to live for”. Say “that sounds unbearable — I'm glad you told me.” Ask what's been happening. Let them feel heard."],
      ["Keep them safe: ask about a plan and means", "“Have you thought about how?” If they have access to pills, a gun, a high place — ask if you can hold onto them or put distance between them and it. Means restriction saves lives; crises pass."],
      ["Help them connect", "Call a crisis line together, right now, on speaker if they like: {{C}}. If there's immediate danger — a plan, the means, tonight — call {{N}} or take them to an emergency department and stay."],
      ["Follow up", "Text tomorrow. Call next week. A short message — “thinking of you, how's today?” — measurably reduces suicide risk afterwards. You are not their therapist; you are the person who stays."],
    ],
    dont: [
      "Don't promise to keep it secret. Say: “I care about you too much to keep this between us.”",
      "Don't lecture about how it would hurt their family — that adds guilt to the burden.",
      "Don't leave someone alone who has a plan and means.",
      "Don't carry this alone yourself. Tell someone you trust, and look after yourself afterwards.",
    ],
    drill: "respond",
    respondDrill: {
      intro: "Pick the better response.",
      items: [
        {
          said: "“Honestly, everyone would be better off without me.”",
          a: ["“Don't say that! You've got so much going for you.”", "“That sounds really heavy. Are you thinking about suicide?”"],
          correct: 1,
          why: "The first response shuts the door. The second opens it and asks the question directly.",
        },
        {
          said: "“...Yeah. I've thought about it.”",
          a: ["“I'm glad you told me. Can you tell me what's been going on?”", "“You wouldn't actually do it though, right?”"],
          correct: 0,
          why: "Thank them, then listen. The second response tells them to retract, so they will — and you lose the chance to help.",
        },
        {
          said: "“I've got the pills. I was going to do it this weekend.”",
          a: ["“Promise me you won't. I'll check on you Monday.”", "“Thank you for trusting me. Can I hold onto the pills for now? Let's call the crisis line together — I'll stay right here.”"],
          correct: 1,
          why: "A plan plus means plus a time is high risk. Separate them from the means and connect them to help now. Don't leave.",
        },
        {
          said: "(Two days later. They've seen a doctor and seem steadier.)",
          a: ["Give them space — they'll reach out if they need to", "Send a short text: “Thinking of you. How's today going?”"],
          correct: 1,
          why: "Brief, regular check-ins after a crisis are one of the best-evidenced ways to reduce suicide risk. People rarely reach out; reach in.",
        },
      ],
    },
    check: [
      {
        q: "Does asking someone directly whether they're thinking of suicide increase the chance they will attempt it?",
        a: ["Yes — it can plant the idea", "No — studies show it reduces distress and risk, and makes help more likely"],
        correct: 1,
        why: "This myth stops people asking. Asking directly is relief for most people in crisis: finally, someone noticed.",
      },
    ],
  },
];

// Short cards for other situations worth knowing.
export const QUICK = [
  { t: "Seizure", pts: ["Don't hold them down, don't put anything in their mouth", "Cushion the head, move hard objects away, time it", "Afterwards: recovery position", "Call {{N}} if it lasts over 5 min, repeats, they're injured, pregnant, in water, or it's their first"] },
  { t: "Severe allergic reaction", pts: ["Swelling lips/tongue, hives, wheeze, faint after food, sting or drug", "Use their adrenaline auto-injector (EpiPen) in the outer thigh, through clothes — hold 3 s", "Call {{N}} even if they improve; a second wave can come", "Lie them down, legs raised, unless struggling to breathe"] },
  { t: "Opioid overdose", pts: ["Unresponsive, slow or no breathing, tiny pupils, blue lips", "Call {{N}}. Give naloxone (Narcan) nasal spray if any is around", "Not breathing normally? CPR", "Breathing? Recovery position. Naloxone wears off in 30–90 min — stay"] },
  { t: "Drowning", pts: ["Drowning is silent — no waving, no shouting, head low in water", "Reach or throw; don't go in unless trained", "Out of the water and not breathing? Start CPR with 5 rescue breaths first if you can", "Call {{N}}. Anyone who inhaled water should be checked"] },
  { t: "Burns", pts: ["Cool running water for 20 minutes — this is the treatment", "Remove rings and tight things before swelling", "Cover loosely with cling film or a clean non-fluffy cloth", "No ice, butter, toothpaste. Call {{N}} for burns bigger than their hand, on face/hands/genitals, or any chemical/electrical burn"] },
  { t: "Diabetic low blood sugar", pts: ["Shaky, sweaty, confused, aggressive or drowsy, in someone with diabetes", "Awake and can swallow? Sugar now: juice, glucose tablets, sweets. Then a snack", "Not improving in 10–15 min, or can't swallow? Call {{N}}", "Unconscious? Recovery position, nothing by mouth, call {{N}}"] },
  { t: "Handwashing", pts: ["Still the single cheapest life-saver on Earth: cuts respiratory illness ~20%, diarrhoeal disease ~30%", "Soap, scrub 20 seconds: backs of hands, between fingers, under nails", "Before eating, after the toilet, after coughing, after being out", "No soap? Alcohol gel (60%+) works if hands aren't visibly dirty"] },
  { t: "Heatstroke", pts: ["Hot, confused, staggering, maybe stopped sweating — after heat or exertion", "Call {{N}}. Move to shade, strip extra clothing", "Cool aggressively: cold water on skin, fan, ice packs to neck, armpits, groin", "Sips of water if fully alert. Nothing if confused"] },
];

export const FINAL_QUIZ = [
  { q: "A woman collapses at a bus stop. She's not responding and not breathing. Nobody else is around. Order of actions?", a: ["Start compressions for 2 minutes, then call", "Call {{N}} on speaker, then start compressions immediately", "Run to find an AED, then come back"], correct: 1, why: "Call first (on speaker, so the dispatcher can coach you), then push. Alone, you don't leave to look for an AED." },
  { q: "You're doing CPR. You feel a rib crack. You:", a: ["Stop — you're hurting her", "Press more gently", "Keep going at full depth. Ribs heal; brains don't"], correct: 2, why: "Cracked ribs are common and expected in effective CPR." },
  { q: "A toddler is choking on a grape and silent. He's 3 years old. You:", a: ["Abdominal thrusts, gently — same as adults", "Back blows along your arm with chest thrusts — the infant technique", "Hold him upside down and shake"], correct: 0, why: "Over 1 year old: same as adults, with less force. Back blows then abdominal thrusts. Under 1: back blows and chest thrusts." },
  { q: "Grandad's speech is suddenly slurred but he says he's fine and it's probably his new glasses. It's 9:15 pm.", a: ["Wait until morning and see the doctor", "Call {{N}}, say “stroke”, and tell them symptoms started at 9:15", "Give him aspirin and put him to bed"], correct: 1, why: "One FAST sign is enough. No aspirin. Note the time." },
  { q: "Blood is pouring from a deep cut in someone's forearm. The very first thing:", a: ["Find a first-aid kit and a bandage", "Press hard directly on the wound with whatever's nearest, and don't let go", "Hold the arm above their head"], correct: 1, why: "Direct, hard pressure within seconds. Everything else comes after." },
  { q: "Your colleague, 55, has had 'indigestion' for 20 minutes, is pale and sweaty, and looks scared. You:", a: ["Offer antacids and a walk outside for air", "Call {{N}}, sit her down, and keep her still", "Tell her to lie flat and rest"], correct: 1, why: "Sweating, pallor and dread with chest discomfort = heart attack until proven otherwise. Sit (not flat), keep still, call." },
  { q: "Someone is unconscious after a seizure, breathing normally, lying on their back. Best position?", a: ["Leave them flat on their back with a pillow under the head", "Sit them upright", "Recovery position on their side, head tilted back"], correct: 2, why: "Side-lying keeps the airway clear if they vomit. Nothing under the head." },
  { q: "A friend texts: “I can't do this anymore. I'm so tired of everything.” You reply:", a: ["“Get some sleep, you'll feel better tomorrow 💙”", "“That sounds really hard. Can I call you? Are you thinking about suicide?”", "“Don't be dramatic, you'll be fine”"], correct: 1, why: "Take it seriously, move to voice, and ask the question directly." },
  { q: "A person is lying face-down at the roadside. They groan when you shout. Blood is spurting from the leg, and they're breathing. Priority?", a: ["Recovery position first", "Stop the bleeding first — hard pressure, tourniquet if needed — then call", "Call {{N}} and wait for instructions before touching them"], correct: 1, why: "Catastrophic bleeding comes before everything. They're breathing, so the airway can wait a moment; the blood can't." },
  { q: "A man collapsed 3 minutes ago. Someone has brought an AED. You're mid-compressions. You:", a: ["Finish a full 2-minute cycle first", "Turn it on immediately, follow its voice prompts, and continue compressions while pads go on", "Wait for the paramedics — only they can use it"], correct: 1, why: "The AED is the thing that actually restarts the heart. The sooner, the better. It's designed for untrained bystanders." },
];
