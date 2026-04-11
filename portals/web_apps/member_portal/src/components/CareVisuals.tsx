export function HomeCareIllustration() {
  return (
    <div className="illustration-shell hero-visual" aria-hidden="true">
      <svg viewBox="0 0 520 360" role="img">
        <defs>
          <linearGradient id="heroBg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#effafd" />
            <stop offset="100%" stopColor="#dff4f5" />
          </linearGradient>
          <linearGradient id="heroAccent" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0e6771" />
            <stop offset="100%" stopColor="#15a4af" />
          </linearGradient>
        </defs>

        <rect x="18" y="18" width="484" height="324" rx="36" fill="url(#heroBg)" />
        <rect x="38" y="52" width="186" height="238" rx="28" fill="#ffffff" stroke="#d7eaef" />
        <rect x="58" y="78" width="146" height="20" rx="10" fill="#d7eef1" />
        <rect x="58" y="114" width="126" height="108" rx="22" fill="#e9f7fb" />
        <path d="M90 166 122 138l32 28v42H90z" fill="url(#heroAccent)" />
        <path d="M116 194h12v14h-12z" fill="#ffffff" />
        <rect x="58" y="238" width="146" height="14" rx="7" fill="#edf4f8" />
        <rect x="58" y="262" width="118" height="14" rx="7" fill="#edf4f8" />

        <rect x="250" y="64" width="222" height="112" rx="24" fill="#ffffff" stroke="#d7eaef" />
        <rect x="270" y="84" width="92" height="16" rx="8" fill="#103f57" opacity="0.92" />
        <rect x="270" y="114" width="64" height="52" rx="16" fill="#e7f5f7" />
        <rect x="346" y="114" width="106" height="12" rx="6" fill="#d8eaf0" />
        <rect x="346" y="136" width="86" height="12" rx="6" fill="#d8eaf0" />
        <rect x="346" y="158" width="74" height="12" rx="6" fill="#d8eaf0" />
        <circle cx="302" cy="140" r="16" fill="#18a4ad" />
        <path d="M296 140l5 5 9-11" fill="none" stroke="#ffffff" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />

        <rect x="264" y="196" width="118" height="108" rx="24" fill="#103f57" />
        <rect x="286" y="220" width="50" height="12" rx="6" fill="#8fe5e2" />
        <rect x="286" y="244" width="72" height="10" rx="5" fill="#2d5f75" />
        <rect x="286" y="262" width="60" height="10" rx="5" fill="#2d5f75" />
        <circle cx="334" cy="284" r="8" fill="#8fe5e2" />

        <rect x="396" y="202" width="86" height="94" rx="22" fill="#ffffff" stroke="#d7eaef" />
        <circle cx="439" cy="232" r="18" fill="#e2f4f5" />
        <path d="M439 222c5 0 9 4 9 9s-4 9-9 9-9-4-9-9 4-9 9-9Zm-18 40c3-10 13-16 24-16s21 6 24 16" fill="none" stroke="#18a4ad" strokeWidth="6" strokeLinecap="round" />
      </svg>
    </div>
  )
}

export function AuthCareIllustration({ title }: { title: string }) {
  return (
    <div className="illustration-shell auth-visual" aria-hidden="true">
      <svg viewBox="0 0 440 220" role="img">
        <defs>
          <linearGradient id="authBg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f2fbfc" />
            <stop offset="100%" stopColor="#ddf2f3" />
          </linearGradient>
          <linearGradient id="authAccent" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#115169" />
            <stop offset="100%" stopColor="#10a0a8" />
          </linearGradient>
        </defs>

        <rect x="14" y="14" width="412" height="192" rx="30" fill="url(#authBg)" />
        <rect x="38" y="38" width="150" height="144" rx="24" fill="#ffffff" stroke="#d7eaef" />
        <rect x="58" y="58" width="68" height="68" rx="20" fill="url(#authAccent)" />
        <path d="M79 95h26" stroke="#ffffff" strokeWidth="10" strokeLinecap="round" />
        <path d="M92 82v26" stroke="#ffffff" strokeWidth="10" strokeLinecap="round" />
        <rect x="58" y="140" width="108" height="12" rx="6" fill="#d7eaef" />
        <rect x="58" y="160" width="84" height="12" rx="6" fill="#d7eaef" />

        <rect x="210" y="44" width="182" height="56" rx="20" fill="#ffffff" stroke="#d7eaef" />
        <rect x="232" y="62" width="74" height="12" rx="6" fill="#103f57" />
        <rect x="316" y="62" width="54" height="12" rx="6" fill="#d8edf0" />

        <rect x="210" y="114" width="88" height="56" rx="20" fill="#103f57" />
        <rect x="228" y="132" width="42" height="10" rx="5" fill="#95ece5" />
        <rect x="228" y="148" width="30" height="10" rx="5" fill="#2f5f74" />

        <rect x="306" y="114" width="86" height="56" rx="20" fill="#ffffff" stroke="#d7eaef" />
        <circle cx="332" cy="142" r="11" fill="#dff4f5" />
        <rect x="350" y="126" width="22" height="10" rx="5" fill="#d8edf0" />
        <rect x="350" y="144" width="28" height="10" rx="5" fill="#d8edf0" />
      </svg>
      <p className="auth-visual-caption">{title}</p>
    </div>
  )
}
