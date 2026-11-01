export const FLAGS = [
  {
    re: /\bbut\b/i,
    title: "but",
    text: "A “but” after an apology erases the sentence before it. End the sentence. If you must explain, do it another day — and only if they ask."
  },
  {
    re: /sorry,? if/i,
    title: "sorry if",
    text: "“Sorry if” makes the apology conditional on their perception. You were there. You can name what you did without “if.”"
  },
  {
    re: /sorry (?:that )?you (?:feel|felt|were offended|got offended|took|are upset|are mad|are angry|got upset|got mad)/i,
    title: "sorry you",
    text: "“Sorry you feel” apologizes for their feeling, not your action. It puts them on trial for having noticed."
  },
  {
    re: /\byou always\b|\byou never\b|\bi never (?:do|did|would)\b|\bi don(?:'|’)t always\b|\bi do not always\b/i,
    title: "always",
    text: "“Always” and “never,” aimed at a character, turn a repair into a trial. A promise can be specific without them: “Next time I will.”"
  },
  {
    re: /you made me/i,
    title: "you made me",
    text: "They can make a situation. They cannot make your conduct. Take the verb back."
  },
  {
    re: /i(?:'|’)m the worst|i am the worst|i hate myself|i(?:'|’)m a terrible|i am a terrible|i ruin everything/i,
    title: "the worst",
    text: "A verdict on your whole self hands them your shame to nurse. That is a second job, on top of being hurt. Own the act, not a monster costume."
  },
  {
    re: /\bat least you\b/i,
    title: "at least",
    text: "“At least” asks them to feel grateful instead of letting them feel found. Save the silver lining. It is not a gift."
  },
  {
    re: /\bcalm down\b|\bjust relax\b|\btoo sensitive\b|\boverreact/i,
    title: "calm down",
    text: "Telling someone their volume is the problem asks them to abandon their own senses. You can ask for a pause without prosecuting the feeling."
  },
  {
    re: /\bjust a joke\b|\bit was (?:just )?a joke\b|\bonly joking\b/i,
    title: "joke",
    text: "“Just a joke” asks them to agree the cost was imaginary. If it landed, the landing is the fact."
  },
  {
    re: /\bobviously\b/i,
    title: "obviously",
    text: "“Obviously” is a small shove. If it were obvious, you would not need the word."
  },
  {
    re: /\bhave you tried\b|\byou should just\b/i,
    title: "advice",
    text: "Advice, this early, is often a wish that their pain would close. Ask before you offer a plan."
  },
  {
    re: /\b(?:please )?forgive me\b|\bare we okay\b|\bneed us to be okay\b|\bneed to know we(?:'|’)re okay\b/i,
    title: "forgive",
    text: "A plea for forgiveness asks them to close their pain so you can rest. Ask for a behavior. Let forgiveness stay theirs, unscheduled."
  }
]

export const BANNED = [
  { id: "but", word: "but", why: "“I’m sorry, but I was stressed” is a prosecution with a soft opening. The “but” hands the blame back. Stop at sorry, or better, stop at the fact. Context can be true and still be a buttress. Save it for a day they ask who you were trying to be." },
  { id: "sorry-you", word: "sorry you feel", why: "This apologizes for their reaction. A camera cannot see a feeling. A camera can see what you did. “I mocked your work in front of your friends” is an apology’s first sentence. “I’m sorry you were embarrassed” is a request that they retract the embarrassment." },
  { id: "if", word: "sorry if", why: "“If” keeps you innocent in the branches where they are wrong. Repair starts by leaving those branches. You can survive having done the thing." },
  { id: "always", word: "you always", why: "Even when the pattern is real, “always” is a fight about memory. Ask for the time that hurt the most. Patterns become visible when you stop litigating the adverb." },
  { id: "worst", word: "I’m the worst", why: "Groveling is not humility. It asks the person you hurt to comfort you for having hurt them. Specific ownership is quieter and much harder." },
  { id: "joke", word: "just a joke", why: "Intent is not the whole event. They can believe you meant to be funny and still have been spent for the laugh. Own the spending." },
  { id: "least", word: "at least", why: "The identifiable good thing in their life does not cancel the pain in the room. “At least” is a trapdoor out of the conversation. Stay in the room." },
  { id: "okay", word: "are we okay?", why: "Sometimes you are not okay, and the honest answer would be no. Asking now pressures them to lie so the evening can end. Offer one next behavior, and permission to need nothing from you tonight." }
]

export const MOVES = [
  {
    n: "01",
    name: "Steady",
    body: "If your face is hot, your hands are cold, or you are rehearsing a victory, you are not ready to be precise. A flooded apology is often a second injury: too long, too much about you, hungry for instant forgiveness.",
    not: "Sending it while your hands shake, because relief cannot wait.",
    yes: "Two inhales through the nose — the second one short, to the top — then a long exhale through the mouth. Three times. Then ask whether you want a better outcome more than you want relief."
  },
  {
    n: "02",
    name: "Fact",
    body: "One sentence a camera would agree with. No motive yet. No “always.” No what they obviously meant. Facts are how you show you were in the same room.",
    not: "“I was just joking. You know I didn’t mean it.”",
    yes: "“I made a joke about your work in front of everyone.”"
  },
  {
    n: "03",
    name: "Own",
    body: "Name the part that was yours, including the motive if you can say it without using it as a cushion. Do not put yourself on trial as a monster. Do not shrink a choice into a misunderstanding.",
    not: "“I’m sorry you felt hurt, but I was stressed.”",
    yes: "“I saw the message and I waited four days. I chose my discomfort over your wait.”"
  },
  {
    n: "04",
    name: "Hear",
    body: "Ask what it was like for them. Then do the harder thing: do not explain, correct, or contextualize until they are done. If they say “always,” do not litigate the word. Ask for the time that hurt the most.",
    not: "“I don’t always do that. Name one time.”",
    yes: "“I want the time that hurt the most. I’ll listen all the way through.”"
  },
  {
    n: "05",
    name: "One",
    body: "One small request about the next time. Not “please forgive me.” Forgiveness is theirs, on no schedule. A behavior is something you can do tomorrow morning. Offer an exit: they may need nothing from you tonight.",
    not: "“Can you forgive me? I need us to be okay.”",
    yes: "“Next time I will answer the same day, even if only to say I saw it. If you need nothing from me tonight, I can live with nothing.”"
  }
]

export const FEELINGS = {
  shame: {
    name: "Shame",
    lead: "Shame says the damage is you, not the thing you did. It will offer hiding, or a grovel, or an attack on whoever saw you. None of those is repair.",
    after: "This is shame. It is hot in the face and cold in the hands. It is not a verdict. Own the act when you speak — not a sentence on your whole self."
  },
  anger: {
    name: "Anger",
    lead: "Anger says the other person is the whole cause. It is often a door in front of fear or humiliation. You may still have been wronged. You are not ready to speak until you want a better outcome more than a victory.",
    after: "This is anger. It wants speed. Do not give it speed. If there is a fact you still need to say, it will still be true in twenty minutes."
  },
  fear: {
    name: "Fear",
    lead: "Fear says silence is safer than a wrong sentence. Sometimes silence is just a slower harm. The future has narrowed to one catastrophic line. It is usually wider than that.",
    after: "This is fear. You can send a shorter, truer sentence than the one you are rehearsing. Short is not cold. Short is often kinder."
  },
  numb: {
    name: "Numb",
    lead: "Numb is not peace. It is a fuse pulled so the house doesn’t burn. You may need it for an hour. Do not make decisions inside it and call them calm.",
    after: "This is numb. Wait until something small is felt again — hunger, temperature, irritation — before you call that clarity. A blank face can still send a cruel message."
  },
  grief: {
    name: "Grief",
    lead: "Grief is not a rupture to fix. If someone died, or left, or a future did, do not mend it shut. Steady is the whole task for now.",
    after: "This is grief. It comes in waves. You do not have to be interesting, productive, or fine. If you tell someone, you may say: I don’t need fixing. I need company."
  }
}

export const PHASES = [
  { name: "Inhale", detail: "Through the nose, until the lungs are nearly full.", dur: 1700, from: 0.85, to: 0.12 },
  { name: "Once more", detail: "A short second inhale, to the very top.", dur: 700, from: 0.12, to: 0 },
  { name: "Let it go", detail: "Long and slow, through the mouth. Longer than you want.", dur: 5400, from: 0, to: 1 }
]

export const SCENES = {
  joke: {
    title: "The joke",
    minutes: 4,
    setting: "The guests have gone. They are drying a glass that is already dry. You joked about their work — the thing they are quiet about — and the table laughed.",
    beats: [
      {
        prompt: "They do not look at you. Say the first true thing.",
        options: [
          {
            kind: "strong",
            say: "I made a joke about your work in front of everyone. I knew it was the sore place. I did it because I wanted the laugh.",
            response: "They nod, once. The glass stops moving.",
            note: "A camera would agree with the first sentence. The motive is owned, not offered as an excuse. Stop there. Do not add why their work is actually great. Not yet."
          },
          {
            kind: "weak",
            say: "Are you actually mad about that? It was a joke.",
            response: "They put the glass down too carefully.",
            note: "Minimizing asks them to abandon their own senses. The laugh was real. So was the cost. A repair starts by trusting where it landed."
          },
          {
            kind: "mid",
            say: "I’m sorry you were embarrassed. You know I think you’re brilliant.",
            response: "“Don’t. Not the compliment.”",
            note: "“Sorry you,” plus a compliment, is a request to skip ahead to comfort. Comfort is their gift to give later, if they want. It is not the price of your apology."
          }
        ]
      },
      {
        prompt: "They say: “You do this. You spend me so you can be the quick one.”",
        options: [
          {
            kind: "weak",
            say: "I don’t “do this.” Name one other time.",
            response: "They almost laugh, and not kindly. “That’s what I mean.”",
            note: "Even if your memory is kinder than theirs, this is a trial. You might win it and lose them."
          },
          {
            kind: "strong",
            say: "I hear that this wasn’t the first time. I want the time that hurt the most. I’ll listen all the way through before I say anything back.",
            response: "They are quiet for a long time. Then they tell you.",
            note: "You asked for their account and surrendered the next turn. That is the whole of Hear. Do not prepare your reply while they give it."
          },
          {
            kind: "mid",
            say: "You’re right. I’m a selfish person. I ruin everything.",
            response: "They look tired. “That’s not what I said.”",
            note: "A verdict on your whole self hands them your shame to manage. Own the pattern if it is real — not a monster costume."
          }
        ]
      },
      {
        prompt: "They have finished. They are waiting to see if you will explain, or leave them with one clean next thing.",
        options: [
          {
            kind: "mid",
            say: "I only joke like that when I’m nervous. My family was like that. If you understood the context—",
            response: "They pick the glass back up.",
            note: "Context can be true and still be a buttress. Save it for another day, if they ask who you were trying to be."
          },
          {
            kind: "weak",
            say: "Can you forgive me? I need to know we’re okay.",
            response: "“I don’t know yet. That’s a lot to ask before I’ve dried this glass.”",
            note: "Forgiveness has no schedule. Asking for it now asks them to close their pain so you can sleep. Ask for a behavior instead."
          },
          {
            kind: "strong",
            say: "Next time I want the laugh, I will leave you out of it. If I slip, stop me in the moment and I will stop. If there’s something that would help before morning, I want to know. If the answer is nothing, I can live with nothing.",
            response: "They consider it. “Nothing tonight. Ask me tomorrow if I want to talk.”",
            note: "One future behavior. One offer. Explicit permission for them to want nothing. That is a repair a person can hold."
          }
        ]
      }
    ]
  },
  silence: {
    title: "The silence",
    minutes: 4,
    setting: "Four days ago they wrote: “The test came back. Can you talk?” You saw it. You did not answer. You are at their door.",
    beats: [
      {
        prompt: "They open the door. They do not perform welcome. What do you say first?",
        options: [
          {
            kind: "weak",
            say: "I’ve been so slammed. You know how work is.",
            response: "They look past you, as if checking whether the excuse brought a suitcase.",
            note: "Busyness is context. It is not the fact. The fact is that you saw a frightened person and looked away."
          },
          {
            kind: "strong",
            say: "I saw your message about the test. I waited four days. That left you alone with it. I was afraid of saying the wrong thing, and I chose my fear over your wait.",
            response: "Something in their shoulder drops, not in forgiveness — in recognition.",
            note: "Fact, then the real motive, named as a choice. Fear is understandable. It is not an alibi."
          },
          {
            kind: "mid",
            say: "I didn’t know what to say, so I said nothing. I’m bad at this stuff.",
            response: "“I didn’t need you to be good at it.”",
            note: "Closer. Still a self-portrait. They already know you said nothing. What they don’t know is whether you will own the choice."
          }
        ]
      },
      {
        prompt: "They say: “I kept checking. I thought maybe something had happened to you. Then I hoped it had, a little, because that was better than you just not caring.”",
        options: [
          {
            kind: "weak",
            say: "That’s a horrible thing to say.",
            response: "They go very still. The door gets heavier.",
            note: "They handed you the worst sentence they have. Punishing it teaches them to edit the truth next time."
          },
          {
            kind: "mid",
            say: "Of course I care. How can you say I don’t care?",
            response: "“Four days didn’t have your care in them. I only had the four days.”",
            note: "“Of course” demands they adopt your self-image. Their week did not contain your care. Start from what they lived."
          },
          {
            kind: "strong",
            say: "I believe you checked, and I believe the hoping. I’m sorry I made absence feel like the safer story. I’m here. If you want to tell me the result, I want it. If you don’t want me as the person you tell, I’ll help you get to the person you do.",
            response: "They cry, briefly, and are annoyed that they cried. They tell you the result anyway.",
            note: "You did not argue with their interpretation. You offered presence without forcing the role. Repair sometimes means accepting a smaller part."
          }
        ]
      },
      {
        prompt: "The result is in the room now. They are tired. Don’t make a speech. Leave one next thing.",
        options: [
          {
            kind: "mid",
            say: "I’ll be better, I promise. You can always count on me from now on.",
            response: "They almost smile. “Don’t say always.”",
            note: "A grand promise is a mood. They have just watched a mood fail. Make the promise small enough to keep on a bad Tuesday."
          },
          {
            kind: "strong",
            say: "If something like this happens again, I will answer the same day, even if the answer is only: I saw this, I’m scared of saying it wrong, I can talk at eight. You don’t have to protect me from how bad the wait was. Is there anything practical you need this week — a ride, company in a waiting room — or nothing?",
            response: "“A ride Thursday. Don’t be late. And don’t thank me for giving you the ride to give.”",
            note: "One behavior. One practical offer. No demand that they soothe you for showing up late to their fear."
          },
          {
            kind: "weak",
            say: "Let me make it up to you. Dinner? I need to fix this tonight.",
            response: "“I’m tired. Dinner would be for you.”",
            note: "Repair on your timetable is another disappearance — this time from their no. Offer, and let the offer be refused."
          }
        ]
      }
    ]
  },
  couch: {
    title: "The couch",
    minutes: 3,
    setting: "Late. A friend has been turning their phone face-down and face-up. They are not asking you to be clever.",
    beats: [
      {
        prompt: "They say: “I’m just tired. Of all of it.”",
        options: [
          {
            kind: "weak",
            say: "At least you’ve got people who love you. Think about them.",
            response: "They nod, to end it. The phone goes face-down again.",
            note: "“At least” is a trapdoor. You asked them to feel grateful instead of letting them feel found."
          },
          {
            kind: "mid",
            say: "You should take a real break. Have you tried going for a walk in the morning? It changes your chemistry.",
            response: "“Sure.” They are already elsewhere.",
            note: "Advice, this early, says their pain is a problem you would like to close. They have not asked for a plan. They have asked, by speaking, not to be alone in it."
          },
          {
            kind: "strong",
            say: "Tired of all of it is a big sentence. I’m not going anywhere. When you say all of it — do you mean you want a rest from your life, or that you don’t want to be alive?",
            response: "They look at you, startled that the question was allowed. Then they answer.",
            note: "You did not flinch, and you did not dramatize. Asking directly does not plant the idea. If the idea is there, the question lets it into a room where someone can help."
          }
        ]
      },
      {
        prompt: "They say, after a while: “Sometimes I think everyone would have an easier week if I weren’t in it.”",
        options: [
          {
            kind: "weak",
            say: "Don’t talk like that. You have so much to live for. It’s selfish to even think it.",
            response: "They apologize for having said it. That is the worst possible outcome.",
            note: "You just taught them that the truth gets them scolded. They will be more alone tomorrow than they were tonight."
          },
          {
            kind: "mid",
            say: "I know exactly how you feel. Last year I went through something really similar — let me tell you what I did.",
            response: "They listen to your year. Theirs leaves the room.",
            note: "A story about you can be company later. Right now it takes the only chair."
          },
          {
            kind: "strong",
            say: "Thank you for telling me. I’m glad you said it out loud. Are you thinking about suicide — and is there a plan, or a way, nearby tonight?",
            response: "They go quiet. They do not leave. They start to answer the actual question.",
            note: "This is no longer an ordinary conversation. Stay. The next page of this site is the one to follow: ask plainly, don’t promise secrecy, get more help than you."
          }
        ]
      }
    ]
  }
}

export const KIND = {
  weak: "This widens the break",
  mid: "This dodges",
  strong: "This can be worked with"
}

export const DRILLS = [
  {
    title: "The interruption",
    setup: "In a meeting, you finished their sentence. You finished it wrong. Their boss watched.",
    options: [
      { kind: "mid", say: "Sorry — I was just trying to help you land the point.", note: "“Just trying to help” is a cushion. The fact is that you took their sentence and spent it." },
      { kind: "strong", say: "I interrupted you and I got it wrong, in front of your boss. I’ll correct it with them today, in writing, and I won’t finish your sentences. I’m sorry.", note: "Fact, a repair they don’t have to perform, and one future behavior. The apology is last, not a disguise for the rest." },
      { kind: "weak", say: "You’re not still thinking about that, are you?", note: "You are asking them to shrink the moment so you don’t have to carry it. They will. They will also remember that you asked." }
    ]
  },
  {
    title: "The secret",
    setup: "You told their story at dinner, without their name. Everyone still knew. They heard about it from someone who was there.",
    options: [
      { kind: "weak", say: "I never said your name. You’re overreacting.", note: "Withholding a name is not the same as keeping a confidence. “Overreacting” prosecutes them for recognizing themselves." },
      { kind: "strong", say: "I told your story to make the table listen. I didn’t have the right. I won’t repeat what you tell me, and I’ll tell the people who were there that it was mine to keep and I didn’t.", note: "You named the motive — attention — without using it as an excuse. The repair includes the audience you created, not only the person you used." },
      { kind: "mid", say: "I’m sorry you feel betrayed. That wasn’t my intention.", note: "Intention is not a refund. “Sorry you feel” puts the betrayal in their feelings instead of in the telling." }
    ]
  },
  {
    title: "The cashier",
    setup: "You were sharp with a cashier who was new. Your kid watched. The cashier’s hands shook afterward.",
    options: [
      { kind: "strong", say: "To the cashier: I spoke to you harshly. That was wrong. It wasn’t about you. To your kid, later: I was unkind to someone who couldn’t talk back. That’s not how we use a bad day.", note: "Power that cannot be refused will pretend to forgive. Repair in public, in front of the witness you accidentally trained." },
      { kind: "weak", say: "To your kid: Some people are just slow. I had a long day.", note: "You just taught a child that less power means less dignity. That lesson will outlive the queue." },
      { kind: "mid", say: "To the cashier, quietly, after: Sorry, I’m just stressed.", note: "Better than nothing. Still mostly about you. Add the fact: I was harsh, you didn’t deserve it, thank you for still helping me." }
    ]
  },
  {
    title: "The cold messages",
    setup: "A friend canceled, badly, on a day you needed them. You sent three cold messages and then went silent. They have just written: “Are you punishing me?”",
    options: [
      { kind: "mid", say: "I’m not punishing you. You’re too sensitive. I was just disappointed.", note: "“Just disappointed” can be true and still ride in on a shove. Take out the diagnosis of their sensitivity." },
      { kind: "weak", say: "If you can’t handle me being honest, maybe we shouldn’t talk.", note: "A threat is not a feeling. You can be hurt without raising the price of the friendship." },
      { kind: "strong", say: "I’m hurt that you canceled, and I was punishing you a little. That wasn’t fair. I still want to tell you what the day was, if you want to hear it. If not, we can talk tomorrow.", note: "You owned the small cruelty inside the legitimate hurt. Both can be true. The exit keeps it from becoming a trap." }
    ]
  }
]

export const ORGS = [
  { name: "Against Malaria Foundation", what: "Funds insecticide-treated bed nets. Nets remain one of the best-studied ways to keep children from dying of malaria." },
  { name: "Malaria Consortium", what: "Seasonal malaria chemoprevention: preventive medicine for young children in the months when transmission is highest." },
  { name: "Helen Keller Intl", what: "Vitamin A supplementation where deficiency is common — fewer children dying of ordinary infections, and sight protected." },
  { name: "New Incentives", what: "Small cash transfers that bring caregivers in for routine childhood vaccines, in places where uptake was low." },
  { name: "GiveDirectly", what: "Cash to people in extreme poverty, who generally know their own emergencies better than a distant donor does." },
  { name: "Lead Exposure Elimination Project", what: "Lead in blood quietly damages children’s minds at a huge scale. Removing it — often from paint — is unglamorous and large." },
  { name: "GiveWell", what: "A research group that publishes the comparisons, including where it changes its mind. Start here if the names above go stale." }
]

export function dayIndex(date = new Date()) {
  const start = new Date(date.getFullYear(), 0, 0)
  return Math.floor((date - start) / 86400000)
}

export function flagsFor(text) {
  if (!text || !text.trim()) return []
  const found = []
  for (const f of FLAGS) {
    if (f.re.test(text)) found.push(f)
    if (found.length === 2) break
  }
  return found
}

export function analyze(text) {
  const raw = text || ""
  const found = []
  for (const f of FLAGS) {
    const m = raw.match(f.re)
    if (m) found.push({ title: f.title, text: f.text, match: m[0] })
  }
  const words = raw.trim() ? raw.trim().split(/\s+/).length : 0
  if (words > 130) {
    found.push({
      title: "length",
      text: "This is long enough to become a speech. A speech asks them to manage your feelings. Cut the context until a tired person could hold it.",
      match: words + " words"
    })
  }
  const goods = []
  if (/\bi chose\b/i.test(raw)) goods.push("You named a choice. That is ownership, not a weather report.")
  if (/\bi will\b|\bnext time\b/i.test(raw)) goods.push("There is a future behavior here. Keep it to one.")
  if (/\?/.test(raw)) goods.push("There is a question. Make sure it asks about them, not a defense in costume.")
  if (!found.length && words > 25) goods.push("Nothing here trips the usual undo-words. Read it aloud once, slowly, before you use it.")
  return { found, goods, words }
}

function sentence(s) {
  const t = (s || "").trim().replace(/\s+/g, " ")
  if (!t) return ""
  return /[.!?]$/.test(t) ? t : t + "."
}

export function composeParts(draft, lessPower) {
  const fact = sentence(draft.fact)
  const ownRaw = (draft.own || "").trim().replace(/\s+/g, " ")
  const hearRaw = (draft.hear || "").trim().replace(/\s+/g, " ")
  const oneRaw = (draft.one || "").trim().replace(/\s+/g, " ")
  const paragraphs = []
  if (fact) paragraphs.push(fact)
  if (ownRaw) {
    const own = sentence(ownRaw)
    if (/^that was mine\b/i.test(ownRaw)) paragraphs.push(own)
    else paragraphs.push(`That was mine. ${own} I am not asking you to say it was fine.`)
  }
  if (hearRaw) {
    if (hearRaw.includes("?")) paragraphs.push(sentence(hearRaw))
    else paragraphs.push(`What was it like for you — ${hearRaw.replace(/\.$/, "")}? I will listen before I explain.`)
  }
  if (oneRaw) {
    const one = sentence(oneRaw)
    paragraphs.push(`${one} If that is not the right request, tell me what would help more — or tell me you need nothing from me tonight.`)
  }
  if (lessPower && paragraphs.length) {
    paragraphs.push("You are allowed to be upset with me. You can say this is not enough. You are safe if you do.")
  }
  const text = paragraphs.join("\n\n")
  const words = text ? text.split(/\s+/).length : 0
  const seconds = Math.max(8, Math.round(words / 2.1))
  return { empty: paragraphs.length === 0, paragraphs, text, words, seconds }
}

export const CRISIS_LINES = [
  { where: "Local emergency", number: "112, 911, 999, 000, or 111", note: "Use the emergency number where you are, now, if danger is close." },
  { where: "United States & Canada", number: "988", note: "Suicide & Crisis Lifeline. Call or text." },
  { where: "United Kingdom & Ireland", number: "116 123", note: "Samaritans. Free, at any hour." },
  { where: "Australia", number: "13 11 14", note: "Lifeline." }
]

export const SAFETY_LINES = [
  { where: "United States", number: "1-800-799-7233", note: "National Domestic Violence Hotline." },
  { where: "United Kingdom", number: "0808 2000 247", note: "National Domestic Abuse Helpline." },
  { where: "Australia", number: "1800 737 732", note: "1800RESPECT." }
]
