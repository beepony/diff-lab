// One value per line, ready to paste into a spreadsheet column.
function cell(value) {
  const raw = String(value)
  // Match CSV export protection: spreadsheet apps must not execute pasted input as a formula.
  const text = /^[ \t\r]*[=+\-@]/.test(raw) ? `'${raw}` : raw
  return /[\t\r\n"]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}

export function resultColumnValues(rows, column) {
  return rows.map(row => row[column]).filter(value => value !== null && value !== undefined)
}

export function formatColumnForClipboard(values) {
  return values.map(cell).join('\n')
}
