import { Link } from "react-router-dom";

const LinkMail = ({ children }) => (
  <a
    href={`mailto:${children}`}
    className="font-medium text-blue-500 hover:text-blue-400 hover:underline"
  >
    {children}
  </a>
);

export const PrivacyPolicy = () => {
  return (
    <article className="space-y-8 text-[15px] leading-relaxed">
      <p className="text-sm text-gray-500">Dènye mizajou: Avril 2026</p>

      <header className="space-y-3">
        <h1 className="font-heading text-2xl font-bold tracking-tight text-gray-200 sm:text-3xl">
          Politik Konfidansyalite — KonekteGroup
        </h1>
        <p className="text-gray-400">
          Dokiman sa a eksplike ki jan KonekteGroup kolekte, itilize, pwoteje epi pataje enfòmasyon
          pèsonèl ou lè w itilize platfòm nou yo, ki gen ladann sèvis AI Recruiter nou an.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">1. Enfòmasyon nou kolekte</h2>
        <p>
          Nou ka kolekte non ou, adrès imèl ou, ak enfòmasyon pwofil rezo sosyal ou lè ou konekte oswa
          otorize aksè (pa egzanp Facebook, Instagram, TikTok, YouTube), ansanm ak done teknik
          nesesè pou fonksyone platfòm nan (jan navigatè, adrès IP, ak kòki).
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">2. Ki jan nou itilize enfòmasyon ou</h2>
        <p>
          Nou itilize done yo pou kominike avè w, amelyore sèvis nou yo, personalize eksperyans ou,
          epi prezante opòtinite ki gen rapò ak platfòm nan, toujou nan limit objektif legal yo.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">3. Pataj enfòmasyon</h2>
        <p>
          Nou pa vann done pèsonèl ou. Nou pa pataje yo ak twazyèm pati san konsantman ou eksepte
          si lalwa mande l oswa pou pwoteje dwa, sekirite, oswa entegrite KonekteGroup ak itilizatè
          lòt yo.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">4. Sekirite done</h2>
        <p>
          Nou aplike mezi sekirite rezonab (teknik ak òganizasyonèl) pou diminye risk aksè san
          otorizasyon, pèdi, oswa divilgasyon done ou. Okenn sistèm pa absoliman envènabl.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">5. Dwa ou yo</h2>
        <p>
          Selon kote ou ye a, ou ka gen dwa pou mande aksè, korije, efase, oswa limite trètman done
          ou. Pou nenpòt demann konsènan done pèsonèl ou, kontakte nou nan{" "}
          <LinkMail>contact@konektegroup.com</LinkMail>.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">6. Kòki (Cookies)</h2>
        <p>
          Nou itilize kòki ak teknoloji ki sanble pou fonksyone sit la, analiz trafik, epi sonje
          preferans ou. Pou detay konplè sou tip kòki yo, twazyèm pati, ak ki jan pou jere yo, gade{" "}
          <Link to="/legal/cookies" className="font-medium text-blue-500 hover:text-blue-400 hover:underline">
            Politik sou Kòki
          </Link>{" "}
          nou an.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">7. Kontakte nou</h2>
        <p>
          Pou kesyon sou politik sa a, ekri nou nan <LinkMail>contact@konektegroup.com</LinkMail>.
        </p>
      </section>
    </article>
  );
};
