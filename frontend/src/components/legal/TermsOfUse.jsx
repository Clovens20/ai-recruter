const LinkMail = ({ children }) => (
  <a
    href={`mailto:${children}`}
    className="font-medium text-blue-500 hover:text-blue-400 hover:underline"
  >
    {children}
  </a>
);

export const TermsOfUse = () => {
  return (
    <article className="mx-auto max-w-2xl space-y-8 text-center text-[15px] leading-relaxed sm:text-left">
      <p className="text-sm text-gray-500">Dènye mizajou: Avril 2026</p>

      <header className="space-y-3">
        <h1 className="font-heading text-2xl font-bold tracking-tight text-gray-200 sm:text-3xl">
          Kondisyon Itilizasyon — KonekteGroup
        </h1>
        <p className="text-gray-400">
          Lè w itilize platfòm KonekteGroup la, ou aksepte kondisyon ki anba yo. Si ou pa dakò ak
          yo, tanpri pa kontinye itilize sèvis la.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">1. Akseptasyon kondisyon yo</h2>
        <p>
          Lè w kreye yon kont, ou konekte, oswa ou itilize nenpòt pati platfòm nan, ou konfime ke
          ou li, ou konprann, epi ou aksepte kondisyon sa yo nan tout entegralite yo.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">2. Sèvis nou ofri</h2>
        <p>
          KonekteGroup ofri yon platfòm ki ede konekte fòmatè ak elèv, epi ki mete disponib yon ajans
          entèlijans atifisyèl pou sipòte aktivite rekritman, analiz pwofil, ak zouti ki gen rapò ak
          sèvis yo. Fonksyonalite espesifik yo ka varye selon pwodwi a ou itilize a.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">3. Konduit itilizatè</h2>
        <p>
          Ou angaje pa itilize platfòm nan pou aktivite ilegal, pou harcele lòt moun, pou kopye done
          san otorizasyon, oswa pou nenpòt konduit ki ka domaje KonekteGroup, itilizatè lòt yo, oswa
          twazyèm pati. Ou dwe respekte lalwa ak règleman ki aplikab yo.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">4. Pwopriyete entelektyèl</h2>
        <p>
          Tout logo, tèks, imaj, mak, kòd, ak lòt eleman vizyèl oswa teknik sou platfòm nan rete
          pwopriyete KonekteGroup oswa patnè ki bay licans yo, sof si yon lòt akò ekri di kontrè a.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">5. Limit responsablite</h2>
        <p>
          Sèvis la bay jan li ye a, san garanti espesifik ki depase sa lalwa pèmèt. KonekteGroup pa
          responsab pou domaj endirè, pèdi benefis, oswa enteripsyon sèvis ki soti nan itilizasyon
          oswa enkapasite pou itilize platfòm nan.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">6. Chanjman nan kondisyon yo</h2>
        <p>
          Nou rezève dwa pou modifye oswa mete ajou kondisyon sa yo nenpòt moman. Dat dènye mizajou
          ap toujou endike anlè paj la. Kontinye itilize platfòm nan apre yon chanjman vle di ou
          aksepte nouvo kondisyon yo.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-200">7. Kontakte nou</h2>
        <p>
          Pou kesyon sou kondisyon sa yo, ekri nou nan <LinkMail>contact@konektegroup.com</LinkMail>.
        </p>
      </section>
    </article>
  );
};
