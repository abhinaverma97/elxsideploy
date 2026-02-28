// Helper component for rendering detailed design sections
import React from 'react'
import { cn } from "@/lib/utils"

export const RenderTable = ({ headers, data, className }) => (
  <div className={cn("overflow-x-auto rounded-lg border border-white/10", className)}>
    <table className="w-full text-sm text-left">
      <thead className="text-xs uppercase bg-[#212121] text-[#878787] border-b border-white/10">
        <tr>
          {headers.map((h, i) => <th key={i} className="px-4 py-3 font-semibold">{h}</th>)}
        </tr>
      </thead>
      <tbody className="divide-y divide-white/5">
        {data && data.length > 0 ? data.map((row, i) => (
          <tr key={i} className="hover:bg-[#212121] transition-colors">
            {Object.values(row).map((v, j) => (
              <td key={j} className="px-4 py-3 text-[#ececec] font-medium">{v || '—'}</td>
            ))}
          </tr>
        )) : <tr><td colSpan={headers.length} className="px-4 py-8 text-center text-muted-foreground italic">No data available</td></tr>}
      </tbody>
    </table>
  </div>
)

export const SectionHeader = ({ title, iecRef }) => (
  <div className="flex items-center justify-between">
    <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">{title}</h4>
    {iecRef && (
      <span className="text-[10px] text-[#38BDF8] font-mono">{iecRef}</span>
    )}
  </div>
)

export const InfoBox = ({ title, children }) => (
  <div className="bg-[#171717] border border-white/10 p-5 rounded-xl text-sm text-[#ececec] leading-relaxed">
    <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider mb-2">{title}</h4>
    {children}
  </div>
)
