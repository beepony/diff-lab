// Tab-separated result table that can be pasted into a spreadsheet.
function cell(value) {
  if (value === null || value === undefined) return ''
  const raw = String(value)
  // Match CSV export protection: spreadsheet apps must not execute pasted input as a formula.
  const text = /^[ \t\r]*[=+\-@]/.test(raw) ? `'${raw}` : raw
  return /[\t\r\n"]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}

export function formatResultForClipboard(rows, headers, statusLabel) {
  return [
    headers.map(cell).join('\t'),
    ...rows.map(row => [row.a, row.b, statusLabel(row.status)].map(cell).join('\t')),
  ].join('\n')
}
