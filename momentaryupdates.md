
## 6.10.2026, 10:40

> wells on site In Kuklitsa Eco Oasis, increase the number to 1. My father told me there is a spring somewhere. I still didn't locate it, but put 1 so it looks promising.

1. The wells figure shows 1: the spring his father knows of, not yet located; the water texts no longer say "no spring". **Status:** done.

## 6.10.2026, 12:30 (from the Green and Go request of 09:25)

2. His own bunja photos (Google Photos album "Brac-5/27/14", 27.5.2014, not copyrighted) in the bunja section, and Green and Go as a child project. **Status:** done, v3: "Prave bunje, Brač, svibanj 2014." with six photos and captions in HR and EN, after the six visualisations; a section "Projekt izdanak: Green and Go Croatian Islands" before the phases, with the solar bunja and a link.

## 12.10.2026 (Three crops app)

> A fun project for Eco Oasis. Next to the section, you need to link— also build a web app. So we have a section of growing food. We have 3 kinds of crops. One is cereal, second is whatever is second, protein or something, and third one is oil. So you read the principles of 3 components of food for humans. which is the basic of calories, and then vegetable came on top. And the function of the app is to choose 3, 3 groups of food with assistance. So for example, I can choose rice as cereal, and then for other 2, the applications give me multiple options like a tree. And then when I select second one, I have a Third one, uh, options. So basically, as I'm selecting, I'm narrowing the options until I find the right 3 combinations. And there will be a map of climates and list of climates. And when user choose a climate, it will be highlighted in the map. And also, if the user click on the map, it will tell where this climate exists. And then this, the source of food will be reduced to the ones which can grow there without any special modifications. So let's make this 3 crops chooser, advisor, educator, etc.

3. "Three crops" web app at `tri/`, linked from the Growing food section. **Status:** done, v4: the principle (cereal, pulse, oil, vegetables on top); a Köppen-Geiger world map (click a place: its climate, country, and where else on Earth that climate exists) and a list of 31 climates that filter the crops; a three-column chooser of 42 crops that narrows like a tree (each branch shows how many options remain); the result shows where the triad grows on rain alone, whether it fits Kukljica, a 2000 kcal day in grams, and 16 traditional triads (Dalmatian wheat, fava, olive first). EN and HR, day and night.

## 15.10.2026 (Owner's manual)

> Please make a new section. This is all public data inside my Google Site Oasis called the Owner's Manual, which is statistical view of the owners of the land inside the parcel I marked for my project. We need to see who to contact to buy the land, but right now make like who owns which parcel. and who is the owner of most of the parcels and make different statistical analysis of parcels, their sizes and owners. So it's easy for my lawyer to make a plan to purchase all these parcels for my NGO.

4. "Owner's manual" section (`#owners`, after The land, in the nav as Owners) built from the parcel map data: 40 private parcels, 3,75 ha, 15 possession sheets, 29 people. A map shaded by number of sheets per parcel (tap a parcel or a holder to light up everything they hold), a ranking by sheet, person and family, size and fragmentation statistics, a purchase plan ordered by area with notes for the lawyer (holders abroad, off-book shares, unknown shares, shared parcels) and next steps, and a searchable, sortable register with CSV download. Municipal land listed separately. **Status:** done, v5.

## 15.10.2026 (map by family)

> Please also make a map and color code each parcel according to the owner so we can see to which family each part belongs. So the— yes, that's it. Make a map, visual representation.

5. The Owner's manual map opens "By family": eight families, one colour each (Vojvodić, Bačić, Martinović / Boško, Ninčević r. Kajica, Kaica, Morović, Gobić, Bosotina), family names written on the map, parcels shared by several families striped in their colours in proportion to their shares, the part not covered by an attached sheet in grey. The legend lists each family's sheets, people, m², share and parcels; tapping a family lights up its land. "By number of sellers" is still one tap away. The ARKOD layer app was not used: it is not in the repository and an Android emulator cannot run here. **Status:** done, v6.

## 15.10.2026 (live cadastre and land register, from the ARKOD Layer app)

> https://github.com/markoboskoauroville/arkod_web https://github.com/markoboskoauroville/mantra_arkod

6. The Owner's manual now reads the state's records the way the ARKOD Layer app does (OSS, oss.uredjenazemlja.hr), fetched 15. 10. 2026, instead of the 2014 sheets: current possession sheets with shares and land use for all 40 parcels (the gaps are closed: PL 405, 410 and 150 found; the core parcels now have their shares), and the 21 land-register folios. A new part "Land register" and a third map view show that only 2456/2 is registered to the people who hold it; on 33 parcels the land register names other people (older generations, the Zaklada Soppe Fortezza on folio 55, the Republic of Croatia for 2450 and 2445/7). Purchase plan and steps rewritten for that. Agreed with him: the page carries names and shares only; addresses, fathers' and maiden names are in `.secret/oss_detail.json`, not published. **Status:** done, v7.

## 15.10.2026 (refresh, the gap, private PDF)

> Please also make in owner's manual refreshment. So if I check refresh, maybe cadaster has changed or owner's manual changed, owner's data changed. So app is live and can fetch new data if something has changed. It will update the page itself. Give me a PDF with the analysis of the owners with all this private data only for me. Nothing goes public. Create PDF.
> Why this part is empty? There is nothing. Who owns this partcel

7. The gap was 2454/1 (3 377 m², PL 150 Fabian Srećko Kaica, folio 55), in the field map but never on the list. Every parcel whose edge runs mostly along the project is now counted, marked "inside the area": ten parcels, 9 327 m² (six of them PL 150, and 2448/5 is PL 442). **Status:** done, v8.
8. "Check the cadastre now" button, a Pages Function proxy that passes names and shares only, and a daily workflow that commits and deploys when the records change. **Status:** done, v8; the button and the morning check need the site on Cloudflare (the deploy secrets).
9. Private PDF with addresses, fathers' and maiden names, burdens: made in `.secret/`, sent to him in the session, never committed. **Status:** done.
