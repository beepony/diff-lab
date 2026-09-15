import assert from 'node:assert/strict'
import { test } from 'node:test'
import { formatResultForClipboard } from '../src/utils/resultClipboard.js'

const headers = ['A 列', 'B 列', '状态']
const labels = {
  intersect: '交集',
  match: '匹配',
  diff_a: '仅 A',
  diff_b: '仅 B',
}

test('copies every result row in order, including rows from all compare modes', () => {
  const rows = [
    { a: 'shared', b: 'shared', status: 'intersect' },
    { a: 'lookup', b: 'lookup', status: 'match' },
    { a: 'only A', b: null, status: 'diff_a' },
    { a: null, b: 'only B', status: 'diff_b' },
  ]

  assert.equal(
    formatResultForClipboard(rows, headers, status => labels[status]),
    'A 列\tB 列\t状态\nshared\tshared\t交集\nlookup\tlookup\t匹配\nonly A\t\t仅 A\n\tonly B\t仅 B',
  )
})

test('quotes spreadsheet delimiters and prevents pasted input from becoming a formula', () => {
  const rows = [
    { a: '=1+1', b: ' quoted "value" ', status: 'match' },
    { a: '  @SUM(A1:A2)', b: 'a\tb', status: 'diff_a' },
  ]

  assert.equal(
    formatResultForClipboard(rows, headers, status => labels[status]),
    'A 列\tB 列\t状态\n\'=1+1\t" quoted ""value"" "\t匹配\n\'  @SUM(A1:A2)\t"a\tb"\t仅 A',
  )
})
