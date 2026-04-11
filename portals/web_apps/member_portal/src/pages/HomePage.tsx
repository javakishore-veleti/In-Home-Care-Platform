import { Link } from 'react-router-dom'

import { CareTypeIllustration, HomeCareIllustration } from '../components/CareVisuals'
import { careTypes } from '../lib/careTypes'

export function HomePage() {
  return (
    <div className="home-page">
      <section className="hero-panel">
        <div className="hero-intro">
          <p className="eyebrow">Member care</p>
          <h1 className="home-hero-title">A calmer way to book care and follow what happens next.</h1>
          <p className="hero-copy">
            Designed to feel clear and reassuring: book in-home care, review visit updates, manage saved addresses,
            and get help without digging through busy screens.
          </p>
          <div className="hero-actions">
            <Link className="primary-button" to="/signup">Create account</Link>
            <Link className="secondary-button" to="/signin">Sign in</Link>
          </div>
          <div className="hero-metrics">
            <div className="metric-card">
              <strong>Book care</strong>
              <span>Use saved addresses</span>
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
          <p className="eyebrow">After sign-in</p>
          <h2>See the next step quickly</h2>
          <HomeCareIllustration />
          <ul className="feature-list">
            <li className="feature-item feature-item-light">
              <strong>Book in minutes</strong>
              <span>Pick a saved address, choose a time window, and send your request.</span>
            </li>
            <li className="feature-item feature-item-light">
              <strong>Review visit updates</strong>
              <span>See notes, documents, decisions, and next steps in one place.</span>
            </li>
            <li className="feature-item feature-item-light">
              <strong>Get guided help</strong>
              <span>Use chat when you need help finding details or deciding what to do next.</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Care types</p>
            <h2>Choose the kind of in-home help you need</h2>
            <p className="muted">These are original member-facing categories. Select one to start a request with that care type already chosen.</p>
          </div>
        </div>
        <div className="care-type-grid">
          {careTypes.map((careType) => (
            <Link className="care-type-card" key={careType.slug} to={`/app/appointments/new?service_type=${encodeURIComponent(careType.label)}`}>
              <CareTypeIllustration variant={careType.slug} title={careType.label} />
              <div className="care-type-copy">
                <strong>{careType.label}</strong>
                <span>{careType.blurb}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="home-grid">
        <article className="card info-card">
          <p className="card-kicker">Booking</p>
          <h3>Simple request flow</h3>
          <p>Booking stays focused on a few important details so members are not overwhelmed at the first step.</p>
          <ul className="card-list">
            <li>Saved address selection</li>
            <li>Preferred date and time window</li>
            <li>Reason for care and member notes</li>
          </ul>
        </article>
        <article className="card info-card">
          <p className="card-kicker">Follow-up</p>
          <h3>Updates without the maze</h3>
          <p>Appointments, visits, documents, and action items stay grouped together so members can orient themselves fast.</p>
          <ul className="card-list">
            <li>Visit summaries and documents</li>
            <li>Decisions and action items</li>
            <li>Notes without leaving the appointment view</li>
          </ul>
        </article>
        <article className="card info-card">
          <p className="card-kicker">Member details</p>
          <h3>Household information that stays ready</h3>
          <p>Addresses and core member details stay easy to update, making repeat booking and support conversations smoother.</p>
          <ul className="card-list">
            <li>Multiple saved addresses</li>
            <li>Default address</li>
            <li>Profile settings and guided support</li>
          </ul>
        </article>
      </section>
    </div>
  )
}
