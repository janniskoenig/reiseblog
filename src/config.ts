// Zentrale Angaben für Impressum, Kontakt und Datenschutz.
export const betreiber = {
  name: 'Jannis König',
  strasse: 'Reinganumstraße 3',
  ort: '60385 Frankfurt am Main',
  // E-Mail wird nicht im Klartext ausgeliefert (Schutz vor Spam-Bots), siehe Email.astro
  emailNutzer: 'jannis.koenig',
  emailDomain: 'gmx.de',
};

// Web3Forms: Zugangsschlüssel (Access Key) von https://web3forms.com.
// Er ist laut Web3Forms öffentlich unbedenklich; er sorgt nur dafür, dass
// Nachrichten an deine Adresse gehen.
export const web3formsKey = '9de9e5c5-588b-4237-950b-c40f4b455ad3';

export const datenschutzStand = 'November 2026';

// Karten: Thunderforest (https://www.thunderforest.com). Kommerzielle Nutzung erlaubt,
// Gratis-Tarif 150.000 Kacheln pro Monat. Der Schlüssel ist im Seitenquelltext sichtbar,
// das ist bei Kartendiensten so vorgesehen. Gleicher Schlüssel steht in scripts/altavia-uebernehmen.py.
export const karte = {
  stil: 'landscape',
  schluessel: 'c4727ce21bbf4fbd8633df99582a9e88',
  trackFarbe: '#d9480f',
};
