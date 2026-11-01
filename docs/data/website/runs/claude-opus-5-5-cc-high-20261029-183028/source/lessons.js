import { h } from "./dom.js";
import { quiz, sorter, sequence, dialogue } from "./components.js";
import { emergencyNumber, cprTrainer, strokeFaces, bleedingPress, orsMixer, drowningScene } from "./widgets.js";

// Each lesson: why it matters, what to do, and a short hands-on practice.
// `remember` is the one line that goes on the take-away card.
export const lessons = [
  {
    id: "call",
    icon: "📞",
    title: "Know your emergency number",
    stat: "In a crisis, people often freeze or waste time searching for the number to call. Every minute it takes to get help on the way counts.",
    steps: [
      "Know the number where you live and wherever you travel. 112 works across Europe and on many mobile networks worldwide.",
      "Say <b>where you are</b> first: the address, or landmarks if you don't know it. Then say what happened.",
      "Put the phone on <b>speaker</b> and stay on the line. Dispatchers can talk you through CPR, childbirth and more.",
      "If others are around, point at one person: <b>“You — call the ambulance.”</b> Send another to find a defibrillator (AED).",
    ],
    remember: "Call first. Say where you are. Speaker on, stay on the line.",
    practice: (done) => h("div", null,
      emergencyNumber(),
      quiz([
        {
          q: "You call for help. What do you tell the dispatcher first?",
          options: [
            { t: "Where you are", correct: true, why: "Right. If the call drops, they still know where to send help." },
            { t: "Your name", why: "They may ask later — location comes first, so help can be sent even if the call drops." },
            { t: "The whole story of what happened", why: "Start with the location. They'll ask the questions they need." },
          ],
        },
        {
          q: "You're doing CPR and the dispatcher is still talking. What do you do?",
          options: [
            { t: "Put the phone on speaker and keep pushing", correct: true, why: "Exactly. Let them coach you. Don't hang up until they tell you to." },
            { t: "Hang up so you can concentrate", why: "Stay on the line — they can coach you and send more help." },
            { t: "Stop CPR to talk to them properly", why: "Keep your hands going. Speakerphone lets you do both." },
          ],
        },
      ], done)),
  },
  {
    id: "cpr",
    icon: "❤️",
    title: "Hands-only CPR",
    stat: "When someone's heart stops, CPR started straight away can double or triple their chance of survival. Without it, they will die within minutes.",
    steps: [
      "An adult collapses and isn't breathing normally (or is only gasping)? <b>Call for help.</b>",
      "Put the heel of one hand in the <b>center of the chest</b> with your other hand on top. Lock your elbows.",
      "Push <b>hard and fast</b>: about 5–6 cm (2 in) deep, <b>100–120 times a minute</b>. Let the chest come all the way back up each time.",
      "Don't stop until help takes over. If an <b>AED</b> arrives, switch it on and do what it says. It won't shock someone who doesn't need it.",
      "Don't be afraid of hurting them. They are already dying, and CPR is their only chance.",
    ],
    note: "If you've been trained, give 2 rescue breaths after every 30 pushes. Breaths matter more for children, babies and drowning victims, so a hands-on course is worth taking.",
    remember: "Not breathing normally → call, then push hard & fast in the center of the chest, 100–120/min.",
    practice: (done) => cprTrainer(done),
  },
  {
    id: "choke",
    icon: "🫁",
    title: "Help someone who is choking",
    stat: "A blocked airway can kill in a few minutes, long before an ambulance arrives. The person beside them is their best chance.",
    steps: [
      "Ask: <b>“Are you choking?”</b> If they can cough, encourage them to keep coughing.",
      "If they can't breathe, speak or cough: lean them forward and give up to <b>5 firm back blows</b> between the shoulder blades with the heel of your hand.",
      "Then give up to <b>5 abdominal thrusts</b>: stand behind them, put a fist just above the belly button, grab it with your other hand and pull sharply in and up.",
      "Keep alternating 5 and 5. If they become unresponsive, call the emergency number and <b>start CPR</b>.",
      "<b>Babies under 1:</b> back blows with the baby face-down along your forearm, then chest thrusts with two fingers. Never abdominal thrusts.",
    ],
    remember: "Can't cough or speak → 5 back blows, 5 abdominal thrusts, repeat.",
    practice: (done) => h("div", null,
      h("p", { class: "practice-lead" }, "A man at the next table grabs his throat. Put the steps in order:"),
      sequence([
        "Ask “Are you choking?”",
        "He can't speak or cough. Shout for someone to call for help",
        "Lean him forward. 5 firm back blows",
        "5 abdominal thrusts, in and up",
        "Repeat 5 and 5 until it comes out",
        "If he becomes unresponsive, start CPR",
      ], done)),
  },
  {
    id: "stroke",
    icon: "🧠",
    title: "Spot a stroke: think F.A.S.T.",
    stat: "During a stroke, about 1.9 million brain cells die every minute. Getting treatment fast can be the difference between going home and lifelong disability.",
    fast: [
      ["F", "Face", "Ask them to smile. Does one side droop?"],
      ["A", "Arms", "Can they raise both arms? Does one drift down?"],
      ["S", "Speech", "Is it slurred or strange? Can they repeat a simple sentence?"],
      ["T", "Time", "Any one of these: call the emergency number now. Note the time it started."],
    ],
    steps: [
      "Other sudden signs: loss of vision, a severe headache, confusion, numbness, trouble walking.",
      "Call an ambulance <b>even if the symptoms go away</b>. It may be a warning stroke.",
      "Don't let them “sleep it off”, and don't give food or drink.",
    ],
    remember: "Face, Arms, Speech: any one → Time to call. Note when it started.",
    practice: (done) => h("div", null,
      strokeFaces(),
      quiz([
        {
          q: "Your aunt's smile is lopsided and her words sound slurred. She says she's fine and just wants to lie down.",
          options: [
            { t: "Call the emergency number now", correct: true, why: "Yes. Two FAST signs. Don't wait to see if it passes; treatments only work in the first few hours." },
            { t: "Let her rest and check on her in an hour", why: "An hour can cost her around 100 million brain cells. Call now." },
            { t: "Give her a glass of water and some food", why: "Strokes can make swallowing unsafe. Nothing by mouth. Call now." },
          ],
        },
        {
          q: "Your neighbor's arm went weak for five minutes, then went back to normal.",
          options: [
            { t: "Get urgent medical help anyway", correct: true, why: "Right. A “mini-stroke” (TIA) is often a warning that a major stroke may follow soon." },
            { t: "No need. It passed", why: "Symptoms that pass can be a warning stroke (TIA). It still needs urgent care." },
          ],
        },
      ], done)),
  },
  {
    id: "heart",
    icon: "🫀",
    title: "Recognize a heart attack",
    stat: "Heart disease is the world's leading cause of death. Many people who die of heart attacks waited too long to call for help.",
    steps: [
      "Chest <b>pressure, squeezing or pain</b> that lasts more than a few minutes, or goes away and comes back.",
      "Pain or discomfort spreading to the <b>arm, jaw, neck, back or stomach</b>.",
      "<b>Shortness of breath</b>, cold sweat, nausea, light-headedness.",
      "Women, older people and people with diabetes more often have the <b>less obvious signs</b>: breathlessness, nausea, back or jaw pain, unusual tiredness.",
      "<b>Call the emergency number straight away.</b> Sit them down and keep them calm. The dispatcher may tell them to chew an aspirin.",
    ],
    remember: "Chest pressure, breathlessness, sweat, jaw or arm pain → call right away. Don't wait.",
    practice: (done) => quiz([
      {
        q: "Your dad has had a crushing feeling in his chest for 10 minutes. He says it's probably indigestion.",
        options: [
          { t: "Call the emergency number now", correct: true, why: "Yes. Paramedics can start treatment on the way and handle cardiac arrest if it happens. (Where there are no ambulances, get to a hospital as fast as you can.)" },
          { t: "Give him an antacid and wait", why: "Waiting is how heart attacks kill. Ten minutes of chest pressure means call now." },
          { t: "Tell him to drive himself to a clinic", why: "If his heart stops while he's driving, he and others are at risk. Call for help." },
        ],
      },
      {
        q: "Which of these can be the main signs of a heart attack, especially in women?",
        options: [
          { t: "Shortness of breath, nausea, jaw or back pain", correct: true, why: "Right. Not every heart attack is the crushing chest pain you see in films." },
          { t: "Only ever crushing chest pain", why: "Many heart attacks, especially in women, show up as breathlessness, nausea, or back or jaw pain." },
          { t: "Only pain in the left arm", why: "Arm pain is one possible sign, but breathlessness, nausea and jaw or back pain are common too." },
        ],
      },
    ], done),
  },
  {
    id: "bleed",
    icon: "🩸",
    title: "Stop severe bleeding",
    stat: "Someone can bleed to death in as little as five minutes. Firm pressure from your hands can keep them alive until help arrives.",
    steps: [
      "Call the emergency number, or get someone else to.",
      "<b>Press hard, directly on the wound</b> with a cloth or clothing, or your bare hands if that's all you have.",
      "<b>Keep pressing. Don't lift to check.</b> If blood soaks through, add more cloth on top.",
      "For life-threatening bleeding from an arm or leg, a <b>tourniquet</b> 5–8 cm (2–3 in) above the wound, pulled very tight, saves lives. Note the time you applied it.",
    ],
    remember: "Press hard on the wound and don't let go. Add cloth on top, never lift.",
    practice: (done) => bleedingPress(done),
  },
  {
    id: "burn",
    icon: "🔥",
    title: "Cool a burn the right way",
    stat: "Burns kill an estimated 180,000 people a year and injure millions more, mostly at home and often children. The right first aid in the first minutes reduces scarring and the need for surgery.",
    steps: [
      "Hold the burn under <b>cool running water for 20 minutes</b>. It still helps if you start up to 3 hours later.",
      "Take off rings, watches and clothing near the burn, unless they're stuck to the skin.",
      "Cover it loosely with <b>cling film</b> or a clean, non-fluffy cloth.",
      "<b>Never</b> use ice, butter, oil or toothpaste. Cool the burn, but keep the person warm.",
      "Get medical help for large or deep burns, burns on the face, hands, feet or genitals, electrical or chemical burns, and any burn on a baby or child.",
    ],
    remember: "Burn → cool running water, 20 minutes. No ice, butter or toothpaste.",
    practice: (done) => h("div", null,
      h("p", { class: "practice-lead" }, "A child grabs a hot pan. Which of these should you do?"),
      sorter({
        items: [
          { t: "Cool running water for 20 minutes", ok: true, why: "Yes. This is the single most important thing: it stops the burn going deeper." },
          { t: "Rub butter or oil on it", ok: false, why: "Fats trap heat and raise the risk of infection." },
          { t: "Put ice on it", ok: false, why: "Ice can damage the skin even more. Use cool, not freezing, water." },
          { t: "Take off rings and tight items nearby", ok: true, why: "Yes. Burns swell fast, and rings can cut off circulation." },
          { t: "Put toothpaste on it", ok: false, why: "A common myth. It traps heat and has to be painfully scrubbed off at the hospital." },
          { t: "Cover loosely with cling film", ok: true, why: "Yes. It protects the burn without sticking to it." },
          { t: "Pop the blisters", ok: false, why: "Blisters protect against infection. Leave them alone." },
        ],
      }, done)),
  },
  {
    id: "ors",
    icon: "💧",
    title: "Save a child from dehydration",
    stat: "Diarrhea kills around 440,000 children under five every year. Most of those deaths could be prevented with a drink made from salt, sugar and clean water.",
    steps: [
      "<b>Oral rehydration solution (ORS)</b> replaces the water and salts lost through diarrhea. Ready-made ORS packets from a pharmacy are best.",
      "No packet? Mix <b>1 liter of clean water + 6 level teaspoons of sugar + ½ level teaspoon of salt</b>.",
      "Give <b>small sips often</b>, a spoonful at a time for small children. Keep breastfeeding and feeding.",
      "<b>Zinc</b> for 10–14 days helps children recover. Ask a health worker.",
      "Get help fast if the child is very sleepy, can't drink, has sunken eyes, blood in their stool, or isn't getting better.",
    ],
    remember: "Diarrhea → 1 L clean water + 6 tsp sugar + ½ tsp salt, sipped often. Keep feeding.",
    practice: (done) => orsMixer(done),
  },
  {
    id: "drown",
    icon: "🌊",
    title: "Drowning doesn't look like drowning",
    stat: "Around 300,000 people drown every year. Young children are at the highest risk, and many drown with adults close by who didn't recognize it.",
    steps: [
      "A drowning person usually <b>can't shout or wave</b>. They're upright, silent, head tilted back, mouth at the surface.",
      "<b>Reach or throw, don't go.</b> Hold out a pole or branch, or throw anything that floats. Jumping in can mean two drownings.",
      "Keep small children <b>within arm's reach</b> near any water, including baths, buckets and ditches.",
      "Fence pools, cover wells and water tanks, and teach children to swim.",
    ],
    remember: "Drowning is silent. Reach or throw, don't go. Kids within arm's reach of water.",
    practice: (done) => drowningScene(done),
  },
  {
    id: "ask",
    icon: "🤝",
    title: "Ask about suicide",
    stat: "More than 700,000 people die by suicide every year. Research shows that asking someone directly does not put the idea in their head. It often brings relief.",
    steps: [
      "<b>Notice:</b> talk of being a burden or hopeless, withdrawing, giving things away, saying goodbye.",
      "<b>Ask directly:</b> “Are you thinking about suicide?” Use the word.",
      "<b>Listen</b> without judging or rushing to fix it. Thank them for telling you.",
      "<b>Keep them safe:</b> stay with them, and put distance between them and pills, weapons or other means.",
      "<b>Connect:</b> call a crisis line together, or the emergency number if they're in immediate danger. Follow up in the days after.",
    ],
    note: "Crisis lines: 988 (US & Canada) · Samaritans 116 123 (UK & Ireland) · Lifeline 13 11 14 (Australia) · others at findahelpline.com. If you're struggling yourself, you deserve that help too.",
    remember: "Ask directly. Listen. Keep them safe. Connect them to help.",
    practice: (done) => dialogue([
      {
        them: "Honestly, I don't see the point anymore. Everyone would be better off without me.",
        choices: [
          { t: "Don't say that! You have so much to live for.", why: "Well meant, but it can shut the conversation down and make them feel unheard." },
          { t: "That sounds really painful. Are you thinking about suicide?", correct: true, why: "Yes. Asking directly shows you can handle the answer." },
          { t: "Come on, let's go out and take your mind off it.", why: "Distraction can feel like dismissal. Ask first." },
        ],
      },
      {
        them: "…Yeah. Sometimes. I've thought about how.",
        choices: [
          { t: "You wouldn't actually do that, right?", why: "This pushes them to say “no” and stop talking." },
          { t: "Thank you for telling me. I'm here. Can you tell me what's been going on?", correct: true, why: "Yes. Thank them, stay calm, and listen." },
          { t: "Okay. I'll keep this between us.", why: "Never promise to keep suicide a secret. Their safety comes first." },
        ],
      },
      {
        them: "It's been months. I'm just so tired of everything.",
        choices: [
          { t: "You should see a therapist sometime.", why: "Good idea, but “sometime” isn't enough when they've thought about how. Help them connect now, and stay." },
          { t: "Let's call a crisis line together right now. I'll stay with you. Is there anything at home we should put away?", correct: true, why: "Yes. Stay with them, reduce access to means, and connect them to help now." },
          { t: "Get some sleep. You'll feel better tomorrow.", why: "This leaves them alone with it. Stay, and help them connect to support now." },
        ],
      },
    ], "Okay… yeah. Thank you for not freaking out.", done),
  },
];

export const habits = [
  ["🚗", "Buckle up, every seat, every trip.", "Seatbelts cut the risk of death for front-seat occupants by about half."],
  ["🛵", "Helmet on two wheels.", "A good helmet cuts the risk of death in a motorcycle crash by over 40%."],
  ["🧼", "Wash hands with soap for 20 seconds.", "It can cut diarrheal illness by up to 40% and respiratory infections by about a fifth."],
  ["📵", "Never drive drunk or on your phone.", "Road crashes kill about 1.2 million people a year, and are the top killer of young people aged 5–29."],
  ["💉", "Keep vaccinations up to date.", "Immunization prevents an estimated 3.5–5 million deaths every year."],
  ["🚨", "Fit a smoke alarm and test it.", "Working smoke alarms cut the risk of dying in a home fire by about half."],
];
