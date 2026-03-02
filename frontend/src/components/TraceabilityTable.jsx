import React, { useState, useEffect } from 'react'
import { getTraceability, downloadCodeZip, downloadDesignPdf } from '../api'
import { ShieldCheck, Download, FileText, CheckCircle2, AlertCircle, AlertTriangle, RefreshCw, ClipboardList } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

// Shared helper: creates a temporary <a> and triggers a browser file download
function _triggerBlobDownload(data, contentDisposition, fallbackName, mimeType) {
  const url = window.URL.createObjectURL(new Blob([data], { type: mimeType }))
  const link = document.createElement('a')
  const match = (contentDisposition || '').match(/filename="?([^"]+)"?/)
  link.download = match ? match[1] : fallbackName
  link.href = url
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export default function TraceabilityTable({ deviceType, hasSubmittedReqs, setView, designData }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [genLoading, setGenLoading] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const matrix = await getTraceability()
      setData(matrix)
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || 'Failed to load traceability data. Ensure you have built the design first.')
    } finally {
      setLoading(false)
    }
  }

  const handleExportZip = async () => {
    setGenLoading(true)
    try {
      const res = await downloadCodeZip()
      _triggerBlobDownload(res.data, res.headers?.['content-disposition'], 'codebase.zip', 'application/zip')
    } catch (err) {
      console.error('ZIP_EXPORT_ERROR:', err)
      alert('Failed to export code. Ensure you have built the design first.')
    } finally {
      setGenLoading(false)
    }
  }

  const handleDownloadPdf = async () => {
    setPdfLoading(true)
    try {
      const res = await downloadDesignPdf()
      _triggerBlobDownload(res.data, res.headers?.['content-disposition'], 'system_design.pdf', 'application/pdf')
    } catch (err) {
      console.error('PDF_EXPORT_ERROR:', err)
      alert('Failed to generate PDF. Ensure you have built the design first.')
    } finally {
      setPdfLoading(false)
    }
  }

  useEffect(() => {
    if (hasSubmittedReqs && designData) {
      loadData()
    }
  }, [deviceType, hasSubmittedReqs, !!designData])

  return (
    <div className="space-y-6 w-full">
      <div className="flex items-center justify-between pb-4 border-b border-white/5">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Traceability & Compliance</h2>
          <p className="text-muted-foreground text-sm mt-1">REQ → Design → Risk → Evidence mapping.</p>
        </div>

        <div className="flex gap-4">
          <Button variant="outline" onClick={loadData} className="gap-2 bg-transparent border-white/10 hover:bg-white/5">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
          <Button onClick={handleDownloadPdf} disabled={pdfLoading} className="gap-2 bg-slate-700 hover:bg-slate-600 text-white border-transparent">
            <FileText className={`h-4 w-4 ${pdfLoading ? 'animate-bounce' : ''}`} />
            {pdfLoading ? 'Generating PDF...' : 'Download Design PDF'}
          </Button>
          <Button onClick={handleExportZip} disabled={genLoading} className="gap-2 bg-teal-600 hover:bg-teal-700 text-white border-transparent">
            <Download className={`h-4 w-4 ${genLoading ? 'animate-bounce' : ''}`} />
            {genLoading ? 'Generating ZIP...' : 'Export Code as ZIP'}
          </Button>
        </div>
      </div>

      {error && hasSubmittedReqs && designData && (
        <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-xl flex items-center gap-3 text-sm text-destructive font-medium">
          <AlertTriangle className="h-5 w-5" />
          {error}
        </div>
      )}

      <div className="border border-white/5 rounded-2xl overflow-hidden bg-[#1a1a1a]">
        {!hasSubmittedReqs ? (
          <div className="flex flex-col items-center justify-center text-center py-32 text-muted-foreground bg-transparent">
            <ClipboardList className="h-12 w-12 opacity-20 mb-4" />
            <p className="text-sm font-medium">No requirements submitted yet.</p>
            <p className="text-xs mt-1">Please submit requirements first to compile traceability data.</p>
            <Button onClick={() => setView('requirements')} className="mt-6 gap-2 bg-white text-black hover:bg-white/90">
              Go to Requirements Intake
            </Button>
          </div>
        ) : data ? (
          <Table>
            <TableHeader className="bg-[#2f2f2f]/30 border-b border-white/5">
              <TableRow className="hover:bg-transparent text-[11px] font-bold tracking-widest uppercase border-none">
                <TableHead className="w-[120px] text-[#878787]">REQ ID</TableHead>
                <TableHead className="text-[#878787]">Requirement</TableHead>
                <TableHead className="w-[200px] text-[#878787]">Hazard / Risk</TableHead>
                <TableHead className="w-[140px] text-[#878787]">Risk Status</TableHead>
                <TableHead className="w-[160px] text-[#878787]">Compliance</TableHead>
                <TableHead className="text-right w-[220px] text-[#878787]">Verification / Evidence</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((entry, idx) => {
                const riskStatus = entry['Risk Status']
                const riskAccept = entry['Risk Acceptability']
                const hazard = entry['Hazard']

                // Show risk data for ANY req that actually has it populated
                const hasHazard = hazard && hazard !== 'N/A' && hazard !== '—'
                const hasRisk = riskStatus && riskStatus !== 'N/A'
                const hasAccept = riskAccept && riskAccept !== 'N/A'

                const statusColor =
                  riskStatus === 'CLOSED' ? 'text-teal-400 bg-teal-500/10 border-teal-500/30' :
                    riskStatus?.startsWith('ALARP') ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' :
                      riskStatus?.startsWith('OPEN') ? 'text-red-400 bg-red-500/10 border-red-500/30' :
                        'text-[#555] bg-[#2f2f2f] border-white/5'

                const acceptIcon =
                  riskAccept === 'ACCEPTABLE' ? <CheckCircle2 className="h-4 w-4 text-teal-500 flex-shrink-0" /> :
                    riskAccept === 'ALARP' ? <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0" /> :
                      riskAccept === 'UNACCEPTABLE' ? <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0" /> :
                        null

                const acceptColor =
                  riskAccept === 'ACCEPTABLE' ? 'text-teal-400' :
                    riskAccept === 'ALARP' ? 'text-amber-400' :
                      riskAccept === 'UNACCEPTABLE' ? 'text-red-400' :
                        'text-[#555]'

                return (
                  <TableRow key={idx} className="border-b border-white/5 hover:bg-white/5 data-[state=selected]:bg-muted">
                    <TableCell className="font-mono text-sky-400 text-xs align-top">
                      {entry['Requirement ID']}
                    </TableCell>

                    {/* Requirement title + type badge */}
                    <TableCell className="align-top">
                      <span className="text-[10px] text-[#878787] block uppercase font-bold tracking-wider mb-1">
                        {entry['Type']}
                      </span>
                      <span className="text-sm text-[#ececec]">{entry['Title']}</span>
                      {entry['Subsystem'] && entry['Subsystem'] !== '—' && (
                        <span className="text-[10px] text-[#555] block mt-1">↳ {entry['Subsystem']}</span>
                      )}
                    </TableCell>

                    {/* Hazard description + P/S badges */}
                    <TableCell className="align-top">
                      {hasHazard ? (
                        <div className="flex flex-col gap-1.5">
                          <span className="text-[#c0c0c0] text-xs leading-tight line-clamp-2">
                            {hazard}
                          </span>
                          <div className="flex gap-2 mt-1 flex-wrap">
                            {entry['Probability'] && entry['Probability'] !== 'N/A' && (
                              <span className="text-[10px] px-1.5 py-0.5 bg-[#2f2f2f] rounded font-bold text-[#878787]">
                                P: {entry['Probability']}
                              </span>
                            )}
                            {entry['Severity'] && entry['Severity'] !== 'N/A' && (
                              <span className="text-[10px] px-1.5 py-0.5 bg-[#2f2f2f] rounded font-bold text-[#878787]">
                                S: {entry['Severity']}
                              </span>
                            )}
                          </div>
                        </div>
                      ) : (
                        <span className="text-[10px] text-[#444] italic">—</span>
                      )}
                    </TableCell>

                    {/* Risk Status: OPEN / ALARP / CLOSED badge */}
                    <TableCell className="align-top">
                      {hasRisk ? (
                        <span className={`text-[10px] px-2 py-1 rounded border font-bold ${statusColor}`}>
                          {riskStatus.startsWith('ALARP') ? 'ALARP' :
                            riskStatus.startsWith('OPEN') ? 'OPEN' : riskStatus}
                        </span>
                      ) : (
                        <span className="text-[10px] text-[#444] italic">—</span>
                      )}
                    </TableCell>

                    {/* Compliance: Risk Acceptability (ISO 14971) */}
                    <TableCell className="align-top">
                      {hasAccept ? (
                        <div className="flex items-center gap-2">
                          {acceptIcon}
                          <span className={`text-xs font-medium ${acceptColor}`}>
                            {riskAccept}
                          </span>
                        </div>
                      ) : (
                        <span className="text-[10px] text-[#444] italic">—</span>
                      )}
                    </TableCell>

                    {/* Verification method + evidence */}
                    <TableCell className="text-right align-top">
                      <div className="flex flex-col gap-1 text-xs text-[#878787]">
                        <span className="font-medium text-[#ececec]">
                          {entry['Verification Method']}
                        </span>
                        <span className="italic line-clamp-3">
                          {entry['Evidence']}
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        ) : (
          <div className="flex flex-col items-center justify-center text-center py-32 text-muted-foreground bg-transparent">
            <ShieldCheck className="h-12 w-12 opacity-20 mb-4" />
            <p className="text-sm font-medium">
              {loading ? 'Crunching compliance data...' : 'Architecture construction needed.'}
            </p>
            {!loading && (
              <p className="text-xs mt-1">Please construct the Design Graph first to compile compliance mapping.</p>
            )}
            {!loading && (
              <Button onClick={() => setView('design')} className="mt-6 gap-2 bg-white text-black hover:bg-white/90">
                Go to Design Graph
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}