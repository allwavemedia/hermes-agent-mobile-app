import {
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join, resolve } from 'node:path'

const scriptDirectory = dirname(fileURLToPath(import.meta.url))
const packageRoot = resolve(scriptDirectory, '..')
const repositoryRoot = resolve(packageRoot, '..', '..')
const canonicalRoot = join(
  repositoryRoot,
  'docs',
  'remote-control',
  'schemas',
  'v1'
)
const outputRoot = join(packageRoot, 'dist', 'schemas', 'v1')
const schemaFiles = readdirSync(canonicalRoot)
  .filter((fileName) => fileName.endsWith('.schema.json'))
  .sort()

if (schemaFiles.length === 0) {
  throw new Error(`no canonical schemas found in ${canonicalRoot}`)
}

rmSync(outputRoot, { force: true, recursive: true })
mkdirSync(outputRoot, { recursive: true })

for (const fileName of schemaFiles) {
  const sourceBytes = readFileSync(join(canonicalRoot, fileName))
  const outputPath = join(outputRoot, fileName)

  writeFileSync(outputPath, sourceBytes)

  const outputBytes = readFileSync(outputPath)
  if (!sourceBytes.equals(outputBytes)) {
    throw new Error(`schema copy is not byte-identical: ${fileName}`)
  }
}

console.log(
  `Copied and verified ${schemaFiles.length} canonical remote-control schemas.`
)
