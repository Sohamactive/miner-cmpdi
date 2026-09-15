export default function PortalHeader() {
  return (
    <div className="bg-surface-container-lowest">
      <div className="w-full px-[var(--spacing-gutter)] h-16 flex items-center justify-between gap-[var(--spacing-space-md)]">
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
        <div className="flex items-center gap-[var(--spacing-space-lg)]">
          <div className="hidden xl:flex items-center bg-surface-container-low px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] rounded-[var(--radius-sm)] w-80 text-on-surface-variant">
            <span className="material-symbols-outlined text-[18px] mr-[var(--spacing-space-sm)] text-outline">search</span>
            <span className="text-[13px] leading-[18px] text-outline">Search boreholes, seismic logs, reports...</span>
          </div>
          <div className="flex items-center gap-[var(--spacing-space-sm)]">
            <div className="text-right hidden md:block">
              <div className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">Er. R. K. Sharma</div>
              <div className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">Chief Manager (Geology &amp; Planning), HQ Ranchi</div>
            </div>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
