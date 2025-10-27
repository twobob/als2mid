// Standalone tester for extractRecentAlsFromPrefsText
// Usage: node dev/test_extract_prefs.js [optional-path-to-Preferences.cfg]

const fs = require('fs');
const path = require('path');
const os = require('os');

function detectUtf16Endian(buf) {
  if (buf.length >= 2) {
    const b0 = buf[0], b1 = buf[1];
    if (b0 === 0xFF && b1 === 0xFE) return 'LE';
    if (b0 === 0xFE && b1 === 0xFF) return 'BE';
  }
  const n = Math.min(buf.length, 4096);
  if (n < 4) return null;
  let zerosOdd = 0, zerosEven = 0, consideredOdd = 0, consideredEven = 0;
  for (let i = 0; i < n; i++) {
    if (i % 2 === 1) { consideredOdd++; if (buf[i] === 0x00) zerosOdd++; }
    else { consideredEven++; if (buf[i] === 0x00) zerosEven++; }
  }
  const fracOdd = consideredOdd ? zerosOdd / consideredOdd : 0;
  const fracEven = consideredEven ? zerosEven / consideredEven : 0;
  if (fracOdd > 0.2 && fracOdd > fracEven * 1.5) return 'LE';
  if (fracEven > 0.2 && fracEven > fracOdd * 1.5) return 'BE';
  return null;
}

function readBuffer(p) {
  return fs.readFileSync(p);
}

function decodeSmart(buf) {
  const endian = detectUtf16Endian(buf);
  let txt;
  if (endian === 'LE') {
    txt = buf.toString('utf16le');
  } else if (endian === 'BE') {
    // Swap bytes to decode as LE
    const swapped = Buffer.allocUnsafe(buf.length);
    for (let i = 0; i + 1 < buf.length; i += 2) { swapped[i] = buf[i + 1]; swapped[i + 1] = buf[i]; }
    if (buf.length % 2 === 1) swapped[buf.length - 1] = buf[buf.length - 1];
    txt = swapped.toString('utf16le');
  } else {
    txt = buf.toString('utf8');
    // If lots of NULs remain after utf8, try latin1
    if ((txt.match(/\x00/g) || []).length > 10) {
      txt = buf.toString('latin1');
    }
  }
  return txt.replace(/\x00/g, '');
}

function headerPresentInBuffer(buf, ascii = 'RecentDocsList') {
  const asciiBytes = Buffer.from(ascii, 'ascii');
  const leBytes = Buffer.allocUnsafe(asciiBytes.length * 2);
  const beBytes = Buffer.allocUnsafe(asciiBytes.length * 2);
  for (let i = 0; i < asciiBytes.length; i++) {
    leBytes[i * 2] = asciiBytes[i];
    leBytes[i * 2 + 1] = 0x00;
    beBytes[i * 2] = 0x00;
    beBytes[i * 2 + 1] = asciiBytes[i];
  }
  const hay = buf;
  const patterns = [asciiBytes, leBytes, beBytes];
  const found = patterns.some(needle => indexOfSubBuffer(hay, needle) !== -1);
  return found;
}

function indexOfSubBuffer(hay, needle) {
  // Naive search is fine for small patterns
  const n = needle.length;
  const limit = hay.length - n;
  outer:
  for (let i = 0; i <= limit; i++) {
    for (let j = 0; j < n; j++) {
      if (hay[i + j] !== needle[j]) continue outer;
    }
    return i;
  }
  return -1;
}

