import assert from 'node:assert/strict'
import { test } from 'node:test'
import { formatColumnForClipboard, resultColumnValues } from '../src/utils/resultClipboard.js'

const rows = [
  { a: 'shared', b: 'shared B', status: 'match' },
  { a: 'only A', b: null, status: 'diff_a' },
  { a: null, b: 'only B', status: 'diff_b' },
  { a: 'shared', b: 'shared B again', status: 'match' },
]

test('copies only the chosen column from the status-filtered result', () => {
  const matches = rows.filter(row => row.status === 'match')
  assert.equal(formatColumnForClipboard(resultColumnValues(matches, 'a')), 'shared\nshared')
  assert.equal(formatColumnForClipboard(resultColumnValues(matches, 'b')), 'shared B\nshared B again')

  const onlyA = rows.filter(row => row.status === 'diff_a')
  assert.equal(formatColumnForClipboard(resultColumnValues(onlyA, 'a')), 'only A')
  assert.deepEqual(resultColumnValues(onlyA, 'b'), [])

  const onlyB = rows.filter(row => row.status === 'diff_b')
  assert.deepEqual(resultColumnValues(onlyB, 'a'), [])
  assert.equal(formatColumnForClipboard(resultColumnValues(onlyB, 'b')), 'only B')
})

test('includes all filtered rows beyond the first page and skips only null cells', () => {
  const manyRows = Array.from({ length: 30 }, (_, index) => ({ a: `value-${index + 1}`, b: null }))
  manyRows.push({ a: null, b: 'B value' }, { a: '', b: null })
  const values = resultColumnValues(manyRows, 'a')

  assert.equal(values.length, 31)
  assert.equal(formatColumnForClipboard(values), `${Array.from({ length: 30 }, (_, index) => `value-${index + 1}`).join('\n')}\n`)
})

test('quotes spreadsheet delimiters and prevents pasted values from becoming formulas', () => {
  const values = ['=1+1', '  @SUM(A1:A2)', 'a\tb', 'quoted "value"']
  assert.equal(
    formatColumnForClipboard(values),
    '\'=1+1\n\'  @SUM(A1:A2)\n"a\tb"\n"quoted ""value"""',
  )
})
