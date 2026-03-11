import SupportForm from '../components/SupportForm'
import { IconBolt, IconClock, IconShield, IconFaq, IconTicket, IconBilling, IconChat } from '../components/Icons'

export default function Overview() {
  return (
    <div className="page-transition">
      <div className="max-w-5xl mx-auto mb-10">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-6">
          <p className="pill">CUSTOMER SUPPORT</p>
        </div>

        <div className="hero">
          <div className="hero-copy">
            <h1 className="heading heading--hero">TechCorp Help Desk</h1>
            <p className="subheading subheading--hero">
              Faster support intake with AI triage and clean handoff to the right team.
            </p>
            <div className="hero-actions">
              <a href="/chat" className="btn-primary">💬 Start Live Chat</a>
              <button type="button" className="btn-ghost">Track ticket</button>
            </div>
            <div className="trust-row">
              <span><IconClock className="icon icon--sm" />Avg response: 5 mins</span>
              <span><IconBolt className="icon icon--sm" />24/7 AI Support</span>
              <span><IconShield className="icon icon--sm" />Secure & private</span>
            </div>
          </div>

          <div className="hero-panel">
            <div className="hero-card">
              <p className="hero-kicker">Today</p>
              <p className="hero-number">1,284</p>
              <p className="hero-label">
                <span className="label-icon"><IconTicket /></span>
                Tickets resolved
              </p>
            </div>
            <div className="hero-card hero-card--accent">
              <p className="hero-kicker">Live status</p>
              <p className="hero-number">2m 40s</p>
              <p className="hero-label">
                <span className="label-icon"><IconClock /></span>
                Median response time
              </p>
            </div>
            <div className="hero-card">
              <p className="hero-kicker">Priority queue</p>
              <p className="hero-number">98%</p>
              <p className="hero-label">
                <span className="label-icon"><IconShield /></span>
                SLA compliance
              </p>
            </div>
          </div>
        </div>

        <div className="section quick-actions">
          <h2 className="section-title">Quick actions</h2>
          <p className="section-subtitle">Pick a shortcut or jump straight into the form.</p>
          <div className="quick-grid">
            <a href="/chat" className="action-card">
              <span className="action-icon"><IconChat /></span>
              <span className="action-title">Live Chat</span>
              <span className="action-text">Chat with our AI assistant instantly.</span>
            </a>
            <button type="button" className="action-card" onClick={() => document.getElementById('support-form')?.scrollIntoView({ behavior: 'smooth' })}>
              <span className="action-icon"><IconTicket /></span>
              <span className="action-title">Track ticket</span>
              <span className="action-text">Check status with your ticket ID.</span>
            </button>
            <button type="button" className="action-card">
              <span className="action-icon"><IconBilling /></span>
              <span className="action-title">Billing help</span>
              <span className="action-text">Invoices, refunds, and payment issues.</span>
            </button>
          </div>
        </div>
      </div>

      <SupportForm apiEndpoint="/api/support/submit" />

      <div className="max-w-5xl mx-auto mt-12 space-y-10">
        <section className="section steps">
          <h2 className="section-title">How it works</h2>
          <p className="section-subtitle">A clean 3-step flow from intake to resolution.</p>
          <div className="steps-grid">
            <div className="step-card">
              <span className="step-number"><IconBolt /></span>
              <h3 className="step-title">Submit your issue</h3>
              <p className="step-text">Provide a short subject and detailed message.</p>
            </div>
            <div className="step-card">
              <span className="step-number"><IconClock /></span>
              <h3 className="step-title">AI triage</h3>
              <p className="step-text">We auto-route and prioritize by category.</p>
            </div>
            <div className="step-card">
              <span className="step-number"><IconShield /></span>
              <h3 className="step-title">Human follow-up</h3>
              <p className="step-text">Get updates and resolution via email.</p>
            </div>
          </div>
        </section>

        <section className="section testimonials">
          <h2 className="section-title">Teams love the speed</h2>
          <p className="section-subtitle">Short feedback from product and finance teams.</p>
          <div className="testimonial-grid">
            <div className="testimonial-card">
              <p className="testimonial-text">“We cut support response time by half in the first week.”</p>
              <p className="testimonial-author">Ayesha Khan, Product Lead</p>
            </div>
            <div className="testimonial-card">
              <p className="testimonial-text">“The triage keeps our billing queue clean and focused.”</p>
              <p className="testimonial-author">Umair Saeed, Finance Ops</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