function extractRecentAlsFromPrefsText(txt) {
  if (!txt) return '';
  try { txt = ('' + txt).replace(/\x00/g, ''); } catch (_) {}
  const idx = ('' + txt).indexOf('RecentDocsList');
  const scope = (idx >= 0) ? txt.substring(idx, Math.min(txt.length, idx + 8192)) : txt;
  // First: try direct ASCII path in scope
  const asciiScope = scope.replace(/[^\x20-\x7E]/g, '');
  const mDir = asciiScope.match(/([A-Za-z]:[\\/](?:(?![A-Za-z]:)[^"\r\n])*?\.als)/);
  if (mDir && mDir[1]) return mDir[1].replace(/\\/g, '/');
  // Fallback: spaced-out encoding
  const re = /([A-Za-z]\s*:\s*(?:\/|\\)\s*.*?\.a\s*l\s*s)/i;
  const m = re.exec(scope);
  if (!m || !m[1]) return '';
  let s = m[1];
  const PLACE = '___SPACE___';
  s = s.replace(/\s{2,}/g, PLACE);
  s = s.replace(/\s+/g, '');
  s = s.replace(new RegExp(PLACE, 'g'), ' ');
  s = s.replace(/\\/g, '/');
  const ascii = s.replace(/[^\x20-\x7E]/g, '');
  const all = ascii.match(/([A-Za-z]:[\\/](?:(?![A-Za-z]:)[^"\r\n])*?\.als)/g);
  if (all && all.length) return all[all.length - 1];
  const m2 = ascii.match(/([A-Za-z]:[\\/](?:(?![A-Za-z]:)[^"\r\n])*?\.als)/);
  if (m2 && m2[1]) return m2[1];
  return s;
}

function findPreferencesCfg() {
  if (process.argv[2]) {
    return path.resolve(process.argv[2]);
  }
  const appdata = process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming');
  const abletonRoot = path.join(appdata, 'Ableton');
  if (!fs.existsSync(abletonRoot)) throw new Error('Ableton prefs root not found: ' + abletonRoot);
  const entries = fs.readdirSync(abletonRoot, { withFileTypes: true })
    .filter(d => d.isDirectory() && d.name.startsWith('Live '))
    .map(d => d.name)
    .sort((a, b) => {
      // naive version compare by numeric segments
      const pa = a.replace(/^Live\s+/, '').split('.').map(n => parseInt(n, 10) || 0);
      const pb = b.replace(/^Live\s+/, '').split('.').map(n => parseInt(n, 10) || 0);
      const len = Math.max(pa.length, pb.length);
      for (let i = 0; i < len; i++) {
        const va = (i < pa.length ? pa[i] : 0);
        const vb = (i < pb.length ? pb[i] : 0);
        if (va !== vb) return va - vb;
      }
      return 0;
    });
  if (!entries.length) throw new Error('No Live */ folders under ' + abletonRoot);
  const latest = entries[entries.length - 1];
  const prefsPath = path.join(abletonRoot, latest, 'Preferences', 'Preferences.cfg');
  return prefsPath;
}

(function main(){
  try {
    const prefsPath = findPreferencesCfg();
    console.log('Using Preferences.cfg:', prefsPath);
    if (!fs.existsSync(prefsPath)) {
      console.error('Preferences.cfg not found.');
      process.exit(2);
    }
    const buf = readBuffer(prefsPath);
    const txt = decodeSmart(buf);
    const found = extractRecentAlsFromPrefsText(txt);
    const hasRecentRaw = (txt.indexOf('RecentDocsList') >= 0);
    const asciiTxt = txt.replace(/[^\x20-\x7E]/g, '');
    const hasRecentAscii = (asciiTxt.indexOf('RecentDocsList') >= 0);
    const hasRecentBytes = headerPresentInBuffer(buf);
    console.log('RecentDocsList present (raw):', hasRecentRaw, '| (printable-only):', hasRecentAscii, '| (byte-scan):', hasRecentBytes);
    if (found) {
      console.log('EXTRACTED:', found);
      process.exit(0);
    } else {
      console.log('EXTRACTED: <empty>');
      // Print a short excerpt for debugging
      const iRaw = txt.indexOf('RecentDocsList');
      const iAscii = asciiTxt.indexOf('RecentDocsList');
      const sliceRaw = (iRaw >= 0) ? txt.substring(iRaw, Math.min(txt.length, iRaw + 2000)) : txt.substring(0, Math.min(2000, txt.length));
      const sliceAscii = (iAscii >= 0) ? asciiTxt.substring(iAscii, Math.min(asciiTxt.length, iAscii + 2000)) : asciiTxt.substring(0, Math.min(2000, asciiTxt.length));
      console.log('SAMPLE raw (first 2KB from RecentDocsList region):');
      console.log(sliceRaw);
      console.log('SAMPLE printable-only (first 2KB from RecentDocsList region):');
      console.log(sliceAscii);
      process.exit(1);
    }
  } catch (e) {
    console.error('Tester error:', e && e.message ? e.message : e);
    process.exit(3);
  }
})();
