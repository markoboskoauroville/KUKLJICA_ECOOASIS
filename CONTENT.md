# Uređivanje sadržaja

Stranica se ne uređuje ručno u HTML-u. Sav tekst i svi popisi žive u `content/`,
a `index.template.html` je samo kostur.

## Kroz admin panel

    https://kukljica-ecooasis.pages.dev/admin

Dva načina, oba vidljiva u istom panelu:

① **Jednostavno** — svih 179 tekstova sa stranice, hrvatski i engleski jedan do
drugog, grupirani po sekcijama. Ovdje se mijenja gotovo sve.

② **Napredno** — popisi i tablice: vrste, fenološki kalendar, faze projekta,
koraci rada, utjecaji. Redoslijed stupaca je važan, ne preimenuj šifre.

Spremanje radi commit na granu `cms`, GitHub Action gradi i objavljuje.
Živo za oko 90 sekundi.

## Ručno

    python3 tools/inject.py   # samo generira .build/index.html
    bash build.sh             # generira i složi dist/

`inject.py` namjerno puca ako nešto nedostaje, umjesto da objavi praznu stranicu.
Provjerava: nedostaje li koja datoteka, je li JSON ispravan, ponavlja li se šifra
u dvije datoteke, i postoji li svaka šifra iz predloška u oba jezika.

## Povratak na ranije stanje

Svaka izmjena je git commit. Povratak na bilo koje ranije stanje:

    git log --oneline content/
    git checkout <commit> -- content/
    git commit -m "Vraćeno na raniji sadržaj" && git push

## Pravila

- Šifre (`key`) se ne mijenjaju. One vežu tekst za mjesto na stranici.
- Mjeseci se pišu brojevima: "8. mjesec", nikad "kolovoz".
- Hrvatski se piše izvorno, nije prijevod engleskog.
- Slike idu u `img/`, panel ih sam sprema tamo.
