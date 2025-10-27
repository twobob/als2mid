autowatch = 1;
inlets = 2;
outlets = 1;

var DEBUG = false;
var DEBUG_LOGGING = false;  // Set to true to enable detailed logging
var ONLY_TEST_SAVE_REQUIRED = false;  // Set to true to ONLY check if save is required, skip all other logic
var TEST_SAVED_AFTER_DEFAULT = false; // Set to true to test "saved after default template" logic only
var projectPath = "";
var exportFolder = "";
var liveApp = null;
var logReadAttempts = 0;

function debug(msg) {
    post(msg + "\n");
    if (DEBUG) outlet(0, "set", "DEBUG: " + msg);
}

function loadbang() {
    if (ONLY_TEST_SAVE_REQUIRED) {
        outlet(0, "set", "Test mode: Trigger device to test");
        return;
    }
    if (TEST_SAVED_AFTER_DEFAULT) {
        outlet(0, "set", "Test mode (saved): Trigger to test");
        return;
    }
    outlet(0, "set", "Click button to export →");
    var task = new Task(getProjectPath, this);
    task.schedule(500);
}

function anything() {
    var msg = messagename || "";
    if (inlet === 1 && typeof msg === "string" && msg.indexOf(".als") !== -1) {
        projectPath = msg;
        var lastSlash = Math.max(projectPath.lastIndexOf("/"), projectPath.lastIndexOf("\\"));
        exportFolder = (lastSlash >= 0) ? projectPath.substring(0, lastSlash) : "";
        outlet(0, "set", "Ready: " + projectPath.substring(lastSlash + 1));
        return;
    }
    initLiveAPI();
}

function initLiveAPI() {
    if (ONLY_TEST_SAVE_REQUIRED) {
        if (DEBUG_LOGGING) post("als2mid: ONLY_TEST_SAVE_REQUIRED - initLiveAPI disabled\n");
        return;
    }
    if (TEST_SAVED_AFTER_DEFAULT) {
        if (DEBUG_LOGGING) post("als2mid: TEST_SAVED_AFTER_DEFAULT - initLiveAPI disabled\n");
        return;
    }
    if (liveApp) return;
    try {
        liveApp = new LiveAPI("live_set");
        getProjectPath();
    } catch(e) {
        outlet(0, "set", "Error initializing: " + e);
    }
}

function normalizePath(p) {
    if (!p) return "";
    return ("" + p).replace(/\\\\/g, "/");
}

function getTempDir() {
    var os = max && max.os ? max.os : "";
    if (os === "windows") {
        var home = getUserHomeFromDevicePath();
        return home ? (home + "/AppData/Local/Temp") : "C:/Windows/Temp";
    }
    return "/tmp";
}

function writeTextFile(path, text) {
    try {
        var f = new File(path, "write");
        f.open();
        if (f.isopen) {
            f.writestring(text);
            f.close();
        }
    } catch (e) {}
}

function writeStatus(msg) {
    var p = getTempDir() + "/als2mid_status.txt";
    writeTextFile(p, msg);
}

function folderExists(path) {
    try {
        var f = new Folder(path);
        var atEnd = f.end;
        f.close();
        return atEnd === false;
    } catch (e) {
        return false;
    }
}

function isLiveSetUnsaved() {
    var devicePath = normalizePath(this.patcher.filepath || "");
    if (!devicePath) return true;
    
    if (devicePath.indexOf("Ableton Live Temporary Project") !== -1) return true;
    
    return false;
}

function findProjectRootFromDevice() {
    var devicePath = normalizePath(this.patcher.filepath);
    if (!devicePath) return "";
    
    var baseDir = devicePath.substring(0, Math.max(devicePath.lastIndexOf("/"), 0));
    var dir = baseDir;
    
    for (var i = 0; i < 10 && dir.length > 1; i++) {
        var probe = dir + "/Ableton Project Info";
        if (folderExists(probe)) return dir;
        
        var nextSlash = dir.lastIndexOf("/");
        if (nextSlash <= 0) break;
        dir = dir.substring(0, nextSlash);
    }
    
    try {
        var queue = [{p: baseDir, d: 0}];
        var seen = {};
        var maxDepth = 3;
        
        while (queue.length) {
            var node = queue.shift();
            var cur = node.p;
            var depth = node.d;
            
            if (seen[cur]) continue;
            seen[cur] = true;
            
            var f = new Folder(cur);
            while (!f.end) {
                var name = f.filename;
                if (name && name.indexOf(".") === -1 && name.length > 0) {
                    var full = cur + "/" + name;
                    if (name === "Ableton Project Info") {
                        f.close();
                        return cur;
                    }
                    if (depth < maxDepth) queue.push({p: full, d: depth + 1});
                }
                f.next();
            }
            f.close();
        }
    } catch (e) {}
    
    return "";
}

