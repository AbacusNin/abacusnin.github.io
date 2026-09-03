(function () {
  const quotes = Object.freeze([
    { text: "Juice is Temporary, Sauce is Forever.", by: "Best Buy Employee" },
    { text: "Character is destiny.", by: "Heraclitus" },
    { text: "Waste no more time arguing what a good man should be. Be one.", by: "Marcus Aurelius, Meditations" },
    { text: "The standard you walk past is the standard you accept.", by: "David Morrison" },
    { text: "Excellence is not an act, but a habit.", by: "Will Durant" },
    { text: "Knowing yourself is the beginning of all wisdom.", by: "Aristotle" },
    { text: "All I know is that I know nothing.", by: "Socrates" },
    { text: "Earned, not given.", by: "" },
    { text: "Death Before Dishonor.", by: "Marine Corps saying" },
    { text: "There's good and evil in each individual's fire, identifies needs and feeds our desires.", by: "Atmosphere, \"Woman with the Tattooed Hands\"" },
    { text: "To secure peace, is to prepare for war.", by: "Metallica" },
    { text: "Speak softly and carry a big stick.", by: "Theodore Roosevelt" },
    { text: "Discipline equals freedom.", by: "Jocko Willink" },
    { text: "It is better to be a warrior in a garden than a gardener in a war.", by: "" },
    { text: "The way of the samurai is found in death.", by: "Yamamoto Tsunetomo, Hagakure" },
    { text: "Improvise. Adapt. Overcome.", by: "USMC ethos" },
    { text: "Slow is smooth, smooth is fast.", by: "shooter's maxim" },
    { text: "Fall seven times, stand up eight.", by: "Japanese proverb" },
    { text: "Everybody has a plan until they get punched in the mouth.", by: "Mike Tyson" },
    { text: "Courage is not the absence of fear, but the triumph over it.", by: "Nelson Mandela" },
    { text: "The best revenge is not to be like your enemy.", by: "Marcus Aurelius, Meditations" },
    { text: "Whoever fights monsters should see that he does not become one.", by: "Friedrich Nietzsche, Beyond Good and Evil" },
    { text: "A lion does not concern himself with the opinions of sheep.", by: "Tywin Lannister" },
    { text: "Well done is better than well said.", by: "Benjamin Franklin" },
    { text: "No man is free who is not master of himself.", by: "Epictetus" },
    { text: "Everyone thinks of changing the world, but no one thinks of changing himself.", by: "Leo Tolstoy" },
    { text: "Hard work beats talent when talent doesn't work hard.", by: "Tim Notke" },
    { text: "The quality of your life is determined by the quality of your thoughts.", by: "Marcus Aurelius" },
    { text: "If you want to buy something without looking at the price tag, you have to be able to work without looking at the clock.", by: "Alex Hormozi" },
    { text: "Hell is other people.", by: "Jean-Paul Sartre, No Exit" },
    { text: "Not everything is a lesson, Ryan. Sometimes you just fail.", by: "Dwight, The Office" },
    { text: "The treasure you seek is in the cave you fear to enter.", by: "Joseph Campbell" },
    { text: "What stands in the way becomes the way.", by: "Marcus Aurelius, Meditations" },
    { text: "Become who you are.", by: "Friedrich Nietzsche" },
    { text: "The privilege of a lifetime is to become who you truly are.", by: "Carl Jung" },
    { text: "My formula for greatness in a man is amor fati - love of fate.", by: "Friedrich Nietzsche, Ecce Homo" },
    { text: "What is to give light must endure burning.", by: "Viktor Frankl" },
    { text: "He who has a why to live can bear almost any how.", by: "Friedrich Nietzsche" },
    { text: "If a man does not know to which port he sails, no wind is favorable.", by: "Seneca, Letters" },
    { text: "A man's worth is measured by the worth of what he values.", by: "Marcus Aurelius, Meditations" },
    { text: "You must have chaos within you to give birth to a dancing star.", by: "Friedrich Nietzsche, Thus Spoke Zarathustra" },
    { text: "I would rather be ashes than dust.", by: "Jack London" },
    { text: "The two most important days are the day you're born and the day you find out why.", by: "Mark Twain" },
    { text: "If you don't take risks, you can't create a future.", by: "Monkey D. Luffy, One Piece" },
    { text: "A lesson without pain is meaningless.", by: "Edward Elric, Fullmetal Alchemist" },
    { text: "In the end, we only regret the chances we didn't take.", by: "" },
    { text: "Hard choices, easy life. Easy choices, hard life.", by: "Jerzy Gregorek" },
    { text: "A ship in harbor is safe, but that is not what ships are built for.", by: "John A. Shedd" },
    { text: "Stay hungry, stay foolish.", by: "Whole Earth Catalog/Steve Jobs" },
    { text: "Fortune Favors The Bold.", by: "" },
    { text: "Nothing Ventured, Nothing Gained.", by: "" },
    { text: "Who Dares, Wins.", by: "SAS" },
    { text: "What disgrace it is for a man to grow old without ever seeing the beauty and strength of which his body is capable.", by: "Socrates" },
    { text: "You're going to be alright. You just stumbled over a stone in the road, it means nothing. Your goal lies far beyond this, doesn't it? I'm sure you'll overcome this. You'll walk again... soon.", by: "Guts to Griffith, Berserk" },
    { text: "You can still be who you wish you is, it ain't happen yet and that's what intuition is", by: "Kanye West, \"I Wonder\"" },
    { text: "I've been waiting on this my whole life", by: "Kanye West, \"I Wonder\"" },
    { text: "The flow of time is always cruel... Its speed seems different for each person, but no one can change it... A thing that doesn't change with time is a memory of younger days.", by: "Sheik, Ocarina of Time" },
    { text: "Whenever there is a meeting, a parting is sure to follow. However, that parting need not last forever... Whether a parting is forever or merely for a short time... That is up to you.", by: "Happy Mask Salesman, Majora's Mask" },
    { text: "Nostalgia is the pain of loss experienced as pleasurable memory.", by: "Raymond Reddington" },
    { text: "No man ever steps in the same river twice.", by: "Heraclitus" },
    { text: "Confine yourself to the present.", by: "Marcus Aurelius, Meditations" },
    { text: "Loss is nothing but change, and change is Nature's delight.", by: "Marcus Aurelius, Meditations" },
    { text: "Time is a river of passing events, and strong is its current.", by: "Marcus Aurelius, Meditations" },
    { text: "You could leave life right now - let that determine what you do.", by: "Marcus Aurelius, Meditations" },
    { text: "We suffer more in imagination than in reality.", by: "Seneca" },
    { text: "Life can only be understood backwards; but it must be lived forwards.", by: "Søren Kierkegaard" },
    { text: "This too shall pass.", by: "Persian adage" },
    { text: "Memento mori.", by: "Stoic maxim" },
    { text: "Empty your mind, be formless. Shapeless, like water. If you put water into a cup, it becomes the cup. You put water into a bottle and it becomes the bottle. You put it in a teapot, it becomes the teapot. Now, water can flow or it can crash. Be water, my friend.", by: "Bruce Lee" },
    { text: "Water shapes its course according to the ground.", by: "Sun Tzu, The Art of War" },
    { text: "The soft overcomes the hard.", by: "Tao Te Ching" },
    { text: "Everything flows.", by: "Heraclitus" },
    { text: "Think lightly of yourself and deeply of the world.", by: "Miyamoto Musashi, Dokkodo" },
    { text: "The only way to make sense out of change is to plunge into it.", by: "Alan Watts" },
    { text: "Muddy water is best cleared by leaving it alone.", by: "Alan Watts" },
    { text: "To a mind that is still, the whole universe surrenders.", by: "Zhuangzi" },
    { text: "When the winds of change blow, some build walls, others build windmills.", by: "Chinese proverb" },
    { text: "What you seek is seeking you.", by: "Rumi" },
    { text: "The wound is the place where the Light enters you.", by: "Rumi" },
    { text: "No man is an island.", by: "John Donne" },
    { text: "If they sleepin on you, tuck 'em in", by: "" },
  ]);

  const box = document.querySelector("[data-ticker]");
  if (!box || quotes.length === 0) return;

  // long list, so each visit starts somewhere different
  const start = Math.floor(Math.random() * quotes.length);
  const order = quotes.slice(start).concat(quotes.slice(0, start));

  const fill = (s, q) => {
    s.replaceChildren(q.text);
    if (q.by) {
      const b = document.createElement("span");
      b.className = "ticker-by";
      b.textContent = q.by;
      s.append(" - ", b);
    }
  };
  const item = (q) => {
    const s = document.createElement("span");
    s.className = "ticker-item";
    fill(s, q);
    return s;
  };

  const track = document.createElement("div");
  track.className = "ticker-track";
  box.append(track);
  box.hidden = false;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    box.classList.add("still");
    order.forEach((q) => track.append(item(q)));
    const items = Array.from(track.children);
    let i = 0;
    items[0].classList.add("on");
    if (items.length < 2) return;
    setInterval(() => {
      items[i].classList.remove("on");
      i = (i + 1) % items.length;
      items[i].classList.add("on");
    }, 10000);
    return;
  }

  // the whole list in one layer gets very wide and browsers stutter moving it,
  // so keep only enough spans to cover the strip twice and recycle them
  box.classList.add("run");
  let next = 0;
  const take = () => order[next++ % order.length];

  const speed = 60;
  let pos = 0;
  let last = 0;
  const step = (now) => {
    // top up here rather than once at load, so a resize never opens a gap
    while (track.scrollWidth + pos < box.clientWidth * 2 && track.children.length < 100) {
      track.append(item(take()));
    }
    if (last && !box.matches(":hover, :focus, :focus-within")) {
      // clamp so a tab left in the background does not jump on return
      pos -= Math.min(now - last, 100) * speed / 1000;
      let first = track.firstElementChild;
      while (first && first.offsetWidth && -pos >= first.offsetWidth) {
        pos += first.offsetWidth;
        fill(first, take());
        track.append(first);
        first = track.firstElementChild;
      }
      track.style.transform = "translateX(" + pos + "px)";
    }
    last = now;
    requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
})();
