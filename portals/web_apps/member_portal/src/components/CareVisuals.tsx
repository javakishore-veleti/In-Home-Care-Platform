export function HomeCareIllustration() {
  return (
    <div className="illustration-shell hero-visual" aria-hidden="true">
      <svg viewBox="0 0 520 360" role="img">
        <defs>
          <linearGradient id="heroBg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f7f2e8" />
            <stop offset="100%" stopColor="#e8f0e2" />
          </linearGradient>
          <linearGradient id="heroAccent" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#607a4d" />
            <stop offset="100%" stopColor="#8ca86e" />
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
        <rect x="270" y="84" width="92" height="16" rx="8" fill="#4f6640" opacity="0.92" />
        <rect x="270" y="114" width="64" height="52" rx="16" fill="#eef4e8" />
        <rect x="346" y="114" width="106" height="12" rx="6" fill="#e2ead9" />
        <rect x="346" y="136" width="86" height="12" rx="6" fill="#e2ead9" />
        <rect x="346" y="158" width="74" height="12" rx="6" fill="#e2ead9" />
        <circle cx="302" cy="140" r="16" fill="#87a267" />
        <path d="M296 140l5 5 9-11" fill="none" stroke="#ffffff" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />

        <rect x="264" y="196" width="118" height="108" rx="24" fill="#5f7651" />
        <rect x="286" y="220" width="50" height="12" rx="6" fill="#efe2bd" />
        <rect x="286" y="244" width="72" height="10" rx="5" fill="#8ea46b" />
        <rect x="286" y="262" width="60" height="10" rx="5" fill="#8ea46b" />
        <circle cx="334" cy="284" r="8" fill="#efe2bd" />

        <rect x="396" y="202" width="86" height="94" rx="22" fill="#ffffff" stroke="#d7eaef" />
        <circle cx="439" cy="232" r="18" fill="#eef1df" />
        <path d="M439 222c5 0 9 4 9 9s-4 9-9 9-9-4-9-9 4-9 9-9Zm-18 40c3-10 13-16 24-16s21 6 24 16" fill="none" stroke="#87a267" strokeWidth="6" strokeLinecap="round" />
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
            <stop offset="0%" stopColor="#f7f2e9" />
            <stop offset="100%" stopColor="#ebf2e5" />
          </linearGradient>
          <linearGradient id="authAccent" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#637d50" />
            <stop offset="100%" stopColor="#88a76a" />
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
        <rect x="232" y="62" width="74" height="12" rx="6" fill="#566d46" />
        <rect x="316" y="62" width="54" height="12" rx="6" fill="#e5eadc" />

        <rect x="210" y="114" width="88" height="56" rx="20" fill="#607a4d" />
        <rect x="228" y="132" width="42" height="10" rx="5" fill="#efe3bc" />
        <rect x="228" y="148" width="30" height="10" rx="5" fill="#93a972" />

        <rect x="306" y="114" width="86" height="56" rx="20" fill="#ffffff" stroke="#d7eaef" />
        <circle cx="332" cy="142" r="11" fill="#eef1df" />
        <rect x="350" y="126" width="22" height="10" rx="5" fill="#e5eadc" />
        <rect x="350" y="144" width="28" height="10" rx="5" fill="#e5eadc" />
      </svg>
      <p className="auth-visual-caption">{title}</p>
    </div>
  )
}

const careTypeAccents: Record<string, { shell: string; detail: string; soft: string }> = {
  'personal-care-companionship': { shell: '#f4ead2', detail: '#7c9362', soft: '#fffaf1' },
  'homemaker-support': { shell: '#efe8da', detail: '#8a7d63', soft: '#fffaf4' },
  'skilled-nursing': { shell: '#e7efe4', detail: '#648455', soft: '#f9fdf7' },
  'physical-therapy': { shell: '#e8f1ea', detail: '#5d8669', soft: '#f7fcf8' },
  'occupational-therapy': { shell: '#f2eee3', detail: '#8a8458', soft: '#fffdf8' },
  'speech-therapy': { shell: '#efe8f2', detail: '#7a6a93', soft: '#fcf9ff' },
  'care-planning-social-support': { shell: '#e8efe8', detail: '#657e5f', soft: '#f9fcf8' },
  'respite-care': { shell: '#f1eadf', detail: '#8c7756', soft: '#fffaf5' },
  'memory-care-support': { shell: '#ece7de', detail: '#7a6b5b', soft: '#fffcf8' },
}

