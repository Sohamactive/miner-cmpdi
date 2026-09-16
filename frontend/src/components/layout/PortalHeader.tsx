export default function PortalHeader() {
  return (
    <div className="bg-surface-container-lowest">
      <div className="w-full px-[var(--spacing-gutter)] h-16 flex items-center gap-[var(--spacing-space-md)]">
        <div className="flex items-center gap-[var(--spacing-space-md)]">
          <img
            alt="CMPDI M.I.N.E.R. Official Emblem"
            className="h-8 w-auto object-contain"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuB_jgH84A_wTDRmx0cxhfRRGVxv_S_2Pv_B_oK8AO2A6gtU-f_fhZod6gIVmdiM4-Tymh_Vd_Mdw_D7TK50kGY0uQisgAiT6R6x-O1dvqO64Urwfqdw-x8EIahmta4xhgFpzgb8sKTDxqA99Brui72mfoOTvnloW5JelifHGgd6k9Dk1J979pJyx0BQJno8BsBmKEyhtjluDNxjnDFKKti-Cnr5BUrN8KHwmNZbgbGFmJQn9CjyhZOX"
          />
          <div className="flex flex-col">
            <div className="flex items-center gap-[var(--spacing-space-sm)]">
              <span className="text-[20px] leading-[28px] font-semibold text-primary tracking-tight">M.I.N.E.R.</span>
              <span className="px-[var(--spacing-space-sm)] py-0.5 rounded-[var(--radius-sm)] bg-secondary-fixed text-on-secondary-fixed text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase">
                Restricted / Official Use
              </span>
            </div>
            <span className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">
              Central Mine Planning &amp; Design Institute • Knowledge Base &amp; AI Retrieval System
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
