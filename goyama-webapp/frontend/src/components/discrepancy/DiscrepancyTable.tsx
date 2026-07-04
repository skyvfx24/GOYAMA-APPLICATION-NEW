import React, { useState } from 'react';
import type { Discrepancy } from '../../types/mfrecon.types';
import { SeverityBadge } from '../dashboard/SeverityBadge';
import { Eye, ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-react';

interface DiscrepancyTableProps {
  discrepancies: Discrepancy[];
  onRowClick: (d: Discrepancy) => void;
}

type SortField = 'pan' | 'investor_name' | 'discrepancy_type' | 'severity' | 'source';

export const DiscrepancyTable: React.FC<DiscrepancyTableProps> = ({ 
  discrepancies, 
  onRowClick 
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const [sortField, setSortField] = useState<SortField>('severity');
  const [sortAsc, setSortAsc] = useState(false);

  const getDiscrepancySource = (d: Discrepancy) => {
    const rule = d.audit_trace?.rule_evaluated || '';
    if (rule.toUpperCase().includes('CAMS')) return 'CAMS';
    if (rule.toUpperCase().includes('KFINTECH') || rule.toUpperCase().includes('KFIN')) return 'KFINTECH';
    if (rule.toUpperCase().includes('BSE')) return 'BSE';
    if (rule.toUpperCase().includes('NSE')) return 'NSE';
    if (rule.toUpperCase().includes('PDF_CAS') || rule.toUpperCase().includes('CAS')) return 'PDF CAS';
    return 'CRM';
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const formatType = (type: string) => {
    return type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  };

  // 1. Sort discrepancies
  const sortedDiscrepancies = [...discrepancies].sort((a, b) => {
    let valA = '';
    let valB = '';

    if (sortField === 'pan') {
      valA = a.pan;
      valB = b.pan;
    } else if (sortField === 'investor_name') {
      // Find name in crm_value or report_value if missing
      valA = a.explanation || '';
      valB = b.explanation || '';
    } else if (sortField === 'discrepancy_type') {
      valA = a.discrepancy_type;
      valB = b.discrepancy_type;
    } else if (sortField === 'severity') {
      // Custom severity priority sorting
      const priority: Record<string, number> = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
      const prioA = priority[a.severity] || 0;
      const prioB = priority[b.severity] || 0;
      return sortAsc ? prioA - prioB : prioB - prioA;
    } else if (sortField === 'source') {
      valA = getDiscrepancySource(a);
      valB = getDiscrepancySource(b);
    }

    if (valA < valB) return sortAsc ? -1 : 1;
    if (valA > valB) return sortAsc ? 1 : -1;
    return 0;
  });

  // 2. Paginate discrepancies
  const totalPages = Math.ceil(sortedDiscrepancies.length / itemsPerPage);
  const paginatedDiscrepancies = sortedDiscrepancies.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  if (discrepancies.length === 0) {
    return (
      <div className="card text-center" style={{ padding: '48px', color: 'hsl(var(--text-secondary))' }}>
        <p className="font-medium">No discrepancies detected.</p>
        <p className="text-sm text-muted mt-2">All scanned statements perfectly match the CRM database records.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th onClick={() => handleSort('pan')} style={{ cursor: 'pointer' }}>
                <div className="flex items-center gap-2">
                  <span>PAN</span>
                  <ArrowUpDown size={14} />
                </div>
              </th>
              <th onClick={() => handleSort('source')} style={{ cursor: 'pointer' }}>
                <div className="flex items-center gap-2">
                  <span>Source</span>
                  <ArrowUpDown size={14} />
                </div>
              </th>
              <th onClick={() => handleSort('discrepancy_type')} style={{ cursor: 'pointer' }}>
                <div className="flex items-center gap-2">
                  <span>Discrepancy Type</span>
                  <ArrowUpDown size={14} />
                </div>
              </th>
              <th onClick={() => handleSort('severity')} style={{ cursor: 'pointer' }}>
                <div className="flex items-center gap-2">
                  <span>Severity</span>
                  <ArrowUpDown size={14} />
                </div>
              </th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedDiscrepancies.map((d, index) => (
              <tr key={`${d.pan}-${d.discrepancy_type}-${index}`} style={{ cursor: 'pointer' }} onClick={() => onRowClick(d)}>
                <td className="font-medium" style={{ fontFamily: 'monospace', letterSpacing: '0.02em', color: 'hsl(var(--text-primary))' }}>
                  {d.pan}
                </td>
                <td>
                  <span 
                    className="badge" 
                    style={{ 
                      backgroundColor: 'hsl(var(--border-color))',
                      color: 'hsl(var(--text-primary))',
                      border: '1px solid hsl(var(--border-color) / 150%)'
                    }}
                  >
                    {getDiscrepancySource(d)}
                  </span>
                </td>
                <td style={{ color: 'hsl(var(--text-secondary))' }}>
                  {formatType(d.discrepancy_type)}
                </td>
                <td>
                  <SeverityBadge severity={d.severity} />
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      onRowClick(d);
                    }}
                    className="btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '0.8rem', borderRadius: '6px', border: 'none' }}
                  >
                    <Eye size={12} className="mr-2" />
                    <span>View Detail</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center px-4 mb-4">
          <span className="text-sm text-muted">
            Showing Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong> ({discrepancies.length} total discrepancies)
          </span>
          <div className="flex gap-2">
            <button 
              onClick={handlePrevPage}
              disabled={currentPage === 1}
              className="btn-secondary"
              style={{ padding: '8px 12px', border: 'none', borderRadius: '6px' }}
            >
              <ChevronLeft size={16} />
            </button>
            <button 
              onClick={handleNextPage}
              disabled={currentPage === totalPages}
              className="btn-secondary"
              style={{ padding: '8px 12px', border: 'none', borderRadius: '6px' }}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
