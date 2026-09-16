import { useState, useEffect } from 'react'

export default function NationalEmblemBar() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const formattedTime = time.toLocaleTimeString('en-IN', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: true, timeZone: 'Asia/Kolkata',
  })

  return (
    <div className="bg-primary text-on-primary">
      <div className="w-full px-[var(--spacing-gutter)] h-8 flex items-center justify-between text-[12px] leading-[16px] tracking-[0.02em] font-medium">
        <div className="flex items-center gap-[var(--spacing-space-sm)]">
          <span>भारत सरकार | Government of India</span>
          <span className="text-outline">|</span>
          <span>Ministry of Coal</span>
          <span className="text-outline">|</span>
          <span className="text-[13px] font-semibold text-secondary-fixed">CMPDI / Coal India Limited</span>
        </div>
        <div className="flex items-center gap-[var(--spacing-space-xs)] text-on-primary-fixed-variant font-mono text-[12px]">
          <span className="material-symbols-outlined text-[14px]">schedule</span>
          <span>IST: {formattedTime}</span>
        </div>
      </div>
    </div>
  )
}
