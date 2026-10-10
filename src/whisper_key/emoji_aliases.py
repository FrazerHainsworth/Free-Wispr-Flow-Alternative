# Spoken names people use that are not the official Unicode name.
# "tick box emoji" and "right pointing thumb emoji" live here. Official names
# are added separately, and these win when both exist.

def _names(emoji, phrases):
    return {phrase: emoji for phrase in phrases}


SPOKEN_ALIASES = {}
SPOKEN_ALIASES.update(_names("😀", (
    "big grin", "big smile", "happy face", "happy", "cheerful", "grinning face",
)))
SPOKEN_ALIASES.update(_names("😃", (
    "smiley with open mouth", "open mouth smile", "happy open mouth",
)))
SPOKEN_ALIASES.update(_names("😄", (
    "grinning eyes", "smiling eyes", "happy eyes",
)))
SPOKEN_ALIASES.update(_names("😁", (
    "beaming", "beaming face", "cheese smile",
)))
SPOKEN_ALIASES.update(_names("😆", (
    "laughing closed eyes", "squinting laugh", "xd",
)))
SPOKEN_ALIASES.update(_names("😅", (
    "nervous laugh", "sweat smile", "awkward laugh", "relief laugh",
)))
SPOKEN_ALIASES.update(_names("🤣", (
    "rolling on the floor", "rolling laughing", "rofl face",
)))
SPOKEN_ALIASES.update(_names("😂", (
    "laughing crying", "tears of laughter", "crying with laughter", "laughing face",
)))
SPOKEN_ALIASES.update(_names("🙂", (
    "slightly smiling", "small smile", "gentle smile",
)))
SPOKEN_ALIASES.update(_names("😉", (
    "winking", "wink face", "winky face",
)))
SPOKEN_ALIASES.update(_names("😊", (
    "blush", "blushing", "happy blush",
)))
SPOKEN_ALIASES.update(_names("😍", (
    "heart eyes face", "love face", "in love", "loved up",
)))
SPOKEN_ALIASES.update(_names("😘", (
    "blowing a kiss", "kiss face", "kissy face",
)))
SPOKEN_ALIASES.update(_names("😜", (
    "wink tongue", "tongue out wink", "crazy wink",
)))
SPOKEN_ALIASES.update(_names("🤪", (
    "zany", "goofy", "silly face", "wild face",
)))
SPOKEN_ALIASES.update(_names("😎", (
    "cool face", "shades", "sunglasses face",
)))
SPOKEN_ALIASES.update(_names("🤓", (
    "nerd", "nerd face", "geek",
)))
SPOKEN_ALIASES.update(_names("🧐", (
    "monocle", "inspecting",
)))
SPOKEN_ALIASES.update(_names("😢", (
    "sad face", "tear", "single tear",
)))
SPOKEN_ALIASES.update(_names("😭", (
    "crying face", "bawling", "sobbing", "lots of tears",
)))
SPOKEN_ALIASES.update(_names("😡", (
    "angry face", "red face", "furious", "mad face",
)))
SPOKEN_ALIASES.update(_names("🤔", (
    "thinking face", "hmm", "pondering",
)))
SPOKEN_ALIASES.update(_names("😴", (
    "sleeping face", "asleep", "sleepy",
)))
SPOKEN_ALIASES.update(_names("🥳", (
    "party face", "birthday face", "celebrating",
)))
SPOKEN_ALIASES.update(_names("🤯", (
    "mind blown face", "shocked head",
)))
SPOKEN_ALIASES.update(_names("👍", (
    "thumbs up hand", "like", "yes", "approve", "approval",
)))
SPOKEN_ALIASES.update(_names("👎", (
    "thumbs down hand", "dislike", "no", "disapprove",
)))
SPOKEN_ALIASES.update(_names("👉", (
    "right pointing thumb", "right pointing hand", "right pointing finger",
    "thumb pointing right", "hand pointing right", "finger pointing right",
    "pointing right thumb", "pointing thumb right", "right thumb",
    "rightwards thumb", "point to the right", "pointing to the right",
    "right point", "pointer right",
)))
SPOKEN_ALIASES.update(_names("👈", (
    "left pointing thumb", "left pointing hand", "left pointing finger",
    "thumb pointing left", "hand pointing left", "finger pointing left",
    "pointing left thumb", "left thumb", "point to the left",
    "pointing to the left", "left point", "pointer left",
)))
SPOKEN_ALIASES.update(_names("👆", (
    "up pointing thumb", "thumb pointing up", "finger pointing up",
    "pointing up", "point up thumb", "pointer up",
)))
SPOKEN_ALIASES.update(_names("👇", (
    "down pointing thumb", "thumb pointing down", "finger pointing down",
    "pointing down", "point down thumb", "pointer down",
)))
SPOKEN_ALIASES.update(_names("☝️", (
    "index up", "finger up", "one finger", "pointing finger up",
)))
SPOKEN_ALIASES.update(_names("✋", (
    "raised hand", "stop hand", "high five", "palm",
)))
SPOKEN_ALIASES.update(_names("👋", (
    "wave hand", "waving hand", "hello hand", "bye hand", "goodbye",
)))
SPOKEN_ALIASES.update(_names("👏", (
    "clapping hands", "applause", "bravo",
)))
SPOKEN_ALIASES.update(_names("🙌", (
    "raised hands", "hooray", "praise", "both hands up",
)))
SPOKEN_ALIASES.update(_names("🙏", (
    "praying hands", "please", "thank you hands", "namaste",
)))
SPOKEN_ALIASES.update(_names("🤝", (
    "handshake", "shaking hands", "deal",
)))
SPOKEN_ALIASES.update(_names("💪", (
    "flexed biceps", "strong", "bicep", "arm muscle",
)))
SPOKEN_ALIASES.update(_names("✅", (
    "tick", "tick mark", "green tick", "green check", "white tick",
    "done", "correct", "yes tick",
)))
SPOKEN_ALIASES.update(_names("☑️", (
    "tick box", "ticked box", "checkbox", "check box", "checked box",
    "box with a tick", "box with tick", "tick in a box", "tick in the box",
    "ballot box", "ballot", "ticked checkbox", "checked checkbox",
)))
SPOKEN_ALIASES.update(_names("☐", (
    "empty box", "empty checkbox", "unticked box", "blank box", "unchecked box",
)))
SPOKEN_ALIASES.update(_names("❌", (
    "cross", "red cross", "cross mark", "x mark", "wrong", "no cross",
)))
SPOKEN_ALIASES.update(_names("❤️", (
    "red heart", "love heart", "heart symbol",
)))
SPOKEN_ALIASES.update(_names("🧡", ("orange heart",)))
SPOKEN_ALIASES.update(_names("💛", ("yellow heart",)))
SPOKEN_ALIASES.update(_names("💚", ("green heart",)))
SPOKEN_ALIASES.update(_names("💙", ("blue heart",)))
SPOKEN_ALIASES.update(_names("💜", ("purple heart",)))
SPOKEN_ALIASES.update(_names("🖤", ("black heart",)))
SPOKEN_ALIASES.update(_names("🤍", ("white heart",)))
SPOKEN_ALIASES.update(_names("🤎", ("brown heart",)))
SPOKEN_ALIASES.update(_names("💔", ("broken heart", "heartbreak", "heartbroken")))
SPOKEN_ALIASES.update(_names("💖", ("sparkling heart", "sparkly heart")))
SPOKEN_ALIASES.update(_names("💗", ("growing heart",)))
SPOKEN_ALIASES.update(_names("💓", ("beating heart",)))
SPOKEN_ALIASES.update(_names("💕", ("two hearts",)))
SPOKEN_ALIASES.update(_names("💞", ("revolving hearts",)))
SPOKEN_ALIASES.update(_names("🔥", ("fire", "flame", "lit", "hot")))
SPOKEN_ALIASES.update(_names("⭐", ("star", "gold star", "yellow star")))
SPOKEN_ALIASES.update(_names("🌟", ("glowing star", "sparkle star")))
SPOKEN_ALIASES.update(_names("✨", ("sparkles", "sparkle", "glitter")))
SPOKEN_ALIASES.update(_names("💯", ("100", "one hundred", "hundred points", "keep it 100")))
SPOKEN_ALIASES.update(_names("🎉", ("party popper", "tada", "celebration", "congrats")))
SPOKEN_ALIASES.update(_names("🎊", ("confetti", "confetti ball")))
SPOKEN_ALIASES.update(_names("🚀", ("rocket", "rocket ship", "spaceship")))
SPOKEN_ALIASES.update(_names("💡", ("light bulb", "lightbulb", "idea", "idea bulb")))
SPOKEN_ALIASES.update(_names("⚠️", ("warning", "warning sign", "caution")))
SPOKEN_ALIASES.update(_names("📌", ("pin", "pushpin", "drawing pin")))
SPOKEN_ALIASES.update(_names("📍", ("round pin", "location pin", "map pin")))
SPOKEN_ALIASES.update(_names("🔗", ("link", "chain link", "url")))
SPOKEN_ALIASES.update(_names("🔒", ("lock", "locked", "padlock")))
SPOKEN_ALIASES.update(_names("🔓", ("unlock", "unlocked")))
SPOKEN_ALIASES.update(_names("🔑", ("key", "old key")))
SPOKEN_ALIASES.update(_names("🔔", ("bell", "notification")))
SPOKEN_ALIASES.update(_names("🔕", ("muted bell", "no bell", "silent")))
SPOKEN_ALIASES.update(_names("📢", ("megaphone", "loudspeaker", "announcement")))
SPOKEN_ALIASES.update(_names("💬", ("speech bubble", "chat bubble", "comment")))
SPOKEN_ALIASES.update(_names("📝", ("memo", "note", "writing")))
SPOKEN_ALIASES.update(_names("📅", ("calendar", "date")))
SPOKEN_ALIASES.update(_names("⏰", ("alarm", "alarm clock")))
SPOKEN_ALIASES.update(_names("⏳", ("hourglass", "timer")))
SPOKEN_ALIASES.update(_names("🎯", ("target", "bullseye", "direct hit")))
SPOKEN_ALIASES.update(_names("🏆", ("trophy", "cup", "winner")))
SPOKEN_ALIASES.update(_names("🥇", ("gold medal", "first place")))
SPOKEN_ALIASES.update(_names("🎁", ("gift", "present")))
SPOKEN_ALIASES.update(_names("🎂", ("birthday cake", "cake")))
SPOKEN_ALIASES.update(_names("☕", ("coffee", "hot drink", "tea")))
SPOKEN_ALIASES.update(_names("🍕", ("pizza", "pizza slice")))
SPOKEN_ALIASES.update(_names("🍔", ("burger", "hamburger")))
SPOKEN_ALIASES.update(_names("🍺", ("beer", "pint")))
SPOKEN_ALIASES.update(_names("🐶", ("dog", "puppy", "dog face")))
SPOKEN_ALIASES.update(_names("🐱", ("cat", "kitty", "cat face")))
SPOKEN_ALIASES.update(_names("🐭", ("mouse", "mouse face")))
SPOKEN_ALIASES.update(_names("🐰", ("rabbit", "bunny")))
SPOKEN_ALIASES.update(_names("🦊", ("fox",)))
SPOKEN_ALIASES.update(_names("🐻", ("bear",)))
SPOKEN_ALIASES.update(_names("🐼", ("panda",)))
SPOKEN_ALIASES.update(_names("🐨", ("koala",)))
SPOKEN_ALIASES.update(_names("🐯", ("tiger",)))
SPOKEN_ALIASES.update(_names("🦁", ("lion",)))
SPOKEN_ALIASES.update(_names("🐮", ("cow",)))
SPOKEN_ALIASES.update(_names("🐷", ("pig",)))
SPOKEN_ALIASES.update(_names("🐸", ("frog",)))
SPOKEN_ALIASES.update(_names("🐵", ("monkey",)))
SPOKEN_ALIASES.update(_names("🐔", ("chicken",)))
SPOKEN_ALIASES.update(_names("🐧", ("penguin",)))
SPOKEN_ALIASES.update(_names("🐦", ("bird",)))
SPOKEN_ALIASES.update(_names("🦆", ("duck",)))
SPOKEN_ALIASES.update(_names("🦉", ("owl",)))
SPOKEN_ALIASES.update(_names("🐝", ("bee", "honeybee")))
SPOKEN_ALIASES.update(_names("🐛", ("bug", "caterpillar")))
SPOKEN_ALIASES.update(_names("🦋", ("butterfly",)))
SPOKEN_ALIASES.update(_names("🐌", ("snail",)))
SPOKEN_ALIASES.update(_names("🐞", ("ladybug", "ladybird")))
SPOKEN_ALIASES.update(_names("🌸", ("cherry blossom", "blossom")))
SPOKEN_ALIASES.update(_names("🌹", ("rose",)))
SPOKEN_ALIASES.update(_names("🌻", ("sunflower",)))
SPOKEN_ALIASES.update(_names("🌳", ("tree", "deciduous tree")))
SPOKEN_ALIASES.update(_names("🌴", ("palm tree",)))
SPOKEN_ALIASES.update(_names("☀️", ("sun", "sunny", "sunshine")))
SPOKEN_ALIASES.update(_names("🌙", ("moon", "crescent moon")))
SPOKEN_ALIASES.update(_names("⭐", ("star",)))
SPOKEN_ALIASES.update(_names("🌈", ("rainbow",)))
SPOKEN_ALIASES.update(_names("☁️", ("cloud",)))
SPOKEN_ALIASES.update(_names("🌧️", ("rain", "rain cloud", "rainy")))
SPOKEN_ALIASES.update(_names("❄️", ("snowflake", "snow")))
SPOKEN_ALIASES.update(_names("⚡", ("lightning", "zap", "high voltage")))
SPOKEN_ALIASES.update(_names("🌊", ("ocean wave", "water wave", "sea wave")))
SPOKEN_ALIASES.update(_names("🍎", ("apple", "red apple")))
SPOKEN_ALIASES.update(_names("🍌", ("banana",)))
SPOKEN_ALIASES.update(_names("🍇", ("grapes",)))
SPOKEN_ALIASES.update(_names("🍓", ("strawberry",)))
SPOKEN_ALIASES.update(_names("🥑", ("avocado",)))
SPOKEN_ALIASES.update(_names("🥕", ("carrot",)))
SPOKEN_ALIASES.update(_names("🍞", ("bread",)))
SPOKEN_ALIASES.update(_names("🧀", ("cheese",)))
SPOKEN_ALIASES.update(_names("🍳", ("egg", "frying pan", "cooking")))
SPOKEN_ALIASES.update(_names("🍜", ("noodles", "steaming bowl")))
SPOKEN_ALIASES.update(_names("🍣", ("sushi",)))
SPOKEN_ALIASES.update(_names("🍦", ("ice cream",)))
SPOKEN_ALIASES.update(_names("🍩", ("donut", "doughnut")))
SPOKEN_ALIASES.update(_names("🍪", ("cookie",)))
SPOKEN_ALIASES.update(_names("🍫", ("chocolate",)))
SPOKEN_ALIASES.update(_names("🚗", ("car", "automobile")))
SPOKEN_ALIASES.update(_names("🚕", ("taxi",)))
SPOKEN_ALIASES.update(_names("🚌", ("bus",)))
SPOKEN_ALIASES.update(_names("🚲", ("bike", "bicycle")))
SPOKEN_ALIASES.update(_names("✈️", ("plane", "airplane", "aeroplane")))
SPOKEN_ALIASES.update(_names("🏠", ("house", "home")))
SPOKEN_ALIASES.update(_names("📱", ("phone", "mobile", "cell phone")))
SPOKEN_ALIASES.update(_names("💻", ("laptop", "computer")))
SPOKEN_ALIASES.update(_names("📷", ("camera",)))
SPOKEN_ALIASES.update(_names("🎥", ("movie camera", "video camera", "film camera")))
SPOKEN_ALIASES.update(_names("📺", ("tv", "television")))
SPOKEN_ALIASES.update(_names("📚", ("books", "stack of books")))
SPOKEN_ALIASES.update(_names("📖", ("open book", "book")))
SPOKEN_ALIASES.update(_names("💰", ("money bag", "money", "cash")))
SPOKEN_ALIASES.update(_names("💵", ("dollar", "banknote")))
SPOKEN_ALIASES.update(_names("💳", ("credit card", "card")))
SPOKEN_ALIASES.update(_names("📧", ("email", "e-mail", "envelope")))
SPOKEN_ALIASES.update(_names("📦", ("package", "parcel", "box")))
SPOKEN_ALIASES.update(_names("🛒", ("shopping cart", "trolley")))
SPOKEN_ALIASES.update(_names("⚽", ("soccer", "football", "soccer ball")))
SPOKEN_ALIASES.update(_names("🏀", ("basketball",)))
SPOKEN_ALIASES.update(_names("🎵", ("music", "musical note")))
SPOKEN_ALIASES.update(_names("🎶", ("music notes", "notes")))
SPOKEN_ALIASES.update(_names("🎤", ("microphone", "mic")))
SPOKEN_ALIASES.update(_names("🎧", ("headphones",)))
SPOKEN_ALIASES.update(_names("🎮", ("video game", "game controller", "controller")))
SPOKEN_ALIASES.update(_names("👻", ("ghost",)))
SPOKEN_ALIASES.update(_names("💀", ("skull",)))
SPOKEN_ALIASES.update(_names("💩", ("poop", "poo", "pile of poo")))
SPOKEN_ALIASES.update(_names("🤖", ("robot",)))
SPOKEN_ALIASES.update(_names("👽", ("alien",)))
SPOKEN_ALIASES.update(_names("👀", ("eyes",)))
SPOKEN_ALIASES.update(_names("🧠", ("brain",)))
SPOKEN_ALIASES.update(_names("💋", ("lips", "kiss mark")))
SPOKEN_ALIASES.update(_names("💤", ("zzz", "sleeping symbol")))
SPOKEN_ALIASES.update(_names("♻️", ("recycle", "recycling")))
SPOKEN_ALIASES.update(_names("🆕", ("new", "new button")))
SPOKEN_ALIASES.update(_names("🆓", ("free", "free button")))
SPOKEN_ALIASES.update(_names("🆙", ("up", "up button")))
SPOKEN_ALIASES.update(_names("🔴", ("red circle", "red dot")))
SPOKEN_ALIASES.update(_names("🟢", ("green circle", "green dot")))
SPOKEN_ALIASES.update(_names("🔵", ("blue circle", "blue dot")))
SPOKEN_ALIASES.update(_names("🟡", ("yellow circle", "yellow dot")))
SPOKEN_ALIASES.update(_names("⬛", ("black square",)))
SPOKEN_ALIASES.update(_names("⬜", ("white square",)))
SPOKEN_ALIASES.update(_names("🔶", ("orange diamond", "large orange diamond")))
SPOKEN_ALIASES.update(_names("🔷", ("blue diamond", "large blue diamond")))