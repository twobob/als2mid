const fs = require('fs');
const path = require('path');

/**
 * Finds the full path to Log.txt in the Ableton Live preferences folder,
 * regardless of the specific Live version number (e.g., Live 11.3.21).
 *
 * @returns {string | null} The full path to Log.txt, or null if not found.
 */
function findAbletonLogPath() {
    // 1. Determine the base AppData\Roaming path
    const appData = process.env.APPDATA || path.join(process.env.USERPROFILE, 'AppData', 'Roaming');
    const abletonRoamingPath = path.join(appData, 'Ableton');

    // 2. Check if the 'Ableton' folder exists
    if (!fs.existsSync(abletonRoamingPath)) {
        console.error(`Error: Ableton Roaming path not found at ${abletonRoamingPath}`);
        return null;
    }

    // 3. Find the Live version directory (e.g., 'Live 11.3.21')
    let liveVersionDir = null;
    try {
        const abletonContents = fs.readdirSync(abletonRoamingPath);
        
        // Regex to match a directory name starting with "Live " (case-insensitive)
        const liveDirPattern = /^Live\s+/i;

        for (const dirName of abletonContents) {
            const fullPath = path.join(abletonRoamingPath, dirName);
            
            // Check if it's a directory and matches the "Live " pattern
            try {
                const stats = fs.statSync(fullPath);
                if (stats.isDirectory() && liveDirPattern.test(dirName)) {
                    liveVersionDir = dirName;
                    break; // Assuming there is only one relevant Live installation
                }
            } catch (statError) {
                // Ignore errors like permission issues
                continue;
            }
        }

    } catch (e) {
        console.error("Error reading Ableton directory contents:", e.message);
        return null;
    }

    // 4. Construct the final log path
    if (liveVersionDir) {
        const logPath = path.join(
            abletonRoamingPath,
            liveVersionDir,
            'Preferences',
            'Log.txt'
        );
        return logPath;
    } else {
        return null;
    }
}

// --- LOGIC FUNCTIONS FROM THE USER'S SCRIPT ---