export function CareTypeIllustration({ variant, title }: { variant: string; title: string }) {
  const accent = careTypeAccents[variant] ?? careTypeAccents['personal-care-companionship']

  return (
    <svg className="care-type-visual" viewBox="0 0 220 132" role="img" aria-label={title}>
      <rect x="8" y="8" width="204" height="116" rx="26" fill={accent.soft} />
      <rect x="22" y="24" width="76" height="84" rx="22" fill={accent.shell} />
      <rect x="112" y="24" width="86" height="14" rx="7" fill={accent.detail} opacity="0.92" />
      <rect x="112" y="48" width="72" height="12" rx="6" fill={accent.shell} />
      <rect x="112" y="68" width="60" height="12" rx="6" fill={accent.shell} />
      <rect x="112" y="88" width="48" height="12" rx="6" fill={accent.shell} />

      {variant === 'personal-care-companionship' ? (
        <>
          <circle cx="48" cy="54" r="15" fill={accent.detail} />
          <circle cx="73" cy="61" r="12" fill={accent.detail} opacity="0.8" />
          <path d="M36 86c6-11 15-16 26-16s20 5 26 16" fill="none" stroke={accent.detail} strokeWidth="7" strokeLinecap="round" />
        </>
      ) : null}

      {variant === 'homemaker-support' ? (
        <>
          <path d="M38 83h44l-7-30H45z" fill={accent.detail} />
          <path d="M52 54h17" stroke={accent.detail} strokeWidth="6" strokeLinecap="round" />
          <circle cx="50" cy="90" r="6" fill={accent.shell} />
          <circle cx="72" cy="90" r="6" fill={accent.shell} />
        </>
      ) : null}

      {variant === 'skilled-nursing' ? (
        <>
          <rect x="40" y="42" width="40" height="40" rx="12" fill={accent.detail} />
          <path d="M60 50v24M48 62h24" stroke="#ffffff" strokeWidth="8" strokeLinecap="round" />
        </>
      ) : null}

      {variant === 'physical-therapy' ? (
        <>
          <circle cx="60" cy="46" r="12" fill={accent.detail} />
          <path d="M60 60v26M60 66l-18 10M60 66l18 10M60 86l-14 12M60 86l14 12" fill="none" stroke={accent.detail} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
        </>
      ) : null}

      {variant === 'occupational-therapy' ? (
        <>
          <circle cx="60" cy="48" r="12" fill={accent.detail} />
          <path d="M40 88c7-13 17-20 28-20s21 7 28 20" fill="none" stroke={accent.detail} strokeWidth="7" strokeLinecap="round" />
          <rect x="48" y="74" width="24" height="20" rx="8" fill={accent.shell} />
        </>
      ) : null}

      {variant === 'speech-therapy' ? (
        <>
          <circle cx="56" cy="52" r="15" fill={accent.detail} />
          <path d="M76 48h11a11 11 0 0 1 0 22h-7l-7 8v-8" fill="none" stroke={accent.detail} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
        </>
      ) : null}

      {variant === 'care-planning-social-support' ? (
        <>
          <rect x="40" y="40" width="42" height="48" rx="12" fill={accent.detail} />
          <path d="M51 56h20M51 67h16M51 78h12" stroke="#ffffff" strokeWidth="6" strokeLinecap="round" />
        </>
      ) : null}

      {variant === 'respite-care' ? (
        <>
          <path d="M60 44c12 0 22 10 22 22S72 94 60 94 38 84 38 66s10-22 22-22Z" fill={accent.detail} />
          <path d="M60 56v12l10 6" fill="none" stroke="#ffffff" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
        </>
      ) : null}

      {variant === 'memory-care-support' ? (
        <>
          <circle cx="60" cy="58" r="22" fill={accent.detail} />
          <path d="M60 47v14l8 6" fill="none" stroke="#ffffff" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="83" cy="43" r="8" fill={accent.shell} />
        </>
      ) : null}
    </svg>
  )
}