function findAlsRecursively(root, targetName) {
    try {
        var stack = [root];
        var safety = 0;
        while (stack.length && safety++ < 5000) {
            var current = stack.pop();
            var f = new Folder(current);
            while (!f.end) {
                var name = f.filename;
                var isdir = f.isdir;
                var full = current + "/" + name;
                
                if (isdir) {
                    if (name !== "." && name !== ".." && name !== "Ableton Project Info") stack.push(full);
                } else {
                    if (name && name.length > 4) {
                        var ext = name.substring(name.length - 4).toLowerCase();
                        if (ext === ".als") {
                            if (!targetName || name.toLowerCase() === targetName.toLowerCase()) {
                                f.close();
                                return full;
                            }
                        }
                    }
                }
                f.next();
            }
            f.close();
        }
    } catch (e) {}
    return "";
}

function findAlsInRoot(root) {
    try {
        var found = [];
        var f = new Folder(root);
        while (!f.end) {
            var name = f.filename;
            if (!f.isdir && name && name.length > 4) {
                var ext = name.substring(name.length - 4).toLowerCase();
                if (ext === ".als") found.push(name);
            }
            f.next();
        }
        f.close();
        
        for (var i = 0; i < found.length; i++) {
            if (found[i].indexOf("[") === -1) return root + "/" + found[i];
        }
        
        return found.length ? root + "/" + found[0] : "";
    } catch (e) {
        return "";
    }
}

function getUserHomeFromDevicePath() {
    var p = normalizePath(this.patcher.filepath || "");
    var m = p.match(/^([A-Za-z]:\/Users\/[^\/\\]+)/);
    if (m && m[1]) return m[1].replace(/\\/g, "/");
    
    var m2 = p.match(/^(\/Users\/[^\/]+)/);
    if (m2 && m2[1]) return m2[1];
    
    return "";
}

function getAbletonPrefsRoot() {
    var os = max && max.os ? max.os : "";
    if (os === "macintosh") return "~/Library/Preferences/Ableton";
    else if (os === "windows") {
        var home = getUserHomeFromDevicePath();
        if (!home) return "";
        return home + "/AppData/Roaming/Ableton";
    }
    return "";
}

function parseVersion(v) {
    var parts = (v || "").split(".");
    var out = [];
    for (var i = 0; i < parts.length; i++) {
        var n = parseInt(parts[i], 10);
        out.push(isNaN(n) ? 0 : n);
    }
    return out;
}

function cmpVersions(a, b) {
    var pa = parseVersion(a), pb = parseVersion(b);
    var len = Math.max(pa.length, pb.length);
    for (var i = 0; i < len; i++) {
        var va = (i < pa.length) ? pa[i] : 0;
        var vb = (i < pb.length) ? pb[i] : 0;
        if (va !== vb) return va - vb;
    }
    return 0;
}

function getLatestLiveLogPath() {
    var root = getAbletonPrefsRoot();
    if (!root) return "";
    
    try {
        var candidates = [];
        var f = new Folder(root);
        while (!f.end) {
            var name = f.filename;
            if (name && name.indexOf("Live ") === 0) {
                var ver = name.substring(5).trim();
                candidates.push({
                    ver: ver,
                    dir: root + "/" + name
                });
            }
            f.next();
        }
        f.close();
        
        if (!candidates.length) return "";
        
        candidates.sort(function(x, y){
            return cmpVersions(x.ver, y.ver);
        });
        
        return candidates[candidates.length - 1].dir + "/Preferences/Log.txt";
    } catch (e) {}
    return "";
}

function readAllText(path) {
    var data = "";
    try {
        var f = new File(path, "read");
        f.open();
        if (f.isopen) {
            // Read entire file at once, let it fail if there's bad UTF-8
            // We'll handle the error at a higher level
            while (f.position < f.eof) {
                data += f.readstring(f.eof - f.position);
            }
            f.close();
        }
    } catch (e) {
        // On UTF-8 error, return whatever we got
        try { f.close(); } catch (e2) {}
    }
    return data;
}

function uriDecodeSafe(s) {
    try {
        return decodeURIComponent(s);
    } catch (e) {
        return s.replace(/%20/g, ' ');
    }
}

function detectDefaultLiveSet(txt) {
    if (!txt) {
        if (DEBUG_LOGGING) post("als2mid: detectDefaultLiveSet - txt is empty or null\n");
        return false;
    }
    
    var lines = ("" + txt).split(/\r?\n/);
    if (DEBUG_LOGGING) post("als2mid: detectDefaultLiveSet - scanning " + lines.length + " lines (already reversed)\n");
    
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if (!line || line.indexOf(".als") === -1) continue;
        
        if (DEBUG_LOGGING) post("als2mid: First .als line (most recent): " + line + "\n");
        var lowerLine = line.toLowerCase();
        var hasDefault = lowerLine.indexOf("defaultliveset") !== -1;
        if (DEBUG_LOGGING) post("als2mid: Contains 'defaultliveset': " + hasDefault + "\n");
        
        if (hasDefault) {
            if (DEBUG_LOGGING) post("als2mid: DefaultLiveSet found at position " + i + ", checking for SavePrefs before it\n");
            for (var j = 0; j < i; j++) {
                var prevLine = lines[j];
                if (!prevLine) continue;
                var prevLower = prevLine.toLowerCase();
                if (prevLower.indexOf("saveprefs") !== -1) {
                    if (DEBUG_LOGGING) post("als2mid: SavePrefs found at position " + j + " (after DefaultLiveSet chronologically)\n");
                    return false;
                }
            }
            if (DEBUG_LOGGING) post("als2mid: No SavePrefs found after DefaultLiveSet - UNSAVED\n");
            return true;
        }
        
        // First .als is NOT DefaultLiveSet
        return false;
    }
    
    if (DEBUG_LOGGING) post("als2mid: No .als found in log\n");
    return false;
}