function extractLatestAlsFromLog(txt) {
    if (!txt) return "";
    
    var candidate = "";
    var lines = ("" + txt).split(/\r?\n/);
    
    for (var i = lines.length - 1; i >= 0; i--) {
        var line = lines[i];
        if (!line) continue;
        
        // Try quoted path first: "C:\path\to\file.als"
        var m = line.match(/"([A-Za-z]:[^"]*\.als)"/i);
        if (m && m[1]) {
            candidate = m[1].replace(/\\/g, "/");
            break;
        }
        
        // Try file:/// URL: file:///C:/path/to/file.als
        var m2 = line.match(/file:\/\/\/([A-Za-z]:[^\s"]*\.als)/i);
        if (m2 && m2[1]) {
            try {
                candidate = decodeURIComponent(m2[1]).replace(/\\/g, "/");
            } catch (e) {
                candidate = m2[1].replace(/%20/g, ' ').replace(/\\/g, "/");
            }
            break;
        }
        
        // Try file:/// with encoded path: file:///C:/path%20with%20spaces/file.als
        var m3 = line.match(/file:\/\/\/([^\s"]*\.als)/i);
        if (m3 && m3[1]) {
            try {
                candidate = decodeURIComponent(m3[1]).replace(/\\/g, "/");
            } catch (e) {
                candidate = m3[1].replace(/%20/g, ' ').replace(/\\/g, "/");
            }
            break;
        }
    }
    
    return candidate;
}

function containsDefaultTemplateReference(txt) {
    if (!txt) return false;
    // Detect Ableton's default template path in log (Windows/Mac), case-insensitive
    // e.g., .../Resources/Builtin/Templates/DefaultLiveSet.als
    var re = /(?:^|.)builtin[\/\\]+templates[\/\\]+DefaultLiveSet\.als/i;
    return re.test(txt);
}

function lastIndexOfDefaultTemplateRef(txt) {
    if (!txt) return -1;
    var norm = ("" + txt).toLowerCase().replace(/\\/g, "/");
    return norm.lastIndexOf("builtin/templates/defaultliveset.als");
}

function lastIndexOfEndSavePrefsMarker(txt) {
    if (!txt) return -1;
    // Find the last occurrence of variants like: "Default App: End SavePrefs" or "Default App - End SavePrefs"
    try {
        var re = /default\s*app\s*[:\-]?\s*end\s+saveprefs/gi;
        var m, last = -1;
        while ((m = re.exec(txt)) !== null) {
            last = m.index;
        }
        if (last >= 0) return last;
    } catch (e) {}
    // Fallback: if specific phrasing not present, fall back to the simpler token to avoid false negatives
    var lower = ("" + txt).toLowerCase();
    return lower.lastIndexOf("end saveprefs");
}

// --- EXECUTION ---

const logPath = findAbletonLogPath();

if (!logPath) {
    console.error('ERROR: Could not find Log.txt path for any Ableton Live version.');
    process.exit(1);
}

console.log('Reading Log.txt from (Version-Agnostic Path):', logPath);

if (!fs.existsSync(logPath)) {
    console.error('ERROR: Log.txt not found at:', logPath);
    process.exit(1);
}

const logContent = fs.readFileSync(logPath, 'utf8');
const lines = logContent.split(/\r?\n/);
// Use the last 800 lines as specified in the test script
const tail800 = lines.slice(-800).join('\n');

console.log('\n=== LOG TAIL (last 800 lines, ' + tail800.length + ' bytes) ===\n');

// --- RUN THE STATE MACHINE ---

const fromLog = extractLatestAlsFromLog(tail800);
const idxDefault = lastIndexOfDefaultTemplateRef(tail800);
const idxSave = lastIndexOfEndSavePrefsMarker(tail800);
const hasDefault = containsDefaultTemplateReference(tail800);
const hasDefaultInLog = fromLog ? containsDefaultTemplateReference(fromLog) : false;

console.log('=== EXTRACTED VALUES ===');
console.log('fromLog:', fromLog || '(none)');
console.log('idxDefault:', idxDefault);
console.log('idxSave:', idxSave);
console.log('hasDefault (entire tail):', hasDefault);
console.log('hasDefaultInLog (fromLog path):', hasDefaultInLog);
console.log('isTempProject:', fromLog ? (fromLog.indexOf('Ableton Live Temporary Project') !== -1) : false);

console.log('\n=== STATE MACHINE DECISION (EXACT DEVICE LOGIC) ===');

// EXACT logic from getProjectPath() quick check (lines 424-434)
if (idxDefault >= 0 && !(idxSave > idxDefault)) {
    console.log('✗ CHECK 1 TRIGGERED: idxDefault >= 0 && !(idxSave > idxDefault)');
    console.log('   → outlet(0, "set", "SAVE YOUR PROJECT FIRST (default template not saved)")');
    console.log('   → return ""');
    // process.exit(0); // Commented out to allow full execution of the test script
}
if (fromLog && containsDefaultTemplateReference(fromLog) && !(idxSave >= 0)) {
    console.log('✗ CHECK 2 TRIGGERED: fromLog contains default && !(idxSave >= 0)');
    console.log('   → outlet(0, "set", "SAVE YOUR PROJECT FIRST (default template not saved)")');
    console.log('   → return ""');
    // process.exit(0);
}
if (fromLog && fromLog.indexOf("Ableton Live Temporary Project") !== -1 && !(idxSave >= 0)) {
    console.log('✗ CHECK 3 TRIGGERED: fromLog is temp && !(idxSave >= 0)');
    console.log('   → outlet(0, "set", "SAVE YOUR PROJECT FIRST")');
    console.log('   → return ""');
    // process.exit(0);
}

console.log('⚠️  NONE OF THE QUICK CHECKS TRIGGERED!');
console.log('   Device would proceed to create helper script...');
console.log('\n=== WHY DID CHECKS FAIL? ===');
console.log('Check 1: idxDefault=' + idxDefault + ', idxSave=' + idxSave + ', condition=' + (idxDefault >= 0 && !(idxSave > idxDefault)));
console.log('Check 2: hasFromLog=' + !!fromLog + ', hasDefaultInFromLog=' + hasDefaultInLog + ', noSave=' + !(idxSave >= 0) + ', condition=' + (fromLog && containsDefaultTemplateReference(fromLog) && !(idxSave >= 0)));
console.log('Check 3: hasFromLog=' + !!fromLog + ', isTemp=' + (fromLog ? (fromLog.indexOf('Ableton Live Temporary Project') !== -1) : false) + ', noSave=' + !(idxSave >= 0) + ', condition=' + (fromLog && fromLog.indexOf("Ableton Live Temporary Project") !== -1 && !(idxSave >= 0)));

console.log('\n=== OLD STATE MACHINE DECISION (FOR REFERENCE) ===');

// Branch 1: default template in log with order check
if (idxDefault >= 0) {
    if (idxSave > idxDefault) {
        console.log('✓ Branch 1: Default template found, SavePrefs AFTER default → USE MRU from Preferences.cfg');
    } else {
        console.log('✗ Branch 1: Default template found, NO SavePrefs after it → SAVE YOUR PROJECT FIRST');
        console.log('   EXPECTED OUTPUT: "SAVE YOUR PROJECT FIRST (default template not saved)"');
    }
} else {
    console.log('  Branch 1: No default template index found in tail (idxDefault=-1)');
    
    // Branch 2: concrete non-temp, non-default path
    if (fromLog && fromLog.indexOf("Ableton Live Temporary Project") === -1 && !containsDefaultTemplateReference(fromLog)) {
        console.log('✓ Branch 2: Concrete non-temp, non-default path → READY (log)');
        console.log('   EXPECTED OUTPUT: "Ready: ' + fromLog.split('/').pop() + '"');
    } else if (fromLog && fromLog.indexOf("Ableton Live Temporary Project") === -1 && containsDefaultTemplateReference(fromLog)) {
        console.log('✗ Branch 2 REJECTED: fromLog contains default template reference');
        console.log('   Should fall through to check SavePrefs or require save...');
    } else if (fromLog && fromLog.indexOf("Ableton Live Temporary Project") !== -1) {
        console.log('  Branch 2 SKIPPED: fromLog is temp project');
    } else {
        console.log('  Branch 2 SKIPPED: No fromLog');
    }
    
    // Branch 3: temp OR default with SavePrefs → use MRU
    if (fromLog && (fromLog.indexOf("Ableton Live Temporary Project") !== -1 || containsDefaultTemplateReference(fromLog)) && idxSave >= 0) {
        console.log('✓ Branch 3: Temp/default path + SavePrefs found → USE MRU from Preferences.cfg');
    } else {
        console.log('  Branch 3 SKIPPED: No (temp/default + SavePrefs) match');
    }
    
    // Branch 4: no explicit path but SavePrefs → use MRU
    if (!fromLog && idxSave >= 0) {
        console.log('✓ Branch 4: No path but SavePrefs → USE MRU from Preferences.cfg');
    } else {
        console.log('  Branch 4 SKIPPED: fromLog exists or no SavePrefs');
    }
    
    // Branch 5: temp OR default without SavePrefs → require save
    if (fromLog && (fromLog.indexOf("Ableton Live Temporary Project") !== -1 || containsDefaultTemplateReference(fromLog)) && !(idxSave >= 0)) {
        console.log('✗ Branch 5: Temp/default path WITHOUT SavePrefs → SAVE YOUR PROJECT FIRST');
        console.log('   EXPECTED OUTPUT: "SAVE YOUR PROJECT FIRST"');
    } else {
        console.log('  Branch 5 SKIPPED: No unsaved temp/default match');
    }
    
    // Belt-and-suspenders: fromLog has default but no SavePrefs
    if (fromLog && containsDefaultTemplateReference(fromLog) && !(idxSave >= 0)) {
        console.log('✗ FINAL GUARD: fromLog contains default, no SavePrefs → SAVE YOUR PROJECT FIRST');
        console.log('   EXPECTED OUTPUT: "SAVE YOUR PROJECT FIRST (default template not saved)"');
    }
}

console.log('\n=== SEARCH FOR KEY MARKERS IN TAIL ===');

// Show occurrences of DefaultLiveSet
const defaultMatches = tail800.match(/builtin[\/\\]+templates[\/\\]+DefaultLiveSet\.als/gi) || [];
console.log('DefaultLiveSet occurrences:', defaultMatches.length);
if (defaultMatches.length > 0) {
    console.log('  Sample:', defaultMatches[defaultMatches.length - 1]);
}

// Show occurrences of End SavePrefs
const saveMatches = tail800.match(/Default\s*App\s*[:\-]?\s*End\s+SavePrefs/gi) || [];
console.log('End SavePrefs occurrences:', saveMatches.length);
if (saveMatches.length > 0) {
    console.log('  Sample:', saveMatches[saveMatches.length - 1]);
}

// Show last 5 .als references
const alsMatches = tail800.match(/(?:file:\/\/\/|")([^"\n\r]*\.als)/g) || [];
console.log('\nLast 5 .als references in tail:');
alsMatches.slice(-5).forEach((m, i) => {
    console.log('  ' + (i + 1) + ':', m.substring(0, 100));
});

console.log('\n=== CONCLUSION ===');
if (idxDefault >= 0 && !(idxSave > idxDefault)) {
    console.log('❌ UNSAVED DEFAULT DETECTED → Should show "SAVE YOUR PROJECT FIRST"');
} else if (fromLog && containsDefaultTemplateReference(fromLog) && !(idxSave >= 0)) {
    console.log('❌ UNSAVED DEFAULT DETECTED (via fromLog) → Should show "SAVE YOUR PROJECT FIRST"');
} else if (idxDefault >= 0 && idxSave > idxDefault) {
    console.log('✅ SAVED DEFAULT → Should show "Ready (prefs)" with MRU path');
} else if (fromLog && fromLog.indexOf("Ableton Live Temporary Project") === -1 && !containsDefaultTemplateReference(fromLog)) {
    console.log('✅ SAVED PROJECT → Should show "Ready (log): ' + fromLog.split('/').pop() + '"');
} else {
    console.log('⚠️  UNCLEAR STATE → May show "Project file not found"');
}