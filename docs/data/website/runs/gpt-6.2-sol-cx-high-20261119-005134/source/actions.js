export const categories = {
  connect: { name: "Connection", symbol: "heart" },
  information: { name: "Better information", symbol: "check" },
  access: { name: "Accessibility", symbol: "asterisk" },
  resources: { name: "Sharing resources", symbol: "box" },
  community: { name: "Community care", symbol: "sun" },
};

export const actions = [
  {
    id: "check-in",
    minutes: 5,
    category: "connect",
    title: "Check in on someone",
    description: "Reach out to someone who might appreciate hearing from you.",
    steps: [
      "Think of one person you haven’t talked to in a while, or someone who has a lot on their plate.",
      "Send a short message. If they reply, listen before offering advice.",
    ],
    example: "Hey, you crossed my mind today. How are things going? I’d love to hear from you whenever you have a moment.",
  },
  {
    id: "verify",
    minutes: 5,
    category: "information",
    title: "Pause before sharing",
    description: "Check the source of a claim before passing it along.",
    steps: [
      "Pick one claim you’re about to forward. Look for the original source and check its date and context.",
      "Look for independent confirmation from a source with direct knowledge. If you’re still unsure, leave the claim unshared.",
    ],
    example: "If you already shared it, reply in the same thread with what you found and correct the original post if you can.",
  },
  {
    id: "alt-text",
    minutes: 5,
    category: "access",
    title: "Add useful alt text",
    description: "Make an image you share easier to understand with a screen reader.",
    steps: [
      "Pick an image that conveys information in a post, document, or presentation you can edit.",
      "Use the alt-text field to describe what matters in context. For a flyer, include the event details in the surrounding text too.",
    ],
    example: "For a photo in a post about a food swap: “Neighbors trade jars of preserves and bunches of herbs at a folding table.”",
  },
  {
    id: "offer",
    minutes: 15,
    category: "connect",
    title: "Offer one specific favor",
    description: "Make it easier for someone to say yes to help they could use.",
    steps: [
      "Think of someone juggling a lot. Choose a favor you know you can follow through on.",
      "Name the thing you can do and when. Give them an easy way to decline or suggest something else.",
    ],
    example: "I’m going to the grocery store tomorrow around six. Want me to pick anything up for you? No worries if you’re all set.",
  },
  {
    id: "give-away",
    minutes: 15,
    category: "resources",
    title: "Pass on something useful",
    description: "Find a new home for a working item you no longer use.",
    steps: [
      "Choose one item in clean, working condition. Describe its condition honestly.",
      "Offer it through a neighborhood giveaway group or check whether a local organization accepts it. Arrange pickup only once someone wants it.",
    ],
    example: "A working desk lamp, a clean winter coat, or a spare set of tools may be useful if someone is looking for one.",
  },
  {
    id: "captions",
    minutes: 15,
    category: "access",
    title: "Fix a video’s captions",
    description: "Make a clip you’ve shared easier to follow without sound.",
    steps: [
      "Open the captions for a short video you own or have permission to edit.",
      "Listen through once and correct names, important sounds, and any words the automatic captions misheard.",
    ],
    example: "If captions can’t be edited, add a transcript near the video or in the post description.",
  },
  {
    id: "volunteer",
    minutes: 60,
    category: "community",
    title: "Take a volunteer shift",
    description: "Give an hour to a group already meeting a local need.",
    steps: [
      "Look for a specific task at a food pantry, community garden, mutual aid group, or library.",
      "Check the hours and sign-up requirements. Choose a shift you can reliably make, and let the organizer know if your availability changes.",
    ],
    example: "Some groups need someone to sort supplies, set up a room, or help with a remote admin task.",
  },
  {
    id: "share-skill",
    minutes: 60,
    category: "resources",
    title: "Share a skill",
    description: "Spend an hour helping someone learn something they want to do.",
    steps: [
      "Ask a friend or neighbor if they’d like help with a skill you know. Let them choose a small goal they care about.",
      "Let them do the task while you guide them. Leave them with a short reminder they can use on their own.",
    ],
    example: "Help someone practice a language, repair a bike tire, or prepare for a job interview.",
  },
  {
    id: "access-barrier",
    minutes: 60,
    category: "access",
    title: "Help fix an access barrier",
    description: "Bring a practical accessibility fix to someone who can make it happen.",
    steps: [
      "Choose a barrier you’ve noticed or that someone has asked you to flag, such as missing step-free directions for a public event.",
      "Send the organizer a brief note with the location, the issue, and a concrete fix. Get permission before sharing anyone’s personal experience.",
    ],
    example: "Could you add the step-free entrance and its opening hours to the event page? I only found directions to the entrance with stairs.",
  },
];
