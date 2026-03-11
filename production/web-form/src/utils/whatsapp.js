const DEFAULT_PREFILL = 'Hi! I need help with my request.';

const sanitizeNumber = (value) => (value || '').toString().replace(/[^\d]/g, '');

export function getWhatsAppConfig() {
  const isDev = import.meta.env.MODE === 'development';
  const rawNumber = import.meta.env.VITE_WHATSAPP_NUMBER || '';
  const joinCode = import.meta.env.VITE_WHATSAPP_JOIN_CODE || '';
  const prefill = import.meta.env.VITE_WHATSAPP_PREFILL || DEFAULT_PREFILL;

  const sanitized = sanitizeNumber(rawNumber);
  const hasConfig = Boolean(sanitized);
  const text = joinCode ? `${prefill} Join code: ${joinCode}` : prefill;
  const link = hasConfig ? `https://wa.me/${sanitized}?text=${encodeURIComponent(text)}` : null;
  const qrSrc = link
    ? `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(link)}`
    : null;

  return {
    hasConfig,
    link,
    qrSrc,
    displayNumber: rawNumber || 'Set VITE_WHATSAPP_NUMBER',
    joinCode,
    showJoinCode: isDev,
  };
}
