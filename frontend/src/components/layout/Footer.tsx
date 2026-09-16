export default function Footer() {
  return (
    <footer className="w-full bg-surface-container-lowest shadow-[0_1px_8px_rgba(0,0,0,0.04)] mt-[var(--spacing-margin)]">
      <div className="w-full px-[var(--spacing-gutter)] py-[var(--spacing-space-lg)] flex flex-col gap-[var(--spacing-space-md)]">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-[var(--spacing-space-md)] pb-[var(--spacing-space-md)]">
          <div className="flex flex-col gap-[var(--spacing-space-xs)]">
            <div className="text-[16px] leading-[24px] font-semibold text-primary">
              Central Mine Planning &amp; Design Institute Limited (CMPDI)
            </div>
            <div className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant max-w-4xl">
              A Subsidiary of Coal India Limited (CIL) • Ministry of Coal, Government of India. Gondwana Place, Kanke Road, Ranchi - 834031, Jharkhand, India. This portal is governed under the IT Act 2000 and institutional data handling guidelines. Non-authorized access is strictly prohibited.
            </div>
          </div>
          <div className="flex flex-col items-start lg:items-end gap-[var(--spacing-space-xs)] font-mono text-[12px] leading-[16px] text-on-surface-variant">
            <div className="flex items-center gap-[var(--spacing-space-xs)]">
              <span className="w-2 h-2 rounded-full bg-tertiary-fixed-dim inline-block"></span>
              <span className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">Qdrant Engine &amp; Gemini AI:</span>
              <span className="text-tertiary-container font-semibold">Operational v2.4.1</span>
            </div>
            <div>Security Audit: STQC Certified (Valid Oct 2026)</div>
            <div>CMPDI IT Helpdesk: 1800-345-6789 / miner-support@cmpdi.co.in</div>
          </div>
        </div>
        <div className="flex flex-col md:flex-row items-center justify-between gap-[var(--spacing-space-sm)] pt-[var(--spacing-space-sm)] text-[12px] leading-[16px] tracking-[0.02em] font-medium text-outline">
          <p>© 2025 Central Mine Planning &amp; Design Institute Limited (CMPDI). Hosted in compliance with NIC Guidelines (GIGW).</p>
          <div className="flex items-center gap-[var(--spacing-space-md)]">
            <a className="hover:text-primary transition-colors" href="#">Security Policy</a>
            <a className="hover:text-primary transition-colors" href="#">Terms of Use</a>
            <a className="hover:text-primary transition-colors" href="#">Hyperlinking Policy</a>
            <a className="hover:text-primary transition-colors" href="#">CIL Portal</a>
          </div>
        </div>
      </div>
    </footer>
  )
}
