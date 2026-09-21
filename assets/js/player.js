(function () {
  const tracks = Object.freeze([
    { artist: "21st Century", title: "Remember The Rain", id: "5PrnZCoC2hQ" },
    { artist: "311", title: "Champagne", id: "hALPmK93VDc" },
    { artist: "311", title: "Whiskey and Wine", id: "JBHXe3B_IeM" },
    { artist: "4 Non Blondes", title: "What's Up", id: "6NXnxTNIWkc" },
    { artist: "AC Slater", title: "Bass Inside", id: "6XJkPtxqWM8" },
    { artist: "Across the Universe (film)", title: "Happiness is a Warm Gun", id: "tTRO3cSFUcE" },
    { artist: "Adrian", title: "9pm in Osaka (Slowed)", id: "oMgo9OdLjW8" },
    { artist: "aftrthght", title: "temptations", id: "Y8vtbOqsP8c" },
    { artist: "AJR", title: "World's Smallest Violin", id: "PEnJbjBuxnw" },
    { artist: "Alan Mooney's Edits", title: "Kofi", id: "u17Sm6PZZhE" },
    { artist: "Andy McKee", title: "Everybody Wants To Rule The World (cover)", id: "FWsTPh1Us5E" },
    { artist: "Animal Collective", title: "Bees", id: "sxm2qTId7zg" },
    { artist: "Arlo Guthrie", title: "The Motorcycle Song (Studio Version)", id: "X4OKPMm-vfc" },
    { artist: "Assassin's Creed IV: Black Flag OST", title: "Leave Her Johnny", id: "nCtn6igpgP4" },
    { artist: "AWOLNATION", title: "Sail", id: "tgIqecROs5M" },
    { artist: "Bee Gees", title: "How Can You Mend A Broken Heart", id: "bpZuAtwDfag" },
    { artist: "Bee Gees", title: "How Deep Is Your Love", id: "XpqqjU7u5Yc" },
    { artist: "Bernard Herrmann", title: "Twisted Nerve", id: "S4QiCD_MZQk" },
    { artist: "Beyoncé", title: "Me, Myself And I", id: "4S37SGxZSMc" },
    { artist: "Big Jay McNeely", title: "There Is Something On Your Mind", id: "LpsM3IkbrfE" },
    { artist: "Bobby Womack", title: "If You Think You're Lonely Now", id: "IKH52rUZj9E" },
    { artist: "Boys Night Out", title: "Composing", id: "o3-nmaxLWXY" },
    { artist: "Brenton Wood", title: "I Like The Way You Love Me", id: "WSdOF1AtPLQ" },
    { artist: "Brenton Wood", title: "Me And You", id: "7mRo7xHs2o4" },
    { artist: "Brief Encounter", title: "Where Will I Go", id: "Vz9-8VslDco" },
    { artist: "Bright Eyes", title: "no lies, just love", id: "SwvWWF9l9E0" },
    { artist: "Bring Me The Horizon", title: "Can You Feel My Heart", id: "QJJYpsA5tv8" },
    { artist: "Brooks & Dunn", title: "Neon Moon", id: "AxFdeZER8Eg" },
    { artist: "Cage The Elephant", title: "Cigarette Daydreams", id: "opeETnB8m8w" },
    { artist: "Cage The Elephant", title: "Come A Little Closer", id: "KVYup3Qwh8Q" },
    { artist: "Chezile", title: "Beanie", id: "tERTBPdVivc" },
    { artist: "Chicano Batman", title: "Black Lipstick", id: "3sOXiL05VSY" },
    { artist: "Ciro Giovanni", title: "Casey's song en melódica", id: "O5qhR1S0IRQ" },
    { artist: "Clint Black", title: "Killin' Time", id: "BAm4nHFOir0" },
    { artist: "Coheed and Cambria", title: "Welcome Home", id: "n0H3RlaQVrM" },
    { artist: "Conway Twitty & Loretta Lynn", title: "After The Fire Is Gone", id: "0_epxhmTnyA" },
    { artist: "Cross Record", title: "High Rise", id: "qdPaNJ35CZo" },
    { artist: "CSGuitar89", title: "Ocarina of Time Title Theme on Guitar", id: "x2I1opYzSD0" },
    { artist: "CSGuitar89", title: "Song of Storms on Guitar", id: "vF_foxXkGMs" },
    { artist: "Dance Gavin Dance", title: "Uneasy Hearts Weigh the Most", id: "b0ZsV3Fzzoo" },
    { artist: "David Kushner", title: "Daylight", id: "MoN9ql6Yymw" },
    { artist: "Delegation", title: "Oh Honey", id: "p4vQ9fl5r9o" },
    { artist: "Delicate Steve", title: "I Can Fly Away", id: "4ldExQku59o" },
    { artist: "Dirty Heads", title: "Vacation", id: "7zok9co_8E4" },
    { artist: "Djo", title: "Charlie's Garden", id: "LyFpwF_m8-g" },
    { artist: "Earth, Wind & Fire", title: "That's the Way of the World", id: "QhW3P7_jvWY" },
    { artist: "Feist", title: "The Water", id: "tSCDxDMMBAA" },
    { artist: "FKJ", title: "Tadow", id: "hC8CH0Z3L54" },
    { artist: "FKJ", title: "Ylang Ylang", id: "EfgAd6iHApE" },
    { artist: "Frankie Valli", title: "Can't Take My Eyes Off You", id: "J36z7AnhvOM" },
    { artist: "Frankie Valli", title: "I Love You Baby", id: "XgvfOjifZl4" },
    { artist: "Galdive", title: "Teach Me How To Love", id: "vPNMI5WQH1o" },
    { artist: "George Strait", title: "Fool Hearted Memory", id: "T__Htin0Ai0" },
    { artist: "Gil Scott-Heron", title: "We Almost Lost Detroit", id: "cpNUqNe0U5g" },
    { artist: "Gitaroo Man OST", title: "The Legendary Theme (Acoustic)", id: "zacUcCCOoRw" },
    { artist: "Glass Animals", title: "Gooey", id: "WGIS8npb5GQ" },
    { artist: "Hal Walker", title: "Low Key Gliding (K08beatz remix)", id: "-in5bumZPZQ" },
    { artist: "Harry Styles", title: "As It Was", id: "H5v3kku4y6Q" },
    { artist: "Henry Mancini", title: "Lujon", id: "wC8FNDXgCnA" },
    { artist: "Herb Alpert", title: "Ladyfingers", id: "FNLf4Dhh-WA" },
    { artist: "Hiroshi Suzuki", title: "Romance", id: "BFmH7moCL2c" },
    { artist: "Incubus", title: "Aqueous Transmission", id: "3k0-sGqxIiQ" },
    { artist: "jades", title: "are you proud of me?", id: "m66I6og5uws" },
    { artist: "Jfarrari", title: "The Unknowing", id: "uThdFoa3sNY" },
    { artist: "Jordan D Piano", title: "Guts' Theme on public piano at the LAX airport", id: "XJfUidN-FMI" },
    { artist: "Joy Division", title: "Transmission", id: "FnWPGSQjFUc" },
    { artist: "Just Jack", title: "Writer's Block", id: "16fBF3Bgd3M" },
    { artist: "Kanye West", title: "Everything I Am", id: "ZtkNfC5Oymw" },
    { artist: "Kanye West", title: "Violent Crimes", id: "DSY7u8Jg9c0" },
    { artist: "Keith Whitley", title: "Miami, My Amy", id: "ka_lJGRGPs8" },
    { artist: "Keyshia Cole", title: "Love", id: "ETpU0obvKrY" },
    { artist: "Kfir Ochaion", title: "Careless Whisper (Metal Ballad Guitar Cover)", id: "yMVBOIYf63Y" },
    { artist: "Khruangbin", title: "Christmas Time Is Here", id: "V4iWO73zPL4" },
    { artist: "LMC", title: "Let Go", id: "JdMs5k3VnaA" },
    { artist: "Lola Young", title: "Messy (live for Like A Version)", id: "h6nVOfThks4" },
    { artist: "Lukas Graham", title: "7 Years", id: "HGGYTg_Y_GA" },
    { artist: "M83", title: "Solitude (Felsmann + Tiley Reinterpretation)", id: "_p2NvO6KrBs" },
    { artist: "Mac DeMarco", title: "Brother (Lollapalooza Chile 2018)", id: "LHH3dfhONzk" },
    { artist: "Macintosh Plus", title: "FLORAL SHOPPE - 02 リサフランク420", id: "bAgmGZ9iQ2Y" },
    { artist: "MAPHRA", title: "Doomed (MAPHRA Vocal Cover)", id: "r6L-GUOAhGo" },
    { artist: "Marlon Funaki", title: "Murphy's Law", id: "JxNbaBiYnJ0" },
    { artist: "Marlon Funaki", title: "when sunday comes around", id: "5nI1oO4B4ok" },
    { artist: "Massive Attack", title: "Teardrop", id: "u7K72X4eo_s" },
    { artist: "Max Backman", title: "Guts theme from Berserk (Guitar cover)", id: "EJLNLWv-nmM" },
    { artist: "Minus the Bear", title: "Pachuca Sunrise", id: "hM_-L4tOQkg" },
    { artist: "My Chemical Romance", title: "Helena", id: "7SM5laxokpg" },
    { artist: "My Chemical Romance", title: "Teenagers", id: "pBqhUarhaAU" },
    { artist: "My Morning Jacket", title: "Wordless Chorus", id: "5OMpaFvTOFk" },
    { artist: "Nathan Evans", title: "Wellerman (Sea Shanty)", id: "qP-7GNoDJ5c" },
    { artist: "Neil Young", title: "Old Man", id: "An2a1_Do_fc" },
    { artist: "Night Verses", title: "Rose Wire", id: "nKyB8nnlWns" },
    { artist: "Oasis", title: "Champagne Supernova", id: "tI-5uv4wryI" },
    { artist: "Oasis", title: "Don't Look Back In Anger", id: "cmpRLQZkTb8" },
    { artist: "Oliver Tree & Robin Schulz", title: "Miss You", id: "BX0lKSa_PTk" },
    { artist: "OMA", title: "C.R.E.A.M. (Wu-Tang Clan Cover Live)", id: "CnpXMVXWhNk" },
    { artist: "Orgōne", title: "Be Thankful For What You Got (Live)", id: "HbygM0kNo_A" },
    { artist: "otuka", title: "skin", id: "mj9av_hGxPc" },
    { artist: "otuka", title: "still save a seat for you", id: "S4D89Z3DXNU" },
    { artist: "Paloma Faith", title: "Only Love Can Hurt Like This", id: "PaKr9gWqwl4" },
    { artist: "Pete Wingfield", title: "18 With A Bullet", id: "To4T8hLE0ow" },
    { artist: "Phosphorescent", title: "Wolves", id: "jH3C8FyHsIk" },
    { artist: "Pink Floyd", title: "Wish You Were Here", id: "IXdNnw99-Ic" },
    { artist: "Polyphia", title: "Playing God", id: "Z5NoQg8LdDk" },
    { artist: "Portishead", title: "Glory Box", id: "4qQyUi4zfDs" },
    { artist: "re6ce", title: "brown eyes* (feat. riovaz)", id: "PntQqVjfRLc" },
    { artist: "Reba McEntire", title: "Does He Love You ft. Linda Davis", id: "FUP9DnurODw" },
    { artist: "Red Village", title: "Feel Good (1950's Motown Soul Cover)", id: "YdbIoI6PYDU" },
    { artist: "Righteous", title: "Mo Beats (Pepe Animations)", id: "vVkfxIlZFY0" },
    { artist: "Ritchie Valens", title: "Sleepwalk", id: "_msjKl1nkqg" },
    { artist: "Royel Otis", title: "Linger (The Cranberries Cover) [Live @ SiriusXM]", id: "JGUVB19e13s" },
    { artist: "Ryan Celsius Sounds", title: "ＢＩＴＴＥＲＷＥＳＴ", id: "2WAAF-si16g" },
    { artist: "Saiko", title: "Big Apple", id: "WNe2N72xiaY" },
    { artist: "Say Anything", title: "Alive With The Glory Of Love", id: "PFR5s96jGeg" },
    { artist: "Show Me The Body", title: "metallic taste (only lovers left alive)", id: "AhgLsxVThUU" },
    { artist: "Silversun Pickups", title: "Lazy Eye", id: "DYd57rkvnpQ" },
    { artist: "Simple Minds", title: "Don't You (Forget About Me)", id: "CdqoNKCCt7A" },
    { artist: "Skinshape", title: "I Didn't Know", id: "ulOgzjdBdzY" },
    { artist: "Sleepy Tom", title: "Pusher feat. Anna Lunoe", id: "jQo_iamn4ik" },
    { artist: "Steve Baker & Carmen Dave", title: "For Whom The Bell Tolls (Donnie Darko OST)", id: "hwmTCIHPRsM" },
    { artist: "Stevie Ray Vaughan", title: "Voodoo Child (Slight Return)", id: "nuI5YPaZXIQ" },
    { artist: "Superheaven", title: "Youngest Daughter", id: "VMk6i7Q0k54" },
    { artist: "Tame Impala", title: "The Less I Know The Better", id: "2SUwOgmvzK4" },
    { artist: "Tears For Fears", title: "Everybody Wants To Rule The World", id: "znDgBy2mHbc" },
    { artist: "Tears For Fears", title: "Head Over Heels", id: "CsHiG-43Fzg" },
    { artist: "The Bravery", title: "An Honest Mistake", id: "O8vzbezVru4" },
    { artist: "The Delfonics", title: "La-La Means I Love You", id: "VlDHi1O2yfs" },
    { artist: "The Drums", title: "Money", id: "IqYgNiZdfh4" },
    { artist: "The Fall of Troy", title: "F.C.P.R.E.M.I.X.", id: "2iijmj5nB6I" },
    { artist: "The Isley Brothers", title: "That Lady, Pts. 1 & 2", id: "S1Mvy3E8P2U" },
    { artist: "The Judds", title: "Grandpa (Tell Me 'Bout The Good Old Days)", id: "cmzd_Xa_2Cc" },
    { artist: "The Neighbourhood", title: "Sweater Weather", id: "GCdwKhTtNNw" },
    { artist: "The Rare Occasions", title: "Notion (Slowed + Reverb)", id: "980aWt3XRCw" },
    { artist: "The Smiths", title: "How Soon Is Now?", id: "hnpILIIo9ek" },
    { artist: "The Velvet Underground", title: "Pale Blue Eyes", id: "KisHhIRihMY" },
    { artist: "The xx", title: "Teardrops", id: "Veoon_N0zuA" },
    { artist: "Thee Sacred Souls", title: "Will I See You Again?", id: "IGgb10A_2c8" },
    { artist: "ThxSoMch", title: "Crumbled", id: "IpBMEFhPEz8" },
    { artist: "Title Fight", title: "Head In The Ceiling Fan", id: "Tu9KgGqXDyw" },
    { artist: "TOOL", title: "Schism", id: "MM62wjLrgmA" },
    { artist: "Top Viral Song", title: "after dark x sweater weather (slowed + reverb)", id: "aZ9B9kY25AQ" },
    { artist: "Tracy Lawrence", title: "Time Marches On", id: "mtgbjdeJgus" },
    { artist: "twenty one pilots", title: "Ride", id: "Pw-0pbY9JeU" },
    { artist: "twenty one pilots", title: "Stressed Out", id: "pXRviuL6vMY" },
    { artist: "TWISTED", title: "WORTH NOTHING (ft. Oliver Tree)", id: "neOQ8s60sHU" },
    { artist: "Tyler Childers", title: "All Your'n (Recorded Live for World Cafe)", id: "ClwLjiyJjQU" },
    { artist: "Tyler, The Creator", title: "SEE YOU AGAIN featuring Kali Uchis", id: "TGgcC5xg9YI" },
    { artist: "VACATIONS", title: "Away", id: "xQc67IKNNYk" },
    { artist: "VACATIONS", title: "Telephones", id: "y7B6Z-_-Bcc" },
    { artist: "VACATIONS", title: "Vibes & Days", id: "2C17yLNe-wo" },
    { artist: "Vincent Moretto", title: "Guts Theme (METAL REMIX)", id: "NrIy0nxbNpc" },
    { artist: "YAD Oud", title: "Guts Theme (The Arabic Version/Rendition)", id: "JAU4xPxop4A" },
    { artist: "Yeah Yeah Yeahs", title: "Warrior (Album Version)", id: "EyHx3HNCHjw" },
    { artist: "Yellow Days", title: "A Little While", id: "7OopD1mdbL8" },
    { artist: "Yellow Days", title: "Slow Dance & Romance", id: "jJHjM3R55gk" },
    { artist: "Yoko Kanno", title: "Green Bird", id: "EL7e5XrzanA" },
    { artist: "yungmaple", title: "TRUST NO MAN", id: "M7Yxj0O2Gos" },
    { artist: "Yuri Wong", title: "I'm Your Huckleberry (Lofi Remix)", id: "YGMasdzlJ9A" },
  ]);

  const ORIGIN = "https://www.youtube-nocookie.com";
  const box = document.querySelector("[data-player]");
  if (!box) return;
  const list = tracks.filter((t) => /^[A-Za-z0-9_-]{11}$/.test(t.id));
  if (list.length === 0) return;
  const details = box.closest("details");

  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    e.className = cls;
    if (text) e.textContent = text;
    return e;
  };
  const btn = (cls, text) => {
    const b = el("button", cls, text);
    b.type = "button";
    return b;
  };

  const rowsBox = el("div", "player-list");
  const rows = list.map((t, i) => {
    const b = btn("player-row", t.artist + " - " + t.title);
    b.tabIndex = -1;
    b.addEventListener("click", () => { select(i); if (frame) load(); else play(); });
    rowsBox.append(b);
    return b;
  });
  const back = btn("", "back");
  const playBtn = btn("", "play");
  const next = btn("", "next");
  const status = el("span", "player-status");
  const ctl = el("div", "player-ctl");
  ctl.append(back, playBtn, next, status);
  const left = el("div", "player-left");
  left.append(rowsBox, ctl);
  const slot = el("div", "player-slot", "press play");
  box.replaceChildren(left, slot);

  let idx = 0;
  let frame = null;
  let playing = false;
  let errs = 0;

  const label = () => list[idx].artist + " - " + list[idx].title;

  function select(i) {
    rows[idx].classList.remove("on");
    idx = (i + list.length) % list.length;
    rows[idx].classList.add("on");
    rows[idx].scrollIntoView({ block: "nearest" });
    if (frame) frame.title = "Now playing: " + label();
    status.textContent = "";
  }

  function cmd(func, args) {
    if (!frame) return;
    frame.contentWindow.postMessage(JSON.stringify({ event: "command", func, args: args || [] }), ORIGIN);
  }

  function play() {
    if (frame) { cmd(playing ? "pauseVideo" : "playVideo"); return; }
    // built from the validated id and fixed parameters only
    const q = new URLSearchParams({
      enablejsapi: "1", origin: location.origin, autoplay: "1", rel: "0", playsinline: "1",
    });
    frame = document.createElement("iframe");
    frame.src = ORIGIN + "/embed/" + list[idx].id + "?" + q;
    frame.title = "Now playing: " + label();
    frame.setAttribute("sandbox", "allow-scripts allow-same-origin allow-presentation");
    frame.setAttribute("allow", "autoplay; encrypted-media");
    frame.referrerPolicy = "strict-origin-when-cross-origin";
    // ask the player to send state and error events
    frame.addEventListener("load", () => {
      frame.contentWindow.postMessage(JSON.stringify({ event: "listening", id: 1, channel: "widget" }), ORIGIN);
    });
    slot.replaceChildren(frame);
  }

  function load() {
    cmd("loadVideoById", [list[idx].id]);
    playing = false;
  }

  function stop() {
    if (!frame) return;
    frame.remove();
    frame = null;
    playing = false;
    playBtn.textContent = "play";
    slot.replaceChildren("press play");
  }

  window.addEventListener("message", (e) => {
    if (!frame || e.origin !== ORIGIN || e.source !== frame.contentWindow) return;
    let m;
    try { m = JSON.parse(e.data); } catch { return; }
    if (!m || typeof m !== "object") return;
    if (m.event === "onStateChange") {
      playing = m.info === 1;
      playBtn.textContent = playing ? "pause" : "play";
      if (playing) errs = 0;
      if (m.info === 0) { select(idx + 1); load(); }
    } else if (m.event === "onError") {
      rows[idx].classList.add("dead");
      errs += 1;
      if (errs >= 2) { status.textContent = "could not play"; playing = false; playBtn.textContent = "play"; return; }
      select(idx + 1);
      load();
    }
  });

  // one tab stop for the whole list; arrows move, enter plays
  rowsBox.tabIndex = 0;
  rowsBox.setAttribute("aria-label", "Tracks. Arrow keys choose, Enter plays.");
  rowsBox.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") select(idx + 1);
    else if (e.key === "ArrowUp") select(idx - 1);
    else if (e.key === "Enter") { if (frame) load(); else play(); }
    else return;
    e.preventDefault();
    if (frame && e.key !== "Enter") load();
  });
  back.addEventListener("click", () => { select(idx - 1); if (frame) load(); });
  next.addEventListener("click", () => { select(idx + 1); if (frame) load(); });
  playBtn.addEventListener("click", play);
  // a hidden player is not allowed to keep playing, so closing tears it down
  details.addEventListener("toggle", () => { if (!details.open) stop(); });

  rows[0].classList.add("on");
})();
