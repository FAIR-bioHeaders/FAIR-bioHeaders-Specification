// Usage: node indexedfasta_probe.mjs MODE FILE
// MODE: indexed (IndexedFasta, reads FILE.fai), bgzip (BgzipIndexedFasta, FILE.fai
// and FILE.gzi) or small (FetchableSmallFasta/parseSmallFasta, the parser that
// JBrowse 2's UnindexedFastaAdapter copies). Prints the record count, then
// name, length, md5 of the whole sequence and of the region 1000-1100.
import { IndexedFasta, FetchableSmallFasta, BgzipIndexedFasta } from '@gmod/indexedfasta'
import { createHash } from 'crypto'
const [mode, f] = process.argv.slice(2)
const t = mode === 'indexed' ? new IndexedFasta({ path: f })
  : mode === 'bgzip' ? new BgzipIndexedFasta({ path: f, faiPath: f + '.fai', gziPath: f + '.gzi' })
  : new FetchableSmallFasta({ path: f })
const md5 = s => createHash('md5').update(s).digest('hex')
const names = await t.getSequenceNames()
console.log(`${names.length} records`)
for (const n of names) {
  const g = (a, b) => (t.fetch ? t.fetch(n, a, b) : t.getSequence(n, a, b))
  const s = await g(0, 1e9)
  console.log(`${n}\t${s.length}\t${md5(s.toUpperCase())}\tregion:${md5(await g(1000, 1100))}`)
}
