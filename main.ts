// main.ts — gta6-meme-x-01 entry program (Node 22, standard library only).
//
// The real entry is a public post on X; this repository proves which post it
// is. POST.json at the repository root holds {"url": "https://x.com/..."}
// and this program's whole job is to copy that file, byte for byte, into the
// output directory the grader points MAKEFUN_OUTPUT_DIR at (default
// /output). The house then reads the post itself from X.
//
// Grader-proofing notes:
//   - The output directory is a mount point: it is never deleted, only
//     written into (POST.json is overwritten in place when it exists).
//   - The working directory is not guaranteed, so POST.json is resolved
//     from MAKEFUN_BOT_DIR, falling back to this script's own directory.
//   - No network, no clock, no randomness: two runs write the same bytes.

import { copyFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

// Where the repository lives: the grader sets MAKEFUN_BOT_DIR; anywhere
// else (a local test run), this script's own directory is the repository.
function repoDir(): string {
  return process.env.MAKEFUN_BOT_DIR ?? dirname(fileURLToPath(import.meta.url));
}

// Where POST.json goes: MAKEFUN_OUTPUT_DIR, or /output when unset. The
// directory is created if missing and never removed — on the grader it is
// a mount point, so the copy below is the only write this program makes.
function outDir(): string {
  return process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
}

const target = outDir();
mkdirSync(target, { recursive: true });
copyFileSync(join(repoDir(), 'POST.json'), join(target, 'POST.json'));
