import { useState } from 'react';
import { getWhatsAppConfig } from '../utils/whatsapp';
import { IconGlobe, IconMail, IconPhone } from './Icons';
import WhatsAppWidget from './WhatsAppWidget';

const CATEGORIES = [
  { value: 'general', label: 'General Question' },
  { value: 'technical', label: 'Technical Support' },
  { value: 'billing', label: 'Billing Inquiry' },
  { value: 'bug_report', label: 'Bug Report' },
  { value: 'feedback', label: 'Feedback' },
];

const PRIORITIES = [
  { value: 'low', label: 'Low - Not urgent' },
  { value: 'medium', label: 'Medium - Need help soon' },
  { value: 'high', label: 'High - Urgent issue' },
];

export default function SupportForm({ apiEndpoint = '/api/support/submit' }) {
  const whatsapp = getWhatsAppConfig();
  const [channel, setChannel] = useState('web');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    category: 'general',
    priority: 'medium',
    message: '',
    attachment: '',
  });

  const [status, setStatus] = useState('idle');
  const [ticketId, setTicketId] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const validateForm = () => {
    if (formData.name.trim().length < 2) {
      setError('Please enter your name (at least 2 characters)');
      return false;
    }
    if (channel === 'email' || channel === 'web') {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        setError('Please enter a valid email address');
        return false;
      }
      if (formData.subject.trim().length < 5) {
        setError('Please enter a subject (at least 5 characters)');
        return false;
      }
    } else {
      if (formData.phone.trim().length < 7) {
        setError('Please enter a valid WhatsApp number');
        return false;
      }
    }
    if (formData.message.trim().length < 10) {
      setError('Please describe your issue in more detail (at least 10 characters)');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) return;

    setStatus('submitting');

    // Auto-generate subject for WhatsApp if not provided
    const submitData = {
      ...formData,
      channel,
      subject: formData.subject || `WhatsApp Support: ${formData.name}`,
    };

    // For WhatsApp, format phone number with country code and remove email
    if (channel === 'whatsapp') {
      delete submitData.email;
      // Ensure phone number starts with + for international format
      let phone = submitData.phone.trim();
      if (!phone.startsWith('+')) {
        // Auto-add Pakistan country code if not present
        phone = phone.startsWith('92') ? '+' + phone : '+92' + phone.replace(/^0/, '');
      }
      submitData.phone = phone;
    }

    // Debug: Log what we're sending
    console.log('=== WHATSAPP SUBMIT DEBUG ===');
    console.log('Selected channel:', channel);
    console.log('Submitting data:', submitData);
    console.log('=============================');

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submitData),
      });

      const rawBody = await response.text();
      const contentType = response.headers.get('content-type') || '';
      const isJsonResponse = contentType.includes('application/json');
      let responseData = null;

      if (isJsonResponse && rawBody) {
        try {
          responseData = JSON.parse(rawBody);
        } catch {
          responseData = null;
        }
      }

      if (!response.ok) {
        let detail =
          responseData?.detail ||
          responseData?.message ||
          (rawBody ? rawBody.slice(0, 160) : null);
        
        // Handle array of errors from Pydantic
        if (Array.isArray(detail)) {
          detail = detail.map(err => err.msg || JSON.stringify(err)).join('; ');
        }
        
        throw new Error(detail || `Submission failed (${response.status})`);
      }

      if (!responseData?.ticket_id) {
        throw new Error('Server returned an invalid response. Please try again.');
      }

      const data = responseData;
      setTicketId(data.ticket_id);
      setStatus('success');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="max-w-2xl mx-auto card">
        <div className="text-center">
          <div className="accent-circle mx-auto mb-4">
            <svg className="accent-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="card-title mb-2">Thank You</h2>
          <p className="card-subtitle mb-4">Your support request has been submitted successfully.</p>
          <div className="ticket-box mb-4">
            <p className="ticket-label">Your Ticket ID</p>
            <p className="ticket-id">{ticketId}</p>
          </div>
          <p className="text-sm muted">
            Our AI assistant will respond to your email within 5 minutes.
            For urgent issues, responses are prioritized automatically.
          </p>
          <button
            onClick={() => {
              setStatus('idle');
              setFormData({
                name: '',
                email: '',
                phone: '',
                subject: '',
                category: 'general',
                priority: 'medium',
                message: '',
                attachment: '',
              });
            }}
            className="mt-6 btn-primary"
          >
            Submit Another Request
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto card" id="support-form">
      <h2 className="card-title mb-2">Contact Support</h2>
      <p className="card-subtitle mb-4">
        Fill out the form below and our AI-powered support team will get back to you shortly.
      </p>

      <div className="toggle-group" role="tablist" aria-label="Support channel">
        <button
          type="button"
          role="tab"
          aria-selected={channel === 'web'}
          className={`toggle-btn ${channel === 'web' ? 'is-active' : ''}`}
          onClick={() => setChannel('web')}
        >
          <IconGlobe className="icon icon--sm" />
          Web Form
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={channel === 'email'}
          className={`toggle-btn ${channel === 'email' ? 'is-active' : ''}`}
          onClick={() => setChannel('email')}
        >
          <IconMail className="icon icon--sm" />
          Email Support
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={channel === 'whatsapp'}
          className={`toggle-btn ${channel === 'whatsapp' ? 'is-active' : ''}`}
          onClick={() => setChannel('whatsapp')}
        >
          <IconPhone className="icon icon--sm" />
          WhatsApp Support
        </button>
      </div>

      {error && (
        <div className="mb-4 alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Name */}
        <div>
          <label htmlFor="name" className="label">
            Your Name *
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="field"
            placeholder="John Doe"
          />
        </div>

        {channel === 'whatsapp' ? (
          <div>
            <label htmlFor="phone" className="label">
              WhatsApp Number *
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              required
              className="field"
              placeholder="+92 300 1234567"
            />
          </div>
        ) : (
          <div>
            <label htmlFor="email" className="label">
              Email Address *
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="field"
              placeholder="john@example.com"
            />
          </div>
        )}

        {/* Subject */}
        {(channel === 'email' || channel === 'web') && (
          <div>
            <label htmlFor="subject" className="label">
              Subject *
            </label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              required
              className="field"
              placeholder="Brief description of your issue"
            />
          </div>
        )}

        {channel === 'web' && (
          <div>
            <label htmlFor="attachment" className="label">
              Attachment link (optional)
            </label>
            <input
              type="url"
              id="attachment"
              name="attachment"
              value={formData.attachment}
              onChange={handleChange}
              className="field"
              placeholder="https://drive.google.com/..."
            />
            <p className="mt-1 text-sm muted">Upload to Drive/Dropbox and paste a shareable link.</p>
          </div>
        )}

        {/* Category + Priority */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="category" className="label">
              Category *
            </label>
            <select
              id="category"
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="field"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="priority" className="label">
              Priority
            </label>
            <select
              id="priority"
              name="priority"
              value={formData.priority}
              onChange={handleChange}
              className="field"
            >
              {PRIORITIES.map((pri) => (
                <option key={pri.value} value={pri.value}>{pri.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Message */}
        <div>
          <label htmlFor="message" className="label">
            How can we help? *
          </label>
          <textarea
            id="message"
            name="message"
            value={formData.message}
            onChange={handleChange}
            required
            rows={6}
            className="field field--textarea"
            placeholder="Please describe your issue or question in detail..."
          />
          <p className="mt-1 text-sm muted">
            {formData.message.length}/1000 characters
          </p>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={status === 'submitting'}
          className={`btn-primary btn-block ${status === 'submitting' ? 'is-disabled' : ''}`}
        >
          {status === 'submitting' ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Submitting...
            </span>
          ) : (
            channel === 'whatsapp' ? 'Start WhatsApp Request' : 'Submit Support Request'
          )}
        </button>

        <p className="text-center text-sm muted">
          By submitting, you agree to our{' '}
          <a href="/privacy" className="link">Privacy Policy</a>
        </p>
      </form>

      {channel === 'whatsapp' && (
        <div className="mt-8 pt-6 divider">
          <div className="flex items-center justify-between gap-3 mb-4">
            <div>
              <h3 className="text-lg font-semibold text-[color:var(--text)]">Prefer WhatsApp?</h3>
              <p className="text-sm muted">Scan the QR or open a chat to create a ticket.</p>
            </div>
            {whatsapp.link && (
              <a
                href={whatsapp.link}
                target="_blank"
                rel="noreferrer"
                className="btn-ghost"
              >
                Open WhatsApp
              </a>
            )}
          </div>

          {!whatsapp.hasConfig && (
            <div className="mb-4 alert alert--warning">
              WhatsApp is not configured yet. Set `VITE_WHATSAPP_NUMBER` (and optional `VITE_WHATSAPP_JOIN_CODE`) to enable.
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="qr-card">
              {whatsapp.qrSrc ? (
                <>
                  <img
                    src={whatsapp.qrSrc}
                    alt="WhatsApp QR code"
                    className="h-40 w-40 rounded-lg border border-[color:var(--border)] bg-white p-2"
                  />
                  <p className="mt-3 text-sm muted">Scan to open chat</p>
                </>
              ) : (
                <div className="h-40 w-40 rounded-lg border border-dashed border-[color:var(--border)] bg-white/70 flex items-center justify-center text-xs muted">
                  QR will appear here
                </div>
              )}
            </div>

            <div className="info-card">
              <p className="text-sm font-semibold text-[color:var(--text)] mb-2">How it works</p>
              <div className="space-y-2 text-sm muted">
                <div>1. Open a chat with: <span className="font-mono text-[color:var(--text)]">{whatsapp.displayNumber}</span></div>
                {whatsapp.showJoinCode && (
                  <div>
                    2. If using Twilio Sandbox, send:{' '}
                    <span className="font-mono text-[color:var(--text)]">{whatsapp.joinCode || 'join <code>'}</span>
                  </div>
                )}
                <div>3. Send your issue details. We will auto-create a ticket.</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {channel === 'whatsapp' && <WhatsAppWidget />}
    </div>
  );
}
