import { Link } from "react-router-dom";

const LinkMail = ({ children }) => (
  <a
    href={`mailto:${children}`}
    className="font-medium text-blue-500 hover:text-blue-400 hover:underline"
  >
    {children}
  </a>
);

export const CookiePolicy = () => {
  return (
    <article className="space-y-8 text-[15px] leading-relaxed">
      <p className="text-sm text-gray-500">Dènye mizajou: Avril 2026</p>

      <header className="space-y-3">
        <h1 className="font-heading text-2xl font-bold tracking-tight text-gray-200 sm:text-3xl">
          Politik sou Kòki — KonekteGroup
        </h1>
        <p className="text-gray-400">
          Politik sa a eksplike ki jan nou itilize kòki ak teknoloji ki sanble (tankou localStorage
          oswa piksel) sou sit ak aplikasyon KonekteGroup yo. Li konplete{" "}
          <Link to="/legal/privacy" className="font-medium text-blue-500 hover:text-blue-400 hover:underline">
            Politik Konfidansyalite
          </Link>{" "}
          nou an.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">1. Sa ki se yon kòki</h2>
        <p>
          Yon kòki se yon ti fichye tèks ki plase sou aparèy ou lè w vizite yon sit. Li pèmèt sit la
          sonje preferans ou, kenbe sesyon ou louvri, oswa konprann ki jan moun itilize sèvis la.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">2. Ki tip kòki nou itilize</h2>
        <ul className="list-inside list-disc space-y-2 text-gray-400">
          <li>
            <span className="font-medium text-gray-300">Nesesè / fonksyonèl :</span> pou sekirite,
            otantifikasyon, ak fonksyone baz platfòm nan.
          </li>
          <li>
            <span className="font-medium text-gray-300">Preferans :</span> pou sonje chwa ou (lang,
            rejyon, paramèt entèfas).
          </li>
          <li>
            <span className="font-medium text-gray-300">Analiz (si aktive) :</span> pou mezire trafik
            epi amelyore pèfòmans ak eksperyans itilizatè.
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">3. Twazyèm pati</h2>
        <p>
          Kèk sèvis (pa egzanp rezo sosyal, analiz, oswa peman) ka mete pwòp kòki yo lè yo entegre
          nan platfòm nan. Nou envite w li politik yo sou sit patnè sa yo.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">4. Ki jan pou jere kòki yo</h2>
        <p>
          Ou ka bloke oswa efase kòki nan paramèt navigatè ou (Chrome, Firefox, Safari, elatriye).
          Si ou dezaktive kòki nesesè yo, kèk fonksyon (koneksyon, sesyon, sekirite) ka pa mache
          kòrèkteman.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">5. Chanjman politik sa a</h2>
        <p>
          Nou ka mete ajou politik kòki a pou reflete chanjman teknik oswa legal. Dat dènye mizajou a
          parèt anlè paj la.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">6. Kontakte nou</h2>
        <p>
          Pou kesyon sou kòki yo, ekri nou nan <LinkMail>contact@konektegroup.com</LinkMail>.
        </p>
      </section>
    </article>
  );
};
