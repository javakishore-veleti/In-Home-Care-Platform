import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <div className="home-page">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Member portal</p>
          <h1>Compassionate care, coordinated beautifully from home.</h1>
          <p className="hero-copy">
            Manage care appointments, review visit follow-ups, update service addresses,
            and message a concierge-style assistant built for members.
          </p>
          <div className="hero-actions">
            <Link className="primary-button" to="/signup">Create account</Link>
            <Link className="secondary-button" to="/signin">Sign in</Link>
          </div>
        </div>
        <div className="hero-summary card accent-card">
          <h2>What members can do</h2>
          <ul className="feature-list">
            <li>Book appointments using a saved address</li>
            <li>Search and page through appointment history</li>
            <li>Review visit documents, notes, decisions, and actions</li>
            <li>Manage profile settings and multiple service locations</li>
            <li>Chat with a helpful care concierge assistant</li>
          </ul>
        </div>
      </section>

      <section className="home-grid">
        <article className="card">
          <h3>Trusted scheduling</h3>
          <p>Request new care with flexible service areas, preferred time windows, and clear visit context.</p>
        </article>
        <article className="card">
          <h3>Clear follow-up</h3>
          <p>Each appointment detail page keeps visits, documents, notes, decisions, and action items together.</p>
        </article>
        <article className="card">
          <h3>Member-first design</h3>
          <p>Built to feel calm, modern, and reassuring for healthcare journeys that need clarity.</p>
        </article>
      </section>
    </div>
  )
}
