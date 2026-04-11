import { Link } from 'react-router-dom'

import { HomeCareIllustration } from '../components/CareVisuals'

export function HomePage() {
  return (
    <div className="home-page">
      <section className="hero-panel">
        <div className="hero-intro">
          <p className="eyebrow">Member portal</p>
          <h1 className="home-hero-title">Manage home-care appointments and member details in one place.</h1>
          <p className="hero-copy">
            Use this portal to manage profile details, saved addresses, appointment requests, visit updates,
            and support after sign-in.
          </p>
          <div className="hero-actions">
            <Link className="primary-button" to="/signup">Create account</Link>
            <Link className="secondary-button" to="/signin">Sign in</Link>
          </div>
          <div className="hero-metrics">
            <div className="metric-card">
              <strong>Book care</strong>
              <span>Use saved service addresses</span>
            </div>
            <div className="metric-card">
              <strong>Track progress</strong>
              <span>Visits, notes, and action items</span>
            </div>
            <div className="metric-card">
              <strong>Get help</strong>
              <span>Chat after sign-in</span>
            </div>
          </div>
        </div>
        <div className="hero-summary card accent-card">
          <p className="eyebrow">Portal walkthrough</p>
          <h2>What you can manage after sign-in</h2>
          <HomeCareIllustration />
          <ul className="feature-list">
            <li className="feature-item feature-item-light">
              <strong>Request care</strong>
              <span>Choose a saved service location and preferred time window.</span>
            </li>
            <li className="feature-item feature-item-light">
              <strong>Review follow-up</strong>
              <span>See visit documents, notes, decisions, and action items together.</span>
            </li>
            <li className="feature-item feature-item-light">
              <strong>Stay organized</strong>
              <span>Keep profile settings, addresses, and support chat connected.</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="home-grid">
        <article className="card info-card">
          <p className="card-kicker">Scheduling workflow</p>
          <h3>Structured appointment intake</h3>
          <p>Request care with the core details operations teams actually need before confirming in-home service.</p>
          <ul className="card-list">
            <li>Saved service address selection</li>
            <li>Preferred date and time window</li>
            <li>Reason for care and member notes</li>
          </ul>
        </article>
        <article className="card info-card">
          <p className="card-kicker">Visit visibility</p>
          <h3>Clinical follow-up in context</h3>
          <p>Each appointment becomes a single review surface for related visits and the artifacts created after care is delivered.</p>
          <ul className="card-list">
            <li>Visit summaries and documents</li>
            <li>Decisions and action items</li>
            <li>Notes without leaving the appointment view</li>
          </ul>
        </article>
        <article className="card info-card">
          <p className="card-kicker">Account readiness</p>
          <h3>Member profile and location management</h3>
          <p>Keep household details current so repeat booking, service coordination, and support interactions stay consistent.</p>
          <ul className="card-list">
            <li>Multiple saved addresses</li>
            <li>Default service location</li>
            <li>Profile settings and guided support</li>
          </ul>
        </article>
      </section>
    </div>
  )
}