function extractLatestAlsFromLog(txt) {
    if (!txt) return "";
    
    var candidate = "";
    var lines = ("" + txt).split(/\r?\n/);
    
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if (!line) continue;
        
        var m = line.match(/"([A-Za-z]:[^"]*\.als)"/i);
        if (m && m[1]) {
            candidate = m[1].replace(/\\/g, "/");
            break;
        }
        
        var m2 = line.match(/file:\/\/\/([A-Za-z]:[^\s"]*\.als)/i);
        if (m2 && m2[1]) {
            candidate = uriDecodeSafe(m2[1]).replace(/\\/g, "/");
            break;
        }
        
        var m3 = line.match(/file:\/\/\/([^\s"]*\.als)/i);
        if (m3 && m3[1]) {
            candidate = uriDecodeSafe(m3[1]).replace(/\\/g, "/");
            break;
        }
    }
    
    return candidate;
}

function containsDefaultTemplateReference(txt) {
    if (!txt) return false;
    var re = /(?:^|.)builtin[\/\\]+templates[\/\\]+DefaultLiveSet\.als/i;
    return re.test(txt);
}

function hasEndSavePrefs(txt) {
    if (!txt) return false;
    return /Default\s*App\s*[:\-]?\s*End\s+SavePrefs/i.test(txt);
}

function extractRecentAlsFromPrefsText(txt) {
    if (!txt) return "";
    try { txt = ("" + txt).replace(/\x00/g, ""); } catch (e) {};
    var raw = "" + txt;
    var idxRaw = raw.indexOf("RecentDocsList");
    var asciiTxt = raw.replace(/[^\x20-\x7E]/g, "");
    var idxAscii = (idxRaw < 0) ? asciiTxt.indexOf("RecentDocsList") : -1;
    var scope;
    if (idxRaw >= 0) {
        scope = raw.substring(idxRaw, Math.min(raw.length, idxRaw + 8192));
    } else if (idxAscii >= 0) {
        scope = asciiTxt.substring(idxAscii, Math.min(asciiTxt.length, idxAscii + 8192));
    } else {
        scope = raw;
    }
    try {
        var frRe = new RegExp('F[^\\x20-\\x7E]*i[^\\x20-\\x7E]*l[^\\x20-\\x7E]*e[^\\x20-\\x7E]*R[^\\x20-\\x7E]*e[^\\x20-\\x7E]*f');
        var frMatch = frRe.exec(scope);
        if (frMatch && typeof frMatch.index === 'number') {
            var start = frMatch.index;
            scope = scope.substring(start, Math.min(scope.length, start + 4096));
        }
    } catch (e) {}
    var asciiScope = scope.replace(/[^\x20-\x7E]/g, "");
    var mDir = asciiScope.match(/([A-Za-z]:[\\\/](?:(?![A-Za-z]:)[^"\r\n])*?\.als)/);
    if (mDir && mDir[1]) return mDir[1].replace(/\\/g, "/");
    var re = /([A-Za-z]\s*:\s*(?:\/|\\)\s*.*?\.a\s*l\s*s)/i;
    var m = re.exec(scope);
    if (!m || !m[1]) return "";
    var s = m[1];
    var PLACE = "___SPACE___";
    s = s.replace(/\s{2,}/g, PLACE);
    s = s.replace(/\s+/g, "");
    s = s.replace(new RegExp(PLACE, 'g'), " ");
    s = s.replace(/\\/g, "/");
    var ascii = s.replace(/[^\x20-\x7E]/g, "");
    var all = ascii.match(/([A-Za-z]:[\\\/](?:(?![A-Za-z]:)[^"\r\n])*?\.als)/g);
    if (all && all.length) return all[all.length - 1];
    var m2 = ascii.match(/([A-Za-z]:[\\\/](?:(?![A-Za-z]:)[^"\r\n])*?\.als)/);
    if (m2 && m2[1]) return m2[1];
    return s;
}

function getProjectPath() {
    var unsavedByDevice = isLiveSetUnsaved();
    
    if (DEBUG_LOGGING) post("Searching for Live project file...\n");
    outlet(0, "set", "Searching for project file...");
    
    var logPath = getLatestLiveLogPath();
    if (logPath) {
        var os = max && max.os ? max.os : "";
        if (os === "windows") {
            var home = getUserHomeFromDevicePath();
            if (home) {
                var tempDir = home + "/AppData/Local/Temp";
                var outputFile = tempDir + "/als2mid_logread.txt";
                var mruFile = tempDir + "/als2mid_MRU.txt";
                var helperScript = tempDir + "/als2mid_readlog.bat";
                
                var doneFile = tempDir + "/als2mid_logread_done.txt";
                
                var scriptContent = '@echo off\n';
                scriptContent += 'set "LOG=' + logPath.replace(/\//g, "\\") + '"\n';
                var prefsPath = logPath.replace(/Log\.txt$/, "Preferences.cfg");
                scriptContent += 'set "PREF=' + prefsPath.replace(/\//g, "\\") + '"\n';
                scriptContent += 'set "OUT=' + outputFile.replace(/\//g, "\\") + '"\n';
                scriptContent += 'set "MRU=' + mruFile.replace(/\//g, "\\") + '"\n';
                scriptContent += 'set "DONE=' + doneFile.replace(/\//g, "\\") + '"\n';
                scriptContent += 'del "%OUT%" 2>nul\n';
                scriptContent += 'del "%MRU%" 2>nul\n';
                scriptContent += 'del "%DONE%" 2>nul\n';
                scriptContent += "powershell -NoProfile -ExecutionPolicy Bypass -Command \"$lines = Get-Content -Tail 500 -Path '%LOG%' -Encoding UTF8; [array]::Reverse($lines); $lines | ForEach-Object { [Text.Encoding]::ASCII.GetString([Text.Encoding]::ASCII.GetBytes($_)) }\" > \"%OUT%\" 2>nul\n";
                scriptContent += "powershell -NoProfile -ExecutionPolicy Bypass -Command \"$raw = Get-Content -Raw '%PREF%'; $raw = $raw -replace '\\x00',''; $idx = $raw.IndexOf('RecentDocsList'); if ($idx -ge 0) { $scope = $raw.Substring($idx, [Math]::Min($raw.Length - $idx, 8192)) } else { $scope = $raw }; $ascii = $scope -replace '[^\\x20-\\x7E]',''; if ($ascii -match '([A-Za-z]:[/\\\\](?:(?![A-Za-z]:)[^\\x22\\r\\n])*?\\.als)') { Write-Output ('\\\"' + ($matches[1] -replace '\\\\','/') + '\\\"') }\" > \"%MRU%\" 2>nul\n";
                scriptContent += 'for %%A in ("%OUT%") do if %%~zA lss 1 echo ERROR:LOGREADFAILED>"%OUT%"\n';
                scriptContent += 'timeout /t 1 /nobreak >nul\n';
                scriptContent += 'echo done > "%DONE%"\n';
                
                try {
                    var sf = new File(helperScript, "write");
                    sf.open();
                    if (sf.isopen) {
                        sf.writestring(scriptContent);
                        sf.close();
                        var launchPath = helperScript.replace(/\//g, "\\");
                        max.launchbrowser(launchPath);
                        
                        logReadAttempts = 0;
                        var t = new Task(readLogResult, this, outputFile, mruFile, doneFile);
                        t.schedule(3000);
                        outlet(0, "set", "Reading project info...");
                        return projectPath;
                    }
                } catch(e) {
                    if (DEBUG_LOGGING) post("Error creating helper script: " + e + "\n");
                }
            }
        }
        
        var content = readAllText(logPath);
        if (content && content.length > 0) {
            var fromLog = extractLatestAlsFromLog(content);
            var idxDefault = lastIndexOfDefaultTemplateRef(content);
            var idxSave = lastIndexOfEndSavePrefsMarker(content);

            if (idxDefault >= 0) {
                if (idxSave > idxDefault) {
                    var prefsPath = logPath.replace(/Log\.txt$/, "Preferences.cfg");
                    var prefsTxt = readAllText(prefsPath);
                    var fromPrefs = extractRecentAlsFromPrefsText(prefsTxt);
                    if (fromPrefs) {
                        projectPath = fromPrefs;
                        var ls0 = Math.max(projectPath.lastIndexOf("/"), projectPath.lastIndexOf("\\"));
                        exportFolder = (ls0 >= 0) ? projectPath.substring(0, ls0) : "";
                        var fn0 = (ls0 >= 0) ? projectPath.substring(ls0 + 1) : projectPath;
                        outlet(0, "set", "Ready: " + fn0);
                        return projectPath;
                    }
                } else {
                    outlet(0, "set", "SAVE YOUR PROJECT FIRST (default template not saved)");
                    return "";
                }
            }

            if (fromLog && fromLog.indexOf("Ableton Live Temporary Project") === -1 && !containsDefaultTemplateReference(fromLog)) {
                projectPath = fromLog;
                var ls = Math.max(projectPath.lastIndexOf("/"), projectPath.lastIndexOf("\\"));
                exportFolder = (ls >= 0) ? projectPath.substring(0, ls) : "";
                var filename = (ls >= 0) ? projectPath.substring(ls + 1) : projectPath;
                outlet(0, "set", "Ready: " + filename);
                return projectPath;
            }

            if (fromLog && (fromLog.indexOf("Ableton Live Temporary Project") !== -1 || containsDefaultTemplateReference(fromLog)) && idxSave >= 0) {
                var prefsPath2 = logPath.replace(/Log\.txt$/, "Preferences.cfg");
                var prefsTxt2 = readAllText(prefsPath2);
                var fromPrefs2 = extractRecentAlsFromPrefsText(prefsTxt2);
                if (fromPrefs2) {
                    projectPath = fromPrefs2;
                    var ls2 = Math.max(projectPath.lastIndexOf("/"), projectPath.lastIndexOf("\\"));
                    exportFolder = (ls2 >= 0) ? projectPath.substring(0, ls2) : "";
                    var fn2 = (ls2 >= 0) ? projectPath.substring(ls2 + 1) : projectPath;
                    outlet(0, "set", "Ready: " + fn2);
                    return projectPath;
                }
            }

            if (!fromLog && idxSave >= 0) {
                var prefsPath3 = logPath.replace(/Log\.txt$/, "Preferences.cfg");
                var prefsTxt3 = readAllText(prefsPath3);
                var fromPrefs3 = extractRecentAlsFromPrefsText(prefsTxt3);
                if (fromPrefs3) {
                    projectPath = fromPrefs3;
                    var ls3 = Math.max(projectPath.lastIndexOf("/"), projectPath.lastIndexOf("\\"));
                    exportFolder = (ls3 >= 0) ? projectPath.substring(0, ls3) : "";
                    var fn3 = (ls3 >= 0) ? projectPath.substring(ls3 + 1) : projectPath;
                    outlet(0, "set", "Ready: " + fn3);
                    return projectPath;
                }
            }

            if (fromLog && (fromLog.indexOf("Ableton Live Temporary Project") !== -1 || containsDefaultTemplateReference(fromLog)) && !(idxSave >= 0)) {
                outlet(0, "set", "SAVE YOUR PROJECT FIRST");
                return "";
            }
        }
    }
    
    var projectRoot = findProjectRootFromDevice();
    if (projectRoot) {
        var rootAls = findAlsInRoot(projectRoot);
        if (rootAls) {
            projectPath = rootAls;
            var lastSlash = projectPath.lastIndexOf("/");
            exportFolder = (lastSlash >= 0) ? projectPath.substring(0, lastSlash) : projectRoot;
            outlet(0, "set", "Ready: " + projectPath.substring(lastSlash + 1));
            return projectPath;
        }
    }
    
    if (DEBUG_LOGGING) post("ERROR: Could not locate .als file\n");
    outlet(0, "set", "Project file not found");
    return "";
}

function readLogResult(outputFile, mruFile, doneFile) {
    var isReady = false;
    var content = "";
    
    try {
        var df = new File(doneFile, "read");
        df.open();
        if (df.isopen) {
            isReady = true;
            df.close();
        }
    } catch(e) {}
    
    if (!isReady) {
        logReadAttempts++;
        try {
            content = readAllText(outputFile);
        } catch(e) { content = ""; }
        if (content && content.length > 0 && logReadAttempts >= 2) {
            isReady = true;
        }
    }
    
    if (!isReady) {
        if (logReadAttempts < 10) {
            var t = new Task(readLogResult, this, outputFile, mruFile, doneFile);
            t.schedule(1000);
            return;
        } else {
            if (ONLY_TEST_SAVE_REQUIRED) {
                if (DEBUG_LOGGING) post("als2mid: ONLY_TEST_SAVE_REQUIRED - timeout, stopping\n");
                outlet(0, "set", "Test mode: Timeout");
                return;
            }
            if (DEBUG_LOGGING) post("Timeout waiting for log read\n");
            // As a last resort, try parsing whatever is in OUT before falling back
            try { content = readAllText(outputFile); } catch(e) { content = ""; }
            if (!(content && content.length > 0)) {
                // Helper failed completely; try direct log read as final attempt
                if (DEBUG_LOGGING) post("Helper output empty; trying direct log read\n");
                var logPath = getLatestLiveLogPath();
                if (logPath) {
                    content = readAllText(logPath);
                    if (!(content && content.length > 0)) {
                        useFilesystemFallback();
                        return;
                    }
                } else {
                    useFilesystemFallback();
                    return;
                }
            }
        }
    }
    
    // Ready: read content from files
    content = readAllText(outputFile);
    
    if (content && content.length > 0) {
        var isDefaultTemplate = detectDefaultLiveSet(content);
        
        if (DEBUG_LOGGING) post("als2mid: isDefaultTemplate=" + isDefaultTemplate + "\n");
        
        if (isDefaultTemplate) {
            if (DEBUG_LOGGING) post("als2mid: UNSAVED DEFAULT TEMPLATE DETECTED\n");
            outlet(0, "set", "SAVE YOUR PROJECT FIRST (default template not saved)");
            writeStatus("source=error; reason=unsavedDefaultTemplate\n");
            projectPath = "";
            return;
        }
        
        if (ONLY_TEST_SAVE_REQUIRED) {
            if (DEBUG_LOGGING) post("als2mid: ONLY_TEST_SAVE_REQUIRED is true - skipping all other logic\n");
            outlet(0, "set", "Test mode: No unsaved default detected");
            return;
        }
        
        if (TEST_SAVED_AFTER_DEFAULT) {
            if (DEBUG_LOGGING) post("als2mid: TEST_SAVED_AFTER_DEFAULT is true - DefaultLiveSet was saved, getting MRU\n");
            // Read MRU from separate file
            var mruContent = readAllText(mruFile);
            if (DEBUG_LOGGING) post("als2mid: TEST MODE - MRU file content: [" + mruContent + "]\n");
            
            try {
                var mf = new File(mruFile, "read");
                mf.open();
                if (mf.isopen) mf.close();
                mf.remove();
            } catch(e) {}
            
            var testFromPrefs = "";
            if (mruContent) {
                var tm = mruContent.trim().match(/"([A-Za-z]:[^"\r\n]*\.als)"/i);
                if (tm && tm[1]) { testFromPrefs = tm[1]; }
            }
            
            if (testFromPrefs) {
                if (DEBUG_LOGGING) post("als2mid: Test mode MRU from MRU file: " + testFromPrefs + "\n");
                outlet(0, "set", "Test mode: Saved default, using MRU");
                return;
            } else {
                if (DEBUG_LOGGING) post("als2mid: Test mode: No MRU found in MRU file\n");
                outlet(0, "set", "Test mode: No MRU found");
                return;
            }
        }
        
        // All other checks
        var fromLog = extractLatestAlsFromLog(content);
        var idxDefault = lastIndexOfDefaultTemplateRef(content);
        var idxSave = lastIndexOfEndSavePrefsMarker(content);
        
        if (DEBUG_LOGGING) post("als2mid: fromLog=" + (fromLog || "(none)") + "\n");
        if (DEBUG_LOGGING) post("als2mid: idxDefault=" + idxDefault + ", idxSave=" + idxSave + "\n");
        
        if (fromLog && fromLog.indexOf("Ableton Live Temporary Project") !== -1 && !(idxSave >= 0)) {
            if (DEBUG_LOGGING) post("als2mid: UNSAVED TEMP DETECTED\n");
            outlet(0, "set", "SAVE YOUR PROJECT FIRST");
            writeStatus("source=error; reason=unsavedTemp; fromLog=" + fromLog + "\n");
            projectPath = "";
            return;
        }
        
        if (DEBUG_LOGGING) post("als2mid: Quick checks passed, proceeding with state machine\n");
        
        var fromPrefs = "";
        var mruContent = readAllText(mruFile);
        if (mruContent) {
            var m = mruContent.trim().match(/"([A-Za-z]:[^"\r\n]*\.als)"/i);
            if (m && m[1]) { fromPrefs = m[1]; }
        }
        
        try {
            var mf = new File(mruFile, "read");
            mf.open();
            if (mf.isopen) mf.close();
            mf.remove();
        } catch(e) {}

        var savedAfterDefault = (idxDefault >= 0 && idxSave > idxDefault);
        if (DEBUG_LOGGING) post("als2mid: idxDefault=" + idxDefault + ", idxSave=" + idxSave + ", savedAfterDefault=" + savedAfterDefault + "\n");
        if (DEBUG_LOGGING && fromPrefs) post("als2mid: prefsLastLine=" + fromPrefs + "\n");
        if (DEBUG_LOGGING && fromLog) post("als2mid: logCandidate=" + fromLog + "\n");

        if (savedAfterDefault) {
            var prefsCandidate = fromPrefs;
            if (!prefsCandidate) {
                var lp = getLatestLiveLogPath();
                if (lp) {
                    var pp = lp.replace(/Log\.txt$/, "Preferences.cfg");
                    var pt = readAllText(pp);
                    prefsCandidate = extractRecentAlsFromPrefsText(pt);
                }
            }
            if (prefsCandidate) {
                projectPath = prefsCandidate.replace(/\\/g, "/");
                var lsA = Math.max(projectPath.lastIndexOf("/"), projectPath.lastIndexOf("\\"));
                exportFolder = (lsA >= 0) ? projectPath.substring(0, lsA) : "";
                var fnA = (lsA >= 0) ? projectPath.substring(lsA + 1) : projectPath;
                outlet(0, "set", "Ready (prefs): " + fnA);
                writeStatus("source=prefsMRU; path=" + projectPath + "; idxDefault=" + idxDefault + "; idxSave=" + idxSave + "; savedAfterDefault=true\n");
                return;
            }
        }

        if (fromLog && fromLog.indexOf("Ableton Live Temporary Project") === -1 && !containsDefaultTemplateReference(fromLog)) {
            projectPath = fromLog.replace(/\\/g, "/");
            var lsB = Math.max(projectPath.lastIndexOf("/"), projectPath.lastIndexOf("\\"));
            exportFolder = (lsB >= 0) ? projectPath.substring(0, lsB) : "";
            var fnB = (lsB >= 0) ? projectPath.substring(lsB + 1) : projectPath;
            outlet(0, "set", "Ready (log): " + fnB);
            writeStatus("source=log; path=" + projectPath + "; idxDefault=" + idxDefault + "; idxSave=" + idxSave + "; savedAfterDefault=" + savedAfterDefault + "\n");
            return;
        }

        if (idxSave >= 0) {
            var lp2 = getLatestLiveLogPath();
            if (lp2) {
                var pp2 = lp2.replace(/Log\.txt$/, "Preferences.cfg");
                var pt2 = readAllText(pp2);
                var pref2 = extractRecentAlsFromPrefsText(pt2);
                if (pref2) {
                    projectPath = pref2.replace(/\\/g, "/");
                    var lsC = Math.max(projectPath.lastIndexOf("/"), projectPath.lastIndexOf("\\"));
                    exportFolder = (lsC >= 0) ? projectPath.substring(0, lsC) : "";
                    var fnC = (lsC >= 0) ? projectPath.substring(lsC + 1) : projectPath;
                    outlet(0, "set", "Ready (prefs): " + fnC);
                    writeStatus("source=prefsMRU-anySave; path=" + projectPath + "; idxDefault=" + idxDefault + "; idxSave=" + idxSave + "; savedAfterDefault=" + savedAfterDefault + "\n");
                    return;
                }
            }
        }

        if (idxDefault >= 0 && !(idxSave > idxDefault)) {
            outlet(0, "set", "SAVE YOUR PROJECT FIRST (default template not saved)");
            writeStatus("source=error; reason=defaultWithoutSavePrefs; idxDefault=" + idxDefault + "; idxSave=" + idxSave + "\n");
            projectPath = "";
            return;
        }
        
        if (fromLog && containsDefaultTemplateReference(fromLog) && !(idxSave >= 0)) {
            outlet(0, "set", "SAVE YOUR PROJECT FIRST (default template not saved)");
            writeStatus("source=error; reason=defaultInLogNoSave; fromLog=" + fromLog + "; idxSave=" + idxSave + "\n");
            projectPath = "";
            return;
        }
    }
    
    if (ONLY_TEST_SAVE_REQUIRED) {
        if (DEBUG_LOGGING) post("als2mid: ONLY_TEST_SAVE_REQUIRED - log empty, stopping\n");
        outlet(0, "set", "Test mode: Log empty");
        return;
    }
    
    if (DEBUG_LOGGING) post("Log file empty or no .als found\n");
    useFilesystemFallback();
}

function useFilesystemFallback() {
    var os = max && max.os ? max.os : "";
    if (os === "windows") {
        if (DEBUG_LOGGING) post("ERROR: Could not locate .als via logs/prefs\n");
        outlet(0, "set", "Project file not found");
        writeStatus("source=error; reason=notFound-windows-noGuess\n");
        return;
    }

    var projectRoot = findProjectRootFromDevice();
    if (projectRoot) {
        var rootAls = findAlsInRoot(projectRoot);
        if (rootAls) {
            projectPath = rootAls;
            var lastSlash = projectPath.lastIndexOf("/");
            exportFolder = (lastSlash >= 0) ? projectPath.substring(0, lastSlash) : projectRoot;
            outlet(0, "set", "Ready: " + projectPath.substring(lastSlash + 1));
            return;
        }
    }

    if (DEBUG_LOGGING) post("ERROR: Could not locate .als file\n");
    outlet(0, "set", "Project file not found");
    writeStatus("source=error; reason=notFound-fallback\n");
}

function exportMidi() {
    if (ONLY_TEST_SAVE_REQUIRED) {
        if (DEBUG_LOGGING) post("als2mid: ONLY_TEST_SAVE_REQUIRED - starting test\n");
        outlet(0, "set", "Test mode: Testing detection...");
        getProjectPath();
        return;
    }
    if (TEST_SAVED_AFTER_DEFAULT) {
        if (DEBUG_LOGGING) post("als2mid: TEST_SAVED_AFTER_DEFAULT - starting test\n");
        outlet(0, "set", "Test mode (saved): Testing...");
        getProjectPath();
        return;
    }
    var alsPath = getProjectPath();
    if (!alsPath) {
        outlet(0, "set", "Reading project info...");
        var retry = new Task(waitForProjectThenExport, this, 0);
        retry.schedule(1500);
        return;
    }
    performExport(alsPath);
}

function waitForProjectThenExport(attempt) {
    if (projectPath && projectPath.length > 0) {
        performExport(projectPath);
        return;
    }
    var tries = (typeof attempt === 'number') ? attempt : 0;
    if (tries < 8) {
        var t = new Task(waitForProjectThenExport, this, tries + 1);
        t.schedule(1000);
    } else {
        outlet(0, "set", "Project file not found");
    }
}

function performExport(alsPath) {
    var baseName = alsPath.substring(
        Math.max(alsPath.lastIndexOf("/"), alsPath.lastIndexOf("\\")) + 1,
        alsPath.lastIndexOf(".als")
    );
    var outputPath = exportFolder + "/" + baseName + ".mid";
    
    var os = max && max.os ? max.os : "";
    var als2midCmd = "";
    
    if (os === "windows") {
        var devicePath = normalizePath(this.patcher.filepath);
        var deviceDir = devicePath.substring(0, Math.max(devicePath.lastIndexOf("/"), 0));
        var localExe = deviceDir + "/als2mid-console.exe";
        var exeExists = false;
        
        try {
            var testFile = new File(localExe, "read");
            testFile.open();
            if (testFile.isopen) {
                exeExists = true;
                testFile.close();
            }
        } catch (e) {}
        
        als2midCmd = exeExists ? ('"' + localExe + '"') : "als2mid-console.exe";
    } else {
        var devicePath = normalizePath(this.patcher.filepath);
        var deviceDir = devicePath.substring(0, Math.max(devicePath.lastIndexOf("/"), 0));
        var localScript = deviceDir + "/als2mid.py";
        var scriptExists = false;
        
        try {
            var testFile = new File(localScript, "read");
            testFile.open();
            if (testFile.isopen) {
                scriptExists = true;
                testFile.close();
            }
        } catch (e) {}
        
        als2midCmd = scriptExists ? ('python "' + localScript + '"') : "python als2mid.py";
    }
    
    outlet(0, "set", "Exporting " + baseName + ".mid...");
    
    var scriptExt = (os === "windows") ? ".bat" : ".sh";
    var tempDir = "/tmp";
    
    if (os === "windows") {
        var home = getUserHomeFromDevicePath();
        tempDir = home ? (home + "/AppData/Local/Temp") : "C:/Windows/Temp";
    }
    
    var tempScript = tempDir + "/als2mid_m4l_temp" + scriptExt;
    var scriptContent = "";
    
    if (os === "windows") {
        scriptContent = '@echo off\n';
        scriptContent += 'cd /d "' + exportFolder + '"\n';
        scriptContent += als2midCmd + ' "' + alsPath + '" -o "' + outputPath + '" > "' + exportFolder + '/als2mid_error.log" 2>&1\n';
        scriptContent += 'if %errorlevel% neq 0 pause\n';
        scriptContent += 'del "%~f0"\n';
    } else {
        scriptContent = '#!/bin/bash\n';
        scriptContent += 'cd "' + exportFolder + '"\n';
        scriptContent += als2midCmd + ' "' + alsPath + '" -o "' + outputPath + '" > "' + exportFolder + '/als2mid_error.log" 2>&1\n';
        scriptContent += 'if [ $? -ne 0 ]; then\n';
        scriptContent += '  read -p "Press Enter to continue..."\n';
        scriptContent += 'fi\n';
        scriptContent += 'rm "$0"\n';
    }
    
    try {
        var sf = new File(tempScript, "write");
        sf.open();
        if (sf.isopen) {
            sf.writestring(scriptContent);
            sf.close();
            max.launchbrowser(tempScript);
            
            var t = new Task(checkComplete, this, outputPath);
            t.schedule(3000);
        } else {
            outlet(0, "set", "Cannot create temp script");
        }
    } catch(e) {
        outlet(0, "set", "Script error: " + e);
    }
}

function checkComplete(midPath) {
    try {
        var f = new File(midPath, "read");
        f.open();
        if (f.isopen) {
            f.close();
            outlet(0, "set", "Export complete!");
        } else {
            var errorLogPath = exportFolder + "/als2mid_error.log";
            var errorMsg = readAllText(errorLogPath);
            
            if (errorMsg && errorMsg.length > 0) {
                var firstLine = errorMsg.split("\n")[0];
                outlet(0, "set", "ERROR: " + firstLine);
                if (DEBUG_LOGGING) post("Full error: " + errorMsg + "\n");
            } else {
                outlet(0, "set", "No MIDI file created - check als2mid_error.log");
            }
        }
    } catch (e) {
        outlet(0, "set", "Error checking output: " + e);
    }
}

function msg_int(v) {
    if (inlet === 0 && v === 1) exportMidi();
}

function bang() {
    if (inlet === 0) exportMidi();
    else if (inlet === 1) initLiveAPI();
}

// Helper: find last occurrence index of DefaultLiveSet template reference
function lastIndexOfDefaultTemplateRef(txt) {
    if (!txt) return -1;
    var norm = ("" + txt).toLowerCase().replace(/\\/g, "/");
    return norm.lastIndexOf("builtin/templates/defaultliveset.als");
}

function lastIndexOfEndSavePrefsMarker(txt) {
    if (!txt) return -1;
    try {
        var re = /default\s*app\s*[:\-]?\s*end\s+saveprefs/gi;
        var m, last = -1;
        while ((m = re.exec(txt)) !== null) {
            last = m.index;
        }
        if (last >= 0) return last;
    } catch (e) {}
    var lower = ("" + txt).toLowerCase();
    return lower.lastIndexOf("end saveprefs");
}