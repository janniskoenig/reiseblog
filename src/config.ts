// Zentrale Angaben für Impressum, Kontakt und Datenschutz.
export const betreiber = {
  name: 'Jannis König',
  strasse: 'Reinganumstraße 3',
  ort: '60385 Frankfurt am Main',
  // E-Mail wird nicht im Klartext ausgeliefert (Schutz vor Spam-Bots), siehe Email.astro
  emailNutzer: 'jannis.koenig',
  emailDomain: 'gmx.de',
};

// Formspree: Auf https://formspree.io ein Konto anlegen, ein Formular erstellen
// und dessen ID eintragen (der Teil nach /f/ in der Adresse, z. B. 'xyzabcd').
// Die ID ist öffentlich unbedenklich, sie steht ohnehin im Seitenquelltext.
export const formspreeId = 'HIER-FORMULAR-ID-EINTRAGEN';

export const datenschutzStand = 'November 2026';
